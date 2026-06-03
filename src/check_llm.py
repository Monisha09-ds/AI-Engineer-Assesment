import os

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def test_key():
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        print("Error: GOOGLE_API_KEY not found in .env")
        return
    
    print(f"Testing key: {key[:5]}...{key[-5:]}")
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say 'Access Confirmed' if you can read this.")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error testing key: {e}")

if __name__ == "__main__":
    test_key()
