
# urls.py
from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('', views.book_list, name='book_list'),
    path('create/', views.create_book, name='create_book'),
    path('book/<int:book_id>/', views.book_detail, name='book_detail'),
    path('book/<int:book_id>/upload/', views.upload_pages, name='upload_pages'),
    path('page/<int:page_id>/editor/', views.page_editor, name='page_editor'),
    path('page/<int:page_id>/data/', views.get_page_data, name='get_page_data'),
    path('page/<int:page_id>/ocr-status/', views.check_ocr_status, name='check_ocr_status'),
    path('region/<int:region_id>/correct/', views.save_correction, name='save_correction'),
    path('region/<int:region_id>/translate/', views.translate_region, name='translate_region'),
]