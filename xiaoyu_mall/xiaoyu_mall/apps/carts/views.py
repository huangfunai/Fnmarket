from django.shortcuts import render
from django.views import View
import json, logging, base64, pickle
from django.http import HttpResponseForbidden, JsonResponse
from django_redis import get_redis_connection
from xiaoyu_mall.utils.response_code import RETCODE
from django.conf import settings
from goods.models import SKU
from verifications import constants

logger = logging.getLogger('django')
from django.views import View
# Create your views here.
class CartsView(View):
	""" 购物车管理 """
	def get(self,request):
		# 判断用户是否登录
		user = request.user
		if user.is_authenticated:
			# 创建连接到 redis 的对象
			redis_conn = get_redis_connection('carts')
			# 查询user_id count sku_id  构成的购物车记录
			redis_carts = redis_conn.hgetall('carts_%s' % user.id)
			# 查询勾选商品 semembers 命令返回集合中所有的成员
			redis_selected = redis_conn.smembers('selected_%s' %  user.id)
			cart_dict = {}
			for sku_id, count in redis_carts.items():
				cart_dict[int(sku_id)] = {
					'count': int(count),
					'selected': sku_id in redis_selected,

				}
		else:
			# 用户未登录 查询 Cookie 购物车
			cart_str = request.COOKIES.get('carts')
			if cart_str:
				# 对 carts_str 进行编码 获取字节类型数据
				cart_str_bytes = cart_str.encode()
				# 对 cart_str_bytes 进行解码获取明文数据
				cart_dict_bytes = base64.b64decode(cart_str_bytes)
				# 对 cart_dict_bytes 进行反序列化 转换成 python 能识别的字典类型数据
				cart_dict = pickle.loads(cart_dict_bytes)
			else:
				cart_dict = {}
		# 构造响应数据
		sku_ids = cart_dict.keys()
		# 一次性查询出所有的 skus
		skus = SKU.objects.filter(id__in=sku_ids)
		cart_skus = []
		for sku in skus:
			cart_skus.append({
				'id': sku.id,
				'count': cart_dict.get(sku.id).get('count'),
				# 将 True, 转 ‘True’ 方便 json 解析
				'selected': str(cart_dict.get(sku.id).get('selected')),
				'name': sku.name,
				'default_image_url': str(settings.STATIC_URL) + 'images/goods' + str(sku.default_image.url) + '.jpg',
				'price': str(sku.price),
				'amount': str(sku.price * cart_dict.get(sku.id).get('count')),
				'stock': sku.stock,

			})
		context = {
			'cart_skus': cart_skus,

		}
		# 渲染购物车页面
		return render(request, 'cart.html', context)

	def post(self, request):
		# 接收参数
		json_dict = json.loads(request.body.decode())
		sku_id = json_dict.get('sku_id')
		count = json_dict.get('count')
		selected = json_dict.get('selected', True)
		# 校验参数
		if not all([sku_id, count]):
			print(' 缺少必传参数 ')
			return HttpResponseForbidden(' 缺少必传参数 ')
		# 校验 sku_id 是否合法
		try:
			SKU.objects.get(id=sku_id)
		except SKU.DoesNotExist:
			print(' 参数 sku_id 有误 ')
			return HttpResponseForbidden(' 参数 sku_id 有误 ')
		# 校验 count 是否为数字
		try:
			count = int(count)
		except Exception as e:
			print(' 参数 count 有误 ')
			return HttpResponseForbidden(' 参数 count 有误 ')
		# 判断用户是否登录
		user = request.user
		if user.is_authenticated:
			# 如果已经登录 操作 redis 购物车
			redis_conn = get_redis_connection('carts')
			pl = redis_conn.pipeline()
			# 需要以增量计算的形式保存商品数据
			pl.hincrby('carts_%s' % user.id, sku_id, count)
			# 保存商品勾选状态
			if selected:
				pl.sadd('selected_%s' % user.id, sku_id)
			pl.execute()
			# 响应结果
			return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
		else:
			# 若用户未登录, 操作 Cookie 购物车
			cart_str = request.COOKIES.get('carts')
			# 若 Cookies 中有数据 则转换成 python 能识别的字典类型数据
			if cart_str:
				# 对字符串类型的 carts_str 进行编码 读取字节类型数据
				cart_str_bytes = cart_str.encode()
				# 对密文形式的carts_str_bytes进行解码 变成明文
				cart_dict_bytes = base64.b64decode(cart_str_bytes)
				# 对 cart_dict_bytes 反序列化 获取 python 能识别的字典类型的数据
				cart_dict = pickle.loads(cart_dict_bytes)
			# 若 Cookies 中没有数据 创建一个空字典
			else:
				cart_dict = {}
			# 判断当前要添加的商品在 cart_dict 中是否存在
			if sku_id in cart_dict:
				# 购物车已存在 增量计算
				origin_count = cart_dict[sku_id]['count']
				count += origin_count
			cart_dict[sku_id] = {
				'count': count,
				'selected': selected,

			}
			# 将 cart_dict 序列化 获取字节类型的数据
			cart_dict_bytes = pickle.dumps(cart_dict)
			# 对 cart_dict_bytes 进行编码 获取加密后的数据
			cart_str_bytes = base64.b64encode(cart_dict_bytes)
			# 对 cart_str_bytes 进行解码 获取字符串类型数据
			cookie_cart_str = cart_str_bytes.decode()
			# 将新的购物车数据写入到 Cookie
			response = JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
			response.set_cookie('carts', cookie_cart_str, max_age=constants.CARTS_COOKIE_EXPIRES)
			# 响应结果
			return response

	# 修改购物车商品方法
	def put(self, request):
		# 接收参数
		json_dict = json.loads(request.body.decode())
		sku_id = json_dict.get('sku_id')
		count = json_dict.get('count')
		selected = json_dict.get('selected', True)
		# 校验参数完整性
		if not all([sku_id, count]):
			print(' 缺少必传参数 ')
			return HttpResponseForbidden(' 缺少必传参数 ')
		# 判断 sku_id 是否存在
		try:
			sku = SKU.objects.get(id=sku_id)
		except SKU.DoesNotExist:
			print(' 商品 sku_id 不存在 ')
			return HttpResponseForbidden(' 商品 sku_id 不存在 ')
		# 判断 count 是否为数字
		try:
			count = int(count)
		except Exception:
			print(' 参数 count 有误 ')
			return HttpResponseForbidden(' 参数 count 有误 ')
		# 判断 selected 是否为布尔值
		if selected:
			if not isinstance(selected, bool):
				print(' 参数 selected 有误 ')
				return HttpResponseForbidden(' 参数 selected 有误 ')
		# 判断用户是否登录
		user = request.user
		if user.is_authenticated:
			# 用户已登录 修改redis购物车
			redis_conn = get_redis_connection('carts')
			pl = redis_conn.pipeline()
			pl.hset('carts_%s' % user.id, sku_id, count)
			if selected:
				# print('已勾选')
				pl.sadd('selected_%s' % user.id, sku_id)
			else:
				# print('未勾选')
				pl.srem('selected_%s' % user.id, sku_id)
			pl.execute()
			# 创建响应对象
			cart_sku = {
				'id': sku_id, 'count': count, 'selected': selected,
				'name': sku.name, 'price': sku.price,
				'amount': sku.price * count, 'stock': sku.stock,
				'default_image_url': str(settings.STATIC_URL) + 'images/goods/' + str(sku.default_image.url) + '.jpg',

			}
			return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'cart_sku': cart_sku})
		else:
			# 用户未登录 修改 Cookie 购物车
			cart_str = request.COOKIES.get('carts')
			if cart_str:
				# 解码序列化数据 获取python数据
				cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
			else:
				cart_dict = {}
			cart_dict[sku_id] = {
				'count': count,
				'selected': selected,

			}
			# 将字典转成 bytes 再将 bytes 转成 base64 的 bytes 最后 bytes 转字符串
			cookie_cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
			# 创建响应对象
			cart_sku = {
				'id': sku_id, 'count': count, 'selected': selected,
				'name': sku.name, 'price': sku.price,
				'amount': sku.price * count, 'stock': sku.stock,
				'default_image_url': str(settings.STATIC_URL) + 'images/goods/' + str(sku.default_image.url) + '.jpg',

			}
			response = JsonResponse({'code': RETCODE.OK, 'errmsg': '修改购物车成功', 'cart_sku': cart_sku})
			# 响应结果并将购物车数据写入到 cookie
			response.set_cookie('carts', cookie_cart_str, max_age=constants.CARTS_COOKIE_EXPIRES)
			return response

	def delete(self, request):
		""" 删除购物车 """
		# 接收参数
		json_dict = json.loads(request.body.decode())
		sku_id = json_dict.get('sku_id')
		# 判断 sku_id 是否存在
		try:
			SKU.objects.get(id=sku_id)
		except SKU.DoesNotExist:
			return HttpResponseForbidden('商品不存在')
		# 判断用户是否登录
		user = request.user
		if user.is_authenticated:
			# 用户登录 删除 redis 购物车
			redis_conn = get_redis_connection('carts')
			pl = redis_conn.pipeline()
			# 删除键 就等于删除了整条记录
			pl.hdel('carts_%s' % user.id, sku_id)
			pl.srem('selected_%s' % user.id, sku_id)
			pl.execute()
			# 删除结束后,没有响应的数据 只需要响应状态码就行
			return JsonResponse({'code': RETCODE.OK, 'errmsg': '删除购物车成功'})
		else:
			# 用户未登录 删除 cookie 购物车
			cart_str = request.COOKIES.get('carts')
			if cart_str:
				cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
			else:
				cart_dict = {}
			# 创建响应对象
			response = JsonResponse({'code': RETCODE.OK, 'errmsg': '删除购物车成功'})
			if sku_id in cart_dict:
				del cart_dict[sku_id]
				cookie_cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
				# 响应结果并将购物车数据写入到 Cookie
				response.set_cookie('carts', cookie_cart_str, max_age=constants.CARTS_COOKIE_EXPIRES)
			return response

class CartsSelectAllView(View):
	""" 全选购物车 """
	def put(self, request):
		# 接收参数
		json_dict = json.loads(request.body.decode())
		selected = json_dict.get('selected')
		# 校验参数
		if selected:
			if not isinstance(selected, bool):
				print(' 参数 selected 有误 ')
				return HttpResponseForbidden(' 参数 selected 有误 ')
		# 判断用户是否登录
		user = request.user
		if user.is_authenticated:
			# 用户登录 操作 redis 购物车
			redis_conn = get_redis_connection('carts')
			redis_cart = redis_conn.hgetall('carts_%s' % user.id)
			cart_sku_ids = redis_cart.keys()
			if selected:
				print('全选')
				# 全选 sadd 命令将一个或多个成员元素加入到集合中
				redis_conn.sadd('selected_%s' % user.id, *cart_sku_ids)
			else:
				print('取消全选')
				# 取消全选 srem 命令用于移除集合中的一个或多个成员元素
				redis_conn.srem('selected_%s' % user.id, *cart_sku_ids)
			return JsonResponse({'code': RETCODE.OK, 'errmsg': '全选购物车成功'})
		else:
			# 用户未登录 操作 cookie 购物车
			cart_str = request.COOKIES.get('carts')
			response = JsonResponse({'code': RETCODE.OK, 'errmsg': '全选购物车成功'})
			if cart_str:
				cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
				for sku_id in cart_dict:
					cart_dict[sku_id]['selected'] = selected
				cookie_cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
				response.set_cookie('carts', cookie_cart_str, max_age=constants.CARTS_COOKIE_EXPIRES)
			return response

# 展示购物车缩略信息
class CartsSimpleView(View):
	""" 商品页面右上角购物车 """
	def get(self, request):
		user = request.user     # 判断用户是否登录
		if user.is_authenticated:
			# 用户已登陆 操作redis购物车
			redis_conn = get_redis_connection('carts')
			redis_cart = redis_conn.hgetall('carts_%s' % user.id)
			cart_selected = redis_conn.smembers('selected_%s' % user.id)
			# 将 redis 中的两个数据统一格式 和Cookie 中的格式一致 方便统一查询
			cart_dict = {}
			for sku_id, count in redis_cart.items():
				cart_dict[int(sku_id)] = {
					'count': int(count),
					'selected': sku_id in cart_selected,

				}
		else:
			# 用户未登录 获取 cookie 购物车
			cart_str = request.COOKIES.get('carts')
			if cart_str:
				cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
			else:
				cart_dict = {}
		# 构造简单购物车 Json 数据
		cart_skus = []
		sku_ids = cart_dict.keys()
		skus = SKU.objects.filter(id__in = sku_ids)
		for sku in skus:
			cart_skus.append({
				'id': sku.id,
				'name': sku.name,
				'count': cart_dict.get(sku.id).get('count'),
				'default_image_url': str(settings.STATIC_URL) + 'images/goods/' + str(sku.default_image.url) + '.jpg',

			})
		# 响应 JSON 列表数据
		return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'cart_skus': cart_skus})