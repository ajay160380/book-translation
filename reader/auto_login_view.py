from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import redirect

def auto_login(request):
    user, _ = User.objects.get_or_create(username='testuser')
    user.set_password('password')
    user.save()
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return redirect('dashboard')
