"""
app/pages/snowflake_setup.py
Snowflake connection test and Phase 2 setup verification page.
"""
from __future__ import annotations

import os
import streamlit as st
from app.theme import page_header


def render():
    page_header(
        "Snowflake Setup",
        "Verify your Phase 2 Snowflake connection and environment."
    )

    st.markdown("### Connection configuration")

    # Show current env var status (values masked)
    env_vars = {
        "SNOWFLAKE_ACCOUNT":           os.environ.get("SNOWFLAKE_ACCOUNT", ""),
        "SNOWFLAKE_USER":              os.environ.get("SNOWFLAKE_USER", ""),
        "SNOWFLAKE_PRIVATE_KEY_PATH":  os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH", ""),
        "SNOWFLAKE_WAREHOUSE":         os.environ.get("SNOWFLAKE_WAREHOUSE", ""),
        "SNOWFLAKE_DATABASE":          os.environ.get("SNOWFLAKE_DATABASE", ""),
        "SNOWFLAKE_SCHEMA":            os.environ.get("SNOWFLAKE_SCHEMA", ""),
        "SNOWFLAKE_ROLE":              os.environ.get("SNOWFLAKE_ROLE", ""),
    }

    rows_html = ""
    all_set = True
    for k, v in env_vars.items():
        if v:
            status = "🟢"
            display = v if k not in ("SNOWFLAKE_PRIVATE_KEY_PATH",) else v
        else:
            status = "🔴"
            display = "not set"
            all_set = False
        rows_html += (
            f'<tr style="border-bottom:1px solid rgba(0,0,0,0.06);">'
            f'<td style="padding:8px 12px;font-family:monospace;font-size:13px;">{k}</td>'
            f'<td style="padding:8px 12px;">{status}</td>'
            f'<td style="padding:8px 12px;color:rgba(0,0,0,0.60);font-size:13px;">{display or "—"}</td>'
            f'</tr>'
        )

    st.markdown(
        f'<table style="width:100%;border-collapse:collapse;font-size:14px;">'
        f'<tr style="border-bottom:2px solid #E6E3F3;">'
        f'<th style="text-align:left;padding:8px 12px;font-size:12px;font-weight:600;'
        f'color:rgba(0,0,0,0.60);text-transform:uppercase;letter-spacing:0.5px;">Variable</th>'
        f'<th style="text-align:left;padding:8px 12px;font-size:12px;font-weight:600;'
        f'color:rgba(0,0,0,0.60);text-transform:uppercase;letter-spacing:0.5px;">Status</th>'
        f'<th style="text-align:left;padding:8px 12px;font-size:12px;font-weight:600;'
        f'color:rgba(0,0,0,0.60);text-transform:uppercase;letter-spacing:0.5px;">Value</th>'
        f'</tr>{rows_html}</table>',
        unsafe_allow_html=True
    )

    st.divider()

    if not all_set:
        st.warning(
            "Some environment variables are not set. "
            "Copy `.env.example` to `.env` and fill in your Snowflake credentials."
        )
        with st.expander("Key-pair setup instructions"):
            st.code("""
# 1. Generate private key (no passphrase — simplest for dev)
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out ~/.ssh/snowflake_rsa_key.p8 -nocrypt

# 2. Generate public key
openssl rsa -in ~/.ssh/snowflake_rsa_key.p8 -pubout -out ~/.ssh/snowflake_rsa_key.pub

# 3. View public key (copy everything between BEGIN/END PUBLIC KEY)
cat ~/.ssh/snowflake_rsa_key.pub

# 4. Register with Snowflake (run in Snowsight)
# ALTER USER <YOUR_USERNAME> SET RSA_PUBLIC_KEY='<paste public key contents here>';

# 5. Add to .env
# SNOWFLAKE_PRIVATE_KEY_PATH=~/.ssh/snowflake_rsa_key.p8
""", language="bash")
        return

    # ── Test connection ───────────────────────────────────────────────────────
    if st.button("▶ Test Connection", type="primary"):
        with st.spinner("Connecting to Snowflake..."):
            try:
                from engine.snowflake.connection import test_connection
                result = test_connection()

                if result["status"] == "connected":
                    st.success("✅ Connected to Snowflake successfully!")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("User",      result["user"])
                    col2.metric("Warehouse", result["warehouse"])
                    col3.metric("Database",  result["database"])
                    st.caption(f"Snowflake version: {result['version']}")

                    # Check Cortex availability
                    st.divider()
                    st.markdown("### Cortex availability")
                    _check_cortex()

                    # Check required objects
                    st.divider()
                    st.markdown("### Required objects")
                    _check_objects()

                else:
                    st.error(f"❌ Connection failed: {result['error']}")
                    st.info("Check your .env values and verify your private key is registered with Snowflake.")

            except ImportError:
                st.error("Snowflake packages not installed. Run: pip install snowflake-snowpark-python")
            except Exception as e:
                st.error(f"❌ Error: {e}")


def _check_cortex():
    """Test Cortex COMPLETE availability."""
    try:
        from engine.snowflake.connection import get_session
        session = get_session()
        result = session.sql(
            "SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2', "
            "'Respond with exactly one word: working') AS test"
        ).collect()[0][0]
        st.success(f"✅ Cortex COMPLETE available — test response: '{result.strip()}'")
    except Exception as e:
        st.warning(f"⚠️ Cortex not available: {e}")
        st.caption("Ensure your account has Cortex enabled and your role has SNOWFLAKE.CORTEX_USER.")


def _check_objects():
    """Check that required Snowflake objects exist."""
    from engine.snowflake.connection import get_session
    session = get_session()

    checks = [
        ("Database",
         "SELECT COUNT(*) FROM DQ_ACCELERATOR.INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = 'ASSESSMENTS'"),
        ("Schema ASSESSMENTS",
         "SELECT COUNT(*) FROM DQ_ACCELERATOR.INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = 'ASSESSMENTS'"),
        ("Schema UNSTRUCTURED",
         "SELECT COUNT(*) FROM DQ_ACCELERATOR.INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = 'UNSTRUCTURED'"),
        ("Table ASSESSMENT_RESULTS",
         "SELECT COUNT(*) FROM DQ_ACCELERATOR.ASSESSMENTS.ASSESSMENT_RESULTS LIMIT 1"),
    ]

    for label, sql in checks:
        try:
            count = session.sql(sql).collect()[0][0]
            if count >= 0:
                st.markdown(f"🟢 {label}")
            else:
                st.markdown(f"🔴 {label} — not found. Run `snowflake/setup.sql` in Snowsight.")
        except Exception as e:
            st.markdown(f"🟡 {label} — could not check: {e}")
