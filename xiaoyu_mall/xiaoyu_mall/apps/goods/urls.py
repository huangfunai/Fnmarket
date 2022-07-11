from django.urls import path, re_path
from . import views

app_name = 'goods'
urlpatterns = [
	# 商品列表页
	path('list/<int:category_id>/<int:page_num>/', views.ListView.as_view(), name = 'list'),
	# 获取热销排行
	path('hot/<int:category_id>/', views.HostGoodsView.as_view()),
	# 商品详情页面
	path('detail/<int:sku_id>/', views.DetailView.as_view(), name = 'detail'),
	# 商品评价
	path('comments/<int:sku_id>', views.GoodsCommentView.as_view()),



]