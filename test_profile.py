import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.test import Client
from django.contrib.auth.models import User
from reader.models import UserProfile

user, _ = User.objects.get_or_create(username='testuser', email='test@test.com')
user.set_password('password')
user.save()

profile, _ = UserProfile.objects.get_or_create(user=user)
profile.onboarded = True
profile.save()

c = Client()
c.login(username='testuser', password='password')
response = c.get('/profile/')
print("Profile Response Status Code:", response.status_code)
if response.status_code == 302:
    print("Redirect Location:", response.url)
