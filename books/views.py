# views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.conf import settings
import json
import os
from .models import Book, BookPage, TextRegion, TextCorrection, Translation, OCRTask
from .services.ocr_service import OCRService
from .services.translation_service import TranslationService
from .tasks import process_ocr_task  # 异步任务
import logging

logger = logging.getLogger(__name__)

@login_required
def book_list(request):
    """书籍列表页面"""
    books = Book.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'books/book_list.html', {'books': books})

@login_required
def book_detail(request, book_id):
    """书籍详情页面"""
    book = get_object_or_404(Book, id=book_id, created_by=request.user)
    pages = book.pages.all().order_by('page_number')
    return render(request, 'books/book_detail.html', {
        'book': book, 
        'pages': pages
    })

@login_required
def page_editor(request, page_id):
    """页面编辑器（校对、比对界面）"""
    page = get_object_or_404(BookPage, id=page_id)
    text_regions = page.text_regions.all().order_by('order_index')
    
    # 获取校对和翻译数据
    for region in text_regions:
        try:
            region.corrected_text = region.correction.corrected_text
        except TextCorrection.DoesNotExist:
            region.corrected_text = None
        
        try:
            region.translated_text = region.translation.translated_text
        except Translation.DoesNotExist:
            region.translated_text = None
    
    return render(request, 'books/page_editor.html', {
        'page': page,
        'text_regions': text_regions
    })

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def upload_pages(request, book_id):
    """上传书籍页面图片"""
    book = get_object_or_404(Book, id=book_id, created_by=request.user)
    
    try:
        files = request.FILES.getlist('pages')
        page_number = int(request.POST.get('start_page_number', 1))
        
        created_pages = []
        for file in files:
            # 保存图片文件
            page = BookPage.objects.create(
                book=book,
                page_number=page_number,
                image=file
            )
            
            # 创建OCR任务
            ocr_task = OCRTask.objects.create(page=page)
            
            # 异步处理OCR
            process_ocr_task.delay(ocr_task.id)
            
            created_pages.append({
                'id': page.id,
                'page_number': page.page_number,
                'image_url': page.image.url,
                'ocr_status': page.ocr_status
            })
            
            page_number += 1
        
        return JsonResponse({
            'success': True,
            'pages': created_pages
        })
        
    except Exception as e:
        logger.error(f"上传页面失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def save_correction(request, region_id):
    """保存文本校对结果"""
    region = get_object_or_404(TextRegion, id=region_id)
    
    try:
        data = json.loads(request.body)
        corrected_text = data.get('corrected_text', '')
        notes = data.get('notes', '')
        
        correction, created = TextCorrection.objects.update_or_create(
            text_region=region,
            defaults={
                'corrected_text': corrected_text,
                'correction_notes': notes,
                'corrector': request.user
            }
        )
        
        return JsonResponse({
            'success': True,
            'correction_id': correction.id,
            'created': created
        })
        
    except Exception as e:
        logger.error(f"保存校对失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def translate_region(request, region_id):
    """翻译文本区域"""
    region = get_object_or_404(TextRegion, id=region_id)
    
    try:
        data = json.loads(request.body)
        target_language = data.get('language', 'zh-cn')
        
        # 获取要翻译的文本（优先使用校对后的文本）
        try:
            text_to_translate = region.correction.corrected_text
        except TextCorrection.DoesNotExist:
            text_to_translate = region.original_text
        
        # 调用翻译服务
        translation_service = TranslationService()
        translated_text = translation_service.translate_text(text_to_translate, target_language)
        
        # 保存翻译结果
        translation, created = Translation.objects.update_or_create(
            text_region=region,
            defaults={
                'translated_text': translated_text,
                'translation_language': target_language,
                'translator': request.user,
                'translation_method': 'auto'
            }
        )
        
        return JsonResponse({
            'success': True,
            'translation': translated_text,
            'translation_id': translation.id
        })
        
    except Exception as e:
        logger.error(f"翻译失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@require_http_methods(["GET"])
@login_required
def get_page_data(request, page_id):
    """获取页面的文本区域数据"""
    page = get_object_or_404(BookPage, id=page_id)
    
    regions_data = []
    for region in page.text_regions.all().order_by('order_index'):
        region_data = {
            'id': region.id,
            'region_id': region.region_id,
            'x': region.x,
            'y': region.y,
            'width': region.width,
            'height': region.height,
            'original_text': region.original_text,
            'confidence': region.confidence,
            'order_index': region.order_index
        }
        
        # 添加校对信息
        try:
            region_data['corrected_text'] = region.correction.corrected_text
            region_data['correction_notes'] = region.correction.correction_notes
        except TextCorrection.DoesNotExist:
            region_data['corrected_text'] = None
            region_data['correction_notes'] = None
        
        # 添加翻译信息
        try:
            region_data['translated_text'] = region.translation.translated_text
            region_data['translation_language'] = region.translation.translation_language
        except Translation.DoesNotExist:
            region_data['translated_text'] = None
            region_data['translation_language'] = None
        
        regions_data.append(region_data)
    
    return JsonResponse({
        'success': True,
        'page': {
            'id': page.id,
            'page_number': page.page_number,
            'image_url': page.image.url,
            'ocr_status': page.ocr_status
        },
        'text_regions': regions_data
    })

@require_http_methods(["GET"])
@login_required
def check_ocr_status(request, page_id):
    """检查OCR处理状态"""
    page = get_object_or_404(BookPage, id=page_id)
    
    return JsonResponse({
        'success': True,
        'status': page.ocr_status,
        'confidence': page.ocr_confidence
    })


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def create_book(request):
    """创建新的古籍"""
    try:
        # 获取表单数据
        title = request.POST.get('title', '').strip()
        author = request.POST.get('author', '').strip()
        dynasty = request.POST.get('dynasty', '').strip()
        description = request.POST.get('description', '').strip()
        start_page_number = int(request.POST.get('start_page_number', 1))
        
        if not title:
            return JsonResponse({
                'success': False,
                'error': '书名不能为空'
            }, status=400)
        
        # 创建书籍
        book = Book.objects.create(
            title=title,
            author=author,
            dynasty=dynasty,
            description=description,
            created_by=request.user
        )
        
        # 处理上传的页面图片
        files = request.FILES.getlist('pages')
        if not files:
            return JsonResponse({
                'success': False,
                'error': '请至少上传一张页面图片'
            }, status=400)
        
        created_pages = []
        page_number = start_page_number
        
        for file in files:
            # 验证文件类型
            if not file.content_type.startswith('image/'):
                continue
                
            # 创建书页
            page = BookPage.objects.create(
                book=book,
                page_number=page_number,
                image=file,
                ocr_status='pending'
            )
            
            # 创建OCR任务
            ocr_task = OCRTask.objects.create(page=page)
            
            # 异步处理OCR
            from .tasks import process_ocr_task
            process_ocr_task.delay(ocr_task.id)
            
            created_pages.append({
                'id': page.id,
                'page_number': page.page_number,
                'image_url': page.image.url,
                'ocr_status': page.ocr_status
            })
            
            page_number += 1
        
        logger.info(f"创建古籍成功: {book.title}, 用户: {request.user.username}, 页数: {len(created_pages)}")
        
        return JsonResponse({
            'success': True,
            'book': {
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'dynasty': book.dynasty,
                'description': book.description,
                'pages_count': len(created_pages)
            },
            'pages': created_pages
        })
        
    except ValueError as e:
        logger.error(f"创建古籍参数错误: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': '参数格式错误'
        }, status=400)
        
    except Exception as e:
        logger.error(f"创建古籍失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'创建失败: {str(e)}'
        }, status=500)