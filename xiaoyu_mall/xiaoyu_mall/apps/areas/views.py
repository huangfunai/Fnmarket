from django.shortcuts import render
from django.views import View
from django.http.response import JsonResponse
import logging
from django.core.cache import cache
from .models import Area
from xiaoyu_mall.utils.response_code import RETCODE

logger = logging.getLogger('django')    # 日志记录器
# Create your views here.
class AreasView(View):
	def get(self, request):
		""" 提供省市区数据 """
		area_id = request.GET.get('area_id')
		if not area_id:
			province_list = cache.get('province_list')
			if not province_list:
				# 提供省份数据
				try:
					province_model_list = Area.objects.filter(parent__isnull=True)
					# 序列化省份数据
					province_list = []
					for province_model in province_model_list:
						province_list.append({'id': province_model.id, 'name': province_model.name})
				except Exception as e:
					logger.error(e)
					return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '省份数据错误'})
				# 缓存省份数据
				cache.set('province_list', province_list, 3600)
			# 响应省份数据
			return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'province_list': province_list})
		else:
			sub_data = cache.get('sub_area_' + area_id)
			if not sub_data:
				# 提供市或区数据
				try:
					parent_model = Area.objects.get(id = area_id)   # 查询市或区的父级
					sub_model_list = parent_model.subs.all()
					# 序列化市或区数据
					sub_list = []
					for sub_model in sub_model_list:
						sub_list.append({'id': sub_model.id, 'name': sub_model.name})
						sub_data = {
							'id': parent_model.id,
							'name': parent_model.name,
							'subs': sub_list
						}
				except Exception as e:
					logger.error(e)
					return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '城市或区数据错误'})
				# 缓存市或区数据
				cache.set('sub_area_' + area_id, sub_data, 3600)
			# 响应市或区数据
			return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'sub_data': sub_data})


