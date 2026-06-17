import json
import os

USE_LLM = False  

DISCLAIMER = (
    "Note: This is an automated compliance check based on structured guideline "
    "parsing and live UI extraction. It is not a substitute for manual QA review."
)

with open("reports/discrepancy_report.json", "r", encoding="utf-8") as f:
    report_data = json.load(f)

results = report_data["results"]

PAGE_ALIASES = {
    "landing": "/",
    "home": "/",
    "login": "/login",
    "sign in": "/login",
    "my applications": "/dashboard/my-applications",
    "dashboard": "/dashboard/my-applications",
    "facilities": "/dashboard/facilities",
    "action items": "/dashboard/action-items",
    "user management": "/dashboard/user-management",
    "announcements": "/dashboard/announcements",
    "settings": "/dashboard/settings",
    "faqs": "/dashboard/faqs",
    "tickets": "/dashboard/tickets",
    "contact": "/dashboard/contact",
    "support": "/dashboard/contact",
}


def find_matching_page_url(question):
    question_lower = question.lower()
    for alias, url in PAGE_ALIASES.items():
        if alias in question_lower:
            return url
    return None


def filter_results(page_url=None, only_discrepancies=False):
    filtered = results
    if page_url:
        filtered = [r for r in filtered if r["page_url"] == page_url]
    if only_discrepancies:
        filtered = [r for r in filtered if r["discrepancy_flag"] is True]
    return filtered


def rule_based_answer(question):
    page_url = find_matching_page_url(question)
    wants_discrepancies = any(
        word in question.lower() for word in ["discrepanc", "mismatch", "wrong", "issue", "list all"]
    )

    if page_url is None:
        return (
            "I couldn't confidently map your question to a specific page in the data. "
            "Try mentioning a page name like 'My Applications', 'Facilities', or 'Contact'.\n\n"
            + DISCLAIMER
        )

    matches = filter_results(page_url=page_url, only_discrepancies=wants_discrepancies)

    if not matches:
        return (
            f"No {'discrepancies' if wants_discrepancies else 'data'} found for page '{page_url}'.\n\n"
            + DISCLAIMER
        )

    lines = [f"Findings for page '{page_url}':\n"]
    for m in matches:
        status = "DISCREPANCY" if m["discrepancy_flag"] else (
            "OK" if m["discrepancy_flag"] is False else "NO GUIDELINE COVERAGE"
        )
        lines.append(
            f"- [{status}] {m['component_type']} ({m['component_selector']}): "
            f"\"{m['actual_text_content']}\""
        )
        if m["guideline_reference"]:
            lines.append(f"    Guideline: {m['guideline_reference']} — \"{m['expected_text_content']}\"")
        if m["discrepancy_reason"]:
            lines.append(f"    Reason: {m['discrepancy_reason']}")
        lines.append(f"    Screenshot: {m['screenshot_path']}")

    lines.append(f"\n{DISCLAIMER}")
    return "\n".join(lines)


def llm_answer(question):
    from comparator.gemini_qa import answer_with_gemini  # only imported if USE_LLM
    page_url = find_matching_page_url(question)
    context = filter_results(page_url=page_url) if page_url else results
    return answer_with_gemini(question, context) + f"\n\n{DISCLAIMER}"


def ask(question):
    if USE_LLM:
        return llm_answer(question)
    return rule_based_answer(question)


if __name__ == "__main__":
    print("WaiverPro Compliance Agent — ask a question (or 'exit' to quit)\n")
    while True:
        q = input("Q: ").strip()
        if q.lower() in ("exit", "quit"):
            break
        print("\nA:", ask(q), "\n")