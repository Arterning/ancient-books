from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm


class PasswordChangeForm(PasswordChangeForm):
    """自定义密码修改表单，添加古风样式"""
    old_password = forms.CharField(
        label="当前密码",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入当前密码',
            'autocomplete': 'current-password'
        })
    )
    new_password1 = forms.CharField(
        label="新密码",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '请设置新密码',
            'autocomplete': 'new-password'
        }),
        help_text="""
        您的密码必须包含至少8个字符，且不能是纯数字。
        请避免使用过于常见的密码或与您的个人信息相关的密码。
        """
    )
    new_password2 = forms.CharField(
        label="确认新密码",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '请再次输入新密码',
            'autocomplete': 'new-password'
        })
    )

    class Meta:
        model = User
        fields = ('old_password', 'new_password1', 'new_password2')

class ProfileForm(UserChangeForm):
    """用户资料编辑表单"""
    password = None  # 不显示密码字段（单独通过修改密码功能处理）
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
        }),
        label='邮箱'
    )

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        }),
        label='用户名'
    )
    
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        }),
        label='姓名'
    )
    
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        }),
        label='研究方向'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')