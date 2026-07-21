import os
import nltk
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)

def get_english_summary(text, sentences_count=3):
    """
    Extracts a summary from the given English text.
    If GROQ_API_KEY is available in the environment, it can be extended to use Groq.
    Currently falls back to an extractive summarizer (LSA via sumy).
    """
    if not text or not text.strip():
        return ""

    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, sentences_count)
        
        # Combine the summarized sentences
        summary_text = " ".join(str(sentence) for sentence in summary)
        return summary_text
    except Exception as e:
        print(f"Summarization error: {e}")
        # Fallback to just returning the first few sentences if sumy fails
        sentences = text.split('.')
        return '. '.join(sentences[:sentences_count]).strip() + '.'
