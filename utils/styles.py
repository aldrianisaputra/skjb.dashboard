import streamlit as st


def inject_main_css():
    """Terapkan CSS utama aplikasi Streamlit."""
    st.markdown(r"""
<style>
/* ==========================================================================
   01. FONT & IMPORT
   ========================================================================== */
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,400,0,0&display=swap');
/* ==========================================================================
   02. GLOBAL: TYPOGRAPHY & BACKGROUND
   ========================================================================== */
html, body, [class*="css"] {
        font-family: "Poppins", sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at top left, rgba(59, 130, 246, 0.20), transparent 30%),
        radial-gradient(circle at top right, rgba(20, 184, 166, 0.18), transparent 28%),
        linear-gradient(135deg, #020617 0%, #0f172a 45%, #111827 100%);
    color: #e5e7eb;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

header[data-testid="stHeader"] {
    background: transparent !important;
    height: 3.2rem !important;
}

.block-container {
    padding-top: 1.0rem !important;
    padding-bottom: 1.5rem !important;
    max-width: 1450px;
}

/* ==========================================================================
   03. SIDEBAR: LAYOUT & BRAND
   ========================================================================== */
section[data-testid="stSidebar"] {
    width: 292px !important;
    min-width: 292px !important;
    max-width: 292px !important;
    background: linear-gradient(180deg, #0B1120 0%, #0d1424 50%, #080d19 100%);
    border-right: 1px solid rgba(148, 163, 184, 0.14);
    box-shadow: 18px 0 48px rgba(2, 6, 23, 0.22);
}

section[data-testid="stSidebar"] * {
    color: #e5e7eb;
}

section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    padding: 0px 17px 20px 17px !important;
}

section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] > div[data-testid="stVerticalBlock"] {
    min-height: calc(100vh - 44px);
}

section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:has(.account-divider) {
    margin-top: auto;
}

.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 5px 5px 22px 5px;
    margin-bottom: 2px;
}

.sidebar-brand-icon {
    width: 48px;
    height: 48px;
    border-radius: 15px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
    box-shadow: 0 12px 30px rgba(79, 70, 229, 0.32);
    border: 1px solid rgba(255,255,255,0.16);
}

.sidebar-brand-icon .material-symbols-rounded {
    font-size: 26px;
    color: #ffffff;
}

.sidebar-brand-title {
    font-size: 21px;
    font-weight: 800;
    color: #f8fafc;
    letter-spacing: -0.04em;
    line-height: 1.1;
}

.sidebar-brand-subtitle {
    font-size: 12px;
    font-weight: 600;
    color: rgba(203, 213, 225, 0.70);
    margin-top: 4px;
    letter-spacing: 0.02em;
}

.sidebar-divider {
    height: 1px;
    width: 100%;
    background: linear-gradient(
        90deg,
        rgba(148, 163, 184, 0),
        rgba(148, 163, 184, 0.28),
        rgba(148, 163, 184, 0)
    );
    margin: 2px 0 18px 0;
}

/* ==========================================================================
   04. PAGE HEADINGS & HERO
   ========================================================================== */
.app-title {
    font-size: 34px;
    font-weight: 800;
    color: #f8fafc;
    letter-spacing: -0.03em;
    margin-bottom: 3px;
}

.app-subtitle {
    color: #94a3b8;
    font-size: 15px;
    margin-bottom: 14px;
}

.hero-card {
    background:
        linear-gradient(135deg, rgba(37, 99, 235, 0.95), rgba(20, 184, 166, 0.90)),
        radial-gradient(circle at top right, rgba(255,255,255,0.25), transparent 25%);
    padding: 22px 26px;
    border-radius: 22px;
    color: white;
    box-shadow: 0 20px 45px rgba(37, 99, 235, 0.25);
    margin-bottom: 13px;
    border: 1px solid rgba(255,255,255,0.18);
}

.hero-title {
    font-size: 31px;
    font-weight: 850;
    margin-bottom: 8px;
    letter-spacing: -0.03em;
}

.hero-desc {
    font-size: 15px;
    opacity: 0.95;
    line-height: 1.6;
    max-width: 960px;
}

/* ==========================================================================
   05. DASHBOARD CARDS & METRICS
   ========================================================================== */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.dashboard-card-marker) {
    background: rgba(15, 23, 42, 0.82) !important;
    padding: 16px 18px !important;
    border-radius: 18px !important;
    border: 1px solid rgba(148, 163, 184, 0.16) !important;
    box-shadow: 0 14px 34px rgba(0,0,0,0.26) !important;
    margin-bottom: 10px !important;
}

.dashboard-card-marker {
    display: none;
}

.metric-card {
    background: rgba(15, 23, 42, 0.88);
    border: 1px solid rgba(148, 163, 184, 0.16);
    padding: 15px 16px 14px 16px;
    border-radius: 20px;
    box-shadow: 0 12px 28px rgba(0,0,0,0.22);
    min-height: 120px;
    position: relative;
    overflow: hidden;
}

.metric-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 5px;
    background: linear-gradient(90deg, #3b82f6, #14b8a6, #a855f7);
}

.metric-icon {
    font-size: 25px;
    margin-bottom: 8px;
}

.metric-icon .material-symbols-rounded {
    font-size: 26px;
    color: #60a5fa;
}

.metric-label {
    font-size: 13px;
    color: #94a3b8;
    font-weight: 600;
    margin-bottom: 8px;
}

.metric-value {
    font-size: 24px;
    color: #f8fafc;
    font-weight: 850;
    letter-spacing: -0.03em;
}

.metric-help {
    margin-top: 7px;
    font-size: 12px;
    color: #64748b;
}

/* ==========================================================================
   06. SECTION HEADINGS
   ========================================================================== */
.section-title {
    font-size: 21px;
    font-weight: 800;
    color: #f8fafc;
    margin-bottom: 5px;
    letter-spacing: -0.02em;
}

.section-desc {
    color: #94a3b8;
    font-size: 14px;
    margin-bottom: 10px;
    line-height: 1.5;
}

/* ==========================================================================
   07. INSIGHTS, RECOMMENDATIONS & BADGES
   ========================================================================== */
.insight-box {
    background: rgba(37, 99, 235, 0.12);
    border: 1px solid rgba(96, 165, 250, 0.22);
    border-radius: 18px;
    padding: 16px 18px;
    margin-bottom: 12px;
    color: #cbd5e1;
}

.rekom-box {
    background: rgba(20, 184, 166, 0.11);
    border: 1px solid rgba(45, 212, 191, 0.22);
    border-radius: 18px;
    padding: 16px 18px;
    margin-bottom: 12px;
    color: #cbd5e1;
}

.warning-box {
    background: rgba(250, 204, 21, 0.10);
    border: 1px solid rgba(250, 204, 21, 0.25);
    border-radius: 18px;
    padding: 16px 18px;
    margin-bottom: 12px;
    color: #cbd5e1;
}

.small-muted {
    color: #cbd5e1;
    font-size: 13px;
    line-height: 1.55;
}

.badge {
    display: inline-block;
    padding: 5px 11px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 800;
    margin-right: 6px;
    margin-bottom: 6px;
}

.badge-blue {
    background: rgba(59, 130, 246, 0.18);
    color: #93c5fd;
    border: 1px solid rgba(59, 130, 246, 0.28);
}

.badge-green {
    background: rgba(34, 197, 94, 0.16);
    color: #86efac;
    border: 1px solid rgba(34, 197, 94, 0.25);
}

.badge-purple {
    background: rgba(168, 85, 247, 0.16);
    color: #d8b4fe;
    border: 1px solid rgba(168, 85, 247, 0.25);
}

/* ==========================================================================
   08. USER PROFILE & ACCOUNT
   ========================================================================== */
.user-box {
    display: flex;
    align-items: center;
    gap: 12px;
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.76), rgba(15, 23, 42, 0.66));
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    padding: 15px;
    border-radius: 20px;
    border: 1px solid rgba(148, 163, 184, 0.15);
    box-shadow: 0 14px 32px rgba(2, 6, 23, 0.26), inset 0 1px 0 rgba(255,255,255,0.04);
    margin-bottom: 19px;
}

.user-avatar {
    width: 43px;
    height: 43px;
    min-width: 43px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background: linear-gradient(135deg, #2563eb, #60a5fa);
    box-shadow: 0 8px 20px rgba(37, 99, 235, 0.28);
    position: relative;
}

.user-avatar .material-symbols-rounded {
    font-size: 23px;
    color: #ffffff;
}

.online-indicator {
    position: absolute;
    right: -1px;
    bottom: 1px;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #22c55e;
    border: 2px solid #172033;
    box-shadow: 0 0 9px rgba(34, 197, 94, 0.72);
}

.user-details {
    min-width: 0;
    flex: 1;
}

.user-caption {
    color: #94a3b8;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 3px;
}

.user-name {
    color: #f8fafc;
    font-size: 15px;
    font-weight: 750;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-bottom: 7px;
}

.badge-admin {
    display: inline-flex;
    align-items: center;
    background: linear-gradient(135deg, #2563eb, #4f46e5);
    color: white;
    padding: 3px 9px;
    border-radius: 999px;
    font-size: 9px;
    font-weight: 750;
    letter-spacing: 0.08em;
    box-shadow: 0 6px 15px rgba(37, 99, 235, 0.22);
}

.badge-owner {
    display: inline-flex;
    align-items: center;
    background: linear-gradient(135deg, #DC2626, #B91C1C);
    color: #ffffff;
    padding: 3px 9px;
    border-radius: 999px;
    font-size: 9px;
    font-weight: 750;
    letter-spacing: 0.08em;
    box-shadow: 0 6px 15px rgba(79, 70, 229, 0.22);
}

.sidebar-section-label {
    color: #64748b;
    font-size: 10px;
    font-weight: 750;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    padding: 0 10px 9px 10px;
}

.account-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(148,163,184,0.20), transparent);
    margin: 20px 3px 14px 3px;
}

/* ==========================================================================
   09. CLUSTER INSIGHT CARDS
   ========================================================================== */
.cluster-insight-card {
    min-height: 270px;
    padding: 18px;
    border-radius: 20px;
    background: rgba(15, 23, 42, 0.78);
    border: 1px solid rgba(148, 163, 184, 0.15);
    box-shadow: 0 14px 34px rgba(2, 6, 23, 0.24);
    position: relative;
    overflow: hidden;
}

.cluster-insight-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 4px;
    background: #3b82f6;
}

.cluster-high::before { background: linear-gradient(90deg, #22c55e, #14b8a6); }
.cluster-medium::before { background: linear-gradient(90deg, #f59e0b, #facc15); }
.cluster-low::before { background: linear-gradient(90deg, #ef4444, #f97316); }

.cluster-insight-title {
    color: #f8fafc;
    font-size: 18px;
    font-weight: 800;
    margin-bottom: 14px;
}

.cluster-insight-label {
    color: #60a5fa;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    margin: 14px 0 7px;
}

.cluster-insight-text {
    color: #cbd5e1;
    font-size: 13px;
    line-height: 1.65;
}

/* ==========================================================================
   10. ACTION & DOWNLOAD BUTTONS
   ========================================================================== */
.stButton > button,
.stFormSubmitButton > button {
    background: linear-gradient(135deg, #2563eb, #14b8a6);
    color: white;
    border: none;
    border-radius: 13px;
    padding: 0.70rem 1.15rem;
    font-weight: 800;
    box-shadow: 0 10px 22px rgba(37, 99, 235, 0.20);
}

.stDownloadButton > button {
    background: linear-gradient(135deg, #22c55e, #14b8a6);
    color: white;
    border: none;
    border-radius: 13px;
    padding: 0.70rem 1.15rem;
    font-weight: 800;
    box-shadow: 0 10px 22px rgba(34, 197, 94, 0.20);
}

/* ==========================================================================
   11. SIDEBAR NAVIGATION & LOGOUT
   ========================================================================== */
section[data-testid="stSidebar"] div[data-testid="stRadio"] > div {
    gap: 6px !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label {
    width: 100%;
    min-height: 48px;
    display: flex !important;
    align-items: center !important;
    padding: 0 14px !important;
    margin: 0 !important;
    border-radius: 14px;
    border: 1px solid transparent;
    background: transparent;
    cursor: pointer;
    position: relative;
    transition: background 0.25s ease, color 0.25s ease, transform 0.25s ease, box-shadow 0.25s ease;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label::after {
    content: "";
    position: absolute;
    left: 0;
    top: 13px;
    width: 3px;
    height: 22px;
    border-radius: 0 4px 4px 0;
    background: #60a5fa;
    opacity: 0;
    transform: scaleY(0.45);
    transition: 0.25s ease;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(59, 130, 246, 0.15);
    border-color: rgba(96, 165, 250, 0.10);
    transform: translateX(2px);
}

section[data-testid="stSidebar"] div[role="radiogroup"] label:hover::after,
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked)::after {
    opacity: 1;
    transform: scaleY(1);
}

section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
    border-color: rgba(147, 197, 253, 0.20);
    box-shadow: 0 10px 24px rgba(37, 99, 235, 0.25), inset 0 1px 0 rgba(255,255,255,0.10);
}

section[data-testid="stSidebar"] div[data-baseweb="radio"] > div:first-child {
    display: none !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label p {
    display: flex;
    align-items: center;
    gap: 12px;
    color: #aeb9ca !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
    transition: color 0.25s ease;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label p::before {
    font-family: 'Material Symbols Rounded';
    font-size: 21px;
    font-weight: 400;
    color: #7f8da3;
    transition: color 0.25s ease, transform 0.25s ease;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label:hover p,
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover p::before,
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p,
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p::before {
    color: #ffffff !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label:hover p::before {
    transform: scale(1.06);
}

section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(1) p::before { content: "dashboard"; }
section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(2) p::before { content: "cloud_upload"; }
section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(3) p::before { content: "lightbulb"; }
section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(4) p::before { content: "dataset"; }
section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(5) p::before { content: "history"; }
section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(6) p::before { content: "manage_accounts"; }

section[data-testid="stSidebar"] .stButton {
    position: sticky;
    bottom: 12px;
    z-index: 5;
}

section[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    min-height: 46px;
    justify-content: flex-start;
    gap: 11px;
    padding: 0 15px;
    border-radius: 14px;
    background: rgba(239, 68, 68, 0.02);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.48);
    box-shadow: none;
    transition: all 0.25s ease;
}

section[data-testid="stSidebar"] .stButton > button::before {
    content: "logout";
    font-family: 'Material Symbols Rounded';
    font-size: 21px;
    font-weight: 400;
    color: #f87171;
    transition: color 0.25s ease;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    color: #ffffff;
    background: #dc2626;
    border-color: #ef4444;
    box-shadow: 0 10px 24px rgba(220, 38, 38, 0.24);
}

section[data-testid="stSidebar"] .stButton > button:hover::before {
    color: #ffffff;
}

/* ==========================================================================
   12. RESPONSIVE (MOBILE)
   ========================================================================== */
@media (max-width: 768px) {
    section[data-testid="stSidebar"] {
        width: 280px !important;
        min-width: 280px !important;
        max-width: 280px !important;
    }

    section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        padding-left: 14px !important;
        padding-right: 14px !important;
    }
}

/* ==========================================================================
   13. TABLES & ROWS
   ========================================================================== */
.custom-table-wrapper {
    width: 100%;
    overflow-x: auto;
    border-radius: 18px;
    border: 1px solid rgba(148, 163, 184, 0.18);
    background: rgba(15, 23, 42, 0.88);
    box-shadow: 0 14px 34px rgba(0,0,0,0.24);
    margin-top: 12px;
    margin-bottom: 18px;
}

.custom-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    color: #e5e7eb;
    min-width: 900px;
}

.custom-table thead tr {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.98), rgba(15, 23, 42, 0.96));
}

.custom-table th {
    padding: 13px 14px;
    text-align: left;
    color: #f8fafc;
    font-weight: 800;
    border-bottom: 1px solid rgba(148, 163, 184, 0.22);
    white-space: nowrap;
}

.custom-table td {
    padding: 12px 14px;
    color: #cbd5e1;
    border-bottom: 1px solid rgba(148, 163, 184, 0.10);
    white-space: nowrap;
}

.custom-table tbody tr {
    background: rgba(15, 23, 42, 0.62);
    transition: 0.18s ease;
}

.custom-table tbody tr:nth-child(even) {
    background: rgba(30, 41, 59, 0.38);
}

.custom-table tbody tr:hover {
    background: rgba(59, 130, 246, 0.16);
}

.custom-table tbody tr:hover td {
    color: #f8fafc;
}

/* ==========================================================================
   14. SPACING, CHARTS & DIVIDERS
   ========================================================================== */
/* Jarak vertikal antarseksi agar dashboard lebih ringkas. */
section[data-testid="stMain"] div[data-testid="stVerticalBlock"] {
    gap: 1.90rem;
}
section[data-testid="stMain"] div[data-testid="stHorizontalBlock"] {
    gap: 0.85rem;
}
section[data-testid="stMain"] div[data-testid="stMarkdownContainer"] > p:empty {
    display: none;
}

div[data-testid="stPlotlyChart"] {
    background: rgba(15, 23, 42, 0.35);
    border-radius: 18px;
}

hr {
    border-color: rgba(148, 163, 184, 0.16);
}
</style>
""", unsafe_allow_html=True)


# CSS UNTUK LOGIN PAGE

def inject_login_css():
    st.markdown("""
    <style>
    /* HEADER */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    /* LOGIN CONTAINER */
    div[data-testid="stAppViewContainer"] .block-container {
        max-width: 900px !important;
        min-height: calc(100vh - 4rem) !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* LOGIN CARD */
    div[data-testid="stVerticalBlock"]:has(.login-card-marker) {
        width: 100% !important;
        max-width: 760px !important;
        padding: 34px 48px !important;
        border-radius: 32px !important;
        background: rgba(15, 23, 42, 0.72) !important;
        border: 1px solid rgba(148, 163, 184, 0.22) !important;
        box-shadow: 0 32px 90px rgba(0, 0, 0, 0.45),
                    inset 0 1px 0 rgba(255, 255, 255, 0.06) !important;
        backdrop-filter: blur(22px) !important;
        -webkit-backdrop-filter: blur(22px) !important;
    }

    .login-card-marker {
        display: none;
    }

    /* LOGO */
    .login-logo {
        width: 72px;
        height: 72px;
        border-radius: 24px;
        margin: 0 auto 20px auto;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #2563eb, #14b8a6);
        box-shadow: 0 18px 42px rgba(37, 99, 235, 0.35);
        font-size: 35px;
        border: 1px solid rgba(255, 255, 255, 0.20);
    }

    /* LOGIN TITLE */
    .login-title {
        text-align: center;
        font-size: 28px;
        font-weight: 900;
        color: #f8fafc;
        letter-spacing: -0.045em;
        line-height: 1.25;
        margin-bottom: 10px;
        max-width: 620px;
        margin-left: auto;
        margin-right: auto;
    }

    .login-desc {
        text-align: center;
        color: #94a3b8;
        font-size: 15px;
        line-height: 1.7;
        margin-bottom: 26px;
        max-width: 620px;
        margin-left: auto;
        margin-right: auto;
    }

    /* FORM */
    div[data-testid="stForm"] {
        border: none !important;
        padding: 0 !important;
        background: transparent !important;
    }

    /* INPUT LABEL */
    div[data-testid="stTextInput"] label {
        color: #cbd5e1 !important;
        font-weight: 700 !important;
        font-size: 14px !important;
    }

    /* INPUT BOX */
    div[data-testid="stTextInput"] div[data-baseweb="input"] {
        background: rgba(2, 6, 23, 0.72) !important;
        border: 1px solid rgba(148, 163, 184, 0.30) !important;
        border-radius: 15px !important;
        height: 52px !important;
        overflow: hidden !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.04) !important;
        padding-right: 0 !important;
    }

    div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.16) !important;
    }

    div[data-testid="stTextInput"] input {
        height: 52px !important;
        background: transparent !important;
        color: #f8fafc !important;
        border: none !important;
        padding: 0 15px !important;
        font-size: 15px !important;
        box-shadow: none !important;
    }

    div[data-testid="stTextInput"] input::placeholder {
        color: #64748b !important;
    }

    /* PASSWORD VISIBILITY BUTTON */
    div[data-testid="stTextInput"] button {
        height: 52px !important;
        width: 56px !important;
        min-width: 56px !important;
        max-width: 56px !important;
        background: linear-gradient(135deg, #1e293b, #334155) !important;
        border: none !important;
        border-left: 1px solid rgba(148, 163, 184, 0.20) !important;
        border-radius: 0 15px 15px 0 !important;
        color: #f8fafc !important;
        box-shadow: none !important;
        margin: 0 !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* LOGIN BUTTON */
    div[data-testid="stFormSubmitButton"] button {
        width: 100% !important;
        height: 52px !important;
        margin-top: 10px !important;
        border-radius: 15px !important;
        border: none !important;
        background: linear-gradient(135deg, #2563eb, #14b8a6) !important;
        color: #ffffff !important;
        font-size: 15px !important;
        font-weight: 850 !important;
        box-shadow: 0 16px 36px rgba(37, 99, 235, 0.28) !important;
        transition: 0.2s ease !important;
    }

    div[data-testid="stFormSubmitButton"] button:hover {
        transform: translateY(-1px);
        box-shadow: 0 20px 42px rgba(20, 184, 166, 0.30) !important;
    }
    </style>
    """, unsafe_allow_html=True)
