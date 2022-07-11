from collections import OrderedDict
from goods.models import GoodsChannel

def get_categories():
	""" 获取商品分类 """
	# 准备商品分类对应的字典
	categories = OrderedDict()
	# 查询并展示商品分类 37个一级类别
	channels = GoodsChannel.objects.order_by('group_id', 'sequence')
	# 遍历所有频道
	for channel in channels:
		group_id = channel.group_id     # 当前组
		# 获取当前频道所在的组: 只有 11 个组
		if group_id not in categories:
			categories[group_id] = {'channels': [], 'sub_cats': []}
		cat1 = channel.category
		# 追加当前频道
		categories[group_id]['channels'].append({
			'id': cat1.id,
			'name': cat1.name,
			'url': channel.url
		})
		# 查询二级和三级类别
		for cat2 in cat1.subs.all():
			cat2.sub_cats = []
			for cat3 in cat2.subs.all():
				cat2.sub_cats.append(cat3)
				# 将二级类别添加到一级类别的sub_cats
			categories[group_id]['sub_cats'].append(cat2)
	return categories