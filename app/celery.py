
# celery.py (项目根目录)
import os
from celery import Celery

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

app = Celery('books')

# 使用Django配置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现任务
app.autodiscover_tasks()

# 配置任务路由
app.conf.task_routes = {
    'books.tasks.process_ocr_task': {'queue': 'ocr'},
    'books.tasks.batch_translate_book': {'queue': 'translation'},
    'books.tasks.cleanup_old_ocr_tasks': {'queue': 'maintenance'},
}

# 配置任务调度
app.conf.beat_schedule = {
    'cleanup-ocr-tasks': {
        'task': 'books.tasks.cleanup_old_ocr_tasks',
        'schedule': 86400.0,  # 每天执行一次
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')