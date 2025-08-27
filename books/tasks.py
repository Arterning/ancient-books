from celery import shared_task
from django.utils import timezone
from .models import OCRTask, BookPage, TextRegion
from .services.ocr_service import OCRService
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_ocr_task(task_id):

    """
    异步处理OCR任务
    
    Args:
        task_id: OCR任务ID
    """
    try:
        # 获取任务
        task = OCRTask.objects.get(id=task_id)
        page = task.page
        
        # 更新任务状态
        task.status = 'processing'
        task.started_at = timezone.now()
        task.save()
        
        # 更新页面状态
        page.ocr_status = 'processing'
        page.save()
        
        logger.info(f"开始处理OCR任务: {task_id}, 页面: {page.id}")
        
        # 初始化OCR服务
        ocr_service = OCRService()
        
        # 处理图片
        image_path = page.image.path
        text_regions = ocr_service.process_image(image_path)
        
        # 保存识别结果
        total_confidence = 0
        region_count = 0
        
        for region_data in text_regions:
            text_region = TextRegion.objects.create(
                page=page,
                region_id=region_data['region_id'],
                x=region_data['x'],
                y=region_data['y'],
                width=region_data['width'],
                height=region_data['height'],
                original_text=region_data['text'],
                confidence=region_data['confidence'],
                order_index=region_data['order_index']
            )
            
            total_confidence += region_data['confidence']
            region_count += 1
            
            logger.debug(f"保存文本区域: {text_region.region_id}, 文本: {region_data['text'][:50]}")
        
        # 计算平均置信度
        avg_confidence = total_confidence / region_count if region_count > 0 else 0
        
        # 更新页面状态
        page.ocr_status = 'completed'
        page.ocr_confidence = avg_confidence
        page.save()
        
        # 更新任务状态
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.save()
        
        logger.info(f"OCR任务完成: {task_id}, 识别了 {region_count} 个文本区域, 平均置信度: {avg_confidence:.2f}")
        
        return {
            'success': True,
            'regions_count': region_count,
            'avg_confidence': avg_confidence
        }
        
    except OCRTask.DoesNotExist:
        logger.error(f"OCR任务不存在: {task_id}")
        return {'success': False, 'error': '任务不存在'}
        
    except Exception as e:
        logger.error(f"OCR任务处理失败: {task_id}, 错误: {str(e)}")
        
        try:
            # 更新任务失败状态
            task.status = 'failed'
            task.error_message = str(e)
            task.completed_at = timezone.now()
            task.save()
            
            # 更新页面状态
            page.ocr_status = 'failed'
            page.save()
        except:
            pass
        
        return {'success': False, 'error': str(e)}


@shared_task
def batch_translate_book(book_id, target_language='zh-cn'):
    """
    批量翻译整本书
    
    Args:
        book_id: 书籍ID
        target_language: 目标语言
    """
    try:
        from .models import Book
        from .services.translation_service import TranslationService
        
        book = Book.objects.get(id=book_id)
        translation_service = TranslationService()
        
        total_regions = 0
        translated_regions = 0
        
        # 遍历所有页面
        for page in book.pages.all():
            # 遍历每个文本区域
            for region in page.text_regions.all():
                total_regions += 1
                
                # 跳过已翻译的区域
                if hasattr(region, 'translation'):
                    continue
                
                try:
                    # 获取要翻译的文本（优先校对后文本）
                    text_to_translate = region.original_text
                    if hasattr(region, 'correction'):
                        text_to_translate = region.correction.corrected_text
                    
                    # 翻译文本
                    translated_text = translation_service.translate_text(
                        text_to_translate, 
                        target_language
                    )
                    
                    # 保存翻译结果
                    from .models import Translation
                    Translation.objects.create(
                        text_region=region,
                        translated_text=translated_text,
                        translation_language=target_language,
                        translator_id=1,  # 系统用户
                        translation_method='auto'
                    )
                    
                    translated_regions += 1
                    logger.info(f"翻译完成: 区域 {region.id}")
                    
                except Exception as e:
                    logger.error(f"翻译失败: 区域 {region.id}, 错误: {str(e)}")
                    continue
        
        logger.info(f"批量翻译完成: 书籍 {book_id}, 总区域数: {total_regions}, 翻译数: {translated_regions}")
        
        return {
            'success': True,
            'total_regions': total_regions,
            'translated_regions': translated_regions
        }
        
    except Exception as e:
        logger.error(f"批量翻译失败: 书籍 {book_id}, 错误: {str(e)}")
        return {'success': False, 'error': str(e)}

@shared_task
def cleanup_old_ocr_tasks():
    """
    清理旧的OCR任务记录
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        # 删除30天前的已完成任务
        cutoff_date = timezone.now() - timedelta(days=30)
        
        deleted_count = OCRTask.objects.filter(
            status__in=['completed', 'failed'],
            completed_at__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"清理了 {deleted_count} 个旧OCR任务记录")
        
        return {'success': True, 'deleted_count': deleted_count}
        
    except Exception as e:
        logger.error(f"清理OCR任务失败: {str(e)}")
        return {'success': False, 'error': str(e)}