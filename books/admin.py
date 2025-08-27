from django.contrib import admin

# Register your models here.
from .models import Book, BookPage, OCRTask, TextRegion, TextCorrection, Translation

admin.site.register(Book)
admin.site.register(BookPage)
admin.site.register(OCRTask)
admin.site.register(TextRegion)
admin.site.register(TextCorrection)
admin.site.register(Translation)