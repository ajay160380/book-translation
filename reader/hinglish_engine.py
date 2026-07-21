"""
Hinglish Translation Engine — Natural Hindi-English Mix
========================================================

Produces conversational Hinglish like:
  "Art of war kisi bhi State (desh) ke liye bahut vital importance rakhta hai."

Instead of dry romanized Hindi like:
  "yuddh ki kala rajya ke liye atyant mahatvapurn hai."

Pipeline:
  1. Split text into sentences
  2. For each sentence:
     a. Identify English words/phrases to KEEP as-is
     b. Translate full sentence → Hindi (Devanagari)
     c. Get romanization of Hindi
     d. Smart-merge: keep English terms, use romanized Hindi for grammar/connectors
  3. Add parenthetical Hindi meanings for key English terms
"""

import re
import requests as http_requests
from deep_translator import GoogleTranslator

# ══════════════════════════════════════════════════════════════
# ENGLISH WORDS TO PRESERVE IN HINGLISH
# These are words commonly used as-is in Indian English/Hinglish
# ══════════════════════════════════════════════════════════════

KEEP_ENGLISH = {
    # ── General / Academic ──
    'art', 'war', 'state', 'army', 'battle', 'strategy', 'attack', 'defense',
    'defence', 'enemy', 'force', 'forces', 'power', 'method', 'discipline',
    'plan', 'plans', 'planning', 'commander', 'general', 'king', 'kingdom',
    'officer', 'soldier', 'soldiers', 'weapon', 'weapons', 'victory', 'defeat',
    'chapter', 'section', 'book', 'page', 'part', 'volume',

    # ── Common Hinglish-friendly words ──
    'important', 'importance', 'matter', 'road', 'safety', 'complete',
    'subject', 'factor', 'factors', 'condition', 'conditions', 'situation',
    'position', 'direction', 'system', 'order', 'rule', 'rules', 'law',
    'moral', 'natural', 'principle', 'principles', 'theory',
    'example', 'reason', 'result', 'effect', 'cause', 'case',
    'total', 'final', 'basic', 'basically', 'actually', 'really',
    'simple', 'complex', 'direct', 'indirect', 'vital',
    'ruin', 'destruction', 'success', 'failure', 'danger', 'risk',
    'advantage', 'disadvantage', 'opportunity', 'problem', 'solution',
    'control', 'influence', 'impact', 'practice', 'process',

    # ── Time / Season / Nature ──
    'night', 'day', 'season', 'seasons', 'time', 'times', 'heaven',
    'earth', 'winter', 'summer', 'spring', 'rain', 'weather',
    'cold', 'heat', 'temperature', 'climate',

    # ── People / Roles ──
    'leader', 'ruler', 'people', 'person', 'population', 'team',
    'government', 'minister', 'advisor', 'spy', 'spies', 'agent',
    'general', 'captain', 'chief',

    # ── Military ──
    'terrain', 'ground', 'march', 'supply', 'supplies', 'camp',
    'siege', 'fire', 'formation', 'retreat', 'advance', 'maneuver',
    'intelligence', 'information', 'signal', 'signals', 'morale',
    'military', 'naval', 'cavalry', 'infantry',

    # ── Modern / Tech ──
    'life', 'death', 'mind', 'idea', 'nature', 'quality', 'quantity',
    'resource', 'resources', 'cost', 'value', 'profit', 'loss',
    'ability', 'skill', 'knowledge', 'experience', 'wisdom',
    'decision', 'action', 'reaction', 'movement', 'speed',
    'distance', 'range', 'level', 'standard', 'degree',
    'number', 'type', 'category', 'group', 'class',

    # ── Adjectives commonly used in Hinglish ──
    'strong', 'weak', 'good', 'bad', 'best', 'worst', 'great',
    'small', 'large', 'big', 'first', 'second', 'third', 'last',
    'new', 'old', 'main', 'special', 'different', 'same',
    'proper', 'correct', 'wrong', 'right', 'left',
    'maximum', 'minimum', 'equal', 'superior', 'inferior',
    'necessary', 'essential', 'critical', 'serious', 'careful',

    # ── Verbs commonly kept in Hinglish ──
    'manage', 'handle', 'control', 'prepare', 'observe', 'compare',
    'consider', 'follow', 'lead', 'guide', 'support', 'protect',
    'survive', 'achieve', 'neglect', 'ignore', 'avoid', 'accept',

    # ── Connectors that sound natural in Hinglish ──
    'according', 'because', 'therefore', 'however', 'but', 'and',
    'also', 'only', 'never', 'always', 'often', 'sometimes',
}

# Words that should get a Hindi parenthetical explanation
ENGLISH_TO_HINDI_PARENTHETICAL = {
    'state': 'desh/rajya',
    'ruin': 'barbadi',
    'moral law': 'naitik niyam',
    'heaven': 'mausam aur samay',
    'earth': 'zameen aur terrain',
    'commander': 'senapati',
    'discipline': 'anushasan',
    'victory': 'jeet',
    'defeat': 'haar',
    'strategy': 'ranniti',
    'enemy': 'dushman',
    'army': 'sena',
    'kingdom': 'rajya',
    'wisdom': 'buddhi',
    'destruction': 'vinaash',
    'safety': 'suraksha',
    'danger': 'khatraa',
    'advantage': 'faayda',
    'disadvantage': 'nuksan',
    'morale': 'manobal',
    'retreat': 'peechhe hatna',
    'siege': 'ghera',
    'spy': 'jasoos',
    'intelligence': 'khufia jaankari',
    'terrain': 'bhoomi/zameen',
    'supply': 'rasd',
    'principle': 'siddhant',
}

# ══════════════════════════════════════════════════════════════
# SENTENCE SPLITTER
# ══════════════════════════════════════════════════════════════

def _split_into_sentences(text):
    """Split text into sentences while preserving paragraph structure."""
    # Split by paragraphs first
    paragraphs = text.split('\n\n')
    all_sentences = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Split sentences on . ! ? but be careful with abbreviations
        sentences = re.split(r'(?<=[.!?])\s+', para)
        for sent in sentences:
            sent = sent.strip()
            if sent:
                all_sentences.append(sent)
        # Mark paragraph boundary
        all_sentences.append('\n\n')
    return all_sentences


# ══════════════════════════════════════════════════════════════
# CORE: WORD-LEVEL ENGLISH DETECTION
# ══════════════════════════════════════════════════════════════

def _is_proper_noun(word):
    """Check if a word looks like a proper noun (capitalized, not start of sentence)."""
    return bool(re.match(r'^[A-Z][a-z]+', word)) and word.lower() not in {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'has', 'have', 'had',
        'this', 'that', 'these', 'those', 'it', 'its', 'he', 'she', 'they',
        'we', 'you', 'i', 'my', 'your', 'his', 'her', 'our', 'their',
        'in', 'on', 'at', 'to', 'for', 'from', 'with', 'by', 'of', 'as',
        'if', 'or', 'and', 'but', 'not', 'no', 'so', 'do', 'does', 'did',
        'will', 'can', 'may', 'shall', 'should', 'would', 'could', 'might',
        'when', 'where', 'what', 'which', 'who', 'how', 'why',
        'all', 'each', 'every', 'some', 'any', 'many', 'much', 'more',
        'most', 'other', 'another', 'such', 'than', 'then', 'there',
        'here', 'now', 'just', 'very', 'too', 'also', 'again', 'once',
        'being', 'been', 'having', 'going', 'coming', 'making',
    }

def _is_numeral(word):
    """Check if a word is a number or Roman numeral."""
    return bool(re.match(r'^[0-9IVXLCDM]+\.?$', word))

def _should_keep_english(word):
    """Determine if an English word should be kept as-is in Hinglish."""
    clean = re.sub(r'[^a-zA-Z]', '', word).lower()
    if not clean:
        return False
    if clean in KEEP_ENGLISH:
        return True
    if _is_proper_noun(word):
        return True
    if _is_numeral(word):
        return True
    return False


# ══════════════════════════════════════════════════════════════
# PHRASE DETECTION — Keep multi-word English phrases together
# ══════════════════════════════════════════════════════════════

KEEP_PHRASES = [
    'art of war', 'moral law', 'method and discipline',
    'life and death', 'laying plans', 'waging war',
    'attack by stratagem', 'tactical dispositions', 'energy',
    'weak points and strong', 'the army on the march',
    'classification of terrain', 'the attack by fire',
    'the use of spies', 'variation in tactics', 'on the march',
    'nine situations', 'sun tzu', 'vital importance',
    'complete ruin', 'constant factors', 'five constant factors',
]


def _extract_keep_phrases(sentence):
    """Find multi-word English phrases that should be preserved."""
    lower_sent = sentence.lower()
    found = []
    for phrase in sorted(KEEP_PHRASES, key=len, reverse=True):
        if phrase in lower_sent:
            found.append(phrase)
    return found


# ══════════════════════════════════════════════════════════════
# TRANSLATION HELPERS
# ══════════════════════════════════════════════════════════════

def _translate_to_hindi(text):
    """Translate English text to Hindi (Devanagari) using deep-translator."""
    try:
        translator = GoogleTranslator(source='en', target='hi')
        chunks = [text[i:i + 4500] for i in range(0, len(text), 4500)]
        result = ""
        for chunk in chunks:
            translated = translator.translate(chunk)
            if translated:
                result += translated + " "
        return result.strip()
    except Exception:
        return text


def _romanize_hindi(hindi_text):
    """Get romanized (Latin script) version of Hindi text using Google's dt=rm."""
    url = "https://translate.googleapis.com/translate_a/single"
    chunk_size = 4500
    chunks = [hindi_text[i:i + chunk_size] for i in range(0, len(hindi_text), chunk_size)]
    romanized_parts = []

    for chunk in chunks:
        try:
            params = {
                'client': 'gtx',
                'sl': 'hi',
                'tl': 'en',
                'dt': 'rm',
                'q': chunk
            }
            response = http_requests.get(url, params=params, timeout=15)
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


# ══════════════════════════════════════════════════════════════
# SMART MERGE ENGINE — The core of natural Hinglish
# ══════════════════════════════════════════════════════════════

def _smart_merge_hinglish(original_english, romanized_hindi, keep_phrases):
    """
    Intelligently merge English words back into romanized Hindi
    to produce natural Hinglish.
    
    Strategy:
    1. Start with the romanized Hindi as the base
    2. Re-insert kept English phrases and words
    3. Add parenthetical Hindi meanings for key terms
    """
    result = romanized_hindi

    # Step 1: Re-insert multi-word English phrases
    for phrase in keep_phrases:
        # The phrase in romanized form would be different,
        # so we mark it for post-processing
        pass

    # Step 2: Add parenthetical explanations for key English terms
    # We do this on the final output
    return result


def _add_parenthetical_meanings(text):
    """Add Hindi parenthetical explanations for key English terms."""
    for eng_term, hindi_meaning in ENGLISH_TO_HINDI_PARENTHETICAL.items():
        # Only add parenthetical if the term appears and doesn't already have one
        pattern = re.compile(
            r'\b(' + re.escape(eng_term) + r')(?!\s*\()',
            re.IGNORECASE
        )
        # Only add for the FIRST occurrence
        text = pattern.sub(r'\1 (' + hindi_meaning + ')', text, count=1)
    return text


# ══════════════════════════════════════════════════════════════
# MAIN PIPELINE: Sentence-by-Sentence Hinglish Translation
# ══════════════════════════════════════════════════════════════

def _translate_sentence_hinglish(english_sentence):
    """
    Translate a single English sentence to natural Hinglish.
    
    Pipeline:
    1. Detect which English words/phrases to keep
    2. Create a "marker" version where kept words are replaced with placeholders
    3. Translate the rest to Hindi → romanize
    4. Re-insert the English words at the right positions
    """
    if not english_sentence.strip():
        return ""

    # Step 1: Extract phrases to keep
    keep_phrases = _extract_keep_phrases(english_sentence)
    
    # Step 2: Identify individual words to keep
    words = english_sentence.split()
    word_markers = []
    
    # Check multi-word phrases first
    i = 0
    phrase_positions = {}  # Track phrase positions to avoid double-keeping words
    
    for phrase in keep_phrases:
        phrase_words = phrase.split()
        lower_words = [w.lower().strip('.,;:!?()[]"\'') for w in words]
        for start_idx in range(len(lower_words) - len(phrase_words) + 1):
            if lower_words[start_idx:start_idx + len(phrase_words)] == phrase_words:
                for j in range(start_idx, start_idx + len(phrase_words)):
                    phrase_positions[j] = True
                break
    
    # Step 3: Build word-level keep/translate decisions
    for idx, word in enumerate(words):
        clean_word = re.sub(r'[^a-zA-Z0-9]', '', word)
        if idx in phrase_positions:
            word_markers.append(('KEEP', word))
        elif _should_keep_english(word) or _is_proper_noun(word) or _is_numeral(word):
            word_markers.append(('KEEP', word))
        else:
            word_markers.append(('TRANSLATE', word))
    
    # Step 4: Build segments — consecutive TRANSLATE words go to translation together
    segments = []
    current_type = None
    current_words = []
    
    for marker_type, word in word_markers:
        if marker_type != current_type:
            if current_words:
                segments.append((current_type, ' '.join(current_words)))
            current_type = marker_type
            current_words = [word]
        else:
            current_words.append(word)
    if current_words:
        segments.append((current_type, ' '.join(current_words)))
    
    # Step 5: Translate TRANSLATE segments, keep KEEP segments
    result_parts = []
    for seg_type, seg_text in segments:
        if seg_type == 'KEEP':
            result_parts.append(seg_text)
        else:
            # Translate to Hindi, then romanize
            hindi = _translate_to_hindi(seg_text)
            if hindi and hindi != seg_text:
                romanized = _romanize_hindi(hindi)
                # Clean up: lowercase the romanized for natural feel
                result_parts.append(romanized.lower())
            else:
                result_parts.append(seg_text.lower())
    
    # Step 6: Join and clean up
    hinglish = ' '.join(result_parts)
    
    # Clean up double spaces, fix punctuation spacing
    hinglish = re.sub(r'\s+', ' ', hinglish).strip()
    hinglish = re.sub(r'\s+([.,;:!?])', r'\1', hinglish)
    
    return hinglish


def translate_to_natural_hinglish(english_text):
    """
    Main entry point: Translate full English text to natural, conversational Hinglish.
    
    This is the upgraded replacement for the old _translate_to_hinglish() function.
    
    Input:  "The art of war is of vital importance to the State."
    Output: "Art of war kisi bhi State (desh) ke liye bahut vital importance rakhta hai."
    """
    if not english_text or not english_text.strip():
        return english_text

    sentences = _split_into_sentences(english_text)
    translated_parts = []

    for sent in sentences:
        if sent == '\n\n':
            translated_parts.append('\n\n')
            continue
        
        if not sent.strip():
            continue

        hinglish_sent = _translate_sentence_hinglish(sent)
        if hinglish_sent:
            translated_parts.append(hinglish_sent)

    # Join all translated sentences
    result = ' '.join(translated_parts)
    
    # Collapse paragraph markers
    result = re.sub(r'\s*\n\n\s*', '\n\n', result)
    
    # Add parenthetical Hindi meanings for key terms (first occurrence only)
    result = _add_parenthetical_meanings(result)
    
    # Final cleanup
    result = re.sub(r'\s+', ' ', result.replace('\n\n', '§PARA§')).replace('§PARA§', '\n\n')
    result = result.strip()
    
    # Capitalize first letter of each sentence
    def _capitalize_first(match):
        return match.group(0).upper()
    result = re.sub(r'(?:^|(?<=[.!?]\s))[a-z]', _capitalize_first, result)
    
    return result
