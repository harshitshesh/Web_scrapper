import pdfplumber
import json
import os
from gemini_extractor import extract_rules_from_text

pdf_path = "docs/Waiverpro.pdf"
os.makedirs("parser", exist_ok=True)

USE_LLM = False  

if USE_LLM:
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text:
                full_text += f"\n\n--- PAGE {page_number} ---\n{text}"

    print("Sending to Gemini...")
    result = extract_rules_from_text(full_text, "all")

    try:
        cleaned = result.replace("```json", "").replace("```", "").strip()
        rules = json.loads(cleaned)
        with open("parser/guideline.json", "w", encoding="utf-8") as f:
            json.dump(rules, f, indent=4, ensure_ascii=False)
        print(f"Done! Total Rules: {len(rules)}")
    except Exception as e:
        print(f"JSON parse failed: {e}")
        print(result[:500])

else:
    print("USE_LLM=False — using manually curated guideline.json as fallback.")
    with open("parser/guideline.json", "r", encoding="utf-8") as f:
        rules = json.load(f)
    print(f"Loaded {len(rules)} rules from fallback file.")