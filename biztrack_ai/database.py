"""
Database module for BizTrack AI
Uses Supabase Python client (URL + service role key only)
"""

import os
import time

from dotenv import load_dotenv

try:
    import httpx
    _RETRYABLE_ERRORS = (
        httpx.ReadError,
        httpx.ConnectError,
        httpx.TimeoutException,
        httpx.NetworkError,
        ConnectionError,
        TimeoutError,
    )
except ImportError:
    _RETRYABLE_ERRORS = (ConnectionError, TimeoutError, OSError)

# Always load .env from project root (works with streamlit run)
_ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(_ENV_PATH)

_client = None


def _get_secret(key, default=None):
    """Prefer .env locally; fall back to Streamlit secrets on Cloud."""
    value = os.getenv(key)
    if value:
        return value

    try:
        import streamlit as st
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        if get_script_run_ctx() is not None and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass

    return default


def get_supabase_client():
    """Get Supabase Python client. Requires SUPABASE_URL + SUPABASE_KEY only."""
    global _client
    if _client is not None:
        return _client

    from supabase import create_client

    url = _get_secret("SUPABASE_URL")
    key = (
        _get_secret("SUPABASE_KEY")
        or _get_secret("SUPABASE_SERVICE_ROLE_KEY")
    )
    if not url or not key:
        raise ValueError(
            "Set SUPABASE_URL and SUPABASE_KEY in .env (local) or "
            ".streamlit/secrets.toml / Streamlit Cloud secrets."
        )
    _client = create_client(url, key)
    return _client


def db():
    """Shortcut to Supabase client."""
    return get_supabase_client()


def execute_with_retry(build_and_execute, retries=3, base_delay=0.5):
    """
    Run a Supabase query callable (lambda that calls .execute()) with retries
    on transient network errors (common on Windows under heavy request load).
    """
    last_error = None
    for attempt in range(retries):
        try:
            return build_and_execute()
        except _RETRYABLE_ERRORS as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(base_delay * (2 ** attempt))
    raise last_error


def is_unique_violation(exc):
    """Check if exception is a duplicate key error."""
    msg = str(exc).lower()
    return "23505" in msg or "duplicate" in msg or "unique" in msg


def log_activity(user_id, action, details=""):
    """Log user activity."""
    db().table("activity_logs").insert({
        "user_id": user_id,
        "action": action,
        "details": details,
    }).execute()


def get_activity_logs(limit=20):
    """Get recent activity logs as (timestamp, name, action, details) tuples."""
    response = (
        db()
        .table("activity_logs")
        .select("timestamp, action, details, users(name)")
        .order("timestamp", desc=True)
        .limit(limit)
        .execute()
    )
    logs = []
    for row in response.data or []:
        name = (row.get("users") or {}).get("name") if row.get("users") else None
        logs.append((row["timestamp"], name, row["action"], row.get("details", "")))
    return logs
