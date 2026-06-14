"""
Utility functions for Vyapar
Handles theming, formatting, and helper functions
"""

import pandas as pd
from datetime import datetime, date, time

def format_currency(amount):
    """Format number as currency"""
    if amount is None:
        return "$0.00"
    return f"${amount:,.2f}"

def format_number(num):
    """Format number with commas"""
    if num is None:
        return "0"
    return f"{num:,}"

def format_percentage(value):
    """Format as percentage"""
    if value is None:
        return "0%"
    return f"{value:.1f}%"

def format_date(date_str):
    """Format date string"""
    if date_str is None:
        return ""
    try:
        if isinstance(date_str, str):
            return datetime.fromisoformat(date_str.replace('Z', '')).strftime('%Y-%m-%d %H:%M')
        return date_str.strftime('%Y-%m-%d %H:%M')
    except:
        return str(date_str)

def get_time_ago(timestamp):
    """Get human-readable time ago"""
    if timestamp is None:
        return "Unknown"

    try:
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', ''))
        else:
            dt = timestamp

        now = datetime.now()
        diff = now - dt

        if diff.days > 365:
            return f"{diff.days // 365}y ago"
        elif diff.days > 30:
            return f"{diff.days // 30}mo ago"
        elif diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return "Just now"
    except:
        return str(timestamp)


def normalize_date_range(start_date, end_date):
    """Convert date/datetime values to ISO bounds for PostgreSQL filters."""
    def to_date(value):
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        text = str(value).strip().split("T")[0].split(" ")[0]
        return date.fromisoformat(text)

    start = to_date(start_date)
    end = to_date(end_date)
    if start > end:
        start, end = end, start

    return (
        datetime.combine(start, time.min).isoformat(),
        datetime.combine(end, time(23, 59, 59)).isoformat(),
    )

# ---------------------------------------------------------------------------
# Vyapar Design System
# ---------------------------------------------------------------------------

_COMMON_CSS = """
<style>
    :root {
        --vy-primary: #0d9488;
        --vy-primary-dark: #0f766e;
        --vy-primary-light: #14b8a6;
        --vy-accent: #f97316;
        --vy-sidebar: #0f172a;
        --vy-sidebar-text: #f1f5f9;
        --vy-sidebar-muted: #94a3b8;
        --vy-bg: #f1f5f9;
        --vy-surface: #ffffff;
        --vy-border: #e2e8f0;
        --vy-text: #0f172a;
        --vy-text-secondary: #475569;
        --vy-text-muted: #64748b;
        --vy-success: #059669;
        --vy-danger: #dc2626;
        --vy-shadow: 0 1px 3px rgba(15, 23, 42, 0.06), 0 4px 16px rgba(15, 23, 42, 0.04);
        --vy-shadow-lg: 0 8px 24px rgba(15, 23, 42, 0.08);
        --vy-radius: 12px;
        --vy-radius-lg: 16px;
    }

    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(12px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    *, *::before, *::after { box-sizing: border-box; }

    html, body, .stApp,
    .stApp [data-testid="stAppViewContainer"],
    .stApp [data-testid="stHeader"],
    .stApp header {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }

    #MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
    .stDeployButton { display: none !important; }

    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(13, 148, 136, 0.35);
        border-radius: 10px;
    }

    /* Custom HTML components — immune to Streamlit typography overrides */
    .vy-brand-name,
    .vy-brand-tag,
    .vy-brand-badge,
    .vy-banner-greeting,
    .vy-banner-name,
    .vy-banner-desc,
    .vy-section-title,
    .vy-section-sub,
    .vy-user-name,
    .vy-user-role,
    .vy-hero-title,
    .vy-hero-sub,
    .vy-hero-item-title,
    .vy-hero-item-desc,
    .vy-login-title,
    .vy-login-sub {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    .vy-brand-name { color: #ffffff !important; font-size: 22px; font-weight: 800; margin: 0; letter-spacing: -0.02em; }
    .vy-brand-tag { color: #cbd5e1 !important; margin: 6px 0 0 0; font-size: 11px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; }
    .vy-brand-badge { display: inline-block; margin-top: 12px; padding: 4px 12px; background: rgba(13, 148, 136, 0.2); border: 1px solid rgba(20, 184, 166, 0.35); border-radius: 20px; font-size: 10px; color: #5eead4 !important; font-weight: 700; }
    .vy-banner-greeting { font-size: 14px; color: rgba(255,255,255,0.85) !important; margin: 0 0 6px 0; font-weight: 500; }
    .vy-banner-name { font-size: 28px; font-weight: 800; margin: 0; color: #ffffff !important; letter-spacing: -0.03em; line-height: 1.2; }
    .vy-banner-desc { color: rgba(255,255,255,0.78) !important; margin: 8px 0 0 0; font-size: 14px; }
    .vy-section-title { margin: 0; font-size: 20px; font-weight: 700; color: var(--vy-text) !important; letter-spacing: -0.02em; }
    .vy-section-sub { color: var(--vy-text-muted) !important; margin: 6px 0 0 0; font-size: 13px; line-height: 1.5; }
    .vy-user-name { color: #ffffff !important; margin: 0; font-weight: 600; font-size: 14px; }
    .vy-user-role { display: inline-block; margin-top: 4px; padding: 2px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; }
    .vy-hero-title { font-size: 36px; font-weight: 800; margin: 0 0 8px 0; letter-spacing: -0.04em; color: #ffffff !important; line-height: 1.1; }
    .vy-hero-sub { color: rgba(255,255,255,0.82) !important; font-size: 16px; margin: 0 0 32px 0; line-height: 1.5; }
    .vy-hero-item-title { color: #ffffff !important; font-weight: 600; margin: 0; font-size: 14px; }
    .vy-hero-item-desc { color: rgba(255,255,255,0.65) !important; margin: 0; font-size: 12px; }
    .vy-login-title { margin: 0; font-size: 22px; color: var(--vy-text) !important; font-weight: 800; }
    .vy-login-sub { margin: 6px 0 0 0; font-size: 14px; color: var(--vy-text-muted) !important; }

    @media screen and (max-width: 1024px) {
        .main .block-container { padding-left: 16px !important; padding-right: 16px !important; max-width: 100% !important; }
        .main [data-testid="metric-container"] [data-testid="stMetricValue"] { font-size: 22px !important; }
    }
    @media screen and (max-width: 768px) {
        .main .block-container { padding-left: 12px !important; padding-right: 12px !important; padding-top: 16px !important; }
        [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex: 1 1 100% !important; min-width: 100% !important; }
        .main [data-testid="metric-container"] { padding: 14px 12px; }
        .main [data-testid="metric-container"] [data-testid="stMetricValue"] { font-size: 18px !important; }
        .stButton > button { padding: 12px 20px !important; min-height: 44px; }
        section[data-testid="stSidebar"] { min-width: 260px !important; max-width: 280px !important; }
    }

    /* ===== Sidebar — dark cohesive nav ===== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0f1a 0%, #0f172a 50%, #111827 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
    }
    section[data-testid="stSidebar"] > div:first-child,
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"],
    section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"],
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div,
    section[data-testid="stSidebar"] .element-container,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    section[data-testid="stSidebar"] [data-testid="stElementContainer"],
    section[data-testid="stSidebar"] div[class*="st-emotion-cache"] {
        background: transparent !important;
        background-color: transparent !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }
    section[data-testid="stSidebar"] nav,
    section[data-testid="stSidebar"] .nav {
        background: transparent !important;
        padding: 6px 0 !important;
        width: 100% !important;
    }
    section[data-testid="stSidebar"] .nav-link {
        font-size: 14px !important;
        font-weight: 500 !important;
        color: #f1f5f9 !important;
        -webkit-text-fill-color: #f1f5f9 !important;
        padding: 11px 16px !important;
        margin: 2px 10px !important;
        border-radius: 10px !important;
        display: flex !important;
        align-items: center !important;
        gap: 12px !important;
        transition: all 0.2s ease !important;
        text-decoration: none !important;
        border: 1px solid transparent !important;
        background-color: transparent !important;
        opacity: 1 !important;
    }
    section[data-testid="stSidebar"] .nav-link i {
        color: #cbd5e1 !important;
        font-size: 17px !important;
        width: 20px !important;
        text-align: center !important;
    }
    section[data-testid="stSidebar"] .nav-link:hover {
        background: rgba(255, 255, 255, 0.08) !important;
        color: #ffffff !important;
        border-color: rgba(255, 255, 255, 0.06) !important;
    }
    section[data-testid="stSidebar"] .nav-link:hover i { color: #5eead4 !important; }
    section[data-testid="stSidebar"] .nav-link-selected {
        background: linear-gradient(135deg, #0f766e 0%, #0d9488 55%, #14b8a6 100%) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 16px rgba(13, 148, 136, 0.35) !important;
        border-color: rgba(255, 255, 255, 0.12) !important;
    }
    section[data-testid="stSidebar"] .nav-link-selected i { color: #ffffff !important; }
    section[data-testid="stSidebar"] hr {
        border: none !important;
        height: 1px !important;
        background: rgba(255, 255, 255, 0.08) !important;
        margin: 12px 16px !important;
    }
    section[data-testid="stSidebar"] .stButton > button {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #fca5a5 !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        box-shadow: none !important;
        margin: 0 10px !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(239, 68, 68, 0.12) !important;
        border-color: rgba(239, 68, 68, 0.25) !important;
        color: #fecaca !important;
    }
</style>
"""

LIGHT_THEME = _COMMON_CSS + """
<style>
    .stApp { background: var(--vy-bg) !important; }

    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p { color: var(--vy-sidebar-text) !important; }

    .main .block-container {
        animation: fadeInUp .35s ease-out;
        max-width: 1280px;
        padding-top: 24px !important;
    }
    .main .block-container h1 { color: var(--vy-text) !important; font-weight: 800 !important; font-size: 1.75rem !important; letter-spacing: -0.03em !important; }
    .main .block-container h2 { color: var(--vy-text) !important; font-weight: 700 !important; letter-spacing: -0.02em !important; }
    .main .block-container h3 { color: var(--vy-text-secondary) !important; font-weight: 600 !important; }
    .main .block-container p,
    .main .block-container label,
    .main .block-container .stMarkdown { color: var(--vy-text-secondary) !important; line-height: 1.6; }

    .main [data-testid="metric-container"] {
        background: var(--vy-surface);
        border: 1px solid var(--vy-border);
        border-radius: var(--vy-radius-lg);
        padding: 20px 18px;
        box-shadow: var(--vy-shadow);
        transition: transform .2s ease, box-shadow .2s ease;
        animation: fadeInUp .4s ease-out both;
    }
    .main [data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: var(--vy-shadow-lg);
        border-color: rgba(13, 148, 136, 0.25);
    }
    .main [data-testid="metric-container"] label,
    .main [data-testid="metric-container"] [data-testid="stMetricLabel"] p {
        font-size: 11px !important;
        font-weight: 700 !important;
        color: var(--vy-text-muted) !important;
        text-transform: uppercase;
        letter-spacing: 0.06em !important;
    }
    .main [data-testid="metric-container"] [data-testid="stMetricValue"],
    .main [data-testid="metric-container"] [data-testid="stMetricValue"] div,
    .main [data-testid="metric-container"] [data-testid="stMetricValue"] p {
        font-size: 24px !important;
        font-weight: 800 !important;
        color: var(--vy-text) !important;
    }
    .main [data-testid="metric-container"] [data-testid="stMetricDelta"] { font-weight: 700 !important; }

    .main .stButton > button {
        background: var(--vy-primary) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: var(--vy-radius) !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        padding: 10px 24px !important;
        box-shadow: 0 2px 8px rgba(13, 148, 136, 0.25);
        transition: all .2s ease !important;
    }
    .main .stButton > button:hover {
        background: var(--vy-primary-dark) !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 14px rgba(13, 148, 136, 0.35) !important;
    }
    .main .stButton > button[kind="primary"],
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: var(--vy-primary) !important;
    }

    .main .stTextInput > div > div > input,
    .main .stNumberInput > div > div > input,
    .main .stTextArea > div > div > textarea,
    .main .stDateInput > div > div > input {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 12px 14px !important;
        font-size: 14px !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
    }

    /* ===== Unified form controls ===== */
    .stApp .main .stTextInput [data-testid="stWidgetLabel"],
    .stApp .main .stTextInput [data-testid="stWidgetLabel"] p,
    .stApp .main .stTextInput [data-testid="stWidgetLabel"] span,
    .stApp .main .stTextInput label,
    .stApp .main .stTextInput label p,
    .stApp .main .stNumberInput [data-testid="stWidgetLabel"],
    .stApp .main .stNumberInput [data-testid="stWidgetLabel"] p,
    .stApp .main .stNumberInput label,
    .stApp .main .stSelectbox [data-testid="stWidgetLabel"],
    .stApp .main .stSelectbox [data-testid="stWidgetLabel"] p,
    .stApp .main .stSelectbox label,
    .stApp .main .stTextArea [data-testid="stWidgetLabel"],
    .stApp .main .stTextArea [data-testid="stWidgetLabel"] p,
    .stApp .main .stTextArea label,
    .stApp .main .stDateInput [data-testid="stWidgetLabel"],
    .stApp .main .stDateInput [data-testid="stWidgetLabel"] p,
    .stApp .main .stDateInput label {
        color: #334155 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
    }
    .stApp .main div[data-baseweb="input"],
    .stApp .main div[data-baseweb="textarea"],
    .stApp .main .stNumberInput div[data-baseweb="input"] {
        background-color: #f8fafc !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 12px !important;
        min-height: 44px !important;
    }
    .stApp .main div[data-baseweb="input"]:focus-within,
    .stApp .main div[data-baseweb="textarea"]:focus-within,
    .stApp .main .stNumberInput div[data-baseweb="input"]:focus-within {
        border-color: #0d9488 !important;
        box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.15) !important;
        background-color: #ffffff !important;
    }
    .stApp .main div[data-baseweb="input"] input::placeholder,
    .stApp .main div[data-baseweb="textarea"] textarea::placeholder {
        color: #94a3b8 !important;
        opacity: 1 !important;
        -webkit-text-fill-color: #94a3b8 !important;
    }
    .stApp .main .stSelectbox [data-baseweb="select"] > div {
        background-color: #f8fafc !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 12px !important;
        min-height: 44px !important;
        color: #0f172a !important;
    }
    .stApp .main .stSelectbox [data-baseweb="select"] span { color: #0f172a !important; }
    .stApp .main .stSelectbox [data-baseweb="select"] > div:focus-within {
        border-color: #0d9488 !important;
        box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.15) !important;
        background-color: #ffffff !important;
    }
    .stApp .main .stNumberInput button {
        color: #0d9488 !important;
        background: transparent !important;
        border: none !important;
        border-left: 1px solid #e2e8f0 !important;
    }
    .stApp .main .stNumberInput button:hover {
        background: rgba(13, 148, 136, 0.08) !important;
    }
    .stApp .main [data-testid="stFormSubmitButton"] button,
    .stApp .main [data-testid="stFormSubmitButton"] > button,
    .stApp .main .stFormSubmitButton button,
    .stApp .main button[data-testid="stBaseButton-primary"],
    .stApp .main .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0f766e, #0d9488, #14b8a6) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 10px rgba(13, 148, 136, 0.3) !important;
    }
    .stApp .main .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: #e2e8f0 !important;
        border-radius: 14px !important;
        padding: 5px !important;
        border: none !important;
    }
    .stApp .main .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important;
        padding: 10px 22px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        color: #64748b !important;
        background: transparent !important;
        border: none !important;
    }
    .stApp .main .stTabs [data-baseweb="tab"]:hover {
        color: #0f766e !important;
        background: rgba(255, 255, 255, 0.65) !important;
    }
    .stApp .main .stTabs [aria-selected="true"] {
        background: #ffffff !important;
        color: #0f766e !important;
        box-shadow: 0 1px 4px rgba(15, 23, 42, 0.08) !important;
    }
    .stApp .main .stTabs [data-baseweb="tab-highlight"],
    .stApp .main .stTabs [data-baseweb="tab-border"] { display: none !important; }

    .main .stDataFrame {
        border-radius: var(--vy-radius-lg) !important;
        overflow: hidden;
        border: 1px solid var(--vy-border) !important;
        box-shadow: var(--vy-shadow);
    }
    .main .stAlert { border-radius: var(--vy-radius) !important; border-left-width: 4px !important; }
    .main hr {
        border: none !important;
        height: 1px !important;
        background: var(--vy-border) !important;
        margin: 28px 0 !important;
    }
    .main [data-testid="stForm"] {
        background: var(--vy-surface);
        border: 1px solid var(--vy-border);
        border-radius: var(--vy-radius-lg);
        padding: 28px !important;
        box-shadow: var(--vy-shadow);
    }
    .main .stDownloadButton > button {
        background: var(--vy-surface) !important;
        color: var(--vy-primary-dark) !important;
        border: 1.5px solid var(--vy-border) !important;
        border-radius: var(--vy-radius) !important;
        font-weight: 600 !important;
        box-shadow: none !important;
    }
    .main .stDownloadButton > button:hover {
        border-color: var(--vy-primary) !important;
        background: rgba(13, 148, 136, 0.06) !important;
    }
</style>
"""

DARK_THEME = _COMMON_CSS + """
<style>
    :root {
        --vy-bg: #0b1120;
        --vy-surface: #111827;
        --vy-border: #1f2937;
        --vy-text: #f8fafc;
        --vy-text-secondary: #cbd5e1;
        --vy-text-muted: #94a3b8;
        --vy-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
    }

    .stApp { background: var(--vy-bg) !important; color: var(--vy-text); }

    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p { color: var(--vy-sidebar-text) !important; }

    .main .block-container { animation: fadeInUp .35s ease-out; max-width: 1280px; }
    .main .block-container h1, .main .block-container h2 { color: var(--vy-text) !important; font-weight: 800 !important; }
    .main .block-container h3 { color: var(--vy-text-secondary) !important; }
    .main .block-container p, .main .block-container label, .main .block-container .stMarkdown { color: var(--vy-text-secondary) !important; }

    .main [data-testid="metric-container"] {
        background: var(--vy-surface);
        border: 1px solid var(--vy-border);
        border-radius: var(--vy-radius-lg);
        padding: 20px 18px;
        box-shadow: var(--vy-shadow);
    }
    .main [data-testid="metric-container"] label,
    .main [data-testid="metric-container"] [data-testid="stMetricLabel"] p {
        color: var(--vy-text-muted) !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase;
    }
    .main [data-testid="metric-container"] [data-testid="stMetricValue"],
    .main [data-testid="metric-container"] [data-testid="stMetricValue"] div,
    .main [data-testid="metric-container"] [data-testid="stMetricValue"] p {
        color: #ffffff !important;
        font-size: 24px !important;
        font-weight: 800 !important;
    }

    .main .stButton > button {
        background: var(--vy-primary) !important;
        color: white !important;
        border-radius: var(--vy-radius) !important;
        font-weight: 600 !important;
        border: none !important;
    }

    /* ===== Unified form controls (dark) ===== */
    .stApp .main .stTextInput [data-testid="stWidgetLabel"],
    .stApp .main .stTextInput [data-testid="stWidgetLabel"] p,
    .stApp .main .stNumberInput [data-testid="stWidgetLabel"],
    .stApp .main .stNumberInput [data-testid="stWidgetLabel"] p,
    .stApp .main .stSelectbox [data-testid="stWidgetLabel"],
    .stApp .main .stSelectbox [data-testid="stWidgetLabel"] p,
    .stApp .main .stTextArea [data-testid="stWidgetLabel"],
    .stApp .main .stTextArea [data-testid="stWidgetLabel"] p,
    .stApp .main .stDateInput [data-testid="stWidgetLabel"],
    .stApp .main .stDateInput [data-testid="stWidgetLabel"] p,
    .stApp .main .stTextInput label,
    .stApp .main .stNumberInput label,
    .stApp .main .stSelectbox label,
    .stApp .main .stTextArea label,
    .stApp .main .stDateInput label {
        color: #e2e8f0 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
    }
    .stApp .main div[data-baseweb="input"],
    .stApp .main div[data-baseweb="textarea"],
    .stApp .main .stNumberInput div[data-baseweb="input"] {
        background-color: #0f172a !important;
        border: 1.5px solid #334155 !important;
        border-radius: 12px !important;
        min-height: 44px !important;
    }
    .stApp .main div[data-baseweb="input"]:focus-within,
    .stApp .main div[data-baseweb="textarea"]:focus-within,
    .stApp .main .stNumberInput div[data-baseweb="input"]:focus-within {
        border-color: #14b8a6 !important;
        box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.2) !important;
    }
    .stApp .main div[data-baseweb="input"] input,
    .stApp .main div[data-baseweb="textarea"] textarea,
    .stApp .main .stTextInput > div > div > input,
    .stApp .main .stNumberInput > div > div > input,
    .stApp .main .stTextArea > div > div > textarea,
    .stApp .main .stDateInput > div > div > input {
        background-color: transparent !important;
        color: #f8fafc !important;
        border: none !important;
        box-shadow: none !important;
        -webkit-text-fill-color: #f8fafc !important;
    }
    .stApp .main .stSelectbox [data-baseweb="select"] > div {
        background-color: #0f172a !important;
        border: 1.5px solid #334155 !important;
        border-radius: 12px !important;
        color: #f8fafc !important;
    }
    .stApp .main .stSelectbox [data-baseweb="select"] span { color: #f8fafc !important; }
    .stApp .main .stNumberInput button {
        color: #5eead4 !important;
        background: transparent !important;
        border-left: 1px solid #334155 !important;
    }
    .stApp .main [data-testid="stFormSubmitButton"] button,
    .stApp .main button[data-testid="stBaseButton-primary"],
    .stApp .main .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0f766e, #0d9488, #14b8a6) !important;
        color: #ffffff !important;
        border: none !important;
    }
    .stApp .main .stTabs [data-baseweb="tab-list"] { background: #1e293b !important; border-radius: 14px; padding: 5px; }
    .stApp .main .stTabs [data-baseweb="tab"] { color: #94a3b8 !important; }
    .stApp .main .stTabs [aria-selected="true"] {
        background: #111827 !important;
        color: #5eead4 !important;
        box-shadow: var(--vy-shadow);
    }
    .stApp .main .stTabs [data-baseweb="tab-highlight"],
    .stApp .main .stTabs [data-baseweb="tab-border"] { display: none !important; }

    .main [data-testid="stForm"] {
        background: var(--vy-surface);
        border: 1px solid var(--vy-border);
        border-radius: var(--vy-radius-lg);
        padding: 28px !important;
    }
    .main hr { border: none !important; height: 1px !important; background: var(--vy-border) !important; margin: 28px 0 !important; }
    .vy-section-title { color: var(--vy-text) !important; }
    .vy-section-sub { color: var(--vy-text-muted) !important; }
</style>
"""

def apply_theme(is_dark=False):
    """Apply theme styling"""
    return DARK_THEME if is_dark else LIGHT_THEME


def get_form_controls_patch(is_dark=False):
    """Late-load patch so form styles override Streamlit's built-in theme."""
    if is_dark:
        field_bg, field_border, field_text, label_color = "#0f172a", "#334155", "#f8fafc", "#e2e8f0"
    else:
        field_bg, field_border, field_text, label_color = "#f8fafc", "#cbd5e1", "#0f172a", "#334155"

    return f"""
<style>
    .stApp div[data-baseweb="input"],
    .stApp div[data-baseweb="textarea"],
    .stApp .stNumberInput div[data-baseweb="input"] {{
        background-color: {field_bg} !important;
        border: 1.5px solid {field_border} !important;
        border-radius: 12px !important;
        min-height: 44px !important;
    }}
    .stApp div[data-baseweb="input"]:focus-within,
    .stApp div[data-baseweb="textarea"]:focus-within,
    .stApp .stNumberInput div[data-baseweb="input"]:focus-within {{
        border-color: #0d9488 !important;
        box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.15) !important;
        background-color: {"#111827" if is_dark else "#ffffff"} !important;
    }}
    .stApp div[data-baseweb="input"] input,
    .stApp div[data-baseweb="textarea"] textarea,
    .stApp .stTextInput input,
    .stApp .stNumberInput input,
    .stApp .stTextArea textarea {{
        background: transparent !important;
        color: {field_text} !important;
        border: none !important;
        box-shadow: none !important;
        -webkit-text-fill-color: {field_text} !important;
    }}
    .stApp .stSelectbox [data-baseweb="select"] > div {{
        background-color: {field_bg} !important;
        border: 1.5px solid {field_border} !important;
        border-radius: 12px !important;
        min-height: 44px !important;
    }}
    .stApp .stSelectbox [data-baseweb="select"] span {{ color: {field_text} !important; }}
    .stApp [data-testid="stWidgetLabel"],
    .stApp [data-testid="stWidgetLabel"] p,
    .stApp [data-testid="stWidgetLabel"] span,
    .stApp .stTextInput label,
    .stApp .stNumberInput label,
    .stApp .stSelectbox label,
    .stApp .stTextArea label,
    .stApp .stDateInput label {{
        color: {label_color} !important;
        font-weight: 600 !important;
    }}
    .stApp [data-testid="stFormSubmitButton"] button,
    .stApp button[data-testid="stBaseButton-primary"],
    .stApp .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #0f766e, #0d9488, #14b8a6) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
    }}
    .stApp .stTabs [data-baseweb="tab-highlight"],
    .stApp .stTabs [data-baseweb="tab-border"] {{ display: none !important; }}
    .stApp .stTabs [aria-selected="true"] {{
        color: {"#5eead4" if is_dark else "#0f766e"} !important;
    }}
    .stApp .stNumberInput button {{
        color: {"#5eead4" if is_dark else "#0d9488"} !important;
        background: transparent !important;
        border-left: 1px solid {field_border} !important;
    }}
</style>
"""


def get_sidebar_patch_css():
    """Sidebar colors — loaded last so they win over Streamlit Cloud light theme."""
    return """
<style>
    /* Dark sidebar shell (section + wrappers — not just transparent) */
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div:first-child,
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        background: linear-gradient(180deg, #0a0f1a 0%, #0f172a 50%, #111827 100%) !important;
        background-color: #0f172a !important;
        color: #f1f5f9 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
    }

    /* Inner panels transparent so dark shell shows through */
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"],
    section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"],
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div,
    section[data-testid="stSidebar"] [data-testid="stSidebarHeader"],
    section[data-testid="stSidebar"] .element-container,
    section[data-testid="stSidebar"] [data-testid="stElementContainer"],
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    section[data-testid="stSidebar"] div[class*="st-emotion-cache"]:not(.nav-link):not(.nav-link-selected) {
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
    }

    /* Stop main-app light textColor from bleeding into sidebar */
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] a {
        color: inherit;
    }

    /* Brand header */
    section[data-testid="stSidebar"] .vy-brand-name {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    section[data-testid="stSidebar"] .vy-brand-tag {
        color: #cbd5e1 !important;
        -webkit-text-fill-color: #cbd5e1 !important;
    }

    /* Nav menu — high contrast on dark bg */
    section[data-testid="stSidebar"] nav,
    section[data-testid="stSidebar"] .nav {
        background: transparent !important;
    }
    section[data-testid="stSidebar"] .nav-link {
        color: #f1f5f9 !important;
        -webkit-text-fill-color: #f1f5f9 !important;
        background-color: transparent !important;
        opacity: 1 !important;
    }
    section[data-testid="stSidebar"] .nav-link span {
        color: #f1f5f9 !important;
        -webkit-text-fill-color: #f1f5f9 !important;
    }
    section[data-testid="stSidebar"] .nav-link i {
        color: #cbd5e1 !important;
    }
    section[data-testid="stSidebar"] .nav-link:hover,
    section[data-testid="stSidebar"] .nav-link:hover span {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        background: rgba(255, 255, 255, 0.1) !important;
    }
    section[data-testid="stSidebar"] .nav-link:hover i {
        color: #5eead4 !important;
    }
    section[data-testid="stSidebar"] .nav-link-selected,
    section[data-testid="stSidebar"] .nav-link-selected span {
        background: linear-gradient(135deg, #0f766e 0%, #0d9488 55%, #14b8a6 100%) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        opacity: 1 !important;
    }
    section[data-testid="stSidebar"] .nav-link-selected i {
        color: #ffffff !important;
    }

    /* User card */
    section[data-testid="stSidebar"] .vy-user-name {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    section[data-testid="stSidebar"] .vy-user-role {
        opacity: 1 !important;
    }

    /* Logout button */
    section[data-testid="stSidebar"] .stButton > button {
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.14) !important;
        color: #fca5a5 !important;
        -webkit-text-fill-color: #fca5a5 !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(239, 68, 68, 0.15) !important;
        border-color: rgba(239, 68, 68, 0.3) !important;
        color: #fecaca !important;
        -webkit-text-fill-color: #fecaca !important;
    }
</style>
"""


def get_sidebar_navigation():
    """Get sidebar navigation header with branding"""
    return """
<div style="
    padding: 22px 16px 18px;
    text-align: center;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 4px;
">
    <div style="
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 48px; height: 48px;
        background: linear-gradient(135deg, #0d9488 0%, #14b8a6 100%);
        border-radius: 14px;
        margin-bottom: 12px;
        box-shadow: 0 4px 16px rgba(13, 148, 136, 0.4);
        font-size: 24px;
        font-weight: 800;
        color: white;
    ">V</div>
    <div class="vy-brand-name">Vyapar</div>
    <div class="vy-brand-tag">Business Management</div>
</div>
"""

def get_login_hero_html():
    """Get the hero section HTML for the login page"""
    html = """
<div style="
    background: linear-gradient(145deg, #0f172a 0%, #134e4a 55%, #0d9488 100%);
    border-radius: 20px;
    padding: 44px 36px;
    position: relative;
    overflow: hidden;
    min-height: 480px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    box-shadow: 0 12px 40px rgba(15, 23, 42, 0.18);
">
    <div style="
        position: absolute; top: -40px; right: -40px;
        width: 160px; height: 160px;
        background: rgba(255,255,255,0.06);
        border-radius: 50%;
    "></div>
    <div style="
        position: absolute; bottom: -60px; left: -30px;
        width: 200px; height: 200px;
        background: rgba(255,255,255,0.04);
        border-radius: 50%;
    "></div>
    <div style="position: relative; z-index: 1;">
        <div style="
            display: inline-flex; align-items: center; justify-content: center;
            width: 64px; height: 64px;
            background: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.18);
            border-radius: 18px;
            margin-bottom: 24px;
            font-size: 32px;
            font-weight: 800;
            color: white;
        ">V</div>
        <div class="vy-hero-title">Vyapar</div>
        <div class="vy-hero-sub">Smart inventory, sales &amp; bookkeeping<br>for growing businesses</div>
        <div style="display: flex; flex-direction: column; gap: 16px;">
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="
                    width: 40px; height: 40px;
                    background: rgba(255,255,255,0.1);
                    border-radius: 12px;
                    display: flex; align-items: center; justify-content: center;
                    font-size: 18px; flex-shrink: 0;
                ">📦</div>
                <div>
                    <div class="vy-hero-item-title">Inventory Management</div>
                    <div class="vy-hero-item-desc">Track stock and reorder alerts</div>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="
                    width: 40px; height: 40px;
                    background: rgba(255,255,255,0.1);
                    border-radius: 12px;
                    display: flex; align-items: center; justify-content: center;
                    font-size: 18px; flex-shrink: 0;
                ">💳</div>
                <div>
                    <div class="vy-hero-item-title">Sales &amp; Expenses</div>
                    <div class="vy-hero-item-desc">Real-time revenue insights</div>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="
                    width: 40px; height: 40px;
                    background: rgba(255,255,255,0.1);
                    border-radius: 12px;
                    display: flex; align-items: center; justify-content: center;
                    font-size: 18px; flex-shrink: 0;
                ">📊</div>
                <div>
                    <div class="vy-hero-item-title">Reports &amp; Forecasting</div>
                    <div class="vy-hero-item-desc">Export data and plan ahead</div>
                </div>
            </div>
        </div>
    </div>
</div>
"""
    return "\n".join(line.strip() for line in html.split("\n"))


def get_login_page_css():
    """Login-page-only CSS — fixes Streamlit default dark inputs and red accents."""
    return """
<style>
    section[data-testid="stSidebar"] { display: none !important; }
    .main .block-container {
        max-width: 1080px !important;
        padding-top: 32px !important;
    }

    /* Form column card */
    .main [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(3) {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 28px 28px 24px 28px !important;
        box-shadow: 0 12px 40px rgba(15, 23, 42, 0.08);
        position: relative;
        overflow: hidden;
    }
    .main [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(3)::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 4px;
        background: linear-gradient(90deg, #0f766e, #0d9488, #14b8a6);
    }

    /* Tabs */
    .main [data-testid="column"]:nth-child(3) .stTabs [data-baseweb="tab-list"] {
        background: #f1f5f9 !important;
        border-radius: 12px !important;
        padding: 5px !important;
        gap: 4px !important;
        border: 1px solid #e2e8f0 !important;
        margin-bottom: 8px;
    }
    .main [data-testid="column"]:nth-child(3) .stTabs [data-baseweb="tab"] {
        border-radius: 9px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        color: #64748b !important;
        background: transparent !important;
        border: none !important;
    }
    .main [data-testid="column"]:nth-child(3) .stTabs [data-baseweb="tab"]:hover {
        color: #0f766e !important;
        background: rgba(255,255,255,0.7) !important;
    }
    .main [data-testid="column"]:nth-child(3) .stTabs [aria-selected="true"] {
        background: #ffffff !important;
        color: #0f766e !important;
        font-weight: 700 !important;
        box-shadow: 0 1px 4px rgba(15, 23, 42, 0.08) !important;
    }
    .main [data-testid="column"]:nth-child(3) .stTabs [data-baseweb="tab-highlight"],
    .main [data-testid="column"]:nth-child(3) .stTabs [data-baseweb="tab-border"] {
        display: none !important;
    }

    /* Labels */
    .main [data-testid="column"]:nth-child(3) .stTextInput label,
    .main [data-testid="column"]:nth-child(3) .stSelectbox label,
    .main [data-testid="column"]:nth-child(3) .stTextInput label p,
    .main [data-testid="column"]:nth-child(3) .stSelectbox label p,
    .main [data-testid="column"]:nth-child(3) .stTextInput label span,
    .main [data-testid="column"]:nth-child(3) .stSelectbox label span {
        color: #334155 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
    }

    /* Text inputs — override Streamlit dark theme */
    .main [data-testid="column"]:nth-child(3) .stTextInput > div > div > input,
    .main [data-testid="column"]:nth-child(3) .stTextInput div[data-baseweb="input"] > input,
    .main [data-testid="column"]:nth-child(3) .stTextInput div[data-baseweb="input"] {
        background-color: #f8fafc !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 12px !important;
        color: #0f172a !important;
        font-size: 14px !important;
        padding: 12px 14px !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    .main [data-testid="column"]:nth-child(3) .stTextInput > div > div > input:focus,
    .main [data-testid="column"]:nth-child(3) .stTextInput div[data-baseweb="input"]:focus-within {
        border-color: #0d9488 !important;
        box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.15) !important;
        background-color: #ffffff !important;
        outline: none !important;
    }
    .main [data-testid="column"]:nth-child(3) .stTextInput input::placeholder {
        color: #94a3b8 !important;
        opacity: 1 !important;
    }

    /* Selectbox */
    .main [data-testid="column"]:nth-child(3) .stSelectbox [data-baseweb="select"] > div {
        background-color: #f8fafc !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 12px !important;
        color: #0f172a !important;
        min-height: 46px !important;
    }
    .main [data-testid="column"]:nth-child(3) .stSelectbox [data-baseweb="select"] span {
        color: #0f172a !important;
    }
    .main [data-testid="column"]:nth-child(3) .stSelectbox [data-baseweb="select"] > div:focus-within {
        border-color: #0d9488 !important;
        box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.15) !important;
    }

    /* Form container */
    .main [data-testid="column"]:nth-child(3) [data-testid="stForm"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 8px 0 0 0 !important;
    }

    /* Submit buttons — teal not red */
    .main [data-testid="column"]:nth-child(3) [data-testid="stFormSubmitButton"] button,
    .main [data-testid="column"]:nth-child(3) [data-testid="stFormSubmitButton"] > button,
    .main [data-testid="column"]:nth-child(3) .stFormSubmitButton button {
        background: linear-gradient(135deg, #0f766e 0%, #0d9488 50%, #14b8a6 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        padding: 12px 24px !important;
        min-height: 48px !important;
        box-shadow: 0 4px 14px rgba(13, 148, 136, 0.35) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    }
    .main [data-testid="column"]:nth-child(3) [data-testid="stFormSubmitButton"] button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(13, 148, 136, 0.4) !important;
    }

    /* Spacing between fields */
    .main [data-testid="column"]:nth-child(3) .stTextInput,
    .main [data-testid="column"]:nth-child(3) .stSelectbox {
        margin-bottom: 4px;
    }
</style>
"""


def get_login_card_header():
    """Header block for the login form card."""
    return """
<div style="text-align: center; padding: 8px 0 20px 0;">
    <div style="
        display: inline-flex; align-items: center; justify-content: center;
        width: 48px; height: 48px;
        background: linear-gradient(135deg, #0f766e, #14b8a6);
        border-radius: 14px;
        margin-bottom: 16px;
        box-shadow: 0 4px 14px rgba(13, 148, 136, 0.3);
        font-size: 22px; font-weight: 800; color: white;
    ">V</div>
    <div class="vy-login-title">Welcome back</div>
    <div class="vy-login-sub">Sign in to manage your business on Vyapar</div>
</div>
"""


def get_login_demo_hint():
    """Demo credentials helper shown below login form."""
    return """
<div style="
    margin-top: 20px;
    padding: 14px 16px;
    background: #f0fdfa;
    border: 1px solid #99f6e4;
    border-radius: 12px;
    text-align: center;
">
    <p style="margin: 0 0 6px 0; font-size: 11px; font-weight: 700; color: #0f766e !important;
        text-transform: uppercase; letter-spacing: 0.06em;">Demo account</p>
    <p style="margin: 0; font-size: 13px; color: #334155 !important; line-height: 1.5;">
        <strong>owner@biztrack.ai</strong> &nbsp;·&nbsp; password: <strong>demo123</strong>
    </p>
</div>
"""


def get_welcome_banner(user_name):
    """Get a styled welcome banner for the dashboard"""
    from datetime import datetime
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good Morning"
        icon = "☀️"
    elif hour < 17:
        greeting = "Good Afternoon"
        icon = "🌤️"
    else:
        greeting = "Good Evening"
        icon = "🌙"

    return f"""
<div style="
    background: linear-gradient(135deg, #0f766e 0%, #0d9488 50%, #14b8a6 100%);
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 8px 24px rgba(13, 148, 136, 0.2);
">
    <div style="
        position: absolute; top: -30px; right: -20px;
        width: 120px; height: 120px;
        background: rgba(255,255,255,0.08);
        border-radius: 50%;
    "></div>
    <div class="vy-banner-greeting">{icon} {greeting}</div>
    <div class="vy-banner-name">{user_name}</div>
    <div class="vy-banner-desc">Here's your business overview for today.</div>
</div>
"""

def get_section_header(icon, title, subtitle=""):
    """Get a styled section header"""
    sub_html = f'<div class="vy-section-sub">{subtitle}</div>' if subtitle else ""
    return f"""
<div style="margin-bottom: 20px;">
    <div class="vy-section-title"><span style="margin-right: 8px;">{icon}</span>{title}</div>
    {sub_html}
</div>
"""

def get_user_card(name, role):
    """Get styled user card for sidebar"""
    role_color = "#6ee7b7" if role == "owner" else "#5eead4"
    role_bg = "rgba(52, 211, 153, 0.2)" if role == "owner" else "rgba(94, 234, 212, 0.15)"
    return f"""
<div style="
    padding: 14px 16px;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 12px;
    margin: 8px 10px 0 10px;
">
    <div style="display: flex; align-items: center; gap: 12px;">
        <div style="
            width: 38px; height: 38px;
            background: linear-gradient(135deg, #0d9488, #14b8a6);
            border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
            font-size: 16px; font-weight: 700; color: white;
            flex-shrink: 0;
        ">{name[0].upper()}</div>
        <div>
            <div class="vy-user-name">{name}</div>
            <span class="vy-user-role" style="background: {role_bg}; color: {role_color} !important; border: 1px solid rgba(255,255,255,0.12);">{role.title()}</span>
        </div>
    </div>
</div>
"""

def get_chart_colors():
    """Get chart color palette"""
    return {
        'primary': '#0d9488',
        'secondary': '#14b8a6',
        'success': '#059669',
        'danger': '#dc2626',
        'warning': '#d97706',
        'info': '#0284c7',
        'sequence': ['#0d9488', '#14b8a6', '#2dd4bf', '#5eead4', '#99f6e4',
                      '#059669', '#10b981', '#34d399'],
        'revenue_color': '#059669',
        'expense_color': '#dc2626',
        'bar_colorscale': 'Teal',
        'pie_colors': ['#0d9488', '#14b8a6', '#2dd4bf', '#059669', '#10b981',
                        '#0284c7', '#0369a1', '#d97706', '#ea580c', '#7c3aed'],
    }
