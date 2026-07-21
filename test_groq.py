import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv('GROQ_API_KEY'))

bad_text = "कोई जवान साली - सलहज नहीं बैठी है , नजसे जा कर कदखाऊ ूँ ।"

prompt = (
    "This is highly corrupted text extracted from a Hindi PDF (Premchand's Godan or similar). "
    "Due to font encoding errors, the characters are scrambled (e.g., 'नजसे' means 'जिसे', 'कदखाऊ' means 'दिखाऊँ', 'ूँ' is broken matra). "
    "Use your knowledge of Hindi language and literature to completely reconstruct and guess the correct intended sentence. "
    "Output ONLY the corrected Hindi sentence."
)

completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "system", "content": prompt},
        {"role": "user", "content": bad_text}
    ],
    temperature=0.1
)
print(completion.choices[0].message.content.strip())
