import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.test import Client
from reader.models import Book

c = Client(SERVER_NAME='127.0.0.1')
c.login(username='testuser', password='password')

books = Book.objects.filter(user__username='testuser')
if not books.exists():
    print("No books to delete.")
else:
    book_id = books.first().id
    print("Attempting to delete book ID:", book_id)
    response = c.post(f'/delete_book/{book_id}/')
    print("Response status:", response.status_code)
    if response.status_code == 302:
        print("Redirects to:", response.url)
    
    still_exists = Book.objects.filter(id=book_id).exists()
    print("Book still exists?", still_exists)
