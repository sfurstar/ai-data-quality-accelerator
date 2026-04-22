-- =============================================================================
-- snowflake/setup.sql
-- DQ & Governance Accelerator — Snowflake Phase 2 Setup
-- Run as SYSADMIN or a role with CREATE DATABASE privileges
-- =============================================================================

-- ── 1. Database & schema ──────────────────────────────────────────────────────
USE ROLE SYSADMIN;

CREATE DATABASE IF NOT EXISTS DQ_ACCELERATOR
    COMMENT = 'CGI Data Quality & Governance Accelerator';

CREATE SCHEMA IF NOT EXISTS DQ_ACCELERATOR.ASSESSMENTS
    COMMENT = 'Assessment results, findings, and metadata';

CREATE SCHEMA IF NOT EXISTS DQ_ACCELERATOR.RAW_DATA
    COMMENT = 'Source data for structured assessments';

CREATE SCHEMA IF NOT EXISTS DQ_ACCELERATOR.UNSTRUCTURED
    COMMENT = 'Stages and metadata for PDF document assessments';

-- ── 2. Warehouse ──────────────────────────────────────────────────────────────
CREATE WAREHOUSE IF NOT EXISTS DQ_WH
    WAREHOUSE_SIZE    = 'XSMALL'
    AUTO_SUSPEND      = 60
    AUTO_RESUME       = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'DQ Accelerator compute — auto-suspends after 60s idle';

-- ── 3. Role & permissions ─────────────────────────────────────────────────────
CREATE ROLE IF NOT EXISTS DQ_APP_ROLE
    COMMENT = 'Role for DQ Accelerator application';

GRANT USAGE ON DATABASE  DQ_ACCELERATOR TO ROLE DQ_APP_ROLE;
GRANT USAGE ON SCHEMA    DQ_ACCELERATOR.ASSESSMENTS TO ROLE DQ_APP_ROLE;
GRANT USAGE ON SCHEMA    DQ_ACCELERATOR.RAW_DATA    TO ROLE DQ_APP_ROLE;
GRANT USAGE ON SCHEMA    DQ_ACCELERATOR.UNSTRUCTURED TO ROLE DQ_APP_ROLE;
GRANT USAGE ON WAREHOUSE DQ_WH TO ROLE DQ_APP_ROLE;

-- Grant CREATE on schemas so app can create tables
GRANT CREATE TABLE ON SCHEMA DQ_ACCELERATOR.ASSESSMENTS  TO ROLE DQ_APP_ROLE;
GRANT CREATE TABLE ON SCHEMA DQ_ACCELERATOR.RAW_DATA     TO ROLE DQ_APP_ROLE;
GRANT CREATE STAGE ON SCHEMA DQ_ACCELERATOR.UNSTRUCTURED TO ROLE DQ_APP_ROLE;

-- Grant Cortex usage (required for COMPLETE/CLASSIFY functions)
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE DQ_APP_ROLE;

-- Assign role to your user (replace <YOUR_USERNAME>)
-- GRANT ROLE DQ_APP_ROLE TO USER <YOUR_USERNAME>;

-- ── 4. Assessment results table ───────────────────────────────────────────────
USE DATABASE DQ_ACCELERATOR;
USE SCHEMA ASSESSMENTS;

CREATE TABLE IF NOT EXISTS ASSESSMENT_RESULTS (
    ASSESSMENT_ID       VARCHAR     DEFAULT UUID_STRING()  PRIMARY KEY,
    SOURCE_NAME         VARCHAR     NOT NULL,
    TRACK               VARCHAR     NOT NULL,   -- 'structured' | 'unstructured'
    RUN_TIMESTAMP       TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    AI_READINESS_INDEX  FLOAT,
    MATURITY_TIER       VARCHAR,
    SUMMARY             VARCHAR,
    CRITICAL_COUNT      INTEGER,
    WARNING_COUNT       INTEGER,
    FINDINGS_JSON       VARIANT,    -- Full findings array as JSON
    METADATA_JSON       VARIANT,    -- Coverage, extraction metadata etc.
    CREATED_BY          VARCHAR     DEFAULT CURRENT_USER()
)
COMMENT = 'One row per assessment run';

CREATE TABLE IF NOT EXISTS DIMENSION_SCORES (
    SCORE_ID        VARCHAR     DEFAULT UUID_STRING()  PRIMARY KEY,
    ASSESSMENT_ID   VARCHAR     NOT NULL REFERENCES ASSESSMENT_RESULTS(ASSESSMENT_ID),
    DIMENSION       VARCHAR     NOT NULL,
    SCORE           FLOAT       NOT NULL,
    WEIGHT          FLOAT       NOT NULL,
    FINDING_COUNT   INTEGER     DEFAULT 0,
    RUN_TIMESTAMP   TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Dimension-level scores per assessment';

-- ── 5. Internal stage for PDF documents ───────────────────────────────────────
USE SCHEMA UNSTRUCTURED;

CREATE STAGE IF NOT EXISTS PDF_INTERNAL_STAGE
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Internal stage for PDF policy/compliance documents';

-- ── 6. External stage for S3 PDFs ────────────────────────────────────────────
-- Replace <YOUR_S3_BUCKET> and <YOUR_IAM_ROLE_ARN> with your values
-- Run this block separately after configuring your S3 integration

/*
CREATE STORAGE INTEGRATION IF NOT EXISTS S3_DQ_INTEGRATION
    TYPE                      = EXTERNAL_STAGE
    STORAGE_PROVIDER          = 'S3'
    ENABLED                   = TRUE
    STORAGE_AWS_ROLE_ARN      = '<YOUR_IAM_ROLE_ARN>'
    STORAGE_ALLOWED_LOCATIONS = ('s3://<YOUR_S3_BUCKET>/dq-docs/');

-- After creating integration, get the AWS external ID and trust ARN:
DESC INTEGRATION S3_DQ_INTEGRATION;
-- Use STORAGE_AWS_IAM_USER_ARN and STORAGE_AWS_EXTERNAL_ID
-- to update your IAM role trust policy in AWS console.

CREATE STAGE IF NOT EXISTS PDF_S3_STAGE
    URL                  = 's3://<YOUR_S3_BUCKET>/dq-docs/'
    STORAGE_INTEGRATION  = S3_DQ_INTEGRATION
    DIRECTORY            = (ENABLE = TRUE)
    FILE_FORMAT          = (TYPE = 'CSV')  -- overridden per query
    COMMENT              = 'External S3 stage for PDF compliance documents';
*/

-- ── 7. Raw data table for structured assessments ──────────────────────────────
USE SCHEMA RAW_DATA;

-- Sample table matching the NYC 311 schema used in Phase 1
-- Replace with your actual source table or use CTAS from your existing data
CREATE TABLE IF NOT EXISTS NYC_311_REQUESTS (
    UNIQUE_KEY              VARCHAR,
    CREATED_DATE            TIMESTAMP_NTZ,
    CLOSED_DATE             TIMESTAMP_NTZ,
    AGENCY                  VARCHAR,
    AGENCY_NAME             VARCHAR,
    COMPLAINT_TYPE          VARCHAR,
    DESCRIPTOR              VARCHAR,
    STATUS                  VARCHAR,
    RESOLUTION_DESCRIPTION  VARCHAR,
    BOROUGH                 VARCHAR,
    INCIDENT_ZIP            VARCHAR,
    LATITUDE                FLOAT,
    LONGITUDE               FLOAT,
    INCIDENT_ADDRESS        VARCHAR
)
COMMENT = 'NYC 311 Service Requests — sample structured dataset';

-- ── 8. Cortex test query ──────────────────────────────────────────────────────
-- Run this to verify Cortex is available in your account/region:
/*
SELECT SNOWFLAKE.CORTEX.COMPLETE(
    'mistral-large2',
    'Respond with exactly: Cortex is working.'
) AS cortex_test;
*/

-- ── 9. Useful views ───────────────────────────────────────────────────────────
USE SCHEMA ASSESSMENTS;

CREATE OR REPLACE VIEW ASSESSMENT_SUMMARY AS
SELECT
    ASSESSMENT_ID,
    SOURCE_NAME,
    TRACK,
    RUN_TIMESTAMP,
    AI_READINESS_INDEX,
    MATURITY_TIER,
    CRITICAL_COUNT,
    WARNING_COUNT,
    CREATED_BY
FROM ASSESSMENT_RESULTS
ORDER BY RUN_TIMESTAMP DESC;

-- =============================================================================
-- Verification queries — run after setup
-- =============================================================================
/*
SHOW TABLES IN SCHEMA DQ_ACCELERATOR.ASSESSMENTS;
SHOW TABLES IN SCHEMA DQ_ACCELERATOR.RAW_DATA;
SHOW STAGES IN SCHEMA DQ_ACCELERATOR.UNSTRUCTURED;
SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE();
*/
