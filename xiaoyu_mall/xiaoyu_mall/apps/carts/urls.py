from django.urls import path,re_path
from . import views

app_name = 'carts'
urlpatterns = [
	# 购物车管理
	path('carts/', views.CartsView.as_view(), name='info'),
	# 全选购物车
	path('carts/selection/', views.CartsSelectAllView.as_view()),
	# 缩略信息路由
	path('carts/simple/', views.CartsSimpleView.as_view()),

]