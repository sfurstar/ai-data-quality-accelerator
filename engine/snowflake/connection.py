"""
engine/snowflake/connection.py

Snowflake connection manager for Phase 2.
Supports key-pair authentication (recommended for production).

Key-pair setup:
    1. Generate private key:
       openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt
    2. Generate public key:
       openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
    3. Register public key with Snowflake user:
       ALTER USER <username> SET RSA_PUBLIC_KEY='<contents of rsa_key.pub minus header/footer>';
    4. Set env vars (see .env.example)
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _get_private_key():
    """Load private key from file or env var for key-pair auth."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend

    key_path = os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH")
    key_passphrase = os.environ.get("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE", "")

    if key_path and Path(key_path).expanduser().exists():
        with open(Path(key_path).expanduser(), "rb") as f:
            key_data = f.read()
    else:
        # Try inline env var (base64 or PEM string)
        key_str = os.environ.get("SNOWFLAKE_PRIVATE_KEY", "")
        if not key_str:
            raise ValueError(
                "No Snowflake private key found. Set SNOWFLAKE_PRIVATE_KEY_PATH "
                "or SNOWFLAKE_PRIVATE_KEY in .env"
            )
        key_data = key_str.encode()

    passphrase = key_passphrase.encode() if key_passphrase else None

    private_key = serialization.load_pem_private_key(
        key_data, password=passphrase, backend=default_backend()
    )

    return private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


@lru_cache(maxsize=1)
def get_session():
    """
    Get a cached Snowpark session using key-pair authentication.
    Called once per app lifecycle — reused for all queries.
    """
    from snowflake.snowpark import Session

    required = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_WAREHOUSE",
                "SNOWFLAKE_DATABASE", "SNOWFLAKE_SCHEMA"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise ValueError(f"Missing Snowflake env vars: {', '.join(missing)}")

    connection_params = {
        "account":   os.environ["SNOWFLAKE_ACCOUNT"],
        "user":      os.environ["SNOWFLAKE_USER"],
        "warehouse": os.environ["SNOWFLAKE_WAREHOUSE"],
        "database":  os.environ["SNOWFLAKE_DATABASE"],
        "schema":    os.environ["SNOWFLAKE_SCHEMA"],
        "private_key": _get_private_key(),
    }

    return Session.builder.configs(connection_params).create()


def get_connection():
    """
    Get a raw Snowflake connector connection (for SQL queries without Snowpark).
    Useful for simple queries and Cortex function calls.
    """
    import snowflake.connector
    from cryptography.hazmat.primitives.serialization import (
        Encoding, PrivateFormat, NoEncryption
    )

    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema=os.environ["SNOWFLAKE_SCHEMA"],
        private_key=_get_private_key(),
    )


def test_connection() -> dict:
    """
    Test the Snowflake connection and return environment info.
    Use this to verify setup before running assessments.
    """
    try:
        session = get_session()
        result = session.sql("SELECT CURRENT_USER(), CURRENT_WAREHOUSE(), "
                             "CURRENT_DATABASE(), CURRENT_SCHEMA(), "
                             "CURRENT_VERSION()").collect()[0]
        return {
            "status": "connected",
            "user":      result[0],
            "warehouse": result[1],
            "database":  result[2],
            "schema":    result[3],
            "version":   result[4],
            "error":     None,
        }
    except Exception as e:
        return {
            "status": "error",
            "error":  str(e),
        }
