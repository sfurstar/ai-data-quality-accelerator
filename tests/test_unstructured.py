"""
tests/test_unstructured.py
Tests for the compliance scanner and scoring engine.

Run with: pytest tests/test_unstructured.py -v
"""
import pytest

from engine import Dimension, Severity
from engine.unstructured.compliance_scanner import run as scan_compliance, get_coverage_summary
from engine.scoring.scorer import build_result, compute_ai_readiness_index, score_dimension
from engine import Finding


# ── Sample texts ──────────────────────────────────────────────────────────────

GOOD_HIPAA_TEXT = """
This data governance policy establishes controls for protected health information (PHI).

In the event of a security breach, the organization will provide breach notification within 60 days
of discovery to all affected individuals as required by HIPAA.

All workforce members who handle PHI must complete HIPAA workforce training annually.
Training covers appropriate use and safeguards for protected health information.

PHI de-identification procedures follow the HIPAA Safe Harbor method.
Physical access controls restrict facility access to authorized personnel only.
"""

POOR_HIPAA_TEXT = """
This is a general IT policy. We store data securely.
Users must use strong passwords. Data is backed up nightly.
"""

GOOD_GDPR_TEXT = """
We process personal data based on lawful basis and consent from data subjects.
Data subjects may exercise their right to erasure by submitting a deletion request.
Personal data will be retained for no more than 3 years from collection.
Our Data Protection Officer (DPO) can be reached at privacy@example.gov.
Cross-border data transfers require standard contractual clauses to ensure data residency compliance.
"""


# ── Compliance scanner tests ──────────────────────────────────────────────────

class TestComplianceScanner:
    def test_good_hipaa_text_has_fewer_findings(self):
        findings = scan_compliance(GOOD_HIPAA_TEXT, standards=["HIPAA"])
        bad_findings = scan_compliance(POOR_HIPAA_TEXT, standards=["HIPAA"])
        assert len(findings) < len(bad_findings)

    def test_poor_text_triggers_critical_hipaa(self):
        findings = scan_compliance(POOR_HIPAA_TEXT, standards=["HIPAA"])
        crits = [f for f in findings if f.severity == Severity.CRITICAL]
        assert len(crits) > 0

    def test_all_findings_are_compliance_dimension(self):
        findings = scan_compliance(POOR_HIPAA_TEXT, standards=["HIPAA", "GDPR"])
        for f in findings:
            assert f.dimension == Dimension.COMPLIANCE

    def test_findings_have_rule_refs(self):
        findings = scan_compliance(POOR_HIPAA_TEXT, standards=["HIPAA"])
        for f in findings:
            assert f.rule_ref is not None
            assert "HIPAA" in f.rule_ref

    def test_good_gdpr_text_passes_most_rules(self):
        findings = scan_compliance(GOOD_GDPR_TEXT, standards=["GDPR"])
        crits = [f for f in findings if f.severity == Severity.CRITICAL]
        assert len(crits) == 0

    def test_standard_filter_respected(self):
        findings_hipaa = scan_compliance(POOR_HIPAA_TEXT, standards=["HIPAA"])
        findings_gdpr  = scan_compliance(POOR_HIPAA_TEXT, standards=["GDPR"])
        hipaa_ids = {f.id for f in findings_hipaa}
        gdpr_ids  = {f.id for f in findings_gdpr}
        assert hipaa_ids.isdisjoint(gdpr_ids)

    def test_coverage_summary_structure(self):
        summary = get_coverage_summary(GOOD_HIPAA_TEXT, standards=["HIPAA", "GDPR"])
        assert "HIPAA" in summary
        assert "GDPR" in summary
        for std in summary.values():
            assert "passed" in std
            assert "failed" in std
            assert "score" in std
            assert 0 <= std["score"] <= 100


# ── Scoring engine tests ──────────────────────────────────────────────────────

class TestScorer:
    def _make_findings(self, n_critical=0, n_warning=0, n_info=0):
        findings = []
        for i in range(n_critical):
            findings.append(Finding(
                id=f"C-{i}", dimension=Dimension.COMPLETENESS,
                severity=Severity.CRITICAL, title="crit", description="x",
            ))
        for i in range(n_warning):
            findings.append(Finding(
                id=f"W-{i}", dimension=Dimension.COMPLETENESS,
                severity=Severity.WARNING, title="warn", description="x",
            ))
        for i in range(n_info):
            findings.append(Finding(
                id=f"I-{i}", dimension=Dimension.COMPLETENESS,
                severity=Severity.INFO, title="info", description="x",
            ))
        return findings

    def test_clean_data_scores_100(self):
        ds = score_dimension([], weight=0.20, dimension=Dimension.COMPLETENESS)
        assert ds.score == 100.0

    def test_critical_findings_deduct_points(self):
        findings = self._make_findings(n_critical=3)
        ds = score_dimension(findings, weight=0.20, dimension=Dimension.COMPLETENESS)
        assert ds.score == 100 - (3 * 15)

    def test_score_floor_is_zero(self):
        findings = self._make_findings(n_critical=20)
        ds = score_dimension(findings, weight=0.20, dimension=Dimension.COMPLETENESS)
        assert ds.score == 0.0

    def test_build_result_computes_index(self):
        from engine import Dimension
        findings_by_dim = {
            Dimension.COMPLETENESS: self._make_findings(n_critical=1),
            Dimension.VALIDITY:     [],
            Dimension.GOVERNANCE:   [],
            Dimension.AI_READINESS: [],
            Dimension.CONSISTENCY:  [],
        }
        result = build_result("test.csv", "structured", findings_by_dim)
        assert 0 <= result.ai_readiness_index <= 100
        assert result.maturity_tier in ["High Risk", "Moderate", "AI Ready"]

    def test_zero_findings_yields_ai_ready(self):
        from engine import Dimension
        findings_by_dim = {d: [] for d in [
            Dimension.COMPLETENESS, Dimension.VALIDITY,
            Dimension.GOVERNANCE, Dimension.AI_READINESS, Dimension.CONSISTENCY,
        ]}
        result = build_result("clean.csv", "structured", findings_by_dim)
        assert result.ai_readiness_index == 100.0
        assert result.maturity_tier == "AI Ready"

    def test_many_criticals_yields_high_risk(self):
        from engine import Dimension
        findings_by_dim = {
            d: self._make_findings(n_critical=10)
            for d in [Dimension.COMPLETENESS, Dimension.VALIDITY, Dimension.GOVERNANCE]
        }
        result = build_result("bad.csv", "structured", findings_by_dim)
        assert result.maturity_tier == "High Risk"
