from django.shortcuts import render
from django.views import View
from  .libs.captcha.captcha import captcha
from django_redis import get_redis_connection
# constant 是配置文件 定义图形验证码有效期和其他有效期变量
from . import constants
from django.http import HttpResponse,JsonResponse
import logging
# SMSCodeView 类需要导入的模块
from .libs.yuntongxun.ccp_sms import CCP
from xiaoyu_mall.utils.response_code import RETCODE
import random

logger = logging.getLogger('django')
# Create your views here.
class ImageCodeView(View):
	def get(self, request, uuid):
		text, image = captcha.generate_captcha()            # 生成图形验证码
		try:
			redis_conn = get_redis_connection('verify_code')    #保存图形验证码
			# setex 保存到redis中并 设置过期时间
			redis_conn.setex('img_%s' % uuid, constants.IMAGE_CODE_REDIS_EXPIRES, text)
		except Exception as e:
			print('错误', e)
		# 响应图形验证码
		return HttpResponse(image, content_type='image/jpg')

# 使用 pipeline 降低延迟
class SMSCodeView(View):
	""" 短信验证码 """
	def get(self, request, mobile):
		# 接收参数
		image_code_client = request.GET.get('image_code')
		uuid = request.GET.get('uuid')
		# 校验参数
		if not all([image_code_client, uuid]):
			return JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '缺少必要参数'})
		# 创建连接到 redis 的对象
		redis_conn = get_redis_connection('verify_code')
		# 60s 避免频繁请求短信验证码
		sent_flag = redis_conn.get('sent_flag_%s' % mobile)
		if sent_flag:
			return JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '发送短信过与频繁'})
		# 提取图形验证码
		image_code_server = redis_conn.get('img_%s' % uuid)
		if image_code_server is None:
			# 图形验证码过期或不存在
			return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码失效'})
		# 删除图形验证码, 避免恶意测试图形验证码
		redis_conn.delete('img_%s' % uuid)
		# 对比图形验证码
		image_code_server = image_code_server.decode()  # bytes 转字符串
		if image_code_client.lower() != image_code_server.lower():
			return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '输入图形验证码有误'})
		# 生成短信验证码, 6 位随机数
		sms_code = '%06d' % random.randint(1, 999999)
		print('--------------------------111111111111111111111111111111111111111111111111短信验证码', sms_code)
		logger.info(sms_code)
		pl = redis_conn.pipeline()  # 创建管道
		# 保存短信验证码
		pl.set('sms_%s' % mobile, sms_code, ex=constants.SMS_CODE_REDIS_EXPIRES)
		# 保存发送短信验证码的标记
		pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
		pl.execute()    # 执行
		# 发送短信验证码
		# CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], constants.SEND_SMS_TEMPLATE_ID)
		# 响应结果
		return JsonResponse({'code': RETCODE.OK, 'errmsg': '短信发送成功'})
