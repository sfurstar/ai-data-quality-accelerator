# Quickstart — from clone to running in ~5 minutes

## 1. Copy the project files into your repo

If you're starting fresh:
```bash
git init ai-data-quality-accelerator
cd ai-data-quality-accelerator
# copy all project files in here (or clone if already pushed)
```

If pushing to an existing remote:
```bash
cd ai-data-quality-accelerator
git init
git remote add origin https://github.com/<your-org>/ai-data-quality-accelerator.git
```

## 2. First commit and push

```bash
cd ai-data-quality-accelerator

git add .
git commit -m "feat: initial DQ & Governance Accelerator scaffold

- Engine: completeness, validity, consistency, PII detection, AI readiness
- Unstructured: PDF extraction, HIPAA/GDPR/FedRAMP/Governance compliance scanner
- LLM gap analysis via Claude API (Phase 1) / Cortex COMPLETE (Phase 2)
- Weighted scoring engine → AI-Readiness Index + maturity tier
- Streamlit UI: structured assessment, PDF assessment, combined report + export
- Config-driven rules and scoring weights (YAML)
- 22 unit tests, all passing
- Snowflake/Cortex migration guide"

git push -u origin main
```

## 3. Set up your local environment

```bash
# Python 3.11+ recommended
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

## 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and set your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-...
```

The app runs fine without the key — LLM gap analysis on the PDF page will be
skipped with a clear notice, and all rule-based checks still work.

## 5. Download the sample dataset

```bash
python scripts/download_sample.py
# Downloads 2,000 rows of NYC 311 Service Requests → data/sample/structured/nyc_311_sample.csv
# Requires internet access to data.cityofnewyork.us
```

## 6. Run the app

```bash
streamlit run app/main.py
```

Opens at http://localhost:8501

## 7. Run the tests

```bash
pytest tests/ -v
```

---

## What to try first

1. **Home page** — overview and navigation
2. **Structured Assessment** → select "Use sample dataset" → click Run Assessment
   - You'll see completeness issues (null agency, missing resolution descriptions)
   - PII flag on the injected `reference_id` column (synthetic SSN values)
   - Class imbalance warning on `status`
3. **Unstructured Assessment** → upload any policy/compliance PDF you have
   - If you don't have one, grab a public example:
     ```bash
     curl -o data/sample/unstructured/sample_policy.pdf \
       https://www.hhs.gov/sites/default/files/hipaa-simplification-201303.pdf
     ```
4. **Report** → after running either or both assessments, see the combined view and export

---

## Project structure recap

```
app/           Streamlit frontend (main.py + pages + components)
engine/        Assessment engine — pure Python, no Streamlit dependency
  structured/  completeness · validity · consistency · pii_detector · ai_readiness
  unstructured/ pdf_extractor · compliance_scanner · llm_analyzer
  scoring/     scorer (weighted aggregate → AI-Readiness Index)
config/        YAML rules and scoring weights — tune without touching code
data/sample/   Sample datasets and documents (gitignored, use download script)
scripts/       download_sample.py
snowflake/     MIGRATION.md — Phase 2 Snowflake/Cortex migration guide
tests/         22 unit tests (pytest)
```
