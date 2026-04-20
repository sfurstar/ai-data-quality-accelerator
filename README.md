# AI Data Quality & Governance Accelerator

> CGI proof-of-concept — *AI starts with data.*

An automated data readiness assessment tool that uses AI to identify quality issues,
governance gaps, and AI-readiness blockers across both **structured** and **unstructured** data.

---

## Architecture

```
ai-data-quality-accelerator/
├── app/                    # Streamlit frontend
│   ├── main.py             # Entry point + navigation
│   ├── pages/
│   │   ├── 01_structured_assessment.py
│   │   ├── 02_unstructured_assessment.py
│   │   └── 03_report.py
│   └── components/
│       ├── score_card.py   # Reusable score display widgets
│       └── findings_table.py
│
├── engine/                 # Assessment engine (Phase 1: pandas/LLM, Phase 2: Snowflake Cortex)
│   ├── __init__.py
│   ├── structured/
│   │   ├── __init__.py
│   │   ├── completeness.py     # Null / missing value checks
│   │   ├── validity.py         # Format, range, type checks
│   │   ├── consistency.py      # Cross-column / referential checks
│   │   ├── pii_detector.py     # PII / HIPAA field flagging
│   │   ├── governance.py       # Ownership, lineage, access gap checks
│   │   └── ai_readiness.py     # Feature engineering readiness, label quality
│   │
│   ├── unstructured/
│   │   ├── __init__.py
│   │   ├── pdf_extractor.py    # Text extraction from PDFs
│   │   ├── policy_checker.py   # Clause / keyword detection
│   │   ├── compliance_scanner.py  # HIPAA / GDPR / FedRAMP rule mapping
│   │   └── llm_analyzer.py     # LLM-powered gap analysis (Phase 1: Claude API, Phase 2: Cortex)
│   │
│   ├── scoring/
│   │   ├── __init__.py
│   │   ├── dimensions.py       # Dimension definitions & weights
│   │   └── scorer.py           # Aggregate scoring → AI-readiness index
│   │
│   └── reporting/
│       ├── __init__.py
│       ├── executive_summary.py
│       └── findings_report.py
│
├── data/
│   ├── sample/
│   │   ├── structured/         # Public government sample datasets
│   │   └── unstructured/       # Sample compliance / policy PDFs
│   └── schemas/
│       └── assessment_schema.json
│
├── config/
│   ├── rules/
│   │   ├── structured_rules.yaml   # Configurable quality rules
│   │   └── compliance_rules.yaml   # HIPAA / GDPR / FedRAMP checklists
│   └── scoring_weights.yaml        # Dimension weights (tunable per engagement)
│
├── tests/
│   ├── test_structured.py
│   ├── test_unstructured.py
│   └── test_scoring.py
│
├── snowflake/              # Phase 2 migration artifacts
│   ├── setup.sql           # Snowflake objects / Cortex setup
│   └── MIGRATION.md
│
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

---

## Quickstart (Phase 1 — Local)

```bash
# 1. Clone and set up environment
git clone <repo>
cd ai-data-quality-accelerator
python -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
cp .env.example .env
# Edit .env — add ANTHROPIC_API_KEY for LLM-powered PDF analysis

# 4. Run the app
streamlit run app/main.py
```

---

## Assessment Tracks

### Structured data
Analyzes CSV / database tables against five quality dimensions:

| Dimension       | What we check                                      |
|-----------------|----------------------------------------------------|
| Completeness    | Null rates, missing required fields                |
| Validity        | Type correctness, format patterns, range bounds    |
| Consistency     | Cross-column rules, referential integrity          |
| Governance      | PII presence, data ownership gaps, lineage         |
| AI Readiness    | Label quality, class balance, feature completeness |

**Sample dataset:** NYC 311 Service Requests (open government data, ~3M rows)

### Unstructured (PDF)
Analyzes policy and compliance documents against regulatory checklists:

| Check                  | Standard         |
|------------------------|------------------|
| Data retention clause  | HIPAA / GDPR     |
| Consent language       | GDPR Art. 7      |
| Breach notification    | HIPAA §164.412   |
| Data residency         | FedRAMP / State  |
| Access control policy  | NIST 800-53      |
| Data owner defined     | Governance       |

---

## Scoring Model

Each dimension is scored 0–100. The **AI-Readiness Index** is a weighted composite:

```
AI-Readiness Index = Σ(dimension_score × weight)

Default weights:
  Completeness   20%
  Validity       20%
  Consistency    15%
  Governance     25%   ← weighted higher for enterprise clients
  AI Readiness   20%
```

Scores map to a traffic-light maturity tier:
- 🔴 **0–40**: High risk — significant remediation needed
- 🟡 **41–70**: Moderate — targeted fixes recommended
- 🟢 **71–100**: AI-ready — minor improvements only

---

## Phase 2 — Snowflake / Cortex Migration

The engine interface is designed so the data and compute layer can be swapped without changing the UI or scoring logic:

| Phase 1 (local)          | Phase 2 (Snowflake)               |
|--------------------------|-----------------------------------|
| `pandas` DataFrames      | Snowpark DataFrames               |
| Local CSV / PDF files    | Snowflake tables + stage          |
| Claude API (LLM gaps)    | Cortex `COMPLETE()` / `CLASSIFY()`|
| Local Streamlit           | Streamlit in Snowflake            |

See `snowflake/MIGRATION.md` for the step-by-step migration guide.
