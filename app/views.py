from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from .forms import ProfileForm, PasswordChangeForm


class RegisterView(CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'register.html'
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        # 保存用户信息
        response = super().form_valid(form)
        # 显示成功消息
        messages.success(self.request, f'账号创建成功！您现在可以登录了')
        return response
    
    def form_invalid(self, form):
        # 显示错误消息
        messages.error(self.request, '注册失败，请检查输入的信息')
        return super().form_invalid(form)

# 如果不使用类视图，也可以使用函数视图
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'账号 {username} 创建成功！您现在可以登录了')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})



@login_required
def profile_view(request):
    """用户个人资料页面"""
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '个人资料更新成功！')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    
    return render(request, 'accounts/profile.html', {
        'form': form
    })


@login_required
def change_password_view(request):
    """修改密码视图"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # 更新会话以防止用户被登出
            update_session_auth_hash(request, user)
            messages.success(request, '密码已成功更新！')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'accounts/change_password.html', {
        'form': form
    })


def terms_view(request):
    """用户服务条款页面"""
    return render(request, 'terms.html')


def privacy_view(request):
    """隐私政策页面"""
    return render(request, 'privacy.html')