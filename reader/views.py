import os
import json
import requests as http_requests
from dotenv import load_dotenv
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from deep_translator import GoogleTranslator
from .models import Book, TranslationCache, Vocabulary, UserProfile, ErrorLog
from .forms import BookForm, UserProfileForm
from .hinglish_engine import translate_to_natural_hinglish
from gtts import gTTS
from io import BytesIO
import google.generativeai as genai

# g4f for free AI Fallback
from g4f.client import Client as G4FClient

# Load environment variables from .env file
load_dotenv()

# ── Groq Config (for premium Hinglish) ──
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_AVAILABLE = bool(GROQ_API_KEY)

if GROQ_AVAILABLE:
    from groq import Groq


def landing_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    # Use landing.html instead of upload.html
    return render(request, 'reader/landing.html')

@login_required(login_url='/')
def dashboard(request):
    if not hasattr(request.user, 'profile') or not request.user.profile.onboarded:
        return redirect('onboarding')

    error = None
    if request.method == 'POST':
        try:
            ErrorLog.objects.create(action="Dashboard POST", error_message="Received POST request", user_info=request.user.username)
            if not request.user.is_authenticated:
                return redirect('landing_page')
                
            form = BookForm(request.POST, request.FILES)
            if form.is_valid():
                title = form.cleaned_data.get('title')
                existing_book = Book.objects.filter(title__iexact=title, user=request.user).first()
                if existing_book:
                    ErrorLog.objects.create(action="Dashboard Upload Duplicate", error_message="Redirecting to existing book", user_info=request.user.username)
                    return redirect('reader_view', book_id=existing_book.id)
                else:
                    new_book = form.save(commit=False)
                    new_book.user = request.user
                    new_book.save()
                    ErrorLog.objects.create(action="Dashboard Upload Success", error_message=f"Book {new_book.id} saved", user_info=request.user.username)
                    return redirect('reader_view', book_id=new_book.id)
            else:
                error_msgs = []
                for field, errors in form.errors.items():
                    for err in errors:
                        error_msgs.append(f"{field}: {err}")
                error = "Upload failed: " + " | ".join(error_msgs)
                ErrorLog.objects.create(action="Dashboard Form Invalid", error_message=error, user_info=request.user.username)
        except Exception as e:
            import traceback
            error = "Upload crashed: " + str(e)
            ErrorLog.objects.create(action="Dashboard Exception", error_message=traceback.format_exc(), user_info=request.user.username)
    else:
        form = BookForm()
        
    books = Book.objects.filter(user=request.user).annotate(pages_translated=Count('translations')).order_by('-uploaded_at')
    
    total_books = books.count()
    total_pages_translated = TranslationCache.objects.filter(book__user=request.user).count()
    recent_book = books.first() if total_books > 0 else None
    
    # Translation DNA calculation
    all_translations = TranslationCache.objects.filter(book__user=request.user)
    total_pages_translated = all_translations.count()
    hindi_count = all_translations.filter(language='hindi').count()
    hinglish_count = all_translations.filter(language='hinglish').count()
    
    hindi_percent = int((hindi_count / total_pages_translated * 100)) if total_pages_translated > 0 else 50
    hinglish_percent = 100 - hindi_percent if total_pages_translated > 0 else 50
    
    # Fetch the latest summary
    latest_translation = TranslationCache.objects.filter(book__user=request.user).exclude(summary_text='').order_by('-id').first()
    latest_summary = latest_translation.summary_text if latest_translation and latest_translation.summary_text else None
    latest_summary_book = latest_translation.book.title if latest_translation else None

    context = {
        'form': form,
        'books': books,
        'error': error,
        'total_books': total_books,
        'total_pages_translated': total_pages_translated,
        'recent_book': recent_book,
        'hindi_percent': hindi_percent,
        'hinglish_percent': hinglish_percent,
        'latest_summary': latest_summary,
        'latest_summary_book': latest_summary_book
    }
    
    return render(request, 'reader/dashboard.html', context)


@login_required(login_url='/')
def onboarding(request):
    # If they are already onboarded, send them to dashboard
    if hasattr(request.user, 'profile') and request.user.profile.onboarded:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            # Update user details
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.save()

            # Create or update profile
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.preferred_language = form.cleaned_data['preferred_language']
            profile.bio = form.cleaned_data['bio']
            profile.onboarded = True
            profile.save()

            return redirect('dashboard')
    else:
        # Pre-fill if Google gave us their name
        form = UserProfileForm(initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
        })

    return render(request, 'reader/onboarding.html', {'form': form})

@login_required(login_url='/')
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.save()
            
            profile.preferred_language = form.cleaned_data['preferred_language']
            profile.bio = form.cleaned_data['bio']
            profile.save()
            return redirect('profile_view')
    else:
        form = UserProfileForm(initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'preferred_language': profile.preferred_language,
            'bio': profile.bio,
        })
        
    stats = {
        'total_books': request.user.books.count(),
        'total_pages_translated': TranslationCache.objects.filter(book__user=request.user).count(),
        'vocab_saved': request.user.vocabulary.count()
    }
    
    return render(request, 'reader/profile.html', {'form': form, 'profile': profile, 'stats': stats})


@login_required(login_url='/')
def delete_book(request, book_id):
    if request.method == 'POST':
        book = get_object_or_404(Book, id=book_id, user=request.user)
        book.pdf_file.delete(save=False) # delete physical file
        book.delete() # delete db entry
    return redirect('dashboard')

def register_user(request):
    if request.method == 'POST':
        data = request.POST
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        if not username or not email or not password or not confirm_password:
            return render(request, 'reader/landing.html', {'auth_error': 'All fields are required', 'auth_action': 'register'})
            
        if password != confirm_password:
            return render(request, 'reader/landing.html', {'auth_error': 'Passwords do not match', 'auth_action': 'register'})
            
        if User.objects.filter(username=username).exists():
            return render(request, 'reader/landing.html', {'auth_error': 'Username already exists', 'auth_action': 'register'})
            
        if User.objects.filter(email=email).exists():
            return render(request, 'reader/landing.html', {'auth_error': 'Email already registered', 'auth_action': 'register'})
            
        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        # Force redirect to dashboard
        return redirect('dashboard')
    return redirect('landing_page')

def login_user(request):
    if request.method == 'POST':
        data = request.POST
        username = data.get('username')
        password = data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next', 'dashboard')
            return redirect(next_url)
        else:
            return render(request, 'reader/landing.html', {'auth_error': 'Invalid credentials', 'auth_action': 'login'})
    return redirect('landing_page')

def logout_user(request):
    logout(request)
    return redirect('landing_page')


def reader_view(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    return render(request, 'reader/reader.html', {'book': book})

import re

def _clean_hindi_ocr(text):
    """Fix common Hindi PDF/OCR extraction errors using regex patterns."""
    
    # Devanagari matra characters (dependent vowel signs)
    # These should NEVER appear with a space before them - they attach to the previous consonant
    matras = 'ा ि ी ु ू ृ ॄ ॅ ॆ े ै ॉ ॊ ो ौ ् ं ँ ः'
    matra_chars = matras.replace(' ', '')
    
    # 1. Remove spaces BEFORE any matra (most critical fix)
    #    e.g., "ल ूँगा" -> "लूँगा", "मा ॅूँने" -> "माॅूँने"
    text = re.sub(r'(\S) ([' + matra_chars + r'])', r'\1\2', text)
    # Run it twice to catch double-spaced matras
    text = re.sub(r'(\S) ([' + matra_chars + r'])', r'\1\2', text)
    
    # 2. Fix ॅ (Candra E) - often a broken chandrabindu, should usually be ँ or ं
    #    "माॅूँ" type patterns - remove extra ॅ when ँ is already present
    text = re.sub(r'ॅ([ँं])', r'\1', text)
    #    Standalone ॅू -> ूँ  (common corruption pattern)
    text = re.sub(r'ॅू', r'ूँ', text)
    #    Standalone ॅ before consonants -> ँ
    text = re.sub(r'ॅ(?=[क-ह])', r'ँ', text)
    #    Remaining standalone ॅ at end of word -> ँ
    text = re.sub(r'ॅ(?=\s|$|[,।\.])', r'ँ', text)
    
    # 3. Fix broken halant/virama combinations
    #    "क् या" -> "क्या"
    text = re.sub(r'(्) +', r'\1', text)
    
    # 4. Fix double matras (impossible in correct Hindi)
    #    "ूू" -> "ू", "ीी" -> "ी" etc.
    for m in matra_chars:
        text = text.replace(m + m, m)
    
    # 5. Clean up multiple spaces
    text = re.sub(r'  +', ' ', text)
    
    # 6. Fix common character substitution errors from PDF encoding
    #    These are specific patterns seen in corrupted Godan/Premchand PDFs
    common_fixes = {
        'लेककन': 'लेकिन',
        'नजसे': 'जिसे', 
        'कदखा': 'दिखा',
        'नहश': 'नहीं',
        'धननया': 'धनिया',
        'भकत': 'भक्त',
        'कक ': 'कि ',
        'ककसी': 'किसी',
        'ककसान': 'किसान',
        'चाकहए': 'चाहिए',
        'लड़ककय': 'लड़कीय',
        'ककया': 'किया',
        'ककस': 'किस',
    }
    for wrong, right in common_fixes.items():
        text = text.replace(wrong, right)
    
    return text.strip()


def _translate_conversational_hindi(text):
    """Translate English to conversational Hindi or fix broken Hindi PDF text using LLM."""
    # Always clean OCR errors first
    text = _clean_hindi_ocr(text)
    
    # Try free AI first for fixing/translating
    try:
        g4f_client = G4FClient()
        system_prompt = (
            "You are an expert Hindi translator and editor. The user will provide text extracted from a PDF. "
            "Your ONLY job is to output perfectly readable and grammatically flawless Hindi IN DEVANAGARI SCRIPT (हिंदी). "
            "If the input text is in English, translate it to natural, conversational Hindi written STRICTLY in Devanagari script. "
            "DO NOT use Latin/English letters for the Hindi translation. DO NOT output Hinglish. "
            "DO NOT output any conversational padding or notes. ONLY output the final translated text."
        )
        completion = g4f_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]
        )
        result = completion.choices[0].message.content.strip()
        if result and len(result) > 10:
            return result
    except Exception as e:
        print("g4f Hindi translation failed:", e)

    # Fallback to Groq if key is available
    if GROQ_AVAILABLE:
        try:
            client = Groq(api_key=GROQ_API_KEY)
            system_prompt = (
                "You are an expert Hindi proofreader and editor. The user will provide text extracted from a Hindi PDF that contains severe OCR and extraction errors. "
                "Your ONLY job is to heavily edit and fix all broken words, wrong matras, weird spacing, and jumbled characters (e.g., 'ल ूँगा' -> 'लूँगा', 'लेककन' -> 'लेकिन', 'क् या' -> 'क्या', 'स्त्र ी' -> 'स्त्री'). "
                "Reconstruct the text so it is 100% perfectly readable and grammatically flawless Hindi.\n"
                "If the input text is in English, translate it to natural, conversational Hindi, keeping common English words (like Energy, System) in Devanagari.\n"
                "DO NOT output any conversational padding or notes. ONLY output the final corrected/translated text."
            )
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.1
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print("Groq translation failed:", e)

    # Ultimate fallback: use Google Translator
    try:
        return _translate_chunks_hindi(text)
    except Exception:
        return text

def _translate_chunks_hindi(text):
    """Translate English text to Hindi (Devanagari) using deep-translator."""
    translator = GoogleTranslator(source='auto', target='hi')
    chunks = [text[i:i + 4500] for i in range(0, len(text), 4500)]
    result = ""
    for chunk in chunks:
        translated = translator.translate(chunk)
        if translated:
            result += translated + " "
    return result.strip()


def _translate_chunks_english(text):
    """Translate text to English using free AI (g4f) or deep-translator."""
    # Try free AI first
    try:
        g4f_client = G4FClient()
        prompt = (
            "You are an expert translator. The user will provide text that might be broken Hindi (OCR errors) or Hinglish. "
            "Please translate it into highly readable, fluent, and conversational English. "
            "If the input is broken, guess the intended meaning and provide the correct English translation. "
            "Do not add any notes, just output the English text."
        )
        completion = g4f_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt + "\n\nText:\n" + text}]
        )
        result = completion.choices[0].message.content.strip()
        if result and len(result) > 10:
            return result
    except Exception as e:
        print("g4f English translation failed:", e)

    # Fallback to Google Translate
    translator = GoogleTranslator(source='auto', target='en')
    chunks = [text[i:i + 4500] for i in range(0, len(text), 4500)]
    result = ""
    for chunk in chunks:
        translated = translator.translate(chunk)
        if translated:
            result += translated + " "
    return result.strip()


def _translate_to_hinglish(english_text):
    """
    Translate text to conversational Hinglish (romanized Hindi) using free AI (g4f)
    or fallback to Google Translate.
    """
    # Try free AI first for natural conversational Hinglish
    try:
        g4f_client = G4FClient()
        prompt = (
            "You are a native Indian speaker. Translate or rewrite the following text into simple, easy-to-read 'Hinglish' (Hindi written in English alphabet). "
            "Make it highly conversational, exactly how young Indians text on WhatsApp (e.g., use 'kya', 'hai', 'main', 'kyun'). "
            "If the input is broken Hindi, figure out the meaning and rewrite it properly in Hinglish. "
            "DO NOT use pure English. DO NOT use Devanagari script. DO NOT add any notes, explanations, or quotes. Output ONLY the Hinglish text."
        )
        completion = g4f_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt + "\n\nText:\n" + english_text}]
        )
        result = completion.choices[0].message.content.strip()
        
        # Sometime g4f fails to return anything, check length
        if result and len(result) > 10:
            # Remove any surrounding quotes
            if result.startswith('"') and result.endswith('"'):
                result = result[1:-1]
            return result
    except Exception as e:
        print("g4f Hinglish failed:", e)

    # Fallback: English -> Hindi -> Romanized Google Translate
    hindi_text = _translate_conversational_hindi(english_text)

    if not hindi_text:
        return english_text

    url = "https://translate.googleapis.com/translate_a/single"
    chunk_size = 4500
    hindi_chunks = [hindi_text[i:i + chunk_size] for i in range(0, len(hindi_text), chunk_size)]
    romanized_parts = []

    for chunk in hindi_chunks:
        try:
            params = {
                'client': 'gtx',
                'sl': 'hi',
                'tl': 'en',
                'dt': 'rm'
            }
            response = http_requests.post(url, params=params, data={'q': chunk}, timeout=15)
            data = response.json()

            if data and data[0]:
                for segment in data[0]:
                    if segment and len(segment) > 3 and segment[3]:
                        romanized_parts.append(segment[3])
                    elif segment and segment[0]:
                        romanized_parts.append(segment[0])
            else:
                romanized_parts.append(chunk)
        except Exception:
            romanized_parts.append(chunk)

    return " ".join(romanized_parts).strip()


def translate_page(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            book_id = data.get('book_id')
            page_number = data.get('page_number')
            english_text = data.get('english_text', '').strip()
            language = data.get('language', 'hindi')
            force_refresh = data.get('force_refresh', False)

            if language not in ('hindi', 'hinglish', 'english'):
                language = 'hindi'

            if not all([book_id, page_number, english_text]):
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            book = get_object_or_404(Book, id=book_id)

            # ── Check cache ──
            if not force_refresh:
                cache_entry = TranslationCache.objects.filter(
                    book=book, page_number=page_number, language=language
                ).first()
                if cache_entry:
                    return JsonResponse({
                        'hindi_text': cache_entry.hindi_text,
                        'summary_text': cache_entry.summary_text or '',
                        'language': language
                    })

            # ── Translate ──
            if language == 'hindi':
                # Use conversational Hindi by default for 'hindi' mode
                translated_text = _translate_conversational_hindi(english_text)
            elif language == 'hinglish':
                translated_text = _translate_to_hinglish(english_text)
            elif language == 'english':
                translated_text = _translate_chunks_english(english_text)
            else:
                return JsonResponse({'error': 'Unsupported language'}, status=400)

            # ── Save to cache ──
            if force_refresh:
                TranslationCache.objects.filter(book=book, page_number=page_number, language=language).delete()
                
            TranslationCache.objects.get_or_create(
                book=book,
                page_number=page_number,
                language=language,
                defaults={
                    'english_text': english_text,
                    'hindi_text': translated_text,
                    'summary_text': ""
                }
            )

            return JsonResponse({
                'hindi_text': translated_text, 
                'summary_text': "",
                'language': language
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


def text_to_speech(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            text = data.get('text', '')
            lang = data.get('language', 'hindi')
            
            if not text:
                return JsonResponse({'error': 'No text provided'}, status=400)

            # gTTS language code
            gtts_lang = 'hi' if lang in ['hindi', 'hinglish'] else 'en'
            
            # Using gTTS to generate natural Google voice
            tts = gTTS(text=text, lang=gtts_lang, slow=False)
            fp = BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            
            return HttpResponse(fp.read(), content_type="audio/mpeg")
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required(login_url='/')
def ask_book(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            question = data.get('question', '').strip()
            page_text = data.get('page_text', '').strip()
            
            if not question:
                return JsonResponse({'error': 'No question provided'}, status=400)
                
            prompt = f"You are a helpful and intelligent reading tutor. The user is reading a book (which might be in Hindi, English, or Hinglish) and is asking a question about the current page.\n\nCurrent Page Text:\n{page_text}\n\nUser Question: {question}\n\nCRITICAL INSTRUCTIONS:\n1. Answer the question concisely and clearly based on the page text.\n2. ALWAYS reply in the exact language the user used in their question! If they ask in 'Hinglish' (e.g., 'hinglish me batao', 'kya ho raha hai'), you MUST reply in Hinglish! If they ask in Hindi, reply in Hindi.\n3. Do NOT say 'the text is in English'. Just explain what is happening."
            
            try:
                # Try Gemini if key exists
                api_key = os.getenv('GEMINI_API_KEY')
                if api_key:
                    import google.generativeai as genai
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(prompt)
                    return JsonResponse({'answer': response.text})
            except Exception:
                pass
                
            # Fallback to g4f
            client = G4FClient()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
            )
            return JsonResponse({'answer': response.choices[0].message.content})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)
