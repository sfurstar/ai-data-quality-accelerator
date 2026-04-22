"""
scripts/generate_sample_policy.py

Generates a realistic synthetic government data governance policy PDF
with deliberate compliance gaps baked in for demo purposes.

Gap map (what the scanner WILL find):
  HIPAA-001  MISSING  — No breach notification timeline (60 days not mentioned)
  HIPAA-003  MISSING  — No PHI de-identification procedure documented
  GDPR-002   MISSING  — No right to erasure / deletion process
  GDPR-003   MISSING  — No data retention period specified
  GDPR-004   MISSING  — No Data Protection Officer (DPO) referenced
  GDPR-005   MISSING  — No cross-border data transfer restrictions
  FEDRAMP-003 MISSING — No patch/vulnerability remediation timeline
  GOV-002    MISSING  — No data classification scheme defined

What PASSES (intentionally):
  HIPAA-002  PASS  — Workforce training on PHI mentioned
  HIPAA-004  PASS  — Physical access controls mentioned
  GDPR-001   PASS  — Consent and lawful basis mentioned
  FEDRAMP-001 PASS — Account management lifecycle defined
  FEDRAMP-002 PASS — Audit logging mentioned
  FEDRAMP-004 PASS — Encryption at rest (AES-256) mentioned
  GOV-001    PASS  — Data owner and steward roles defined
  GOV-003    PASS  — Data lineage / source system mentioned
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

OUTPUT_PATH = Path(__file__).parent.parent / "data" / "sample" / "unstructured" / "state_data_governance_policy.pdf"


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

    # Custom styles
    title_style = ParagraphStyle(
        "PolicyTitle",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#3A2679"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "PolicySubtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#5236AB"),
        spaceAfter=4,
    )
    h1_style = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        fontSize=14,
        textColor=colors.HexColor("#3A2679"),
        spaceBefore=18,
        spaceAfter=6,
        borderPad=4,
    )
    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#2D1E5E"),
        spaceBefore=12,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        spaceAfter=8,
    )
    note_style = ParagraphStyle(
        "Note",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#5C5C5C"),
        leftIndent=20,
        spaceAfter=6,
        leading=13,
    )

    story = []

    # ── Cover block ───────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("STATE OF LAKEWOOD", subtitle_style))
    story.append(Paragraph("Department of Health and Human Services", subtitle_style))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Data Governance & Information Management Policy", title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#3A2679")))
    story.append(Spacer(1, 0.1 * inch))

    meta = [
        ["Policy Number:", "DHHS-DG-2024-001"],
        ["Effective Date:", "January 1, 2024"],
        ["Last Reviewed:", "March 15, 2024"],
        ["Status:", "Active"],
        ["Classification:", "Internal Use"],
        ["Owner:", "Office of the Chief Information Officer"],
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
        "This policy establishes the framework for data governance and information management "
        "within the State of Lakewood Department of Health and Human Services (DHHS). It defines "
        "roles, responsibilities, and controls for managing data assets in compliance with applicable "
        "federal and state regulations, including the Health Insurance Portability and Accountability "
        "Act (HIPAA) and applicable privacy statutes.",
        body_style
    ))
    story.append(Paragraph(
        "This policy applies to all DHHS employees, contractors, and third-party vendors who "
        "collect, process, store, or transmit departmental data, including protected health "
        "information (PHI) and personally identifiable information (PII).",
        body_style
    ))

    # ── Section 2: Data Governance Roles ──────────────────────────────────────
    story.append(Paragraph("2. Data Governance Roles and Responsibilities", h1_style))

    story.append(Paragraph("2.1 Data Owner", h2_style))
    story.append(Paragraph(
        "Each data domain within DHHS shall have a designated Data Owner who is a senior "
        "department official responsible for authorizing access, ensuring data quality, and "
        "approving use of the data asset. The Data Owner is accountable for compliance with "
        "this policy and applicable regulatory requirements.",
        body_style
    ))

    story.append(Paragraph("2.2 Data Steward", h2_style))
    story.append(Paragraph(
        "Data Stewards are appointed by Data Owners to manage day-to-day data quality, "
        "metadata maintenance, and operational governance activities. Each data steward is "
        "responsible for maintaining data lineage documentation and tracking source systems "
        "for all assigned data assets.",
        body_style
    ))

    story.append(Paragraph("2.3 Data Custodian", h2_style))
    story.append(Paragraph(
        "Data Custodians (typically IT staff) are responsible for the technical implementation "
        "of data security controls, backup procedures, and storage management as directed by "
        "the Data Owner.",
        body_style
    ))

    # ── GAP: No DPO referenced ────────────────────────────────────────────────
    # GDPR-004 will FAIL — no DPO mentioned anywhere in this section

    # ── Section 3: Data Security Controls ────────────────────────────────────
    story.append(Paragraph("3. Data Security and Access Controls", h1_style))

    story.append(Paragraph("3.1 Access Management", h2_style))
    story.append(Paragraph(
        "Access to DHHS data systems shall be granted based on the principle of least privilege. "
        "User accounts must be provisioned through the IT Service Desk with written approval from "
        "the relevant Data Owner. All user accounts are subject to quarterly access reviews. "
        "Accounts for terminated employees shall be deactivated within 24 hours of separation.",
        body_style
    ))

    story.append(Paragraph("3.2 Encryption", h2_style))
    story.append(Paragraph(
        "All data at rest containing PHI or PII must be encrypted using AES-256 encryption "
        "or equivalent. Data in transit must use TLS 1.2 or higher. Unencrypted PHI shall not "
        "be stored on portable media or transmitted via unencrypted email.",
        body_style
    ))

    story.append(Paragraph("3.3 Physical Safeguards", h2_style))
    story.append(Paragraph(
        "Physical access controls must restrict facility access to authorized personnel only. "
        "Workstation security policies require screen locks after 10 minutes of inactivity. "
        "Server rooms and data centers must maintain access logs reviewed monthly.",
        body_style
    ))

    story.append(Paragraph("3.4 Audit Logging", h2_style))
    story.append(Paragraph(
        "All access to systems containing PHI or sensitive data must be logged. Audit logs "
        "must capture user identity, timestamp, action performed, and data elements accessed. "
        "Audit trail records must be retained for a minimum of six years and protected from "
        "unauthorized modification.",
        body_style
    ))

    # ── GAP: No patch management timeline ────────────────────────────────────
    # FEDRAMP-003 will FAIL — security patching not addressed

    story.append(PageBreak())

    # ── Section 4: PHI and HIPAA Compliance ───────────────────────────────────
    story.append(Paragraph("4. Protected Health Information (PHI) Handling", h1_style))

    story.append(Paragraph("4.1 Workforce Training", h2_style))
    story.append(Paragraph(
        "All workforce members who handle protected health information must complete HIPAA "
        "workforce training upon hire and annually thereafter. Training must cover appropriate "
        "use and disclosure of PHI, minimum necessary standards, and consequences of unauthorized "
        "disclosure. Training completion must be documented and retained.",
        body_style
    ))

    # ── GAP: Breach notification — no 60-day timeline ────────────────────────
    # HIPAA-001 will FAIL — mentions breach notification but NOT the 60-day requirement
    story.append(Paragraph("4.2 Security Incident Response", h2_style))
    story.append(Paragraph(
        "Security incidents involving potential unauthorized access to PHI must be reported "
        "immediately to the DHHS Security Officer. The Security Officer will conduct a risk "
        "assessment to determine whether a reportable breach has occurred. Affected individuals "
        "and relevant authorities will be notified in accordance with applicable law.",
        body_style
    ))
    story.append(Paragraph(
        "Note: Incident response procedures are documented separately in the DHHS Incident "
        "Response Plan (DHHS-IR-2024-001). Staff should refer to that document for detailed "
        "escalation procedures.",
        note_style
    ))
    # DELIBERATE GAP: "60 days" / "60-day" notification timeline NOT mentioned

    # ── GAP: No de-identification procedure ──────────────────────────────────
    # HIPAA-003 will FAIL — PHI de-identification not addressed
    story.append(Paragraph("4.3 Minimum Necessary Standard", h2_style))
    story.append(Paragraph(
        "Workforce members must only access, use, or disclose the minimum necessary PHI "
        "required to perform their job functions. Requests for PHI from external parties must "
        "be reviewed and approved by the Data Owner prior to disclosure.",
        body_style
    ))

    # ── Section 5: Privacy and Consent ───────────────────────────────────────
    story.append(Paragraph("5. Privacy, Consent, and Individual Rights", h1_style))

    story.append(Paragraph("5.1 Lawful Basis for Processing", h2_style))
    story.append(Paragraph(
        "DHHS collects and processes personal data only on the basis of lawful authority, "
        "including statutory mandates, contractual necessity, and explicit consent from "
        "data subjects where required. Privacy notices are provided to individuals at the "
        "point of data collection describing the purpose and use of their personal data.",
        body_style
    ))

    # ── GAP: No right to erasure ─────────────────────────────────────────────
    # GDPR-002 will FAIL — no deletion/erasure rights mentioned
    story.append(Paragraph("5.2 Individual Access Rights", h2_style))
    story.append(Paragraph(
        "Individuals have the right to access their personal data held by DHHS. Requests "
        "for access must be submitted in writing to the DHHS Privacy Office and will be "
        "fulfilled within 30 days. The department will verify the identity of the requestor "
        "before releasing any personal information.",
        body_style
    ))
    # DELIBERATE GAP: Right to erasure / deletion not mentioned

    # ── GAP: No retention period ─────────────────────────────────────────────
    # GDPR-003 will FAIL — no specific retention period stated
    story.append(Paragraph("5.3 Data Minimization", h2_style))
    story.append(Paragraph(
        "DHHS shall collect only the personal data necessary for the stated purpose. "
        "Data that is no longer required for its original purpose shall be reviewed "
        "by the Data Owner for potential disposal. Disposal procedures must comply with "
        "applicable records retention schedules.",
        body_style
    ))
    # DELIBERATE GAP: No specific retention period (e.g. "3 years", "7 years") stated

    story.append(PageBreak())

    # ── Section 6: Data Quality ───────────────────────────────────────────────
    story.append(Paragraph("6. Data Quality and Lineage", h1_style))
    story.append(Paragraph(
        "Data Stewards are responsible for maintaining documented data lineage for all "
        "critical data elements, including source system identification, transformation "
        "rules, and data flow diagrams. Data quality metrics must be reviewed quarterly "
        "and reported to the Data Governance Committee.",
        body_style
    ))
    story.append(Paragraph(
        "Data quality issues identified through automated monitoring or manual review "
        "must be logged in the departmental issue tracking system and resolved within "
        "timeframes established by the Data Owner based on severity.",
        body_style
    ))

    # ── GAP: No data classification scheme ───────────────────────────────────
    # GOV-002 will FAIL — no classification levels defined
    story.append(Paragraph("6.1 Data Inventory", h2_style))
    story.append(Paragraph(
        "The department shall maintain a current inventory of all data assets including "
        "description, owner, steward, storage location, and applicable regulatory "
        "requirements. The data inventory shall be reviewed and updated annually.",
        body_style
    ))
    # DELIBERATE GAP: No classification scheme (Public/Internal/Confidential/Restricted)

    # ── GAP: No cross-border transfer restrictions ────────────────────────────
    # GDPR-005 will FAIL — no mention of cross-border or data residency
    story.append(Paragraph("6.2 Third-Party Data Sharing", h2_style))
    story.append(Paragraph(
        "Data sharing with external parties requires a formal Data Sharing Agreement (DSA) "
        "approved by the DHHS General Counsel and the relevant Data Owner. All third-party "
        "recipients must demonstrate equivalent data protection controls prior to receiving "
        "DHHS data.",
        body_style
    ))
    # DELIBERATE GAP: No mention of cross-border restrictions, data residency, or sovereignty

    # ── Section 7: Compliance and Enforcement ────────────────────────────────
    story.append(Paragraph("7. Compliance and Enforcement", h1_style))
    story.append(Paragraph(
        "Violations of this policy may result in disciplinary action up to and including "
        "termination of employment or contract. Suspected violations must be reported to "
        "the DHHS Security Officer or the Office of Inspector General.",
        body_style
    ))
    story.append(Paragraph(
        "This policy will be reviewed annually by the Data Governance Committee and updated "
        "as necessary to reflect changes in law, regulation, or departmental operations.",
        body_style
    ))

    # ── Section 8: Related Documents ─────────────────────────────────────────
    story.append(Paragraph("8. Related Policies and References", h1_style))
    refs = [
        ["DHHS-IR-2024-001", "Incident Response Plan"],
        ["DHHS-IT-2024-003", "Information Security Policy"],
        ["DHHS-HR-2024-007", "Acceptable Use Policy"],
        ["45 CFR Parts 160 and 164", "HIPAA Security and Privacy Rules"],
        ["State Statute 42.7.110", "State Data Privacy Act"],
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
        "State of Lakewood — Department of Health and Human Services | "
        "Policy DHHS-DG-2024-001 | For internal use only",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8,
                       textColor=colors.HexColor("#888888"), alignment=1)
    ))

    doc.build(story)
    print(f"✅ Generated: {OUTPUT_PATH}")
    print(f"   Size: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")
    print()
    print("Gap map — scanner WILL find these:")
    gaps = [
        ("HIPAA-001", "FAIL", "No 60-day breach notification timeline"),
        ("HIPAA-003", "FAIL", "No PHI de-identification procedure"),
        ("GDPR-002",  "FAIL", "No right to erasure / deletion"),
        ("GDPR-003",  "FAIL", "No data retention period specified"),
        ("GDPR-004",  "FAIL", "No DPO referenced"),
        ("GDPR-005",  "FAIL", "No cross-border transfer restrictions"),
        ("FEDRAMP-003","FAIL","No patch/vulnerability remediation timeline"),
        ("GOV-002",   "FAIL", "No data classification scheme"),
    ]
    passing = [
        ("HIPAA-002",  "PASS", "Workforce training on PHI"),
        ("HIPAA-004",  "PASS", "Physical safeguards"),
        ("GDPR-001",   "PASS", "Lawful basis / consent"),
        ("FEDRAMP-001","PASS", "Account management"),
        ("FEDRAMP-002","PASS", "Audit logging"),
        ("FEDRAMP-004","PASS", "AES-256 encryption at rest"),
        ("GOV-001",    "PASS", "Data owner and steward roles"),
        ("GOV-003",    "PASS", "Data lineage / source system"),
    ]
    for rule, status, desc in gaps:
        print(f"  ❌ {rule:15} {status}  {desc}")
    print()
    print("Scanner WILL pass these:")
    for rule, status, desc in passing:
        print(f"  ✅ {rule:15} {status}  {desc}")


if __name__ == "__main__":
    build()
