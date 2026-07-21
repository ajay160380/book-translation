from g4f.client import Client
import sys

def test():
    try:
        client = Client()
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Translate 'Hello, how are you?' to conversational Hinglish."}]
        )
        print("G4F Output:", completion.choices[0].message.content)
    except Exception as e:
        print("G4F Error:", e)

test()
