import base64,pickle
from django_redis import get_redis_connection

def merge_carts_cookies_redis(request, user, response):
	# 获取 Cookie 中的购物车数据
	cookie_cart_str = request.COOKIES.get('carts')
	# COOKIES 中没有数据就响应结果
	if not cookie_cart_str:
		return response
	cookie_cart_dict = pickle.loads(base64.b64decode(cookie_cart_str.encode()))
	new_cart_dict = {}
	new_cart_selected_add = []
	new_cart_selected_remove = []
	# 同步 Cookie 中购物车数据
	for sku_id, cookie_dict in cookie_cart_dict.items():
		new_cart_dict[sku_id] = cookie_dict['count']
		if cookie_dict['selected']:
			new_cart_selected_add.append(sku_id)
		else:
			new_cart_selected_remove.append(sku_id)
	# 将 new_cart_dict 写入到 redis 数据库
	redis_conn = get_redis_connection('carts')
	pl = redis_conn.pipeline()
	if new_cart_dict:
		pl.hmset('carts_%s' % user.id, new_cart_dict)
		# 将勾选状态同步到redis数据库
		if new_cart_selected_add:
			pl.sadd('selected_%s' % user.id, *new_cart_selected_add)
		if new_cart_selected_remove:
			pl.srem('selected_%s' % user.id, *new_cart_selected_remove )
		pl.execute()
	# 清除 Cookie
	response.delete_cookie('carts')
	return response
