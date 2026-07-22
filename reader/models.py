from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator

class Book(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='books')
    title = models.CharField(max_length=255)
    pdf_file = models.FileField(
        upload_to='books/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class TranslationCache(models.Model):
    LANGUAGE_CHOICES = [
        ('hindi', 'Hindi'),
        ('hinglish', 'Hinglish'),
    ]
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='translations')
    page_number = models.IntegerField()
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='hindi')
    english_text = models.TextField()
    hindi_text = models.TextField()
    summary_text = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('book', 'page_number', 'language')

    def __str__(self):
        return f"{self.book.title} - Page {self.page_number} ({self.language})"


class Vocabulary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vocabulary')
    english_word = models.CharField(max_length=255)
    hindi_translation = models.CharField(max_length=255)
    context_sentence = models.TextField(blank=True, null=True)
    saved_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.english_word} -> {self.hindi_translation}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    onboarded = models.BooleanField(default=False)
    preferred_language = models.CharField(max_length=10, choices=[('hindi', 'Hindi'), ('hinglish', 'Hinglish')], default='hindi')
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

class ErrorLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=255)
    error_message = models.TextField()
    user_info = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"[{self.timestamp}] {self.action}: {self.error_message}"
