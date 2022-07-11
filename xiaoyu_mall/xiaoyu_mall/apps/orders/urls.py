from django.urls import path, re_path
from . import views

app_name = 'orders'
urlpatterns = [
	# 结算订单
	path('orders/settlement/', views.OrderSettlementView.as_view(), name='settlement'),
	path('orders/commit/', views.OrdersCommitView.as_view()),
	path('orders/success/', views.OrderSuccessView.as_view()),

]