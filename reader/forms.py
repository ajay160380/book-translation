import filetype
from django import forms
from .models import Book
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'pdf_file']
        
    def clean_pdf_file(self):
        file = self.cleaned_data.get('pdf_file', False)
        if file:
            if file.size > 50 * 1024 * 1024:
                raise ValidationError("PDF file too large ( > 50mb )")
                
            # Read first 2048 bytes for magic validation
            file_header = file.read(2048)
            file.seek(0)
            kind = filetype.guess(file_header)
            
            if kind is None or kind.mime != 'application/pdf':
                raise ValidationError("Uploaded file is not a valid PDF document.")
                
        return file

class UserProfileForm(forms.Form):
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    preferred_language = forms.ChoiceField(choices=[('hindi', 'Hindi'), ('hinglish', 'Hinglish')], required=True)
    bio = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Tell us a bit about yourself (optional)', 'rows': 3}), required=False)

class RegisterForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    password = forms.CharField(min_length=8, widget=forms.PasswordInput, required=True)
    confirm_password = forms.CharField(min_length=8, widget=forms.PasswordInput, required=True)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match")
            
        if User.objects.filter(username=cleaned_data.get("username")).exists():
            raise ValidationError("Username already exists")
            
        if User.objects.filter(email=cleaned_data.get("email")).exists():
            raise ValidationError("Email already registered")

class PageTranslationForm(forms.Form):
    book_id = forms.IntegerField(required=True)
    page_number = forms.IntegerField(required=True)
    english_text = forms.CharField(required=True, max_length=10000)
    language = forms.ChoiceField(choices=[('hindi', 'Hindi'), ('hinglish', 'Hinglish'), ('english', 'English')], required=False)
    force_refresh = forms.BooleanField(required=False)

class AskBookForm(forms.Form):
    question = forms.CharField(required=True, max_length=1000)
    page_text = forms.CharField(required=True, max_length=10000)

class TTSForm(forms.Form):
    text = forms.CharField(required=True, max_length=5000)
    language = forms.ChoiceField(choices=[('hindi', 'Hindi'), ('hinglish', 'Hinglish'), ('english', 'English')], required=False)

