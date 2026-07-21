# Anuvad - The Intelligent Bilingual Book Reader

![Anuvad Reader](media/books/logo.png) <!-- Update logo path if applicable -->

Anuvad is a powerful, elegant web application that allows users to upload English PDF books and read them with side-by-side **Hindi** or **Hinglish** translations. Designed with a premium, distraction-free aesthetic, Anuvad brings a world-class reading experience to users who prefer consuming literature in their native language context.

## 🚀 Live Demo

**Experience Anuvad live:** [https://book-translation.onrender.com](https://book-translation.onrender.com)

## ✨ Key Features

- **Side-by-Side Bilingual Reading:** Upload any English PDF and instantly get contextual translations (Hindi or Hinglish) mapped page by page.
- **Smart Vocabulary Tracker:** Select any difficult word while reading to get its meaning and automatically save it to your personal vocabulary library.
- **AI-Powered "Ask Book":** Chat directly with your book. Ask questions about the plot, characters, or concepts, and the AI will answer based on the book's context.
- **Zen Mode (Focus Timer):** A built-in pomodoro-style focus timer with ambient background audio (rain, ocean, etc.) for a distraction-free reading session.
- **Intelligent Caching:** Translations are cached securely using Supabase (PostgreSQL), ensuring lightning-fast loads on subsequent reads.
- **Cloud Synchronization:** Google OAuth integration ensures your library, vocabulary, and reading progress are always synced and accessible anywhere.

## 🛠️ Technology Stack

- **Backend:** Django 5.x, Python 3.14
- **Database:** PostgreSQL (Supabase)
- **Frontend:** Vanilla JS, Custom CSS (Glassmorphism, Modern UI)
- **AI / Translation Engine:** Groq API (Llama 3)
- **Authentication:** Django Allauth (Google OAuth)
- **Hosting:** Render

## ⚙️ Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ajay160380/book-translation.git
   cd book-translation
   ```

2. **Set up Virtual Environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_groq_api_key
   DATABASE_URL=your_postgres_db_url
   GOOGLE_CLIENT_ID=your_google_oauth_client_id
   GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret
   ```

5. **Run Migrations & Server**
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```
   *Visit `http://127.0.0.1:8000` to start reading.*

## 📄 License

This project is open-source and available under the MIT License.
