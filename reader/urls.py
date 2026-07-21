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
]
