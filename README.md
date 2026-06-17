# Web_scrapper — WaiverPro Documentation Compliance Agent

An automated pipeline that checks whether the live **WaiverPro** web application
conforms to its official user guidelines (provided as a PDF). It ingests the PDF
into structured rules, extracts the live UI via browser automation, compares the
two using LLM-based reasoning (with a deterministic fallback), and produces a
structured discrepancy report with citations and screenshots.

> [Author name here]

---

## 1. Pipeline Overview

```
docs/Waiverpro.pdf
      │
      ▼
parser/          → pdfplumber + Gemini prompting → guideline.json
      │
extractor/        → Playwright (login + navigate + capture) → extracted_data.json
      │
comparator/       → matches extracted_data.json against guideline.json → discrepancy_report.json
      │
      └── agent_qa.py → CLI to ask natural-language questions over the report
```

| Stage | Folder | Output |
|---|---|---|
| Ingest & Parse | `parser/` | `parser/guideline.json` |
| Extract | `extractor/` | `report/extracted_data.json`, `screenshots/` |
| Compare (Agent) | `comparator/` | `report/discrepancy_report.json` |
| Coverage | `extractor/` | `report/coverage_report.json` |
| Q&A interface | `comparator/agent_qa.py` | CLI |

---

## 2. Setup Instructions

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 2. Install dependencies
pip install pdfplumber playwright google-generativeai python-dotenv
playwright install chromium

# 3. Add your Gemini API key
# Create a .env file in the project root with:
GEMINI_KEY=your_api_key_here
```

Place the official guideline PDF at `docs/Waiverpro.pdf`.

---

## 3. How to Run Each Stage

```bash
# Stage 1 — Parse the PDF into structured guideline rules
python parser/pdf_parser.py

# Stage 2 — Log in to the live app and extract UI state from every page
python extractor/extract_pages.py

# Stage 3 — Compare extracted data against the guidelines
python comparator/compare_agent.py

# Stage 4 — Ask questions about the results (interactive CLI)
python comparator/agent_qa.py
```

Each stage writes its output to disk, so stages can be re-run independently
without re-running earlier ones (e.g. you can re-run the comparator multiple
times against the same `extracted_data.json` while tuning the matching logic).

---

## 4. Architectural Decisions & Tool Justification

### 4.1 Playwright over Selenium / raw requests
The live app is a modern JS-rendered SPA behind authentication, with data
loaded asynchronously (tables, charts). Raw HTTP requests (`requests`,
`BeautifulSoup`) would only see the initial HTML shell, not the rendered
state. Playwright was chosen over Selenium because it has first-class
auto-waiting, a simpler async-friendly API, and built-in screenshotting —
reducing the amount of custom wait-handling code needed.

### 4.2 pdfplumber for guideline ingestion
The guideline PDF is text-based (not scanned/image), so `pdfplumber` was
sufficient for clean text extraction per page without needing OCR
(`pytesseract`) or layout-heavy libraries (`pymupdf`'s block-detection),
which would have been overkill for a 27-page text document.

### 4.3 Structured LLM prompting instead of RAG / vector embeddings
The assignment explicitly allows either RAG or structured prompting. We
deliberately chose **structured prompting over a RAG + vector-DB pipeline**
(e.g. ChromaDB/FAISS embeddings) for this dataset, because:

- The guideline document is small (~27 pages, 68 extracted rules). A vector
  database is designed to make *retrieval* over large corpora efficient;
  at this scale, the entire ruleset fits comfortably inside a single LLM
  context window, so semantic retrieval adds infrastructure complexity
  (embedding generation, indexing, similarity search, an extra dependency)
  without a measurable benefit.
- Retrieval is instead done with a lightweight keyword/page-URL match
  (`get_relevant_guidelines()` in `comparator/compare_agent.py`), which is
  fast, fully deterministic, and easy to debug — important given the time
  constraints on this assignment.
- If the guideline document were significantly larger (hundreds of pages,
  multiple manuals), or if rules needed to be retrieved by *semantic
  similarity* rather than page/section keyword overlap, a proper RAG setup
  with embeddings would become the right tool, and the codebase is
  structured so that `get_relevant_guidelines()` could be swapped for a
  vector-search call without touching the rest of the pipeline.

### 4.4 Schema design
All extracted and compared data follows the canonical schema specified in
the assignment (`page_url`, `component_type`, `component_selector`,
`actual_text_content`, `expected_text_content`, `guideline_reference`,
`discrepancy_flag`, `discrepancy_reason`, `screenshot_path`,
`retrieved_at`). Fields are `null` until the relevant stage fills them in
(extraction leaves comparison fields null; the comparator fills them),
which keeps each stage's responsibility clear and makes partial pipeline
runs easy to inspect.

---

## 5. Known Limitation: Gemini Free-Tier Quota

During development, the Gemini free-tier API key used for this project hit
`RESOURCE_EXHAUSTED` (quota limit: 0 requests) across multiple models
(`gemini-2.0-flash-lite`, `gemini-2.0-flash`), even after generating a fresh
key. This blocked live LLM calls for both the guideline-parsing step and the
comparison step.

**What was done about it:**

- The structured prompts for both stages were fully written and tested
  against the API before the quota ran out (see `parser/gemini_extractor.py`
  and `comparator/gemini_compare.py`), so the prompting design itself is
  implemented and ready, not theoretical.
- Both stages are wired behind a `USE_LLM` flag:
  - `parser/pdf_parser.py` → `USE_LLM = False` loads a manually-curated
    `guideline.json` (built by hand, following the exact schema the LLM was
    prompted to produce) instead of calling Gemini.
  - `comparator/compare_agent.py` → `USE_LLM = False` runs a deterministic
    rule-based fallback (`rule_based_compare()`) using normalized text
    overlap matching instead of LLM reasoning.
- **To re-enable the real LLM pipeline:** add a working `GEMINI_KEY` to
  `.env` and flip `USE_LLM = True` in both `parser/pdf_parser.py` and
  `comparator/compare_agent.py` (and `comparator/agent_qa.py` for the Q&A
  layer). No other code changes are required — the LLM call paths
  (`gemini_extractor.py`, `gemini_compare.py`) are already implemented and
  call-ready.

This was communicated to the assignment contacts (Manohar/Akshay) via
WhatsApp as it happened, along with the workaround taken, rather than
submitting silently.

---

## 6. What Was Missed / Not Covered

- The public landing page (`/`) and the unauthenticated `/login` page were
  not run through the automated extractor — extraction currently covers
  only the authenticated `/dashboard/...` routes. These were spot-checked
  manually (e.g. the landing page's Sign In button was found to actually
  read "Get Started" — see Section 7) but are not yet part of the automated
  JSON output.
- Extraction currently captures headings, buttons, and table headers per
  page. It does not yet capture every component type mentioned in the
  schema example (`navigation_item` as a distinct type is implicit in the
  sidebar but not separately tagged), and modal/panel content (e.g. the
  "New Waiver Application" step panel) is not yet extracted since it
  requires an extra click sequence to open.
- Badge counts are sometimes concatenated with their label in the raw
  extraction (e.g. `"All0"`, `"Draft 0"`) because Playwright reads the
  button's full inner text as one string. This wasn't cleaned up via regex
  splitting — it's flagged here as a known data-quality issue rather than
  silently left in.
- The rule-based comparator fallback is intentionally simple (text overlap),
  so some discrepancies it reports may be false positives that a true LLM
  comparison (once quota allows) would correctly resolve as matches.

---

## 7. Sample Finding

One discrepancy was confirmed manually during development: the guideline
(Section 2) states the landing page button reads **"Sign In"**, but the
live site's button reads **"Get Started"**. This is captured in
`screenshots/01_landing_page.png`.

---

## 8. What I'd Improve Next

1. Get a working Gemini key and flip `USE_LLM = True` to validate the real
   LLM-based comparison and Q&A against the rule-based fallback's output —
   compare the two to sanity-check the fallback's false-positive rate.
2. Extend extraction to the landing page, login page, and modal/panel flows
   (New Waiver Application, Create Support Ticket) for full coverage of all
   14 guideline sections.
3. Clean up badge-count text concatenation in extraction with a small regex
   post-processing pass.
4. Add retry logic with exponential backoff around the Playwright navigation
   steps (currently uses fixed waits/selectors), to harden against network
   hiccups during longer extraction runs.
5. If the guideline document were to grow significantly, swap the keyword-based
   `get_relevant_guidelines()` for a proper embedding-based retrieval step.
