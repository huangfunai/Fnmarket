from django.shortcuts import render
from django.views import View

from goods.models import GoodsChannel
from collections import OrderedDict
from contents.models import ContentCategory     # 导入广告类别
from contents.utils import get_categories

# Create your views here.
class IndexView(View):
	""" 首页广告 """
	def get(self, request):
		""" 提供首页广告页面 """
		# 准备商品分类对应的字典
		# categories = OrderedDict()
		categories = get_categories()
		# 查询所有的商品频道--37个一级类别
		channels = GoodsChannel.objects.all().order_by('group_id', 'sequence')
		# # 遍历所有频道
		# for channel in channels:
		# 	# 获取当前频道所在的组--一个组只有11个
		# 	group_id = channel.group_id
		# 	# 构造基本的数据框架
		# 	if group_id not in categories:
		# 		categories[group_id] = {'channels': [], 'sub_cats': [], }
		# 	# 查询当前频道对应的一级类别
		# 	cat1 = channel.category
		# 	# 将 cat1 添加到 channels -- 将类别添加到频道
		# 	categories[group_id]['channels'].append({
		# 		'id': cat1.id,
		# 		'name': cat1.name,
		# 		'url': channel.url
		# 	})
		# 	# 查询二级和三级类别
		# 	for cat2 in cat1.subs.all():    # 从一级类别找二级类别
		# 		cat2.sub_cats = []
		# 		for cat3 in cat2.subs.all():    # 从二级类别找三级类别
		# 			cat2.sub_cats.append(cat3)  # 将三级类别添加到二级
		# 		# 将二级类别添加到一级类别的sub_cats
		# 		categories[group_id]['sub_cats'].append(cat2)
		# 查询所有的广告类别
		contents = OrderedDict()
		contents_categories = ContentCategory.objects.all()
		# 查询出未下架的广告并排序
		for content_category in contents_categories:
			contents[content_category.key] = content_category.content_set.filter(status=True).order_by('sequence')
		# 构造上下文
		context = {
			'categories': categories,
			'contents': contents,

		}
		return render(request, 'index.html', context)
