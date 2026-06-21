# Web_scrapper — WaiverPro Documentation Compliance Agent

Automated pipeline that checks whether the live **WaiverPro** web app matches its official guideline PDF: parses the PDF into rules, extracts the live UI via Playwright, compares the two, and produces a discrepancy report with citations and screenshots.



---

## Pipeline

```
docs/Waiverpro.pdf → parser/ → guideline.json
                                    │
extractor/ (Playwright login + crawl) → extracted_data.json + screenshots/
                                    │
comparator/ (compare_agent.py) → discrepancy_report.json
                                    │
comparator/agent_qa.py → CLI to query the report
```

| Stage | Output |
|---|---|
| Ingest & Parse | `parser/guideline.json` |
| Extract | `report/extracted_data.json`, `screenshots/`, `report/coverage_report.json` |
| Compare | `report/discrepancy_report.json` |
| Q&A | `comparator/agent_qa.py` (CLI) |

---

## Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install pdfplumber playwright google-generativeai python-dotenv
playwright install chromium
```

Add a `.env` file with `GEMINI_KEY=your_api_key_here`, and place the guideline PDF at `docs/Waiverpro.pdf`.

## Run

```bash
python parser/pdf_parser.py          # Stage 1: parse PDF
python extractor/extract_pages.py    # Stage 2: login + extract live UI
python comparator/compare_agent.py   # Stage 3: compare against guidelines
python comparator/agent_qa.py        # Stage 4: ask questions interactively
```

---

## Key Decisions

- **Playwright over Selenium/requests** — the app is a JS-rendered SPA with async-loaded data behind auth; needed real rendering + auto-waiting.
- **pdfplumber** — guideline PDF is plain text, no OCR needed.
- **Structured prompting over RAG/embeddings** — only ~68 rules from a 27-page PDF, so the full ruleset fits in one LLM call. A vector DB (ChromaDB/FAISS) would be the right next step if the guideline set grows much larger; the retrieval function (`get_relevant_guidelines()`) is isolated so it can be swapped for embedding-based search later without touching the rest of the pipeline.

---

## Known Limitation: Gemini Quota

Gemini free-tier key hit `RESOURCE_EXHAUSTED` (limit: 0) across models, even on a fresh key — blocked live LLM calls for parsing and comparison.

Both stages are wired behind a `USE_LLM` flag. When `False`:
- PDF parsing loads a manually-curated `guideline.json` (same schema the LLM was prompted to produce).
- Comparison runs a deterministic text-overlap fallback instead of LLM reasoning.

To re-enable: add a working `GEMINI_KEY` to `.env` and set `USE_LLM = True` in `parser/pdf_parser.py`, `comparator/compare_agent.py`, and `comparator/agent_qa.py` — no other changes needed (prompts already written in `gemini_extractor.py` / `gemini_compare.py`).

---

## What Was Missed

- Landing page (`/`) and `/login` aren't covered by the automated extractor yet — only authenticated `/dashboard/...` routes are. (Manually spot-checked: landing page button reads "Getting Started", guideline says "Sign In".)
- Modal/panel flows (New Waiver Application, Create Support Ticket) aren't extracted yet.
- Badge counts sometimes concatenate with labels in raw extraction (e.g. `"All0"`) — not yet cleaned up.
- Rule-based comparator fallback is simple text overlap, so some flagged discrepancies may be false positives a real LLM pass would resolve.

---

## Next Steps

1. Validate real Gemini comparison once quota is available, against the fallback's output.
2. Extend extraction to landing/login pages and modal flows for full guideline coverage.
3. Clean up badge-count text concatenation.
4. Move to embedding-based retrieval if the guideline document grows significantly.
