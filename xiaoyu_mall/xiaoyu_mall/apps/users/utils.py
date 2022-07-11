import re
from .models import User
from django.contrib.auth.backends import ModelBackend

# 添加用户用手机号登录的功能
def get_user_by_account(account):
	try:
		if re.match(r'^1[3-9]\d{9}', account):
			user = User.objects.get(mobile = account)
		else:
			user = User.objects.get(username = account)
	except User.DoesNotExist:
		return None
	else:
		return user

class UsernameModelBackend(ModelBackend):
	def authenticate(self, request, username=None, password=None, **kwargs):
		user = get_user_by_account(username)
		if user and user.check_password(password):
			return user
		else:
			return None

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.conf import settings
# 将提供的constants.py 复制到 users 应用, 该文件包含设置验证链接的有效期
from . import constants
def generate_verify_email_url(user):
	serializer = Serializer(settings.SECRET_KEY, expires_in=constants.VERIFY_EMAIL_TOKEN_EXPIRES)
	data = {'user_id': user.id, 'email': user.email}
	token = serializer.dumps(data).decode()
	verify_url = settings.EMAIL_VERIFY_URL + '?rtoken=' + token
	return verify_url

# 反序列化 token 的方法
from itsdangerous import BadData
def check_verify_email_token(token):
	"""
	反序列 token，获取 user
	: param token: 序列化后的用户信息
	: return: user
	"""
	serializer = Serializer(settings.SECRET_KEY, expires_in=constants.VERIFY_EMAIL_TOKEN_EXPIRES)
	try:
		data = serializer.loads(token)
	except BadData:
		return None
	else:
		# 从 data 中取出 user_id 和 email
		user_id = data.get('user_id')
		email = data.get('email')
		try:
			user = User.objects.get(id=user_id, email=email)
		except User.DoesNotExist:
			return None
		else:
			return user
