from django.urls import path
from . import views
urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('delete_book/<int:book_id>/', views.delete_book, name='delete_book'),
    path('register/', views.register_user, name='register_user'),
    path('login/', views.login_user, name='login_user'),
    path('logout/', views.logout_user, name='logout_user'),
    path('read/<int:book_id>/', views.reader_view, name='reader_view'),
    path('api/translate-page/', views.translate_page, name='translate_page'),
    path('api/tts/', views.text_to_speech, name='text_to_speech'),
    path('api/ask-book/', views.ask_book, name='ask_book'),
    path('onboarding/', views.onboarding, name='onboarding'),
    path('profile/', views.profile_view, name='profile_view'),
    # New feature APIs
    path('api/progress/', views.api_update_progress, name='api_update_progress'),
    path('api/bookmark/', views.api_toggle_bookmark, name='api_toggle_bookmark'),
    path('api/bookmarks/<int:book_id>/', views.api_get_bookmarks, name='api_get_bookmarks'),
    path('api/note/', views.api_save_note, name='api_save_note'),
    path('api/tags/', views.api_manage_tags, name='api_manage_tags'),
]
