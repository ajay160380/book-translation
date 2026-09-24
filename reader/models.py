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
    cover_color = models.IntegerField(default=0, help_text="Index for gradient color theme (0-7)")

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


class ReadingProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reading_progress')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='progress')
    current_page = models.IntegerField(default=1)
    total_pages = models.IntegerField(default=0)
    last_read_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'book')

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.current_page}/{self.total_pages})"

    @property
    def percent(self):
        if self.total_pages <= 0:
            return 0
        return min(int(self.current_page / self.total_pages * 100), 100)


class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='bookmarks')
    page_number = models.IntegerField()
    note = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book', 'page_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"Bookmark: {self.book.title} p.{self.page_number}"


class BookTag(models.Model):
    COLORS = [
        ('#8b5cf6', 'Purple'), ('#06b6d4', 'Cyan'), ('#f59e0b', 'Amber'),
        ('#ef4444', 'Red'), ('#10b981', 'Green'), ('#ec4899', 'Pink'),
        ('#3b82f6', 'Blue'), ('#f97316', 'Orange'),
    ]
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, choices=COLORS, default='#8b5cf6')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tags')

    class Meta:
        unique_together = ('name', 'user')

    def __str__(self):
        return self.name


class BookTagAssignment(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='tag_assignments')
    tag = models.ForeignKey(BookTag, on_delete=models.CASCADE, related_name='assignments')

    class Meta:
        unique_together = ('book', 'tag')

    def __str__(self):
        return f"{self.book.title} → {self.tag.name}"

