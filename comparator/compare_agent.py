
import json
import re
from datetime import datetime, timezone

USE_LLM = False

with open("parser/guideline.json", "r", encoding="utf-8") as f:
    guidelines = json.load(f)

with open("reports/extracted_data.json", "r", encoding="utf-8") as f:
    extracted = json.load(f)



def get_relevant_guidelines(page_url):
    """Very simple retrieval: match guidelines whose section/rule text references
    a keyword that appears in the page_url. This is the 'R' in a lightweight RAG —
    no vector DB needed since the guideline set is small (68 rules)."""
    url_keyword = page_url.strip("/").split("/")[-1].replace("-", " ")
    relevant = []
    for g in guidelines:
        text_blob = (g["section"] + " " + g["rule"]).lower()
        if url_keyword.lower() in text_blob or any(
            word in text_blob for word in url_keyword.lower().split()
        ):
            relevant.append(g)
    return relevant


def normalize(text):
    if isinstance(text, list):
        text = " ".join(text)
    return re.sub(r"[^a-z0-9 ]", "", str(text).lower()).strip()


def rule_based_compare(component, relevant_guidelines):
    """Checks if the component's actual text appears (loosely) inside any relevant
    guideline rule text. Flags a discrepancy if nothing matches reasonably well."""
    actual = normalize(component["actual_text_content"])

    if not actual:
        return False, None, None 

    best_match = None
    for g in relevant_guidelines:
        rule_norm = normalize(g["rule"])
       
        if actual in rule_norm or rule_norm in actual:
            best_match = g
            break
       
        actual_tokens = set(actual.split())
        rule_tokens = set(rule_norm.split())
        if actual_tokens and len(actual_tokens & rule_tokens) / len(actual_tokens) > 0.5:
            best_match = g
            break

    if best_match:
        return False, best_match["rule"], best_match["section"]
    elif relevant_guidelines:
       
        return True, relevant_guidelines[0]["rule"], relevant_guidelines[0]["section"]
    else:
        return None, None, None 


def llm_compare(component, relevant_guidelines):
    from comparator.gemini_compare import compare_with_gemini 
    flag, reason, expected, ref = compare_with_gemini(component, relevant_guidelines)
    return flag, reason, expected, ref



results = []
stats = {"total": 0, "discrepancies": 0, "matched": 0, "no_guideline_coverage": 0}

for component in extracted:
    stats["total"] += 1
    relevant = get_relevant_guidelines(component["page_url"])

    if USE_LLM:
        flag, reason, expected, ref = llm_compare(component, relevant)
    else:
        flag, expected, ref = rule_based_compare(component, relevant)
        reason = (
            f"Live text '{component['actual_text_content']}' did not match any "
            f"guideline rule found for this page (closest: '{expected}')."
            if flag else None
        )

    component_result = dict(component)  # copy
    component_result["expected_text_content"] = expected
    component_result["guideline_reference"] = ref
    component_result["discrepancy_flag"] = flag
    component_result["discrepancy_reason"] = reason

    if flag is True:
        stats["discrepancies"] += 1
    elif flag is False:
        stats["matched"] += 1
    else:
        stats["no_guideline_coverage"] += 1

    results.append(component_result)

output = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "comparison_method": "rule_based_fallback" if not USE_LLM else "gemini_llm",
    "stats": stats,
    "results": results,
}

with open("reports/discrepancy_report.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=4, ensure_ascii=False)

print(f"Comparison method: {output['comparison_method']}")
print(f"Total components checked: {stats['total']}")
print(f"Discrepancies flagged: {stats['discrepancies']}")
print(f"Matched: {stats['matched']}")
print(f"No guideline coverage (couldn't map to a rule): {stats['no_guideline_coverage']}")
print("Saved: reports/discrepancy_report.json")