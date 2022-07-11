"""xiaoyu_mall URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls', namespace='users')),
    path('', include('contents.urls', namespace='contents')),
    path('', include('verifications.urls')),
    path('', include('areas.urls')),
    path('', include('goods.urls', namespace='goods')),
    path('search/', include('haystack.urls')),
    path('', include('carts.urls', namespace = 'carts')),
    path('', include('orders.urls', namespace='orders')),
    path('', include('payment.urls', namespace='payment')),
    

]
