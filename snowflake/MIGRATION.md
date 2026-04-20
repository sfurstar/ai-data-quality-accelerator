# Phase 2 — Snowflake / Cortex Migration Guide

This document describes how to migrate the DQ Accelerator from the local
Phase 1 prototype to a fully cloud-native Snowflake deployment.

The key design principle: **the engine interface doesn't change**.
Only the data access and compute layers swap out.

---

## What changes in Phase 2

| Component | Phase 1 (local) | Phase 2 (Snowflake) |
|-----------|-----------------|---------------------|
| Data ingestion | CSV upload in Streamlit | Snowflake tables / external stages |
| Data processing | `pandas` DataFrames | Snowpark DataFrames |
| LLM gap analysis | Anthropic Claude API | `SNOWFLAKE.CORTEX.COMPLETE()` |
| Text classification | regex / keyword rules | `SNOWFLAKE.CORTEX.CLASSIFY_TEXT()` |
| PII detection | presidio / regex | Snowflake GDPR/PII policies |
| Frontend hosting | Local Streamlit | Streamlit in Snowflake (SiS) |
| Report storage | Local file export | Snowflake table + stage |

---

## Step 1 — Snowflake objects setup

Run `snowflake/setup.sql` in a Snowflake worksheet to create the required
databases, schemas, warehouses, and stages.

```sql
-- Run as ACCOUNTADMIN or SYSADMIN
USE ROLE SYSADMIN;
CREATE DATABASE IF NOT EXISTS DQ_ACCELERATOR;
CREATE SCHEMA IF NOT EXISTS DQ_ACCELERATOR.ASSESSMENTS;
CREATE WAREHOUSE IF NOT EXISTS DQ_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE;

-- Stage for CSV uploads
CREATE STAGE IF NOT EXISTS DQ_ACCELERATOR.ASSESSMENTS.UPLOAD_STAGE;

-- Stage for PDF documents
CREATE STAGE IF NOT EXISTS DQ_ACCELERATOR.ASSESSMENTS.DOC_STAGE;

-- Assessment results table
CREATE TABLE IF NOT EXISTS DQ_ACCELERATOR.ASSESSMENTS.RESULTS (
  ASSESSMENT_ID     VARCHAR DEFAULT UUID_STRING(),
  SOURCE_NAME       VARCHAR,
  TRACK             VARCHAR,
  RUN_TIMESTAMP     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  AI_READINESS_INDEX FLOAT,
  MATURITY_TIER     VARCHAR,
  SUMMARY           VARCHAR,
  FINDINGS_JSON     VARIANT,
  METADATA_JSON     VARIANT
);
```

---

## Step 2 — Swap pandas for Snowpark

Replace `pandas` DataFrame operations with Snowpark equivalents.
The module interfaces stay identical.

### Completeness (example)

```python
# Phase 1 — pandas
def run(df: pd.DataFrame) -> list[Finding]:
    null_pct = df[col].isna().sum() / len(df)

# Phase 2 — Snowpark
from snowflake.snowpark import Session
from snowflake.snowpark import functions as F

def run(df: snowflake.snowpark.DataFrame) -> list[Finding]:
    total = df.count()
    null_count = df.filter(F.col(col).is_null()).count()
    null_pct = null_count / total
```

---

## Step 3 — Swap Claude API for Cortex COMPLETE

Replace calls in `engine/unstructured/llm_analyzer.py`:

```python
# Phase 1 — Claude API
import anthropic
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
message = client.messages.create(model="claude-sonnet-4-20250514", ...)

# Phase 2 — Snowflake Cortex
from snowflake.snowpark.context import get_active_session
session = get_active_session()

result = session.sql(f"""
  SELECT SNOWFLAKE.CORTEX.COMPLETE(
    'mistral-large',
    '{prompt.replace("'", "''")}'
  ) AS response
""").collect()[0]["RESPONSE"]
```

---

## Step 4 — Deploy Streamlit in Snowflake

1. Upload `app/` directory to a Snowflake stage
2. Create a Streamlit app pointing to `app/main.py`
3. Grant appropriate roles

```sql
CREATE STREAMLIT DQ_ACCELERATOR.ASSESSMENTS.DQ_APP
  ROOT_LOCATION = '@DQ_ACCELERATOR.ASSESSMENTS.UPLOAD_STAGE/app'
  MAIN_FILE = 'main.py'
  QUERY_WAREHOUSE = DQ_WH;
```

---

## Step 5 — Store results in Snowflake

After running an assessment, persist results:

```python
import json
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark import types as T

session = get_active_session()

session.sql(f"""
  INSERT INTO DQ_ACCELERATOR.ASSESSMENTS.RESULTS
    (SOURCE_NAME, TRACK, AI_READINESS_INDEX, MATURITY_TIER, SUMMARY, FINDINGS_JSON, METADATA_JSON)
  SELECT
    '{result.source_name}',
    '{result.track}',
    {result.ai_readiness_index},
    '{result.maturity_tier}',
    '{result.summary.replace("'", "''")}',
    PARSE_JSON('{json.dumps([f.__dict__ for f in result.all_findings])}'),
    PARSE_JSON('{json.dumps(result.metadata)}')
""").collect()
```

---

## Cortex functions reference

| Task | Cortex function |
|------|----------------|
| Gap analysis / summarization | `SNOWFLAKE.CORTEX.COMPLETE('mistral-large', prompt)` |
| Text classification | `SNOWFLAKE.CORTEX.CLASSIFY_TEXT(text, ['HIPAA', 'GDPR', ...])` |
| Sentiment / tone | `SNOWFLAKE.CORTEX.SENTIMENT(text)` |
| Translation | `SNOWFLAKE.CORTEX.TRANSLATE(text, 'en', 'es')` |
| Embedding (for similarity) | `SNOWFLAKE.CORTEX.EMBED_TEXT_768('e5-base-v2', text)` |

---

## Notes

- Cortex COMPLETE is only available in select Snowflake regions. Verify availability
  for your account at: https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions
- For FedRAMP or GovCloud deployments, check which Cortex models are approved
- Streamlit in Snowflake does not support all Streamlit components — test `st.file_uploader`
  behavior; large PDFs may need to be loaded via stage rather than direct upload
