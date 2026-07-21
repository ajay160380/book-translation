from django.contrib import admin
from .models import Book, TranslationCache

admin.site.register(Book)
admin.site.register(TranslationCache)
