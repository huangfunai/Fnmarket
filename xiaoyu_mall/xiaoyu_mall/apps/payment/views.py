from django.shortcuts import render
import os
from alipay import AliPay
from django.conf import settings
from django.views import View
from django.http import HttpResponseForbidden, JsonResponse
from xiaoyu_mall.utils.views import LoginRequiredJSONMixin
from xiaoyu_mall.utils.response_code import RETCODE
from orders.models import OrderInfo


# Create your views here.
class PaymentView(LoginRequiredJSONMixin, View):
	""" 订单支付功能 """
	def get(self, request, order_id):
		# 查询要支付的订单
		user = request.user
		try:
			order = OrderInfo.objects.get(order_id= order_id, user = user, status = OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
		except OrderInfo.DoesNotExist:
			print('订单信息错误')
			return HttpResponseForbidden(' 订单信息错误 ')
		# 创建支付对象
		alipay = AliPay(
			appid = settings.ALIPAY_APPID,
			app_notify_url = None,  # 默认回调url
			app_private_key_string = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem")).read(),
			alipay_public_key_string = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/alipay_public_key.pem")).read(),
			sign_type = 'RSA2',
			debug = settings.ALIPAY_DEBUG,

		)
		# 生成支付宝登录链接
		order_string = alipay.api_alipay_trade_page_pay(
			out_trade_no = order_id,                    # 订单编号
			total_amount = str(order.total_amount),     # 订单金额
			subject = '小鱼商城%s' % order_id,            # 订单标题
			return_url = settings.ALIPAY_RETURN_URL,    # 回调地址
		)
		# 响应登录支付宝链接
		alipay_url = settings.ALIPAY_URL + '?' + order_string
		return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'alipay_url': alipay_url})

from .models import Payment
class PaymentStatusView(View):
	""" 保存订单支付结果 """
	def get(self, request):
		query_dict = request.GET    # 获取前端传入的请求参数
		data = query_dict.dict()
		signature = data.pop('sign')    # 从请求参数中剔除 signature
		# 创建支付宝支付对象
		alipay = AliPay(
			appid=settings.ALIPAY_APPID,
			app_notify_url=None,  # 默认回调url
			app_private_key_string=open(
				os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem")).read(),
			alipay_public_key_string=open(
				os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/alipay_public_key.pem")).read(),
			sign_type='RSA2',
			debug=settings.ALIPAY_DEBUG,

		)
		# 校验这个重定向是否是alipay重定向过来的
		success = alipay.verify(data, signature)
		if success:
			order_id = data.get('out_trade_no')     # 读取 order_id
			trade_id = data.get('trade_no')         # 读取支付宝流水号
			# 保存 Payment 模型类数据
			Payment.objects.create(
				order_id = order_id,
				trade_id = trade_id,

			)
			# 修改订单状态为待评价
			OrderInfo.objects.filter(
				order_id = order_id,
				status = OrderInfo.ORDER_STATUS_ENUM['UNPAID']
			).update(status = OrderInfo.ORDER_STATUS_ENUM['UNCOMMENT'])
			# 响应 trade_id
			context = {
				'trade_id': trade_id
			}
			return render(request, 'pay_success.html', context)
		else:
			# 订单支付失败,重定向到我的订单
			print(' 非法请求 ')
			return HttpResponseForbidden(' 非法请求 ')

from django.contrib.auth.mixins import LoginRequiredMixin
from orders.models import OrderGoods
import json
from goods.models import SKU
class OrderCommentView(LoginRequiredMixin, View):
	""" 订单商品评价 """
	def get(self, request):
		""" 展示商品评价页面 """
		order_id = request.GET.get('order_id')      # 接收参数(订单编号)
		# 校验参数
		try:
			OrderInfo.objects.get(order_id = order_id, user = request.user)
		except OrderInfo.DoesNotExist:
			print(' 订单不存在 ')
			return HttpResponseForbidden(' 订单不存在 ')
		# 查询订单中未被评价的商品信息
		try:
			uncomment_goods = OrderGoods.objects.filter(order_id = order_id, is_commented = False)
		except Exception:
			print(' 订单商品信息错误 ')
			return HttpResponseForbidden(' 订单商品信息错误 ')
		# 构造待评价商品订单数据
		uncomment_goods_list = []
		for goods in uncomment_goods:
			uncomment_goods_list.append({
				'order_id': goods.order.order_id, 'sku_id': goods.sku.id,
				'name': goods.sku.name, 'price': str(goods.price),
				'default_image_url': str(settings.STATIC_URL) + 'images/goods/' + str(goods.sku.default_image.url) + '.jpg',
				'comment': goods.comment, 'score': goods.score,
				'is_anonymous': str(goods.is_anonymous),

			})
		# 渲染模板
		context = {
			'uncomment_goods_list': uncomment_goods_list
		}
		return render(request, 'goods_judge.html', context)

	def post(self, request):
		""" 商品评价 """
		json_dict = json.loads(request.body.decode())
		order_id = json_dict.get('order_id')
		sku_id = json_dict.get('sku_id')
		score = json_dict.get('score')
		comment = json_dict.get('comment')
		is_anonymous = json_dict.get('is_anonymous')
		# 校验参数
		if not all([order_id, sku_id, score, comment]):
			print(' 缺少必传参数 ')
			return HttpResponseForbidden(' 缺少必传参数 ')
		try:
			OrderInfo.objects.filter(order_id = order_id, user = request.user, status = OrderInfo.ORDER_STATUS_ENUM['UNCOMMENT'])
		except OrderInfo.DoesNotExist:
			return HttpResponseForbidden(' 参数 order_id 错误 ')
		try:
			sku = SKU.objects.get(id = sku_id)
		except SKU.DoesNotExist:
			return HttpResponseForbidden(' 参数 sku_id 错误 ')
		if is_anonymous:
			if not isinstance(is_anonymous, bool):
				return HttpResponseForbidden('  参数 is_anonymous 错误 ')
		# 保存订单商品评价数据
		OrderGoods.objects.filter(order_id = order_id, sku_id = sku_id, is_commented = False).update(
			comment = comment, score = score,
			is_anonymous = is_anonymous,
			is_commented = True
		)
		# 累计评价数据
		sku.comments += 1
		sku.save()
		sku.spu.comments += 1
		sku.spu.save()
		# 如果所有订单商品都已评价,则修改订单状态为已完成
		if OrderGoods.objects.filter(order_id = order_id, is_commented = False).count() == 0:
			OrderInfo.objects.filter(order_id = order_id).update(
				status = OrderInfo.ORDER_STATUS_ENUM['FINISHED']
			)
		return JsonResponse({'code': RETCODE.OK, 'errmsg': '评价成功'})