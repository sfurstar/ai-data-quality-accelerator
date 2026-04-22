"""
scripts/generate_compliant_policy.py

Generates a synthetic "model" data governance policy PDF that passes
most compliance rules — scoring ~85/100 for demo contrast.

Gap map (deliberate minor gaps to keep it realistic, not perfect):
  HIPAA-003  MISSING  — De-identification method not fully specified (warning only)
  GDPR-004   MISSING  — DPO contact details not provided (info only)

Everything else PASSES:
  HIPAA-001  PASS  — 60-day breach notification timeline explicit
  HIPAA-002  PASS  — Workforce PHI training
  HIPAA-004  PASS  — Physical safeguards
  GDPR-001   PASS  — Consent and lawful basis
  GDPR-002   PASS  — Right to erasure process
  GDPR-003   PASS  — Data retention period (7 years)
  GDPR-005   PASS  — Cross-border / data residency
  FEDRAMP-001 PASS — Account management lifecycle
  FEDRAMP-002 PASS — Audit logging
  FEDRAMP-003 PASS — Patch management (30-day timeline)
  FEDRAMP-004 PASS — AES-256 encryption at rest
  GOV-001    PASS  — Data owner and steward
  GOV-002    PASS  — Data classification scheme
  GOV-003    PASS  — Data lineage / source system
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)

OUTPUT_PATH = Path(__file__).parent.parent / "data" / "sample" / "unstructured" / "model_data_governance_policy.pdf"


def build():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=letter,
        rightMargin=1 * inch,
        leftMargin=1 * inch,
        topMargin=1 * inch,
        bottomMargin=1 * inch,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("T", parent=styles["Title"], fontSize=20,
                                  textColor=colors.HexColor("#3A2679"), spaceAfter=6)
    subtitle_style = ParagraphStyle("S", parent=styles["Normal"], fontSize=11,
                                     textColor=colors.HexColor("#5236AB"), spaceAfter=4)
    h1_style = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=14,
                               textColor=colors.HexColor("#3A2679"), spaceBefore=18, spaceAfter=6)
    h2_style = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12,
                               textColor=colors.HexColor("#2D1E5E"), spaceBefore=12, spaceAfter=4)
    body_style = ParagraphStyle("B", parent=styles["Normal"], fontSize=10, leading=15, spaceAfter=8)
    note_style = ParagraphStyle("N", parent=styles["Normal"], fontSize=9,
                                 textColor=colors.HexColor("#5C5C5C"), leftIndent=20,
                                 spaceAfter=6, leading=13)
    callout_style = ParagraphStyle("C", parent=styles["Normal"], fontSize=9,
                                    textColor=colors.HexColor("#128354"),
                                    leftIndent=20, spaceAfter=6, leading=13,
                                    borderPad=6)

    story = []

    # ── Cover ─────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("CITY OF MERIDIAN", subtitle_style))
    story.append(Paragraph("Office of Digital Services & Information Technology", subtitle_style))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Enterprise Data Governance & Privacy Policy", title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#3A2679")))
    story.append(Spacer(1, 0.1 * inch))

    meta = [
        ["Policy Number:", "ODSIT-DG-2024-005"],
        ["Version:", "2.1"],
        ["Effective Date:", "January 1, 2024"],
        ["Last Reviewed:", "April 1, 2024"],
        ["Next Review:", "April 1, 2025"],
        ["Status:", "Active — Approved"],
        ["Classification:", "Internal Use — Controlled"],
        ["Owner:", "Chief Data Officer, Office of Digital Services"],
        ["Data Protection Officer:", "privacy@meridian.gov"],
    ]
    meta_table = Table(meta, colWidths=[2 * inch, 4 * inch])
    meta_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#5236AB")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.2 * inch))

    # ── Section 1: Purpose ────────────────────────────────────────────────────
    story.append(Paragraph("1. Purpose and Scope", h1_style))
    story.append(Paragraph(
        "This policy establishes the City of Meridian's enterprise framework for data governance, "
        "privacy protection, and regulatory compliance. It defines roles, responsibilities, standards, "
        "and controls for all data assets processed by or on behalf of the City, in compliance with "
        "the Health Insurance Portability and Accountability Act (HIPAA), the General Data Protection "
        "Regulation (EU) 2016/679 (GDPR), FedRAMP authorization requirements, and applicable "
        "state privacy statutes.",
        body_style
    ))
    story.append(Paragraph(
        "This policy applies to all City employees, contractors, vendors, and partners who collect, "
        "process, store, or transmit City data, including protected health information (PHI), "
        "personally identifiable information (PII), and confidential government records.",
        body_style
    ))

    # ── Section 2: Data Classification ───────────────────────────────────────
    story.append(Paragraph("2. Data Classification Scheme", h1_style))
    story.append(Paragraph(
        "All City data assets must be classified according to the following four-tier scheme. "
        "Data Owners are responsible for assigning and maintaining the correct classification "
        "for all data under their stewardship.",
        body_style
    ))

    class_data = [
        ["Level", "Label", "Description", "Examples"],
        ["1", "Public", "Approved for public release", "Open data, press releases"],
        ["2", "Internal", "For City staff use only", "Internal memos, staff directories"],
        ["3", "Confidential", "Sensitive, restricted access", "PHI, PII, financial records"],
        ["4", "Restricted", "Highest sensitivity, strictly controlled", "Law enforcement, SSNs, biometrics"],
    ]
    class_table = Table(class_data, colWidths=[0.6*inch, 1.2*inch, 2.5*inch, 1.7*inch])
    class_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E6E3F3")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C0C0C0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F1F9")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(class_table)
    story.append(Spacer(1, 0.15 * inch))

    # ── Section 3: Governance Roles ───────────────────────────────────────────
    story.append(Paragraph("3. Data Governance Roles", h1_style))

    story.append(Paragraph("3.1 Chief Data Officer (CDO)", h2_style))
    story.append(Paragraph(
        "The CDO is accountable for enterprise data strategy, policy compliance, and the "
        "overall Data Governance Program. The CDO chairs the Data Governance Committee "
        "and reports data quality and compliance metrics to the City Manager quarterly.",
        body_style
    ))

    story.append(Paragraph("3.2 Data Owner", h2_style))
    story.append(Paragraph(
        "Each data domain has a designated Data Owner — a senior official responsible for "
        "authorizing access, ensuring quality, approving use cases, and maintaining the "
        "data asset inventory entry. Data Owners must be identified for all Confidential "
        "and Restricted classification data assets.",
        body_style
    ))

    story.append(Paragraph("3.3 Data Steward", h2_style))
    story.append(Paragraph(
        "Data Stewards manage day-to-day quality, metadata, and lineage documentation. "
        "Each steward must maintain source system documentation, transformation rules, "
        "and data flow diagrams for assigned data assets. Stewards report quality metrics "
        "monthly to the Data Owner.",
        body_style
    ))

    story.append(Paragraph("3.4 Data Protection Officer (DPO)", h2_style))
    story.append(Paragraph(
        "The City's Data Protection Officer is responsible for overseeing GDPR compliance, "
        "advising on data protection impact assessments, and serving as the point of contact "
        "for data subjects exercising their rights. The DPO can be reached at privacy@meridian.gov.",
        body_style
    ))

    story.append(PageBreak())

    # ── Section 4: Security Controls ─────────────────────────────────────────
    story.append(Paragraph("4. Data Security Controls", h1_style))

    story.append(Paragraph("4.1 Access Management", h2_style))
    story.append(Paragraph(
        "User accounts are provisioned using role-based access control (RBAC) with written "
        "Data Owner approval. All accounts undergo quarterly access reviews. Accounts for "
        "terminated employees or contractors must be deactivated within 4 hours of separation. "
        "Privileged accounts require multi-factor authentication and are reviewed monthly.",
        body_style
    ))

    story.append(Paragraph("4.2 Encryption", h2_style))
    story.append(Paragraph(
        "All data at rest classified as Confidential or Restricted must be encrypted using "
        "AES-256 encryption. Data in transit must use TLS 1.3. Portable media containing "
        "PHI or PII must be encrypted prior to removal from City premises.",
        body_style
    ))

    story.append(Paragraph("4.3 Physical Safeguards", h2_style))
    story.append(Paragraph(
        "Physical access to data centers and server rooms is restricted to authorized personnel "
        "via badge access systems. Workstations must lock automatically after 5 minutes of "
        "inactivity. Visitor access logs are maintained and reviewed monthly. All City facilities "
        "housing Confidential or Restricted data must maintain 24/7 physical access controls.",
        body_style
    ))

    story.append(Paragraph("4.4 Patch and Vulnerability Management", h2_style))
    story.append(Paragraph(
        "Security patches classified as Critical must be applied within 30 days of release. "
        "High-severity vulnerabilities must be remediated within 60 days. The IT Security team "
        "conducts monthly vulnerability scans and reports remediation status to the CDO. "
        "Systems that cannot be patched within the required window must be risk-accepted by "
        "the CISO with compensating controls documented.",
        body_style
    ))
    story.append(Paragraph(
        "Note: Patch management compliance is tracked in the City's IT Service Management "
        "system with monthly reporting to the Data Governance Committee.",
        note_style
    ))

    story.append(Paragraph("4.5 Audit Logging", h2_style))
    story.append(Paragraph(
        "All access to systems containing PHI, PII, or Confidential data must generate audit "
        "log entries capturing: user identity, timestamp, action, data elements accessed, and "
        "source IP. Audit logs must be retained for a minimum of seven years and protected "
        "from unauthorized modification or deletion. Logs are reviewed weekly by the Security "
        "Operations team for anomalous activity.",
        body_style
    ))

    # ── Section 5: HIPAA Compliance ───────────────────────────────────────────
    story.append(Paragraph("5. HIPAA Compliance and PHI Handling", h1_style))

    story.append(Paragraph("5.1 Workforce Training", h2_style))
    story.append(Paragraph(
        "All workforce members who handle protected health information (PHI) must complete "
        "HIPAA workforce training within 30 days of hire and annually thereafter. Training "
        "covers minimum necessary standards, authorized disclosures, and consequences of "
        "violations. Training records are retained for six years.",
        body_style
    ))

    story.append(Paragraph("5.2 Breach Notification", h2_style))
    story.append(Paragraph(
        "In the event of a security incident involving potential unauthorized access to PHI, "
        "the Security Officer must conduct a risk assessment within 72 hours of discovery. "
        "Where a reportable breach is confirmed, affected individuals must receive written "
        "notification within 60 days of discovery, as required by HIPAA §164.412. "
        "Notifications to HHS and, where applicable, prominent media outlets must be made "
        "in accordance with the applicable breach notification timeline.",
        body_style
    ))
    story.append(Paragraph(
        "The 60-day notification requirement is tracked in the Incident Response system "
        "with automated escalation if deadlines approach.",
        callout_style
    ))

    story.append(Paragraph("5.3 Minimum Necessary Standard", h2_style))
    story.append(Paragraph(
        "Workforce members must access only the minimum necessary PHI required for their "
        "job function. All PHI requests from external parties require Data Owner approval "
        "and a valid legal basis documented in the request system.",
        body_style
    ))

    story.append(PageBreak())

    # ── Section 6: Privacy and Individual Rights ──────────────────────────────
    story.append(Paragraph("6. Privacy, Consent, and Individual Rights", h1_style))

    story.append(Paragraph("6.1 Lawful Basis for Processing", h2_style))
    story.append(Paragraph(
        "The City processes personal data only on the basis of lawful authority including "
        "statutory mandates, contractual necessity, vital interests, and explicit consent "
        "from data subjects. Privacy notices describing the purpose, legal basis, and "
        "data subject rights are provided at the point of collection.",
        body_style
    ))

    story.append(Paragraph("6.2 Data Retention", h2_style))
    story.append(Paragraph(
        "Personal data shall be retained only as long as necessary for the stated purpose "
        "and in accordance with the City's Records Retention Schedule. Unless a longer "
        "statutory retention period applies, personal data must be securely disposed of "
        "after seven years from the date of last activity. Retention periods are documented "
        "in the data asset inventory for each data domain.",
        body_style
    ))

    story.append(Paragraph("6.3 Right to Erasure and Data Subject Rights", h2_style))
    story.append(Paragraph(
        "Data subjects have the right to request erasure of their personal data where "
        "it is no longer necessary for the original purpose or where consent has been "
        "withdrawn. Deletion requests must be submitted to the DPO at privacy@meridian.gov "
        "and fulfilled within 30 days unless a statutory retention obligation applies. "
        "The City also honors requests for data access, rectification, restriction of "
        "processing, and data portability in accordance with applicable law.",
        body_style
    ))

    story.append(Paragraph("6.4 Cross-Border Data Transfers and Data Residency", h2_style))
    story.append(Paragraph(
        "Personal data collected by the City shall be stored and processed within the "
        "continental United States. Cross-border transfers of personal data to third "
        "countries are prohibited unless approved by the CDO and the DPO, and require "
        "appropriate safeguards such as standard contractual clauses or adequacy decisions. "
        "Data residency requirements must be documented in all vendor contracts involving "
        "personal data processing.",
        body_style
    ))

    # ── Section 7: Data Quality and Lineage ───────────────────────────────────
    story.append(Paragraph("7. Data Quality and Lineage", h1_style))
    story.append(Paragraph(
        "Data Stewards must maintain documented data lineage for all Confidential and "
        "Restricted data assets, including source system identification, ETL transformation "
        "rules, and data flow diagrams. Lineage documentation is stored in the enterprise "
        "data catalog and reviewed quarterly.",
        body_style
    ))

    # ── Section 8: Third-Party and Vendor Management ──────────────────────────
    story.append(Paragraph("8. Third-Party Data Management", h1_style))
    story.append(Paragraph(
        "All third-party vendors processing City personal data must sign a Data Processing "
        "Agreement (DPA) prior to receiving access. DPAs must specify: data retention and "
        "deletion obligations, security controls, breach notification obligations (within "
        "48 hours to the City), data residency requirements, and prohibition on sub-processing "
        "without prior written consent. Vendor compliance is assessed annually.",
        body_style
    ))

    # ── Section 9: Compliance ─────────────────────────────────────────────────
    story.append(Paragraph("9. Compliance and Enforcement", h1_style))
    story.append(Paragraph(
        "Violations of this policy may result in disciplinary action up to and including "
        "termination. This policy is reviewed annually by the Data Governance Committee "
        "and updated to reflect changes in law, regulation, or City operations.",
        body_style
    ))

    # ── Section 10: Related Documents ────────────────────────────────────────
    story.append(Paragraph("10. Related Policies and References", h1_style))
    refs = [
        ["ODSIT-IR-2024-001", "Incident Response Plan"],
        ["ODSIT-IS-2024-002", "Information Security Policy"],
        ["ODSIT-VM-2024-003", "Vulnerability Management Standard"],
        ["45 CFR Parts 160 and 164", "HIPAA Security and Privacy Rules"],
        ["EU Regulation 2016/679", "General Data Protection Regulation"],
        ["NIST SP 800-53 Rev 5", "Security and Privacy Controls"],
        ["City Ordinance 2024-14", "City of Meridian Data Privacy Act"],
    ]
    ref_table = Table(
        [["Document Number", "Title"]] + refs,
        colWidths=[2.2 * inch, 3.8 * inch]
    )
    ref_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E6E3F3")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C0C0C0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F1F9")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(ref_table)

    story.append(Spacer(1, 0.3 * inch))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#C0C0C0")))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "City of Meridian — Office of Digital Services & Information Technology | "
        "Policy ODSIT-DG-2024-005 v2.1 | Classification: Internal Use — Controlled",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8,
                       textColor=colors.HexColor("#888888"), alignment=1)
    ))

    doc.build(story)
    print(f"✅ Generated: {OUTPUT_PATH}")
    print(f"   Size: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    build()
