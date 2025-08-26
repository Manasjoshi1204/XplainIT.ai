# explain_engine.py - Google AI Studio
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def generate_explanation(topic, level, tone, extras, language):
    prompt = f"""Explain '{topic}' clearly for someone at {level} level.

Use a {tone} tone and {language or 'English'} language.
{f'Additional requirements: {extras}' if extras else ''}

Make it comprehensive, engaging, and easy to understand with examples."""
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text if response.text else "No response generated. Try again."
    except Exception as e:
        return f"Error: {str(e)}"

def test_connection():
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say hello!")
        return True, "Google AI working!"
    except Exception as e:
        return False, str(e)
