import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_KEY"))

model = genai.GenerativeModel("gemini-2.0-flash")

def extract_rules_from_text(text, page_number):
    prompt = f"""
You are a compliance document parser.

Extract ONLY actionable compliance requirements from the provided text.

Return ONLY valid JSON array. No extra text. No markdown.

Format:
[
    {{
        "section": "section name",
        "rule": "exact requirement",
        "page": "{page_number}"
    }}
]

If no rules found, return: []

Text:
{text}
"""
    try:
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        print(f"Error: {e}")
        return "[]"