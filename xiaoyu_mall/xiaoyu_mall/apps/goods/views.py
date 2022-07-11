from django.shortcuts import render
from django.views import View
from goods.models import GoodsCategory
from django.http import HttpResponseNotFound, HttpResponseForbidden
from contents.utils import get_categories
from .models import SKU
from .utils import get_breadcrumb
from django.core.paginator import Paginator, EmptyPage

# Create your views here.
class ListView(View):
	""" 商品列表页 """
	def get(self, request, category_id, page_num):
		""" 查询并渲染商品列表页 """
		# 校验参数category_id
		try:
			# 三级类别
			category = GoodsCategory.objects.get(id=category_id)
		except GoodsCategory.DoesNotExist:
			return HttpResponseNotFound('" 参数 category_id 不存在 "')
		# 查询商品分类
		categories = get_categories()
		# 查询面包屑导航: 一级 -> 二级 -> 三级
		breadcrumb = get_breadcrumb(category)
		# 接收 sort 参数: 若未接收到 则使用默认的排序规则
		sort = request.GET.get('sort', 'default')
		# 按照排序规则查询该分类商品 SKU 信息
		if sort == 'price':
			sort_field = 'price'
		elif sort == 'hot':
			sort_field = '-sales'
		else:
			sort = 'default'
			sort_field = 'create_time'
		skus = SKU.objects.filter(category=category, is_launched=True).order_by(sort_field)
		# 创造分页器
		paginator = Paginator(skus, 5)
		try:
			page_skus = paginator.page(page_num)
		except EmptyPage:
			print('Empty Page')
			return HttpResponseForbidden('Empty Page')
		# 获取总页数
		total_page = paginator.num_pages
		# 构造上下文
		context = {
			'categories': categories,
			'breadcrumb': breadcrumb,
			'sort': sort,
			'page_skus': page_skus,
			'total_page': total_page,
			'page_num': page_num,
			'category_id': category_id,

		}
		return render(request, 'list.html', context)

from django.conf import settings
from django.http import JsonResponse
from xiaoyu_mall.utils.response_code import RETCODE
class HostGoodsView(View):
	""" 热销排行 """
	def get(self, request, category_id):
		# 查询热销数据(结果为 SKU 模型类的对象列表)
		skus = SKU.objects.filter(category_id = category_id, is_launched = True).order_by('-sales')[:2]
		# 将模型列表转字典构造 JSON 数据
		hot_skus = []
		for sku in skus:
			sku_dict = {
				'id': sku.id,
				'name': sku.name,
				'price': sku.price,
				'default_image_url': str(settings.STATIC_URL) + 'images/goods/' + str(sku.default_image) + '.jpg'
			}
			hot_skus.append(sku_dict)
		return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'hot_skus': hot_skus})

class DetailView(View):
	""" 商品详情页 """
	def get(self, request, sku_id):
		""" 提供商品详情页 """
		# 获取当前SKU的信息
		try:
			sku = SKU.objects.get(id = sku_id)
		except SKU.DoesNotExist:
			return render(request, '404.html')
		# 查询商品频道分类
		categories = get_categories()
		# 查询面包屑导航
		breadcrumb = get_breadcrumb(sku.category)
		# 构建当前商品的规格键
		sku_specs = sku.specs.order_by('spec_id')
		# 记录当前 SKU 的规格选项 id（列表）
		sku_key = []
		for spec in sku_specs:
			sku_key.append(spec.option.id)
		# 获取当前商品的所有 SKU
		skus = sku.spu.sku_set.all()
		# 构建当前商品所有 SKU 的规格参数字典,键为规格的 id 元组, 值为 sku_id
		spec_sku_map = {}
		for s in skus:
			# 获取 SKU 的规格参数
			s_specs = s.specs.order_by('spec_id')
			# 用于形成规格参数 -SKU 字典的键
			key = []
			for spec in s_specs:
				key.append(spec.option.id)      # 制作键--规格元组
			# 向规格参数 -SKU 字典添加记录
			spec_sku_map[tuple(key)] = s.id
		# 获取当前商品所属SPU的规格
		goods_specs = sku.spu.specs.order_by('id')
		# 若当前 SKU 的规格信息不完整,则不再继续
		if len(sku_key) < len(goods_specs):
			return
		# 找到与 key 关联的SKU
		for index, spec in enumerate(goods_specs):
			# 复制当前 SKU 的规格键
			key = sku_key[:]
			# 该规格的选项
			spec_options = spec.options.all()
			for option in spec_options:
				# 在规格参数 SKU 字典中查找符合当前规格的 sku
				key[index] = option.id
				option.sku_id = spec_sku_map.get(tuple(key))
			spec.spec_options = spec_options        # 为 SPU 选项赋值
		# 渲染页面
		context = {
			'categories': categories,
			'breadcrumb': breadcrumb,
			'sku': sku,
			'specs': goods_specs,
			'stock': sku.stock,


		}
		return render(request, 'detail.html', context)

from orders.models import OrderGoods
class GoodsCommentView(View):
	""" 订单商品评价信息 """
	def get(self, request, sku_id):
		# 获取被评价的订单商品信息
		order_goods_list = OrderGoods.objects.filter(sku_id = sku_id, is_commented = True).order_by('-create_time')[:30]
		comment_list = []
		for order_goods in order_goods_list:
			username = order_goods.order.user.username
			comment_list.append({
				'username': username[0] + '***' + username[-1] if order_goods.isanonymous else username,
				'comment': order_goods.comment,
				'score': order_goods.score,

			})
		return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'comment_list': comment_list})