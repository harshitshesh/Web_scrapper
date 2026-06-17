import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_KEY"))

model = genai.GenerativeModel("gemini-2.0-flash")  


def compare_with_gemini(component, relevant_guidelines):
    """
    Sends one extracted UI component + its candidate guideline rules to Gemini,
    and asks it to decide whether there's a discrepancy, citing the exact rule.

    Returns: (discrepancy_flag, discrepancy_reason, expected_text_content, guideline_reference)
    """

    if not component["actual_text_content"]:
        return None, None, None, None  

    if not relevant_guidelines:
        return None, "No guideline section found referencing this page.", None, None

    guideline_block = "\n".join(
        f"- Section: \"{g['section']}\" | Rule: \"{g['rule']}\""
        for g in relevant_guidelines
    )

    prompt = f"""
You are a strict compliance-checking assistant comparing a live web application's UI
against official written guidelines.

LIVE UI COMPONENT:
- Page URL: {component['page_url']}
- Component type: {component['component_type']}
- Selector: {component['component_selector']}
- Actual text/content found on the live site: {json.dumps(component['actual_text_content'])}

CANDIDATE GUIDELINE RULES FOR THIS PAGE:
{guideline_block}

TASK:
Decide if the live component's actual content conforms to ONE of the guideline rules above.

Respond with ONLY valid JSON in this exact format, no markdown, no extra text:
{{
    "discrepancy_flag": true or false,
    "matched_section": "the section name of the rule you matched against, or null if none matched",
    "expected_text_content": "what the guideline says should be there, or null",
    "discrepancy_reason": "a one-sentence explanation citing the guideline, written for a non-technical reader"
}}

Rules for your judgment:
- If the actual text is a reasonable match (even if reworded) for what a guideline rule describes, discrepancy_flag = false.
- If the actual text clearly contradicts or differs from what every relevant rule describes, discrepancy_flag = true.
- Do not invent guideline content beyond what's given above.
- Be conservative: if you're unsure, prefer discrepancy_flag = false rather than a false alarm.
"""

    try:
        response = model.generate_content(prompt)
        cleaned = response.text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(cleaned)

        return (
            parsed.get("discrepancy_flag"),
            parsed.get("discrepancy_reason"),
            parsed.get("expected_text_content"),
            parsed.get("matched_section"),
        )

    except Exception as e:
        print(f"  [Gemini error] {e} — falling back to 'unknown' for this component")
        return None, f"LLM comparison failed: {e}", None, None