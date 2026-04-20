"""
tests/test_structured.py
Unit tests for the structured assessment engine modules.

Run with: pytest tests/test_structured.py -v
"""
import numpy as np
import pandas as pd
import pytest

from engine import Dimension, Severity
from engine.structured import completeness, validity, pii_detector, ai_readiness, consistency


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def clean_df():
    """A well-formed government-style DataFrame with no issues."""
    return pd.DataFrame({
        "unique_key":   [f"REQ-{i:04d}" for i in range(200)],
        "created_date": pd.date_range("2024-01-01", periods=200, freq="1h").astype(str),
        "closed_date":  pd.date_range("2024-01-02", periods=200, freq="1h").astype(str),
        "status":       ["Closed"] * 200,
        "agency":       ["NYPD"] * 200,
        "borough":      ["BROOKLYN"] * 200,
        "zip_code":     ["10001"] * 200,
        "resolution_description": ["Issue resolved."] * 200,
    })


@pytest.fixture
def dirty_df():
    """A DataFrame with deliberately injected quality issues."""
    rng = np.random.default_rng(42)
    n = 500

    df = pd.DataFrame({
        "unique_key":   [f"REQ-{i:04d}" for i in range(n)],
        "created_date": pd.date_range("2024-01-01", periods=n, freq="1h").astype(str),
        "status":       ["Closed"] * n,
        "agency":       [None if i % 20 == 0 else "NYPD" for i in range(n)],  # 5% null
        "zip_code":     ["INVALID" if i % 50 == 0 else "10001" for i in range(n)],  # 2% invalid
        "resolution_description": [None if i % 3 == 0 else "Resolved." for i in range(n)],  # 33% null
    })
    return df


# ── Completeness tests ────────────────────────────────────────────────────────

class TestCompleteness:
    def test_no_findings_on_clean_data(self, clean_df):
        findings = completeness.run(clean_df)
        assert len(findings) == 0

    def test_detects_high_null_column(self, dirty_df):
        findings = completeness.run(dirty_df)
        null_cols = [f.column for f in findings]
        assert "resolution_description" in null_cols

    def test_severity_critical_above_threshold(self):
        df = pd.DataFrame({"id": range(100), "agency": [None] * 100})
        findings = completeness.run(df)
        crit = [f for f in findings if f.severity == Severity.CRITICAL]
        assert len(crit) > 0

    def test_empty_dataframe_returns_no_findings(self):
        findings = completeness.run(pd.DataFrame())
        assert findings == []

    def test_all_findings_are_completeness_dimension(self, dirty_df):
        findings = completeness.run(dirty_df)
        for f in findings:
            assert f.dimension == Dimension.COMPLETENESS


# ── Validity tests ────────────────────────────────────────────────────────────

class TestValidity:
    def test_no_findings_on_clean_data(self, clean_df):
        findings = validity.run(clean_df)
        assert len(findings) == 0

    def test_detects_invalid_zip(self, dirty_df):
        findings = validity.run(dirty_df)
        zip_findings = [f for f in findings if "zip" in (f.column or "").lower()]
        assert len(zip_findings) > 0

    def test_all_findings_validity_dimension(self, dirty_df):
        findings = validity.run(dirty_df)
        for f in findings:
            assert f.dimension == Dimension.VALIDITY

    def test_date_column_checked(self):
        df = pd.DataFrame({
            "created_date": ["2024-01-01", "not-a-date"] * 100,
        })
        findings = validity.run(df)
        date_findings = [f for f in findings if "date" in (f.column or "").lower()]
        assert len(date_findings) > 0


# ── PII detector tests ────────────────────────────────────────────────────────

class TestPIIDetector:
    def test_detects_email_column(self):
        df = pd.DataFrame({"email": ["user@example.com", "other@test.gov"]})
        findings = pii_detector.run(df)
        assert len(findings) == 1
        assert findings[0].severity == Severity.CRITICAL

    def test_detects_ssn_values(self):
        df = pd.DataFrame({"reference_id": ["123-45-6789", "987-65-4321", None, "normal"]})
        findings = pii_detector.run(df)
        assert len(findings) == 1

    def test_no_false_positive_on_clean_data(self, clean_df):
        findings = pii_detector.run(clean_df)
        assert len(findings) == 0

    def test_detects_lat_lon_as_geolocation_pii(self):
        df = pd.DataFrame({
            "latitude":  [40.7128, 40.6501],
            "longitude": [-74.0060, -73.9496],
        })
        findings = pii_detector.run(df)
        assert len(findings) >= 1


# ── AI readiness tests ────────────────────────────────────────────────────────

class TestAIReadiness:
    def test_small_dataset_warning(self):
        df = pd.DataFrame({"id": range(50), "status": ["Open"] * 50})
        findings = ai_readiness.run(df)
        row_findings = [f for f in findings if "row" in f.id.lower()]
        assert len(row_findings) > 0

    def test_duplicate_rows_detected(self):
        base = pd.DataFrame({"id": range(100), "val": ["x"] * 100})
        duped = pd.concat([base] * 3, ignore_index=True)
        findings = ai_readiness.run(duped)
        dup_findings = [f for f in findings if "dup" in f.id.lower()]
        assert len(dup_findings) > 0

    def test_class_imbalance_detected(self):
        n = 1000
        labels = ["Closed"] * 980 + ["Fraud"] * 20
        df = pd.DataFrame({"id": range(n), "status": labels})
        findings = ai_readiness.run(df)
        imbal = [f for f in findings if "imbal" in f.id.lower()]
        assert len(imbal) > 0

    def test_clean_large_dataset_has_no_critical(self):
        rng = np.random.default_rng(0)
        n = 5000
        df = pd.DataFrame({
            "id":     range(n),
            "status": rng.choice(["Open", "Closed", "Pending"], n).tolist(),
            "val":    rng.normal(0, 1, n).tolist(),
        })
        findings = ai_readiness.run(df)
        crits = [f for f in findings if f.severity == Severity.CRITICAL]
        assert len(crits) == 0


# ── Consistency tests ─────────────────────────────────────────────────────────

class TestConsistency:
    def test_detects_inverted_dates(self):
        df = pd.DataFrame({
            "created_date": ["2024-03-01", "2024-01-01"],
            "closed_date":  ["2024-01-01", "2024-03-01"],  # First row: closed before created
        })
        findings = consistency.run(df)
        assert len(findings) >= 1
        assert findings[0].severity == Severity.CRITICAL

    def test_no_findings_on_valid_dates(self, clean_df):
        findings = consistency.run(clean_df)
        assert len(findings) == 0
