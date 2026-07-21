<div align="center">
  
# 📖 Anuvad.ai — The Ultimate PDF Translator
**Read any English PDF book in natural Hindi or Hinglish without losing the layout.**

[![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![PDF.js](https://img.shields.io/badge/PDF.js-FF0000?style=for-the-badge&logo=adobeacrobatreader&logoColor=white)](https://mozilla.github.io/pdf.js/)
[![Google Translate](https://img.shields.io/badge/Translation-4285F4?style=for-the-badge&logo=google&logoColor=white)](#)

</div>

<br>

Anuvad.ai is a premium, minimal, and highly optimized web application that allows users to upload English PDF books and instantly read them side-by-side in **Hindi** or **Hinglish** (Romanized Hindi).

Unlike traditional translation tools that destroy the formatting of PDFs, Anuvad renders the original PDF intact and uses **On-Demand Lazy Loading** to translate the text of the *current page* you are reading in real time.

---

## ✨ Features

- **🎨 Luxury Brutalist UI**: A stunning, premium "Swiss Minimalist" design using `Clash Display` and `Satoshi` typography.
- **📄 Pixel-Perfect PDF Rendering**: Renders your actual PDF on the left pane exactly as published using `pdf.js`.
- **⚡ Lazy "On-Demand" Translation**: Translations only run for the specific page you are looking at, saving massive API costs and rendering instantly.
- **🇮🇳 Hindi & Hinglish Support**: Read in pure Devanagari Hindi, or switch instantly to **Hinglish** (*e.g., "yudh ki kala rajya ke liye atyant mahatvapurn hai"*).
- **🧠 Smart Formatting & Watermark Removal**: Automatically detects and drops annoying URL footers/watermarks and perfectly re-constructs paragraphs that PDF extractors normally break.
- **💾 Local Database Caching**: Once a page is translated, it's saved locally to SQLite. Re-reading a page loads in `<50ms`.

---

## 🏗️ Architecture & Workflow

Here is how the translation engine works under the hood when a user flips a page:

```mermaid
sequenceDiagram
    participant User 
    participant Browser (PDF.js)
    participant Django Backend
    participant SQLite Cache
    participant Google Translate API

    User->>Browser (PDF.js): Flips to Page 2
    Browser (PDF.js)->>Browser (PDF.js): Renders PDF Canvas visually
    Browser (PDF.js)->>Browser (PDF.js): Extracts raw text & coordinates
    Browser (PDF.js)->>Browser (PDF.js): Reconstructs Paragraphs & Removes Watermarks
    Browser (PDF.js)->>Django Backend: POST /api/translate-page/ (english_text, page_number)
    
    Django Backend->>SQLite Cache: Check if translation exists?
    
    alt Cache Hit
        SQLite Cache-->>Django Backend: Returns saved Hindi/Hinglish text
    else Cache Miss
        Django Backend->>Google Translate API: Translate English -> Hindi
        Google Translate API-->>Django Backend: Returns Hindi (Devanagari)
        
        alt Mode = Hinglish
            Django Backend->>Google Translate API: Request dt=rm (Romanization)
            Google Translate API-->>Django Backend: Returns Hinglish (Roman script)
        end
        
        Django Backend->>SQLite Cache: Save new translation to database
    end
    
    Django Backend-->>Browser (PDF.js): Return Translated Text
    Browser (PDF.js)-->>User: Display beautifully on Right Pane
```

---

## 🛠️ Translation Logic Pipeline

We employ a multi-step extraction and translation pipeline to ensure maximum accuracy:

```mermaid
graph TD
    A[Raw PDF Text] --> B{Text Coordinate Check};
    B -- Y-Axis Delta > 5 --> C[Insert Paragraph Break];
    B -- Same Line --> D[Add Space];
    C --> E[Combined English String];
    D --> E;
    
    E --> F[Regex Watermark Filter];
    F -- Detects URLs/Headers --> G[Strip URL];
    G --> H{Is line empty or just a number?};
    H -- Yes --> I[Drop Line Completely];
    H -- No --> J[Keep Cleaned Text];
    
    J --> K[Send to Backend];
```

---

## 🚀 Setup & Installation

Follow these steps to run Anuvad.ai on your local machine.

### 1. Clone the repository
```bash
git clone https://github.com/ajay160380/book-translation.git
cd book-translation
```

### 2. Create a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Migrations
Sets up the SQLite database and translation cache schemas.
```bash
python manage.py migrate
```

### 5. Start the Development Server
```bash
python manage.py runserver
```

Open your browser and navigate to **`http://127.0.0.1:8000/`**. Upload a PDF and start reading!

---

## 📂 Project Structure

```text
book-translation/
├── config/                 # Django settings & routing
├── reader/                 # Core translation app
│   ├── models.py           # Book & TranslationCache schemas
│   ├── views.py            # API logic and page serving
│   └── urls.py             # App routing
├── templates/
│   └── reader/
│       ├── upload.html     # The Landing/Upload page
│       └── reader.html     # The Split-Screen reader UI
├── requirements.txt        # Python dependencies
└── manage.py               # Django entrypoint
```

---

*Designed and Built by Ajay Vishwakarma. Contributions by aryamady.*
