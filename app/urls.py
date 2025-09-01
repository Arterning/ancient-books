"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView, PasswordResetView, TemplateView
from .views import home_view, RegisterView, profile_view, terms_view, privacy_view, change_password_view

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_URL = '/book_pages/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'book_pages')

urlpatterns = [
    # 首页路由：访问网站根目录时，渲染 index.html
    path('', home_view, name='home'),

    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    # 登出
    path('logout/', 
         auth_views.LogoutView.as_view(next_page='login'),  # 登出后跳转登录页
         name='logout'),
     # 密码重置 - 请求
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='password_reset.html',
             email_template_name='password_reset_email.html',
             success_url='/accounts/password-reset/done/'
         ), 
         name='password_reset'),
    
    # 密码重置 - 请求成功
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    # 密码重置 - 确认
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='password_reset_confirm.html',
             success_url='/accounts/password-reset-complete/'
         ), 
         name='password_reset_confirm'),
    
    # 密码重置 - 完成
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # 注册
    path('register/', 
         RegisterView.as_view(),  # 如果使用函数视图则改为 register_view
         name='register'),

    # 个人资料
    path('accounts/profile/', profile_view, name='profile'),
    path('profile/', profile_view, name='profile'),
    path('profile/change-password/', change_password_view, name='change_password'),

    # 用户条款和隐私政策
    path('terms/', terms_view, name='terms'),
    path('privacy/', privacy_view, name='privacy'),

    path('admin/', admin.site.urls),
    path('books/', include("books.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
