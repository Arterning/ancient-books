# models.py
from django.db import models
from django.contrib.auth.models import User
import json

class Book(models.Model):
    """书籍模型"""
    title = models.CharField(max_length=200, verbose_name="书名")
    author = models.CharField(max_length=100, blank=True, verbose_name="作者")
    dynasty = models.CharField(max_length=50, blank=True, verbose_name="朝代")
    description = models.TextField(blank=True, verbose_name="描述")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="创建者")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "书籍"
        verbose_name_plural = "书籍"
    
    def __str__(self):
        return self.title

class BookPage(models.Model):
    """书页模型"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='pages', verbose_name="书籍")
    page_number = models.IntegerField(verbose_name="页码")
    image = models.ImageField(upload_to='book_pages/', verbose_name="页面图片")
    ocr_status = models.CharField(
        max_length=20, 
        choices=[
            ('pending', '待处理'),
            ('processing', '处理中'),
            ('completed', '已完成'),
            ('failed', '处理失败')
        ],
        default='pending',
        verbose_name="OCR状态"
    )
    ocr_confidence = models.FloatField(null=True, blank=True, verbose_name="OCR置信度")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        verbose_name = "书页"
        verbose_name_plural = "书页"
        unique_together = ['book', 'page_number']
        ordering = ['page_number']
    
    def __str__(self):
        return f"{self.book.title} - 第{self.page_number}页"

class TextRegion(models.Model):
    """文本区域模型 - 存储OCR识别出的文本区域信息"""
    page = models.ForeignKey(BookPage, on_delete=models.CASCADE, related_name='text_regions', verbose_name="页面")
    region_id = models.CharField(max_length=50, verbose_name="区域ID")
    
    # 区域坐标信息 (相对于图片的像素坐标)
    x = models.IntegerField(verbose_name="X坐标")
    y = models.IntegerField(verbose_name="Y坐标")
    width = models.IntegerField(verbose_name="宽度")
    height = models.IntegerField(verbose_name="高度")
    
    # OCR识别的原始文本
    original_text = models.TextField(verbose_name="原始识别文本")
    confidence = models.FloatField(verbose_name="识别置信度")
    
    # 用于排序显示
    order_index = models.IntegerField(verbose_name="显示顺序")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        verbose_name = "文本区域"
        verbose_name_plural = "文本区域"
        ordering = ['order_index']
    
    def __str__(self):
        return f"{self.page} - 区域{self.region_id}"

class TextCorrection(models.Model):
    """文本校对模型"""
    text_region = models.OneToOneField(TextRegion, on_delete=models.CASCADE, related_name='correction', verbose_name="文本区域")
    corrected_text = models.TextField(verbose_name="校对后文本")
    corrector = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="校对者")
    correction_notes = models.TextField(blank=True, verbose_name="校对备注")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="校对时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "文本校对"
        verbose_name_plural = "文本校对"
    
    def __str__(self):
        return f"{self.text_region} - 校对"

class Translation(models.Model):
    """翻译模型"""
    text_region = models.OneToOneField(TextRegion, on_delete=models.CASCADE, related_name='translation', verbose_name="文本区域")
    translated_text = models.TextField(verbose_name="翻译文本")
    translation_language = models.CharField(
        max_length=10,
        choices=[
            ('zh-cn', '简体中文'),
            ('en', '英语'),
            ('ja', '日语'),
        ],
        default='zh-cn',
        verbose_name="翻译语言"
    )
    translator = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="翻译者")
    translation_method = models.CharField(
        max_length=20,
        choices=[
            ('manual', '人工翻译'),
            ('auto', '机器翻译'),
            ('hybrid', '人工+机器')
        ],
        default='auto',
        verbose_name="翻译方式"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="翻译时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "翻译"
        verbose_name_plural = "翻译"
    
    def __str__(self):
        return f"{self.text_region} - 翻译"

class OCRTask(models.Model):
    """OCR任务模型"""
    page = models.ForeignKey(BookPage, on_delete=models.CASCADE, verbose_name="页面")
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '待处理'),
            ('processing', '处理中'),
            ('completed', '已完成'),
            ('failed', '失败')
        ],
        default='pending',
        verbose_name="任务状态"
    )
    error_message = models.TextField(blank=True, verbose_name="错误信息")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="开始时间")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间")
    
    class Meta:
        verbose_name = "OCR任务"
        verbose_name_plural = "OCR任务"
    
    def __str__(self):
        return f"{self.page} - OCR任务"