import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.test import Client
from reader.models import Book

c = Client(SERVER_NAME='127.0.0.1')
c.login(username='testuser', password='password')
with open('/Users/ajayvishwakarma/Desktop/godan.pdf', 'rb') as pdf_file:
    response = c.post('/dashboard/', {'title': 'Godan', 'pdf_file': pdf_file}, follow=True)

print("Status Code:", response.status_code)
if response.status_code == 200:
    print("Redirected to URL:", response.redirect_chain)
    print("Books in DB:", list(Book.objects.all().values('title', 'user__username')))
    if b'Upload failed' in response.content or b'A book named' in response.content:
        print("FOUND ERROR IN HTML!")
        if b'A book named' in response.content:
            print("DUPLICATE ERROR")
        else:
            print("FORM ERROR")
    else:
        print("UPLOAD SUCCESSFUL!")
else:
    print("ERROR:", response.status_code)
