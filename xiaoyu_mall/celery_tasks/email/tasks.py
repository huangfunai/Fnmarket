# 定义任务
from ..main import celery_app
from django.core.mail import send_mail
from django.conf import settings
import logging
# 日志记录器
logger = logging.getLogger('django')
@celery_app.task(bind=True, name='send_verify_email', retry_backoff=3)
def send_verify_email(self,to_email, verify_url):

	subject = "小鱼商城邮箱验证"
	html_message = '<p>尊敬的用户您好!</p>'\
	               '<p>感谢您使用小鱼商城。</p>' \
	               '<p>您的邮箱为: %s 。请单击此链接验证您的邮箱:</p>' \
	               '<p><a href="%s">%s</a></p>' % (to_email, verify_url, verify_url)
	try:
		send_mail(subject, "", settings.EMAIL_FROM, [to_email], html_message=html_message)
	except Exception as e:
		print('有没有to_email', to_email)
		print("这里错啦！邮件发不出去！！")
		logger.error(e)
		# 有异常重连 3 次
		raise self.retry(exc = e, max_retries = 3)