from django.urls import path, re_path
from . import views

# 设置应用程序命名空间
app_name = 'users'
urlpatterns = [
	# 用户注册
	path('register/', views.RegisterView.as_view(), name = 'register'),
	re_path('usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/', views.UsernameCountView.as_view()),
	re_path('usernames/(?P<mobile>1[3-9]\d{9})/count/', views.MobileCountView.as_view()),
	# 用户登录
	path('login/', views.LoginView.as_view(), name = 'login'),
	# 退出登录
	path('logout/', views.LogoutView.as_view(), name = 'logout'),
	# 用户限制访问
	path('info/', views.UserInfoView.as_view(), name = 'info'),
	# 邮箱路由
	path('emails/', views.EmailView.as_view()),
	# 验证邮箱
	path('emails/verification', views.VerifyEmailView.as_view()),
	# 设置收货地址
	path('addresses/create/', views.AddressCreateView.as_view()),
	# 展示地址
	path('addresses/', views.AddressView.as_view(), name = 'address'),
	# 默认收货地址的路由
	path('addresses/<int:address_id>/default/', views.DefaultAddressView.as_view()),
	# 删除地址路由
	path('addresses/<int:address_id>/', views.UpdateDestroyAddressView.as_view()),
	# 设置地址标题
	path('addresses/<int:address_id>/title', views.UpdateTitleAddressView.as_view()),
	# 修改密码路由
	path('editpassword/', views.ChangePasswordView.as_view(), name = 'editpwd'),
	# 历史浏览记录路由
	path('browse_histories/', views.UserBrowseHistory.as_view()),
	# 查看订单路由
	path('orders/info/<int:page_num>/', views.UserOrderInfoView.as_view(), name = 'myorderinfo')

]