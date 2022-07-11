import re
from django.db import DatabaseError
from .models import User
from django.urls import reverse
from django.http import HttpResponseForbidden, JsonResponse
from xiaoyu_mall.utils.response_code import RETCODE
from django_redis import get_redis_connection

from django.contrib.auth import authenticate, login, logout

from django.contrib.auth.mixins import LoginRequiredMixin

from django.shortcuts import render, redirect
import logging
logger = logging.getLogger('django')
from django.views import View

# Create your views here.
class RegisterView(View):
	def get(self, request):
		""" 处理 get 请求: 提供用户注册页面 """
		return render(request, 'register.html')

	def post(self, request):
		""" 处理 post 请求: 完成注册 """
		# 1.接收请求参数
		username = request.POST.get('username')
		password = request.POST.get('password')
		password2 = request.POST.get('password2')
		mobile = request.POST.get('mobile')
		sms_code_client = request.POST.get('sms_code')
		allow = request.POST.get('allow')   # 用户协议
		print(username, password, password2, mobile, sms_code_client, allow)
		# 2.校验请求参数
		# 判断参数是否齐全
		if not all([username, password, password2, mobile, sms_code_client, allow]):
			return HttpResponseForbidden(' 缺少必传参数 ')
		# 判断短信验证码是否输入正确
		redis_conn = get_redis_connection('verify_code')
		sms_code_server = redis_conn.get('sms_%s' % mobile)
		if sms_code_server is None:
			return render(request, 'register.html', {'sms_code_errmsg': '短信验证码已失效'})
		if sms_code_client != sms_code_server.decode():
			return render(request, 'register.html', {'sms_code_errmsg': '输入短信验证码有误'})
		# 判断用户名是否为 5~20 个字符
		if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
			return HttpResponseForbidden(' 请输入5-20个字符的用户名 ')
		# 判断密码是否为 8-20 个数字
		if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
			return HttpResponseForbidden(' 请输入8-20位的密码 ')
		# 判断两次密码是否一致
		if password != password2:
			return HttpResponseForbidden(' 两次输入的密码不一致 ')
		# 判断手机号是否合法
		if not re.match(r'^1[3-9]\d{9}$', mobile):
			return HttpResponseForbidden(' 请输入正确的手机号码 ')
		# 判断是否勾选用户协议
		if allow != 'on':
			return HttpResponseForbidden(' 请勾选用户协议 ')
		# 3.保存注册数据
		try:
			# 注册成功的用户对象
			user = User.objects.create_user(username=username, password=password, mobile=mobile)
			print('注册成功')
		except DatabaseError:
		# 4. 返回注册结果
			print('这一步有错')
			return render(request, 'register.html', {'register_errmsg': '注册失败'})
		login(request, user)    # 登入用户,实现状态保持
		# 生成响应
		response = redirect(reverse('contents:index'))
		response.set_cookie('username', user.username, max_age=3600 * 24 * 14)
		# 响应登录结果: 重定向到首页
		return response


# 检验用户名唯一性 后端逻辑
class UsernameCountView(View):
	""" 判断用户名是否重复注册 """
	def get(self, request, username):
		count = User.objects.filter(username = username).count()
		return JsonResponse({'code': RETCODE.OK, 'errmsg':  'OK', 'count': count})

# 检验手机号唯一性 后端逻辑
class MobileCountView(View):
	def get(self, request, mobile):
		count = User.objects.filter(mobile = mobile).count()
		return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})

from carts.utils import merge_carts_cookies_redis
class LoginView(View):
	""" 用户名登录 """
	def get(self, request):
		return render(request, 'login.html')

	def post(self, request):
		""" 接收参数 """
		username = request.POST.get('username')
		password = request.POST.get('password')
		remembered = request.POST.get('remembered')
		# 校验参数
		if not all([username, password]):
			return HttpResponseForbidden(' 缺少必传参数 ')
		# 判断用户名是否是5-20个字符
		if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
			return HttpResponseForbidden(' 请输入正确的用户名或手机号 ')
		# 判断密码是否为 8-20 为数字
		if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
			return HttpResponseForbidden(' 密码最少 8 位 ')
		# 认证登录用户
		user = authenticate(username=username, password=password)
		if user is None:
			return render(request, 'login.html', {'account_errmsg': '账号或密码错误'})
		login(request, user)                    # 实现状态保持
		if remembered != 'on':
			request.session.set_expiry(0)       # 没有记住用户: 浏览器会话结束就过期
		else:
			request.session.set_expiry(None)    # 记住用户: None 表示两周后过期
		# 先取出 next
		next = request.GET.get('next')
		if next:
			# 重定向到 next
			response = redirect(next)
		else:
			response = redirect(reverse('contents:index'))

		# 登录时用户名写入到Cookie, 有效期 15 天
		response.set_cookie('username', user.username, max_age=3600 * 24 * 15)
		print('登录成功！！！')
		# 用户登录成功 合并 Cookie 购物车到 Redis 购物车
		response = merge_carts_cookies_redis(request=request, user=user, response=response)
		return response  # 响应登录结果

class LogoutView(View):
	""" 用户退出登录 """
	def get(self, request):
		# 清除状态保持信息
		logout(request)
		# 响应结果 重定向到首页
		response = redirect(reverse('contents:index'))
		# 删除 Cookie 中的用户名
		response.delete_cookie('username')
		return response

# 处理用户中心的 视图类
class UserInfoView(LoginRequiredMixin, View):
	""" 用户中心 """
	def get(self, request):
		""" 提供用户中心页面 """
		context = {
			'username': request.user.username,
			'mobile': request.user.mobile,
			'email': request.user.email,
			'email_active': request.user.email_active,

		}
		return render(request, 'user_center_info.html', context=context)

# 处理保存邮箱信息的 视图类
import json
from xiaoyu_mall.utils.views import LoginRequiredJSONMixin
from celery_tasks.email.tasks import send_verify_email
from .utils import generate_verify_email_url
class EmailView(LoginRequiredJSONMixin, View):
	""" 添加邮箱 """
	def put(self, request):
		""" 实现添加邮箱逻辑 """
		# 接收参数 body, 类型时 bytes 类型
		json_str = request.body.decode()
		json_dict = json.loads(json_str)
		email = json_dict.get('email')
		verify_url = generate_verify_email_url(request.user)
		print(email)
		if not email:   # 校验参数
			# print('缺少 Email 参数')
			return HttpResponseForbidden(' 缺少 Email 参数 ')
		if not re.match(r'^[a-z0-9][\w\\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
			# print('参数 Email 有误')
			return HttpResponseForbidden(' 参数 Email 有误 ')
		# 赋值 Email 字段
		try:
			request.user.email = email
			request.user.save()
		except Exception as e:
			logger.error(e)
			print('添加邮箱失败,失败原因:', e)
			return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '添加邮箱失败'})
		# 异步发送验证邮件
		verify_url = ' 邮件验证链接 '
		send_verify_email.delay(email, verify_url)
		# 响应添加邮箱结果
		print('添加邮箱成功')
		return JsonResponse({'code': RETCODE.OK, 'errmsg': '添加邮箱成功'})

from django.http import HttpResponseBadRequest, HttpResponseServerError
from .utils import check_verify_email_token
class VerifyEmailView(View):
	""" 验证邮箱 """
	def get(self, request):
		token = request.GET.get('token')
		if not token:
			return HttpResponseForbidden(' 缺少 token ')
		user = check_verify_email_token(token)
		if not user:
			return HttpResponseBadRequest(' 无效的 token ')
		try:
			user.email_active = True    # 将用户的 email_active 设置为true
			user.save()
		except Exception as e:
			logger.error(e)
			return HttpResponseServerError(' 验证邮箱失败 ')
		# 响应结果: 重定向到用户中心
		return redirect(reverse('users:info'))

# 用户地址
from . import constants
from .models import Address
class AddressCreateView(LoginRequiredJSONMixin, View):
	""" 新增地址 """
	def post(self, request):
		# 校验用户收货地址数量
		print('你点击了创建')
		count = request.user.addresses.filter(is_deleted__exact=False).count()
		if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
			return JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '超出用户地址上限'})
		# 校验用户输入的地址信息
		json_dict = json.loads(request.body.decode())
		receiver = json_dict.get('receiver')
		province_id = json_dict.get('province_id')
		city_id = json_dict.get('city_id')
		district_id = json_dict.get('district_id')
		place = json_dict.get('place')
		mobile = json_dict.get('mobile')
		tel = json_dict.get('tel')
		email = json_dict.get('email')
		print(receiver, province_id, city_id, district_id, place, mobile)
		# 校验参数
		if not all([receiver, province_id, city_id, district_id, place, mobile]):
			print('缺少必要参数')
			return HttpResponseForbidden('缺少必要参数')
		if not re.match(r'^1[3-9]\d{9}$', mobile):
			print('参数 mobile 有误')
			return HttpResponseForbidden('参数 mobile 有误')
		if tel:
			if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
				print('参数 tel 有误')
				return HttpResponseForbidden('参数 tel 有误')
		if email:
			if not re.match(r'^[a-zA-Z0-9][\w\\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
				print('参数 Email 有误')
				return HttpResponseForbidden('参数 Email 有误')
		# 保存收货地址
		try:
			address = Address.objects.create(
				user = request.user, title = receiver, receiver = receiver,
				province_id = province_id, place = place, tel = tel,
				city_id = city_id, district_id =district_id,
				mobile = mobile, email = email
			)
			# 设置默认收货地址
			if not request.user.default_address:
				request.user.default_address = address
				request.user.save()
		except Exception as e:
			print('错误了:', e)
			logger.error(e)
			return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '新增地址失败'})
		# 返回响应,新增地址成功,将新增的地址响应给前端实现页面刷新 构造新增地址字典数据
		address_dict = {
			'id': address.id, 'title': address.title,
			'receiver': address.receiver, 'province': address.province.name,
			'city': address.city.name, 'district': address.district.name,
			'place': address.place, 'mobile': address.mobile,
			'tel': address.tel, 'email': address.email
		}
		# 响应新增地址结果: 需要将新增的地址返回给前端渲染
		return JsonResponse({'code': RETCODE.OK, 'errmsg': '新增地址成功', 'address': address_dict})

# 展示收货地址视图
class AddressView(LoginRequiredJSONMixin, View):
	""" 展示地址 """
	def get(self, request):
		""" 提供收货地址界面 """
		login_user = request.user   # 获取当前登录用户对象
		addresses = Address.objects.filter(user=login_user, is_deleted=False)
		addresses_list = []     # 将用户地址模型列表转字典列表
		for address in addresses:
			address_dict = {
				'id': address.id, 'title': address.title,
				'receiver': address.province.name, 'place': address.place,
				'district': address.district.name, 'tel': address.tel,
				'mobile': address.mobile, 'email': address.email
			}
			addresses_list.append(address_dict)
		context = {
			'default_address_id': login_user.default_address_id or '0',
			'addresses': addresses_list
		}
		return render(request, 'user_center_site.html', context)

class DefaultAddressView(LoginRequiredJSONMixin, View):
	""" 设置默认地址 """
	def put(self, request, address_id):
		""" 设置默认地址 """
		try:
			address = Address.objects.get(id=address_id)
			request.user.default_address = address
		except Exception as e:
			logger.error(e)
			return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置默认地址失败'})
		# 响应设置默认地址结果
		return JsonResponse({'code': RETCODE.OK, 'errmsg': '设置默认地址成功'})

class UpdateTitleAddressView(LoginRequiredJSONMixin, View):

	def put(self, request, address_id):
		""" 修改地址 """
		json_dist = json.loads(request.body.decode())   # 接收参数,地址标题
		receiver = json_dist.get('receiver')
		province_id = json_dist.get('province_id')
		city_id = json_dist.get('city_id')
		district_id = json_dist('district_id')
		place = json_dist('place')
		mobile = json_dist('mobile')
		tel = json_dist('tel')
		email = json_dist('email')
		# 校验参数
		if not all([receiver, province_id, city_id, district_id,place,mobile]):
			print(' 缺少必传参数 ')
			return HttpResponseForbidden(' 缺少必传参数 ')
		if not re.match(r'^1[3-9]\d{9}$', mobile):
			print(' 参数 mobile 有误 ')
			return HttpResponseForbidden(' 参数 mobile 有误 ')
		if tel:
			if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
				print(' 参数 tel 有误 ')
				return HttpResponseForbidden(' 参数 tel 有误 ')
		if email:
			if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
				print(' 参数 Email 有误 ')
				return HttpResponseForbidden(' 参数 Email 有误 ')
		# 判断地址是否存在, 并更新地址信息
		try:
			Address.objects.filter(id=address_id).update(
				user = request.user, title = receiver, reciver = receiver,
				province_id = province_id, city_id = city_id, place=place,
				district_id = district_id, mobile = mobile, tel=tel,
				email = email
			)
		except Exception as e:
			logger.error(e)
			return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '更新地址失败'})
		# 构造响应数据
		address = Address.objects.get(id=address_id)
		address_dict = {
			'id': address.id, 'title': address.title,
			'receiver': address.receiver, 'province': address.province.name,
			'city': address.city.name, 'district': address.district.name,
			'place': address.place, 'mobile': address.mobile,
			'tel': address.tel, 'email': address.email
		}
		# 响应更新地址结果
		return JsonResponse({'code': RETCODE.OK, 'errmsg': '更新地址成功', 'address': address_dict})

class UpdateDestroyAddressView(LoginRequiredJSONMixin, View):
	def delete(self, request, address_id):
		""" 删除地址 """
		default_address_id = request.user.default_address
		try:
			address = Address.objects.get(id=address_id)
			if default_address_id == address.id:
				request.user.default_address_id = None
				request.user.save()
			address.is_deleted = True
			address.save()
		except Exception as e:
			logger.error(e)
			return JsonResponse({'code':RETCODE.DBERR, 'errmsg': '删除地址失败'})
		return JsonResponse({'code': RETCODE.OK, 'errmsg': '删除地址成功'})

class ChangePasswordView(LoginRequiredJSONMixin, View):
	""" 修改密码 """
	def get(self, request):
		""" 展示修改密码界面 """
		return render(request, 'user_center_pass.html')

	def post(self, request):
		""" 实现修改密码逻辑 """
		# 接收参数
		old_password = request.POST.get('old_password')
		new_password = request.POST.get('new_password')
		new_password2 = request.POST.get('new_password2')
		print(old_password, new_password, new_password2)
		# 校验参数
		if not all([old_password, new_password, new_password2]):
			print(' 参数不完整 ')
			return HttpResponseForbidden(' 参数不完整 ')
		try:
			if not request.user.check_password(old_password):
				print('原始密码错误')
				return render(request, 'user_center_pass.html', {'origin_password_s=errmsg': '原始密码错误'})
		except Exception as e:
			print('查询密码失败')
			logger.error(e)
			return render(request, 'user_center_pass.html', {'origin_password_s=errmsg': '查询密码失败'})
		if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
			print('密码最少 8 位,最长 20 位')
			return HttpResponseForbidden('密码最少 8 位,最长 20 位')
		if new_password2 != new_password:
			print(' 连两次密码不一致 ')
			return HttpResponseForbidden(' 连两次密码不一致 ')
		# 修改密码
		try:
			request.user.set_password(new_password)
			request.user.save()
		except Exception as e:
			print('尝试修改密码,但是失败了')
			logger.error(e)
			return render(request, 'user_center_pass.html', {'change_pwd_errmsg': '修改密码失败'})
		# 清理状态保持信息
		logout(request)
		response = redirect(reverse('users:login'))
		response.delete_cookie('username')
		# 响应密码修改结果: 重定向到登录界面
		return response

from goods.models import SKU
from django.conf import settings
class UserBrowseHistory(LoginRequiredJSONMixin, View):
	""" 用户浏览记录 """
	def get(self, request):
		""" 获取用户浏览记录 """
		# 获取 Redis 存储的 sku_id 列表信息
		redis_conn = get_redis_connection('history')
		sku_ids = redis_conn.lrange('history_%s' % request.user.id, 0, -1)
		# 根据 sku_ids 列表数据, 查询出商品的 sku 信息
		skus = []
		for sku_id in sku_ids:
			sku = SKU.objects.get(id=sku_id)
			skus.append({
				'id': sku.id,
				'name': sku.name,
				'default_image_url': str(settings.STATIC_URL) + 'images/goods/' + str(sku.default_image) + '.jpg',
				'price': sku.price,

			})
		return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'skus': skus})

	def post(self, request):
		""" 保存用户商品浏览记录 """
		# 接收参数
		json_dict = json.loads(request.body.decode())
		sku_id = json_dict.get('sku_id')
		# 校验参数
		try:
			SKU.objects.get(id=sku_id)
		except SKU.DoesNotExist:
			return HttpResponseForbidden(' sku 不存在 ')
		# 保存 sku_id 到 redis
		redis_conn = get_redis_connection('history')
		pl = redis_conn.pipeline()
		user_id = request.user.id
		# 先去重
		pl.lrem('history_%s' % user_id, 0, sku_id)
		# 再储存
		pl.lpush('history_%s' % user_id, sku_id)
		# 最后截取
		pl.ltrim('history_%s' % user_id, 0, 4)
		# 执行管道
		pl.execute()
		# 响应结果
		return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

from orders.models import OrderInfo
from django.core.paginator import Paginator, EmptyPage
from django.http import HttpResponseNotFound
class UserOrderInfoView(LoginRequiredMixin, View):
	def get(self, request, page_num):
		""" 提供我的订单页面 """
		user = request.user
		# 查询订单
		orders = user.orderinfo_set.all().order_by("-create_time")
		# 遍历所有订单
		for order in orders:
			# 绑定订单状态
			order.status_name = OrderInfo.ORDER_STATUS_CHOICES[order.status - 1][1]
			# 绑定支付方式
			order.pay_method_name = OrderInfo.PAY_METHODS_CHOICES[order.pay_method - 1][1]
			order.sku_list = []
			# 查询订单商品
			order_goods = order.skus.all()
			# 遍历订单商品
			for order_good in order_goods:
				sku = order_good.sku
				sku.count = order_good.count
				sku.amount = sku.price * sku.count
				order.sku_list.append(sku)
			# 分页
			page_num = int(page_num)
			try:
				paginator = Paginator(orders, constants.ORDERS_LIST_LIMIT)
				page_orders = paginator.page(page_num)
				total_page = Paginator.num_pages
			except EmptyPage:
				print(EmptyPage)
				return HttpResponseNotFound(' 订单不存在 ')
			context = {
				'page_orders': page_orders,
				'total_page': total_page,
				'page_num': page_num,

			}
			return render(request, 'user_center_order.html', context)

# 支付宝密钥 # at+B4FNAZkX0RuwtVxNLRw==