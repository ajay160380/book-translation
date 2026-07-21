from django import forms
from .models import Book

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'pdf_file']

class UserProfileForm(forms.Form):
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    preferred_language = forms.ChoiceField(choices=[('hindi', 'Hindi'), ('hinglish', 'Hinglish')], required=True)
    bio = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Tell us a bit about yourself (optional)', 'rows': 3}), required=False)
