import streamlit as st
import pandas as pd
import numpy as np
import pymysql     
# mengintegrasi dari sqlite3 ke mysql
import hashlib
import io
import re
import csv
import zipfile
import posixpath
import xml.etree.ElementTree as ET
from collections import defaultdict
import hmac
import os
import html
import json
from contextlib import contextmanager

import plotly.express as px
import plotly.graph_objects as go

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score
# import config.py
from config import (
    APP_DIR,
    DEFAULT_FILE,
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_USER,
    MYSQL_DATABASE
)
# import database.connection sebagai db_conn
from database.connection import get_connection
# import database.repository sebagai db_repo
from database.repository import (
    init_db,
    login_user,
    add_user,
    get_all_users,
    delete_user,
    save_sales_data_to_db,
    load_sales_data_from_db,
    clear_sales_data_db,
    dataframe_to_json,
    dataframe_from_json,
    save_dataset_history,
    get_dataset_history,
    load_dataset_by_id,
    get_active_dataset_record,
    get_active_dataset_metadata,
    save_clustering_history,
    get_clustering_history,
    load_clustering_history_by_id,
    load_latest_clustering_for_dataset,
    delete_clustering_history,
    get_cluster_order,
    buat_rekomendasi,
    build_clustering_insight,
    set_active_dataset,
    delete_dataset_by_id
)
from processing.data_loader import (
    get_default_data,
    load_uploaded_file,
    normalize_column_key,
    clean_column_names,
    COLUMN_CANDIDATE_GROUPS
)

from processing.clustering import (
    build_data_signature,
    validate_clustering_input,
    run_clustering,
)

from utils.helpers import (
    format_rupiah,
    format_number,
    format_table_value,
)
# ============================================================
# PATH FILE
# ============================================================

# ============================================================
# PAGE CONFIG 
# ============================================================

st.set_page_config(
    page_title="Dashboard Toko SJB",
    page_icon="👟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS UI
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,400,0,0&display=swap');
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


# ============================================================
# WARNA CHART
# ============================================================

COLOR_BLUE = "#3b82f6"
COLOR_TEAL = "#14b8a6"
COLOR_PURPLE = "#a855f7"
COLOR_GREEN = "#22c55e"
COLOR_YELLOW = "#facc15"
COLOR_RED = "#ef4444"
COLOR_ORANGE = "#fb923c"
COLOR_TEXT = "#e5e7eb"
COLOR_MUTED = "#94a3b8"
COLOR_GRID = "rgba(148, 163, 184, 0.18)"
COLOR_BG = "rgba(15, 23, 42, 0)"

CHART_COLORS = [
    COLOR_BLUE, COLOR_TEAL, COLOR_PURPLE, COLOR_GREEN, 
    COLOR_YELLOW, COLOR_ORANGE, COLOR_RED
]

def apply_plotly_theme(fig, height=315):
    fig.update_layout(
        height=height,
        paper_bgcolor=COLOR_BG,
        plot_bgcolor=COLOR_BG,
        font=dict(color=COLOR_TEXT, family="Inter"),
        title=dict(font=dict(size=16, color="#f8fafc")),
        legend=dict(
            bgcolor="rgba(15,23,42,0)",
            font=dict(color=COLOR_TEXT)
        ),
        margin=dict(l=10, r=12, t=22, b=28),
        hoverlabel=dict(
            bgcolor="#0f172a",
            font_size=13,
            font_family="Inter",
            font_color="#f8fafc"
        )
    )

    fig.update_xaxes(showgrid=True, gridcolor=COLOR_GRID, zeroline=False, color=COLOR_MUTED, automargin=True, tickfont=dict(size=10))
    fig.update_yaxes(showgrid=True, gridcolor=COLOR_GRID, zeroline=False, color=COLOR_MUTED, automargin=True, tickfont=dict(size=10))
    return fig

def show_plotly(fig, height=315, showlegend=True):
    fig.update_layout(showlegend=showlegend)
    fig = apply_plotly_theme(fig, height=height)
    st.plotly_chart(fig, use_container_width=True)


def activate_dataset(dataset_id):
    record = load_dataset_by_id(dataset_id)
    if record is None or record["data"].empty: 
        return False
    
    # Mengubah status dataset di MySQL melalui repository
    set_active_dataset(dataset_id)

    save_sales_data_to_db(record["data"])
    st.session_state.active_dataset_id = int(dataset_id)
    st.session_state.df_selected = record["data"].copy()
    st.session_state.df_product = aggregate_product_data(record["data"])
    st.session_state.analysis_dataset_id = int(dataset_id)
    st.session_state.analysis_dataset_name = record["name"]
    st.session_state.analysis_df_selected = record["data"].copy()
    reset_analysis_results()
    reset_date_filter_state()
    return True

def use_dataset_for_analysis(dataset_id):
    record = load_dataset_by_id(dataset_id)
    if record is None or record["data"].empty: return False
    st.session_state.analysis_dataset_id = int(dataset_id)
    st.session_state.analysis_dataset_name = record["name"]
    st.session_state.analysis_df_selected = record["data"].copy()
    reset_analysis_results()
    return True


def delete_dataset_history(dataset_id):
    record = load_dataset_by_id(dataset_id)

    if record is None:
        return False
    delete_dataset_by_id(dataset_id)

    # Jika dataset yang dihapus adalah dataset aktif
    if record["is_active"]:
        clear_sales_data_db()
        st.session_state.active_dataset_id = None
        st.session_state.df_selected = None
        st.session_state.df_product = None
        reset_analysis_results()
        reset_date_filter_state()

    # Menghapus referensi dataset dari session analisis
    if st.session_state.get("analysis_dataset_id") == int(dataset_id):
        st.session_state.analysis_dataset_id = None
        st.session_state.analysis_dataset_name = None
        st.session_state.analysis_df_selected = None

    return True


# ============================================================
# FORMATTER DAN HELPER
# ============================================================

def format_rupiah(value):
    try: return f"Rp {float(value):,.0f}".replace(",", ".")
    except Exception: return "Rp 0"

def format_number(value):
    try: return f"{int(value):,}".replace(",", ".")
    except Exception: return "0"

def format_table_value(value):
    if pd.isna(value): return ""
    if isinstance(value, pd.Timestamp): return value.strftime("%d/%m/%Y")
    if isinstance(value, (int, np.integer)): return f"{int(value):,}".replace(",", ".")
    if isinstance(value, (float, np.floating)):
        if abs(value) >= 1000: return f"{value:,.0f}".replace(",", ".")
        return f"{value:,.2f}".replace(",", ".")
    return str(value)

def show_table(df, max_rows=50):
    if df is None or df.empty:
        st.info("Data tidak tersedia.")
        return
    df_show = df.copy().head(max_rows)
    html_table = f'<div class="custom-table-wrapper"><table class="custom-table"><thead><tr>'
    for col in df_show.columns: html_table += f"<th>{html.escape(str(col))}</th>"
    html_table += '</tr></thead><tbody>'
    for _, row in df_show.iterrows():
        html_table += "<tr>"
        for col in df_show.columns: html_table += f"<td>{html.escape(str(format_table_value(row[col])))}</td>"
        html_table += "</tr>"
    html_table += '</tbody></table></div>'
    st.markdown(html_table, unsafe_allow_html=True)
    if len(df) > max_rows: st.caption(f"Menampilkan {max_rows} dari {len(df)} baris data.")

def interactive_table(df, key, page_size=10, default_sort=None):
    if df is None or df.empty:
        st.info("Data tidak tersedia.")
        return
    working_df = df.copy().reset_index(drop=True)
    control_search, control_sort, control_order = st.columns([2, 1, 1])

    with control_search: search_text = st.text_input("Cari data", placeholder="Ketik kata kunci...", key=f"{key}_search").strip()
    with control_sort:
        sort_options = ["Urutan awal"] + list(working_df.columns)
        default_index = sort_options.index(default_sort) if default_sort in sort_options else 0
        sort_column = st.selectbox("Urutkan berdasarkan", sort_options, index=default_index, key=f"{key}_sort")
    with control_order: sort_direction = st.selectbox("Arah", ["Menurun", "Menaik"], key=f"{key}_direction")

    if search_text:
        search_mask = working_df.astype(str).apply(lambda column: column.str.contains(search_text, case=False, na=False, regex=False)).any(axis=1)
        working_df = working_df[search_mask].copy()

    if sort_column != "Urutan awal" and not working_df.empty:
        try: working_df = working_df.sort_values(sort_column, ascending=sort_direction == "Menaik", kind="stable")
        except TypeError: working_df = working_df.assign(_sort_value=working_df[sort_column].astype(str)).sort_values("_sort_value", ascending=sort_direction == "Menaik", kind="stable").drop(columns="_sort_value")

    total_rows = len(working_df)
    total_pages = max(1, int(np.ceil(total_rows / page_size)))

    page_column, info_column = st.columns([1, 3])
    with page_column: selected_page = st.selectbox("Halaman", list(range(1, total_pages + 1)), key=f"{key}_page")
    with info_column: st.caption(f"{total_rows} data ditemukan · {page_size} data per halaman · Halaman {selected_page} dari {total_pages}")

    start_index = (selected_page - 1) * page_size
    page_df = working_df.iloc[start_index:start_index + page_size].copy()
    page_df.insert(0, "No.", range(start_index + 1, start_index + len(page_df) + 1))
    show_table(page_df, max_rows=page_size)

def navigate_to_sidebar(display_label):
    st.session_state.main_sidebar_navigation = display_label

def build_clustering_report_html(result, dataset_name):
    df_result = result["df_result"]
    cluster_summary = df_result.groupby("Kategori_Cluster").agg(Jumlah_Produk=("Product Name", "nunique"), Total_Quantity=("Quantity", "sum"), Total_Revenue=("Revenue", "sum")).reset_index()
    return f"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<title>Clustering Report</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 36px; color: #172033; }}
h1, h2 {{ color: #1d4ed8; }}
.metrics {{ display: flex; gap: 18px; margin: 20px 0; }}
.metric {{ padding: 14px 18px; border: 1px solid #dbeafe; border-radius: 12px; }}
table {{ width: 100%; border-collapse: collapse; margin: 16px 0 28px; font-size: 12px; }}
th, td {{ border: 1px solid #dbe2ea; padding: 8px; text-align: left; }}
th {{ background: #eff6ff; }}
</style>
</head>
<body>
<h1>Business Intelligence — Clustering Report</h1>
<p><strong>Dataset:</strong> {html.escape(str(dataset_name))}</p>
<div class="metrics">
  <div class="metric"><strong>Nilai K</strong><br>{result['k']}</div>
  <div class="metric"><strong>Silhouette</strong><br>{result['silhouette']:.4f}</div>
  <div class="metric"><strong>Davies-Bouldin</strong><br>{result['dbi']:.4f}</div>
</div>
<h2>Ringkasan Cluster</h2>
{cluster_summary.rename(columns={"Total_Revenue": "Total Omzet"}).to_html(index=False, border=0)}
<h2>Hasil Clustering</h2>
{df_result.rename(columns={"Revenue": "Omzet", "Revenue_Per_Transaksi": "Omzet per Transaksi"}).to_html(index=False, border=0)}
</body>
</html>"""

def safe_html(value):
    return html.escape(str(value), quote=True)

@contextmanager
def card_container():
    try: container = st.container(border=True)
    except TypeError: container = st.container()
    with container:
        st.markdown('<span class="dashboard-card-marker"></span>', unsafe_allow_html=True)
        yield

def section_header(title, desc=""):
    st.markdown(f'<div class="section-title">{safe_html(title)}</div><div class="section-desc">{safe_html(desc)}</div>', unsafe_allow_html=True)

def metric_card(icon, title, value, help_text=""):
    st.markdown(f'<div class="metric-card"><div class="metric-icon"><span class="material-symbols-rounded">{safe_html(icon)}</span></div><div class="metric-label">{safe_html(title)}</div><div class="metric-value">{safe_html(value)}</div><div class="metric-help">{safe_html(help_text)}</div></div>', unsafe_allow_html=True)

def top_bar(title, subtitle=""):
    st.markdown(f'<div class="app-title">{safe_html(title)}</div><div class="app-subtitle">{safe_html(subtitle)}</div>', unsafe_allow_html=True)



# ============================================================
# LOAD DAN PREPROCESSING DATA
# ============================================================

def parse_number_value(x):
    if pd.isna(x): return np.nan
    if isinstance(x, (int, float, np.integer, np.floating)): return float(x)
    text = str(x).strip().replace("Rp", "").replace("rp", "").replace("IDR", "").replace("idr", "").replace(" ", "")
    allowed = "0123456789.,-"
    text = "".join(ch for ch in text if ch in allowed)
    if text in ["", "-", ".", ","]: return np.nan
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."): text = text.replace(".", "").replace(",", ".")
        else: text = text.replace(",", "")
    elif "," in text:
        parts = text.split(",")
        if len(parts[-1]) == 3 and all(part.isdigit() for part in parts): text = text.replace(",", "")
        else: text = text.replace(",", ".")
    elif "." in text:
        parts = text.split(".")
        if len(parts) > 1 and all(len(part) == 3 for part in parts[1:]) and all(part.isdigit() for part in parts): text = text.replace(".", "")
        elif len(parts) == 2 and len(parts[-1]) == 3 and parts[0].isdigit() and parts[1].isdigit(): text = text.replace(".", "")
    try: return float(text)
    except Exception: return np.nan

def parse_number_series(series):
    if pd.api.types.is_numeric_dtype(series): return pd.to_numeric(series, errors="coerce")
    return series.apply(parse_number_value)

def normalize_column_key(column_name):
    text = str(column_name).replace("\ufeff", " ").replace("\n", " ").replace("\r", " ").replace("\t", " ")
    return " ".join(re.sub(r"[^0-9a-zA-Z]+", " ", text).lower().strip().split())

COLUMN_CANDIDATE_GROUPS = {
    "product": ["Product Name", "Product", "Nama Produk", "Produk", "SKU Product Name", "Seller SKU Product Name", "SKU Name", "Product Title", "Nama Barang"],
    "quantity": ["Quantity", "Qty", "Jumlah", "Jumlah Terjual", "Quantity Sold", "SKU Quantity", "Item Quantity"],
    "order": ["Order ID", "Order", "Orders", "ID Pesanan", "Nomor Pesanan", "Jumlah Transaksi", "Transaksi", "Order Number"],
    "revenue": ["SKU Subtotal After Discount", "SKU Subtotal", "Subtotal After Discount", "SKU Subtotal (After Discount)"],
    "date": ["Created Time", "Paid Time", "Date", "Tanggal", "Created Date", "Order Created Time", "Order Paid Time", "Creation Time"],
    "status": ["Order Status", "Status Pesanan", "Status"],
    "city": ["Regency and City", "City", "Buyer City", "Recipient City", "Shipping City", "Kota", "Kabupaten Kota"],
    # baru nambahin kolum provinsi
    "province": ["Province", "Provinsi","Buyer Province","Recipient Province", "Shipping Province"],
    # metode pembayaran 
    "payment_method": ["Payment Method", "Payment Type", "Metode Pembayaran", "Pembayaran Channel"]
}

REQUIRED_COLUMN_GROUPS = ("product", "quantity", "order", "revenue")

def clean_column_names(df):
    df = df.copy()
    df.columns = [" ".join(str(c).replace("\ufeff", " ").replace("\n", " ").replace("\r", " ").replace("\t", " ").strip().split()) for c in df.columns]
    return df

def clean_loaded_dataframe(df):
    if df is None: return None
    df = clean_column_names(df).dropna(axis=0, how="all").dropna(axis=1, how="all")
    removable_columns = [col for col in df.columns if normalize_column_key(col).startswith("unnamed") and df[col].isna().all()]
    if removable_columns: df = df.drop(columns=removable_columns)
    return df

def detect_sales_columns(df):
    normalized_map = {normalize_column_key(col): col for col in df.columns}
    detected = {}
    for group_name, candidates in COLUMN_CANDIDATE_GROUPS.items():
        detected_col = None
        for candidate in candidates:
            candidate_key = normalize_column_key(candidate)
            if candidate_key in normalized_map:
                detected_col = normalized_map[candidate_key]
                break
        if detected_col is None:
            for candidate in candidates:
                candidate_key = normalize_column_key(candidate)
                if len(candidate_key) < 5: continue
                for norm_col, orig_col in normalized_map.items():
                    if candidate_key in norm_col or norm_col in candidate_key:
                        detected_col = orig_col
                        break
                if detected_col is not None: break
        detected[group_name] = detected_col
    return detected

def score_sales_dataframe(df):
    if df is None or df.empty: return -1, 0, 0
    detected = detect_sales_columns(df)
    required_count = sum(detected[g] is not None for g in REQUIRED_COLUMN_GROUPS)
    optional_count = sum(detected[g] is not None for g in ("date", "status"))
    return (required_count * 10_000) + (optional_count * 1_000) + len(df.columns), required_count, optional_count

def find_column(df, candidates):
    normalized_map = {normalize_column_key(col): col for col in df.columns}
    for candidate in candidates:
        candidate_key = normalize_column_key(candidate)
        if candidate_key in normalized_map: return normalized_map[candidate_key]
    for candidate in candidates:
        candidate_key = normalize_column_key(candidate)
        if len(candidate_key) < 5: continue
        for norm_col, orig_col in normalized_map.items():
            if candidate_key in norm_col or norm_col in candidate_key: return orig_col
    return None

# Transform
def preprocess_data(df):
    # Membersihkan nama kolom
    df = clean_column_names(df)
    # Mencari kolom yang diperlukan
    p_col = find_column(df, COLUMN_CANDIDATE_GROUPS["product"])
    q_col = find_column(df, COLUMN_CANDIDATE_GROUPS["quantity"])
    o_col = find_column(df, COLUMN_CANDIDATE_GROUPS["order"])
    r_col = find_column(df, COLUMN_CANDIDATE_GROUPS["revenue"])
    d_col = find_column(df, COLUMN_CANDIDATE_GROUPS["date"])
    s_col = find_column(df, COLUMN_CANDIDATE_GROUPS["status"])
    c_col = find_column(df, COLUMN_CANDIDATE_GROUPS["city"])
    prov_col = find_column(df, COLUMN_CANDIDATE_GROUPS["province"])
    pay_col = find_column(df, COLUMN_CANDIDATE_GROUPS["payment_method"])

    missing = []
    if p_col is None: missing.append("Product Name")
    if q_col is None: missing.append("Quantity")
    if o_col is None: missing.append("Order ID")
    if r_col is None: missing.append("SKU Subtotal After Discount")
    if pay_col is None: missing.append("Payment Method")

    if missing:
        st.error("Kolom wajib tidak ditemukan: " + ", ".join(missing) + ".")
        st.info("Kolom yang terbaca dari file: " + ", ".join(str(c) for c in df.columns))
        return None

    selected_columns = [p_col, q_col, o_col, r_col]
    if d_col is not None: selected_columns.append(d_col)
    if s_col is not None: selected_columns.append(s_col)
    if c_col is not None: selected_columns.append(c_col)
    if prov_col is not None : selected_columns.append(prov_col)
    if pay_col is not None: selected_columns.append(pay_col)

    df_selected = df[selected_columns].copy()

    # Mengubah nama kolom menjadi standar
    rename_dict = {p_col: "Product Name", q_col: "Quantity", o_col: "Order", r_col: "Revenue"}
    if d_col is not None: rename_dict[d_col] = "Date"
    if s_col is not None: rename_dict[s_col] = "Order Status"
    # nambahin kolom kota sm provinsi untuk dipake didashborad
    if c_col is not None: rename_dict[c_col] = "Regency and City"
    if prov_col is not None: rename_dict[prov_col] = "Province"
    if pay_col is not None: rename_dict[pay_col] = "Payment Method"
    df_selected = df_selected.rename(columns=rename_dict)

    df_selected = df_selected[df_selected["Order"].astype(str).str.strip().str.lower() != "platform unique order id."].copy()

    if "Order Status" in df_selected.columns:
        df_selected["Order Status"] = df_selected["Order Status"].astype(str).str.lower().str.strip()
        status_mapping = {"selesai": "selesai", "completed": "selesai", "complete": "selesai", "delivered": "selesai", "dikirim": "dikirim", "shipped": "dikirim"}
        df_selected["Order Status"] = df_selected["Order Status"].map(status_mapping)
        df_selected = df_selected.dropna(subset=["Order Status"])

    # Membersihkan data kosong
    df_selected = df_selected.dropna(subset=["Product Name", "Quantity", "Order", "Revenue"])

    # Mengubah Quantity dan Revenue menjadi numerik
    df_selected["Quantity"] = parse_number_series(df_selected["Quantity"])
    df_selected["Revenue"] = parse_number_series(df_selected["Revenue"])
    df_selected = df_selected.dropna(subset=["Quantity", "Revenue"])
    df_selected = df_selected[(df_selected["Quantity"] > 0) & (df_selected["Revenue"] >= 0)].copy()

    if "Date" in df_selected.columns:
        df_selected["Date"] = pd.to_datetime(df_selected["Date"], errors="coerce", dayfirst=True)
        if df_selected["Date"].notna().any(): df_selected = df_selected.dropna(subset=["Date"])
        else: df_selected = df_selected.drop(columns=["Date"])

    df_selected["Harga_Per_Unit"] = df_selected["Revenue"] / df_selected["Quantity"]
    return df_selected

def aggregate_product_data(df_selected):
    df_selected = df_selected.copy()
    agg_dict = {"Quantity": "sum", "Order": "nunique", "Revenue": "sum"}
    use_date = "Date" in df_selected.columns and df_selected["Date"].notna().any()
    if use_date: agg_dict["Date"] = ["min", "max"]
    df_product = df_selected.groupby("Product Name").agg(agg_dict)
    if use_date: df_product.columns = ["Quantity", "Order", "Revenue", "Tanggal_Awal", "Tanggal_Akhir"]
    else: df_product.columns = ["Quantity", "Order", "Revenue"]
    df_product = df_product.reset_index()
    df_product["Harga_Rata_Rata"] = df_product["Revenue"] / df_product["Quantity"]
    df_product["Revenue_Per_Transaksi"] = df_product["Revenue"] / df_product["Order"]
    return df_product

def get_active_selected_data():
    active_metadata = get_active_dataset_metadata()
    if active_metadata is not None:
        cached_id = st.session_state.get("active_dataset_id")
        cached_df = st.session_state.get("df_selected")
        if cached_id == active_metadata["id"] and cached_df is not None and not cached_df.empty: return cached_df.copy(), active_metadata["name"]
        active_record = load_dataset_by_id(active_metadata["id"])
        if active_record is not None and not active_record["data"].empty:
            st.session_state.active_dataset_id = active_record["id"]
            st.session_state.df_selected = active_record["data"].copy()
            st.session_state.df_product = aggregate_product_data(active_record["data"])
            return active_record["data"].copy(), active_record["name"]

    st.session_state.active_dataset_id = None
    st.session_state.df_selected = None
    st.session_state.df_product = None
    df_db = load_sales_data_from_db()
    if df_db is not None and not df_db.empty:
        st.session_state.df_selected = df_db.copy()
        return df_db.copy(), "Data Upload Tersimpan"

    df_default = get_default_data()
    if df_default.empty: return None, "Tidak Ada Data"
    df_selected = preprocess_data(df_default)
    if df_selected is None or df_selected.empty: return None, "Data Default Tidak Valid"
    return df_selected, "Data Default k-means.xlsx"

def apply_date_filter(df_selected):
    df_selected = df_selected.copy()
    if "Date" not in df_selected.columns: return df_selected
    df_selected["Date"] = pd.to_datetime(df_selected["Date"], errors="coerce", dayfirst=True)
    if not df_selected["Date"].notna().any(): return df_selected.drop(columns=["Date"])
    df_selected = df_selected.dropna(subset=["Date"])
    min_date = df_selected["Date"].min()
    max_date = df_selected["Date"].max()
    if pd.isna(min_date) or pd.isna(max_date): return df_selected

    return df_selected

def get_active_selected_data_filtered():
    df_selected, sumber_data = get_active_selected_data()
    if df_selected is None or df_selected.empty: return None, sumber_data
    df_filtered = apply_date_filter(df_selected)
    if df_filtered is None or df_filtered.empty: return None, sumber_data
    return df_filtered, sumber_data

def get_active_product_data(with_filter=True):
    if with_filter: df_selected, sumber_data = get_active_selected_data_filtered()
    else: df_selected, sumber_data = get_active_selected_data()
    if df_selected is None or df_selected.empty: return None, sumber_data
    return aggregate_product_data(df_selected), sumber_data

def reset_analysis_results():
    st.session_state.clustering_result = None

def reset_date_filter_state():
    st.session_state.pop("tanggal_mulai_filter", None)
    st.session_state.pop("tanggal_akhir_filter", None)

def invalidate_stale_analysis(df_product):
    current_signature = build_data_signature(df_product)
    stale_found = False
    stored_result = st.session_state.get("clustering_result")
    if stored_result is not None and stored_result.get("data_signature") != current_signature:
        st.session_state.clustering_result = None
        stale_found = True
    return stale_found, current_signature

def get_valid_clustering_result():
    result = st.session_state.get("clustering_result")
    if result is None: return None
    df_selected = st.session_state.get("analysis_df_selected")
    if df_selected is None or df_selected.empty:
        df_selected, _ = get_active_selected_data()
    if df_selected is None or df_selected.empty:
        reset_analysis_results()
        return None
    df_product = aggregate_product_data(df_selected)
    if result.get("data_signature") != build_data_signature(df_product):
        reset_analysis_results()
        return None
    return result

# ============================================================
# SESSION STATE
# ============================================================

init_db()
if "login_status" not in st.session_state: st.session_state.login_status = False
if "username" not in st.session_state: st.session_state.username = None
if "role" not in st.session_state: st.session_state.role = None
if "df_selected" not in st.session_state: st.session_state.df_selected = None
if "df_product" not in st.session_state: st.session_state.df_product = None
if "active_dataset_id" not in st.session_state:
    active_record = get_active_dataset_metadata()
    st.session_state.active_dataset_id = active_record["id"] if active_record is not None else None
if "analysis_dataset_id" not in st.session_state: st.session_state.analysis_dataset_id = None
if "analysis_dataset_name" not in st.session_state: st.session_state.analysis_dataset_name = None
if "analysis_df_selected" not in st.session_state: st.session_state.analysis_df_selected = None
if "clustering_result" not in st.session_state: st.session_state.clustering_result = None

# ============================================================
# LOGIN PAGE
# ============================================================

def inject_login_css():
    st.markdown("""
    <style>
    header[data-testid="stHeader"] { background: transparent !important; }
    div[data-testid="stAppViewContainer"] .block-container {
        max-width: 900px !important; min-height: calc(100vh - 4rem) !important;
        padding-top: 0 !important; padding-bottom: 0 !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
    }
    div[data-testid="stVerticalBlock"]:has(.login-card-marker) {
        width: 100% !important; max-width: 760px !important; padding: 34px 48px !important;
        border-radius: 32px !important; background: rgba(15, 23, 42, 0.72) !important;
        border: 1px solid rgba(148, 163, 184, 0.22) !important;
        box-shadow: 0 32px 90px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.06) !important;
        backdrop-filter: blur(22px) !important; -webkit-backdrop-filter: blur(22px) !important;
    }
    .login-card-marker { display: none; }
    .login-logo { width: 72px; height: 72px; border-radius: 24px; margin: 0 auto 20px auto; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #2563eb, #14b8a6); box-shadow: 0 18px 42px rgba(37, 99, 235, 0.35); font-size: 35px; border: 1px solid rgba(255, 255, 255, 0.20); }
    .login-title { text-align: center; font-size: 28px; font-weight: 900; color: #f8fafc; letter-spacing: -0.045em; line-height: 1.25; margin-bottom: 10px; max-width: 620px; margin-left: auto; margin-right: auto; }
    .login-desc { text-align: center; color: #94a3b8; font-size: 15px; line-height: 1.7; margin-bottom: 26px; max-width: 620px; margin-left: auto; margin-right: auto; }
    div[data-testid="stForm"] { border: none !important; padding: 0 !important; background: transparent !important; }
    div[data-testid="stTextInput"] label { color: #cbd5e1 !important; font-weight: 700 !important; font-size: 14px !important; }
    div[data-testid="stTextInput"] div[data-baseweb="input"] { background: rgba(2, 6, 23, 0.72) !important; border: 1px solid rgba(148, 163, 184, 0.30) !important; border-radius: 15px !important; height: 52px !important; overflow: hidden !important; box-shadow: inset 0 1px 0 rgba(255,255,255,0.04) !important; padding-right: 0 !important; }
    div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within { border-color: #38bdf8 !important; box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.16) !important; }
    div[data-testid="stTextInput"] input { height: 52px !important; background: transparent !important; color: #f8fafc !important; border: none !important; padding: 0 15px !important; font-size: 15px !important; box-shadow: none !important; }
    div[data-testid="stTextInput"] input::placeholder { color: #64748b !important; }
    div[data-testid="stTextInput"] button { height: 52px !important; width: 56px !important; min-width: 56px !important; max-width: 56px !important; background: linear-gradient(135deg, #1e293b, #334155) !important; border: none !important; border-left: 1px solid rgba(148, 163, 184, 0.20) !important; border-radius: 0 15px 15px 0 !important; color: #f8fafc !important; box-shadow: none !important; margin: 0 !important; padding: 0 !important; display: flex !important; align-items: center !important; justify-content: center !important; }
    div[data-testid="stFormSubmitButton"] button { width: 100% !important; height: 52px !important; margin-top: 10px !important; border-radius: 15px !important; border: none !important; background: linear-gradient(135deg, #2563eb, #14b8a6) !important; color: #ffffff !important; font-size: 15px !important; font-weight: 850 !important; box-shadow: 0 16px 36px rgba(37, 99, 235, 0.28) !important; transition: 0.2s ease !important; }
    div[data-testid="stFormSubmitButton"] button:hover { transform: translateY(-1px); box-shadow: 0 20px 42px rgba(20, 184, 166, 0.30) !important; }
    </style>
    """, unsafe_allow_html=True)

def login_page():
    inject_login_css()
    st.markdown("""
    <div class="login-card-marker"></div>
    <div class="login-logo">👟</div>
    <div class="login-title">Dashboard Toko Sepatu Jakarta Barat</div>
    <div class="login-desc">Masuk untuk mengakses dashboard analisis penjualan, monitoring omzet, insight produk, dan clustering K-Means.</div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Masukkan username")
        password = st.text_input("Password", type="password", placeholder="Masukkan password")
        submit = st.form_submit_button("Login")
        if submit:
            user = login_user(username, password)
            if user:
                st.session_state.login_status = True
                st.session_state.username = user[1]
                st.session_state.role = user[2]
                st.success("Login berhasil.")
                st.rerun()
            else: st.error("Username atau password salah.")


# maps
def show_province_map(df_selected):

    if "Province" not in df_selected.columns:
        st.warning("Kolom Province tidak tersedia pada dataset aktif.")
        return

    # Mengambil data provinsi dan quantity
    provinsi_data = df_selected[
        ["Province", "Quantity"]
    ].copy()

    provinsi_data["Province"] = (
        provinsi_data["Province"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    provinsi_data["Quantity"] = pd.to_numeric(
        provinsi_data["Quantity"], errors="coerce"
    )

    provinsi_data = provinsi_data.dropna(
        subset=["Province", "Quantity"]
    )

    # Normalisasi nama provinsi
    province_mapping = {
        "D.I. ACEH": "ACEH",
        "CENTRAL JAVA": "JAWA TENGAH",
        "EAST JAVA": "JAWA TIMUR",
        "WEST JAVA": "JAWA BARAT",
        "CENTRAL KALIMANTAN": "KALIMANTAN TENGAH",
        "EAST KALIMANTAN": "KALIMANTAN TIMUR",
        "WEST KALIMANTAN": "KALIMANTAN BARAT",
        "SOUTH KALIMANTAN": "KALIMANTAN SELATAN",
        "NORTH KALIMANTAN": "KALIMANTAN UTARA",
        "CENTRAL SULAWESI": "SULAWESI TENGAH",
        "NORTH SULAWESI": "SULAWESI UTARA",
        "SOUTH SULAWESI": "SULAWESI SELATAN",
        "SOUTHEAST SULAWESI": "SULAWESI TENGGARA",
        "WEST SULAWESI": "SULAWESI BARAT",
        "NORTH SUMATRA": "SUMATERA UTARA",
        "SOUTH SUMATRA": "SUMATERA SELATAN",
        "WEST SUMATRA": "SUMATERA BARAT",
        "RIAU ISLANDS": "KEPULAUAN RIAU",
        "BANGKA BELITUNG": "KEPULAUAN BANGKA BELITUNG",
        "BANGKA BELITUNG ISLANDS": "KEPULAUAN BANGKA BELITUNG",
        "JAKARTA": "DKI JAKARTA",
        "JAKARTA RAYA": "DKI JAKARTA",
        "DAERAH KHUSUS IBUKOTA JAKARTA": "DKI JAKARTA",
        "YOGYAKARTA": "DAERAH ISTIMEWA YOGYAKARTA",
        "DI YOGYAKARTA": "DAERAH ISTIMEWA YOGYAKARTA",
        "D.I. YOGYAKARTA": "DAERAH ISTIMEWA YOGYAKARTA",
        "EAST NUSA TENGGARA": "NUSA TENGGARA TIMUR",
        "WEST NUSA TENGGARA": "NUSA TENGGARA BARAT",
        "NORTH MALUKU": "MALUKU UTARA",
        "WEST PAPUA": "PAPUA BARAT",
        "CENTRAL PAPUA": "PAPUA TENGAH",
        "SOUTH PAPUA": "PAPUA SELATAN",
        "SOUTHWEST PAPUA": "PAPUA BARAT DAYA",
        "HIGHLAND PAPUA": "PAPUA PEGUNUNGAN"
    }

    provinsi_data["Province"] = (
        provinsi_data["Province"].replace(province_mapping)
    )

    provinsi_data = provinsi_data[
        provinsi_data["Province"].notna()
        & provinsi_data["Province"].ne("")
    ]

    provinsi_data = (
        provinsi_data.groupby("Province", as_index=False)
        .agg(Total_Quantity=("Quantity", "sum"))
    )

    if provinsi_data.empty:
        st.warning("Data provinsi tidak tersedia.")
        return

    # Membaca file GeoJSON
    geojson_path = os.path.join(
        APP_DIR, "indonesia_provinces.geojson"
    )

    if not os.path.exists(geojson_path):
        st.error("File GeoJSON tidak ditemukan.")
        return

    with open(geojson_path, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    # Atribut dari file GeoJSON yang kamu kirim
    for feature in geojson_data["features"]:
        nama = feature["properties"]["PROVINSI"]
        feature["properties"]["PROVINSI"] = (
            str(nama).strip().upper()
        )

    nama_geojson = {
        feature["properties"]["PROVINSI"]
        for feature in geojson_data["features"]
    }

    tidak_cocok = provinsi_data[
        ~provinsi_data["Province"].isin(nama_geojson)
    ]

    if not tidak_cocok.empty:
        with st.expander("Provinsi yang belum cocok"):
            st.dataframe(tidak_cocok)

    cocok = provinsi_data[
        provinsi_data["Province"].isin(nama_geojson)
    ]

    if cocok.empty:
        st.warning("Tidak ada nama provinsi yang cocok.")
        return

    # Peta menggunakan MapLibre
    fig = px.choropleth_map(
        cocok,
        geojson=geojson_data,
        locations="Province",
        featureidkey="properties.PROVINSI",
        color="Total_Quantity",
        hover_name="Province",
        map_style="carto-darkmatter",
        center={"lat": -2.5, "lon": 118},
        zoom=3.4,
        opacity=0.85,
        color_continuous_scale=[
            "#1e3a8a",
            "#3b82f6",
            "#14b8a6"
        ],
        labels={
            "Total_Quantity": "Produk Terjual"
        }
    )

    fig.update_layout(
        height=520,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#e5e7eb"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )



# ============================================================
# DASHBOARD PAGE
# ============================================================

def dashboard_page():
    top_bar("Dashboard Overview", "Ringkasan kondisi penjualan dari Dataset Aktif saat ini.")

    df_selected, sumber_data = get_active_selected_data_filtered()
    if df_selected is None or df_selected.empty:
        st.error("Data tidak tersedia atau tidak dapat diproses.")
        return

    df_product = aggregate_product_data(df_selected)
    total_produk = df_product["Product Name"].nunique()
    total_quantity = df_selected["Quantity"].sum()
    total_revenue = df_selected["Revenue"].sum()
    total_order = df_selected["Order"].nunique()

    session_clustering = st.session_state.get("clustering_result")
    active_dataset_id = st.session_state.get("active_dataset_id")
    session_matches_active = False
    if session_clustering is not None:
        if active_dataset_id is not None:
            session_matches_active = (session_clustering.get("dataset_id") == active_dataset_id)
        else:
            session_matches_active = (session_clustering.get("dataset_id") is None and session_clustering.get("dataset_name") == "Data Default k-means.xlsx")

    clustering_for_filter = session_clustering if session_matches_active else load_latest_clustering_for_dataset(active_dataset_id)

    st.markdown(f'<span class="badge badge-green">Dataset Aktif: {safe_html(sumber_data)}</span>', unsafe_allow_html=True)

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1: metric_card("inventory_2", "Total Produk", format_number(total_produk), "Jenis produk yang laku")
    with kpi2: metric_card("shopping_cart", "Total Quantity Terjual", format_number(total_quantity), "unit")
    with kpi3: metric_card("payments", "Total Omzet", format_rupiah(total_revenue), "Total nilai penjualan setelah diskon")
    with kpi4: metric_card("receipt_long", "Total Transaksi", format_number(total_order), "Total pesanan yang masuk")

    # grafik maps
    with card_container():
        section_header(
            "Persebaran Produk Terjual Berdasarkan Provinsi",
            "Distribusi jumlah unit produk terjual "
            "berdasarkan provinsi tujuan pengiriman."
        )
    
        show_province_map(df_selected)

    chart_left, chart_right = st.columns(2)
    with chart_left:
        with card_container():
                    section_header("Top 10 Kota Berdasarkan Omzet", "10 Kota dengan total omzet tertinggi.")
                    if "Regency and City" in df_selected.columns:
                        kota_data = df_selected[["Regency and City", "Revenue"]].copy()
                        kota_data["Regency and City"] = kota_data["Regency and City"].astype("string").str.strip()
                        kota_data = kota_data.dropna(subset=["Regency and City", "Revenue"])
                        kota_data = kota_data[kota_data["Regency and City"].ne("")]
                        kota_data = kota_data[~kota_data["Regency and City"].str.lower().isin(["nan", "none", "null", "-"])]
        
                        top10_kota = (
                            kota_data.groupby("Regency and City", as_index=False)["Revenue"]
                            .sum()
                            .rename(columns={"Revenue": "Total_Omzet"})
                            .nlargest(10, "Total_Omzet")
                            .sort_values("Total_Omzet")
                        )
                        if not top10_kota.empty:
                            kota_fig = px.bar(
                                top10_kota, x="Total_Omzet", y="Regency and City",
                                orientation="h", color="Total_Omzet",
                                color_continuous_scale=["#1e3a8a", "#3b82f6", "#14b8a6"],
                                labels={"Total_Omzet": "Omzet (Rp)", "Regency and City": "Kota"},
                            )
                            kota_fig.update_layout(
                                xaxis_title="Omzet (Rp)", yaxis_title="Kota",
                                coloraxis_showscale=False,
                                margin=dict(l=16, r=12, t=18, b=20),
                            )
                            kota_fig.update_yaxes(tickfont=dict(size=10), automargin=True)
                            show_plotly(kota_fig, height=350, showlegend=False)
                        else:
                            st.info("Data kota masih kosong. Periksa kolom Regency and City pada file Excel.")
                    else:
                        st.info("Kolom kota belum tersedia pada dataset aktif. Upload ulang file Excel yang memiliki kolom Regency and City.")
    with chart_right:
        with card_container():
            section_header("Top 10 Produk Terjual", "10 Produk dengan jumlah terjual tertinggi.")
            top10_quantity = df_product.sort_values("Quantity", ascending=False).head(10)
            quantity_fig = px.bar(top10_quantity.sort_values("Quantity"), x="Quantity", y="Product Name", orientation="h", color="Quantity", color_continuous_scale=["#1e3a8a", "#3b82f6", "#14b8a6"])
            quantity_fig.update_layout(xaxis_title="Quantity", yaxis_title="Produk", coloraxis_showscale=False, margin=dict(l=16, r=12, t=18, b=20))
            quantity_fig.update_yaxes(tickfont=dict(size=10), automargin=True)
            show_plotly(quantity_fig, height=350, showlegend=False)


    if clustering_for_filter is not None:
        df_result = clustering_for_filter["df_result"]
        color_map = {
            "Cluster Sangat Tinggi": "#15803d", "Cluster Tinggi": COLOR_GREEN,
            "Cluster Menengah Atas": "#65a30d", "Cluster Sedang": COLOR_YELLOW,
            "Cluster Menengah Bawah": "#f59e0b", "Cluster Rendah": COLOR_RED,
            "Cluster Sangat Rendah": "#991b1b"
        }
        
        c_left, c_right = st.columns(2)
        with c_left:
            with card_container():
                section_header("Distribusi Cluster", "Menampilkan jumlah produk pada setiap kategori penjualan berdasarkan hasil pengelompokan K-Means.")
                cluster_count = df_result["Kategori_Cluster"].value_counts().rename_axis("Kategori_Cluster").reset_index(name="Jumlah")
                distribution_cluster = px.bar(cluster_count, x="Kategori_Cluster", y="Jumlah", text="Jumlah", color="Kategori_Cluster", color_discrete_map=color_map)
                distribution_cluster.update_xaxes(tickangle=-25, automargin=True)
                show_plotly(distribution_cluster, height=320, showlegend=False)
        with c_right:
            with card_container():
                section_header("Omzet per Cluster", "Menampilkan total omzet yang dihasilkan dari setiap kategori produk berdasarkan hasil pengelompokan K-Means.")
                revenue_cluster = df_result.groupby("Kategori_Cluster")["Revenue"].sum().reset_index().sort_values("Revenue", ascending=False)
                revenue_cluster_fig = px.bar(revenue_cluster, x="Kategori_Cluster", y="Revenue", text="Revenue", color="Kategori_Cluster", color_discrete_map=color_map, labels={"Kategori_Cluster": "Kategori Cluster", "Revenue": "Omzet (Rp)"})
                revenue_cluster_fig.update_xaxes(tickangle=-25, automargin=True)
                show_plotly(revenue_cluster_fig, height=320, showlegend=False)

 # tren penjualan
    chart_left, chart_right = st.columns(2)
    with chart_left:
        with card_container():
                    section_header("Tren Omzet Penjualan", "Perkembangan omzet penjualan berdasarkan tanggal.")
                    if "Date" in df_selected.columns:
                        df_trend = df_selected.copy()
                        df_trend["Date"] = pd.to_datetime(df_trend["Date"], errors="coerce")
                        df_trend = df_trend.dropna(subset=["Date"])
                        if not df_trend.empty:
                            trend_revenue = df_trend.groupby(df_trend["Date"].dt.date).agg(Total_Revenue=("Revenue", "sum")).reset_index()
                            trend_fig = px.line(trend_revenue, x="Date", y="Total_Revenue", markers=True, labels={"Date": "Tanggal", "Total_Revenue": "Omzet (Rp)"})
                            show_plotly(trend_fig, height=305, showlegend=False)
    
    with chart_right:
        with card_container():
            section_header(
                "Distribusi Metode Pembayaran",
                "Persentase penggunaan metode pembayaran berdasarkan jumlah pesanan."
            )

            if "Payment Method" in df_selected.columns:

                payment_data = df_selected[
                    ["Payment Method", "Order"]
                ].copy()

                payment_data["Payment Method"] = (
                    payment_data["Payment Method"]
                    .astype("string")
                    .str.strip()
                )

                payment_data = payment_data.dropna(
                    subset=["Payment Method", "Order"]
                )

                payment_data = payment_data[
                    ~payment_data["Payment Method"].str.lower().isin(
                        ["", "nan", "none", "null", "-"]
                    )
                ]

                if not payment_data.empty:

                    payment_summary = (
                        payment_data
                        .groupby("Payment Method", as_index=False)
                        .agg(Jumlah_Pesanan=("Order", "nunique"))
                        .sort_values("Jumlah_Pesanan", ascending=False)
                    )

                    fig_payment = px.pie(
                        payment_summary,
                        names="Payment Method",
                        values="Jumlah_Pesanan",
                        hole=0,
                        color_discrete_sequence=CHART_COLORS
                    )

                    fig_payment.update_traces(
                        textinfo="percent",
                        textposition="inside",
                        hovertemplate=(
                            "%{label}<br>"
                            "Pesanan: %{value}<br>"
                            "Persentase: %{percent}"
                            "<extra></extra>"
                        )
                    )

                    fig_payment.update_layout(
                        legend_title_text="Metode Pembayaran",
                        margin=dict(l=10, r=10, t=20, b=20)
                    )

                    show_plotly(
                        fig_payment,
                        height=305,
                        showlegend=True
                    )

                else:
                    st.info("Data metode pembayaran belum tersedia.")

            else:
                st.info(
                    "Kolom Payment Method belum tersedia pada dataset aktif."
                )

                

    
    if st.session_state.role == "admin" and clustering_for_filter is not None:
        with card_container():
            section_header("Insight Hasil Clustering", "Rekomendasi berdasarkan segmentasi produk.")
            df_result_admin = clustering_for_filter["df_result"]
            for category in get_cluster_order(clustering_for_filter["k"]):
                if category in df_result_admin["Kategori_Cluster"].values:
                    cluster_df = df_result_admin[df_result_admin["Kategori_Cluster"] == category]
                    rekomendasi = cluster_df["Rekomendasi"].dropna().iloc[0] if not cluster_df["Rekomendasi"].dropna().empty else "-"
                    st.markdown(f"**{category} ({len(cluster_df)} Produk):** {rekomendasi}")


# ============================================================
# CLUSTERING PAGE 
# ============================================================

def upload_page():
    top_bar("Clustering", "Upload, validasi dataset, dan jalankan clustering dengan mudah.")

    if st.session_state.role not in ["owner", "admin"]:
        st.error("Fitur ini hanya dapat diakses oleh Owner atau Admin.")
        return

    with card_container():
        section_header("Upload & Validasi Dataset", "Fitur yang digunakan: Quantity, Order, dan Omzet")
        uploaded_file = st.file_uploader("Pilih file data penjualan", type=["csv", "xlsx"], key="combined_upload_file")
        make_active = st.toggle("Gunakan dataset ini sebagai Dataset Aktif di Dashboard", value=True)
        process_upload = st.button("Upload & Validasi Dataset", disabled=uploaded_file is None)

            #Extract
            # Tahap Extract mengambil data dari file CSV atau Excel.
        if process_upload and uploaded_file is not None:
            df_raw = load_uploaded_file(uploaded_file)
            if df_raw is not None:
                df_selected = preprocess_data(df_raw)
                if df_selected is not None and not df_selected.empty:
                    # lOAD : disimpan ke tabel datasets di SQLite.
                    dataset_id = save_dataset_history(df_selected, uploaded_file.name, st.session_state.username, make_active=make_active)
                    st.session_state.analysis_dataset_id = dataset_id
                    st.session_state.analysis_dataset_name = uploaded_file.name
                    st.session_state.analysis_df_selected = df_selected.copy()
                    reset_analysis_results()
                    
                    if make_active:
                        st.session_state.active_dataset_id = dataset_id
                        st.session_state.df_selected = df_selected.copy()
                        st.session_state.df_product = aggregate_product_data(df_selected)
                        reset_date_filter_state()
                    st.success("✓ Dataset berhasil divalidasi dan disimpan.")
                else:
                    st.error("Gagal memproses data.")

    analysis_df = st.session_state.get("analysis_df_selected")
    analysis_dataset_name = st.session_state.get("analysis_dataset_name")

    if analysis_df is None or analysis_df.empty:
        analysis_df, analysis_dataset_name = get_active_selected_data()

    if analysis_df is not None and not analysis_df.empty:
        df_product = aggregate_product_data(analysis_df)
        with card_container():
            section_header("Jalankan Clustering", f"Dataset saat ini: {analysis_dataset_name}")
            
            # Pilihan Nilai K interaktif sebelum menjalankan clustering
            selected_k = st.slider("Tentukan Jumlah Cluster (K)", min_value=2, max_value=6, value=3, step=1, key="input_k_slider")
            
            if st.button("Jalankan Clustering"):
                if run_clustering(df_product, selected_k, dataset_id=st.session_state.get("analysis_dataset_id"), dataset_name=analysis_dataset_name, save_history=True):
                    st.success("✓ Clustering berhasil")

        result = st.session_state.get("clustering_result")
        if result is not None:
            with card_container():
                section_header("Ringkasan Hasil Clustering", "Hasil segmentasi produk")
                df_res = result["df_result"]
                
                counts = df_res["Kategori_Cluster"].value_counts()
                st.caption(f"Jumlah cluster (K): {result['k']}. Kategori diurutkan berdasarkan performa relatif Quantity, Order, dan Omzet.")
                for category in get_cluster_order(result["k"]):
                    if category in counts.index:
                        st.markdown(f"- **{category}**: {int(counts[category])} produk")

                col_down, col_exp, col_spacer = st.columns([1, 1, 5.8])
                with col_down:
                    report_html = build_clustering_report_html(result, analysis_dataset_name)
                    st.download_button(
                        "Export Laporan",
                        data=report_html.encode("utf-8"),
                        file_name="clustering_report.html",
                        mime="text/html"
                    )
                with col_exp:
                    st.download_button(
                    "Download CSV",
                        data=df_res.to_csv(index=False).encode("utf-8"),
                        file_name="hasil_clustering_penjualan.csv",
                        mime="text/csv"
                    )

# ============================================================
# INSIGHT PAGE (Owner only)
# ============================================================

def insight_page():
    top_bar("Insight & Recommendation", "Interpretasi bisnis dan tindakan yang disarankan untuk setiap cluster.")

    result = get_valid_clustering_result()
    if result is None:
        st.warning("Belum ada hasil clustering yang valid. Jalankan K-Means melalui halaman Clustering.")
        return

    df_result = result["df_result"]
    preferred_order = get_cluster_order(result["k"])
    available_categories = list(df_result["Kategori_Cluster"].dropna().unique())
    ordered_categories = [cat for cat in preferred_order if cat in available_categories] + [cat for cat in available_categories if cat not in preferred_order]

    if not ordered_categories:
        st.info("Kategori cluster belum tersedia.")
        return

    cluster_columns = st.columns(min(3, len(ordered_categories)))

    for index, category in enumerate(ordered_categories):
        cluster_df = df_result[df_result["Kategori_Cluster"] == category].copy()
        top_product = cluster_df.sort_values("Revenue", ascending=False).iloc[0]
        recommendation = (cluster_df["Rekomendasi"].dropna().astype(str).iloc[0] if cluster_df["Rekomendasi"].notna().any() else "Lakukan analisis lanjutan terhadap kelompok produk ini.")

        if category in ["Cluster Sangat Tinggi", "Cluster Tinggi"]: accent_class = "cluster-high"
        elif category in ["Cluster Menengah Atas", "Cluster Sedang", "Cluster Menengah Bawah"]: accent_class = "cluster-medium"
        elif category in ["Cluster Rendah", "Cluster Sangat Rendah"]: accent_class = "cluster-low"
        else: accent_class = "cluster-default"

        insight_text = f"{len(cluster_df)} produk menghasilkan {format_number(cluster_df['Quantity'].sum())} unit dan {format_rupiah(cluster_df['Revenue'].sum())}. Produk utama: {top_product['Product Name']}."

        with cluster_columns[index % len(cluster_columns)]:
            st.markdown(f"""
            <div class="cluster-insight-card {accent_class}">
                <div class="cluster-insight-title">{safe_html(category)}</div>
                <div class="cluster-insight-label">Insight</div>
                <div class="cluster-insight-text">{safe_html(insight_text)}</div>
                <div class="cluster-insight-label">Recommendation</div>
                <div class="cluster-insight-text">{safe_html(recommendation)}</div>
            </div>
            """, unsafe_allow_html=True)


# ============================================================
# RIWAYAT DATASET
# ============================================================

def dataset_history_page():
    top_bar("Riwayat Dataset", "Lihat, aktifkan, unduh, dan kelola dataset yang pernah diunggah.")
    history_df = get_dataset_history()

    with card_container():
        section_header("Dataset Aktif", "Dashboard selalu membaca dataset yang berstatus aktif.")
        active_record = get_active_dataset_record()
        if active_record is None: st.info("Dataset aktif: Data Default k-means.xlsx")
        else: st.success(f"Dataset aktif: {active_record['name']}")

        if st.button("Gunakan Data Default k-means.xlsx", key="use_default_dataset"):
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE datasets SET is_active=0")
                conn.commit()

            except Exception:
                conn.rollback()
                raise

            finally:
                cursor.close()
                conn.close()
            clear_sales_data_db()
            st.session_state.active_dataset_id = None
            st.session_state.df_selected = None
            st.session_state.df_product = None
            st.session_state.analysis_dataset_id = None
            st.session_state.analysis_dataset_name = None
            st.session_state.analysis_df_selected = None
            reset_analysis_results()
            reset_date_filter_state()
            st.success("Dashboard kembali menggunakan Data Default k-means.xlsx.")
            st.rerun()

    if history_df.empty:
        st.info("Belum ada riwayat dataset upload.")
        return

    display_df = history_df.copy()
    display_df["Status"] = display_df["is_active"].map({1: "Aktif", 0: "Tidak Aktif"})
    display_df = display_df.rename(columns={"id": "ID", "name": "Nama Dataset", "uploaded_at": "Tanggal Upload", "uploaded_by": "Pengguna"})

    with card_container():
        section_header("Daftar Dataset", "Seluruh upload tersimpan dan dapat dipakai kembali.")
        interactive_table(display_df[["ID", "Nama Dataset", "Tanggal Upload", "Pengguna", "Status"]], key="dataset_history_table", page_size=10, default_sort="Tanggal Upload")

    dataset_options = {f"#{row.id} - {row.name} ({row.uploaded_at})": row.id for row in history_df.itertuples(index=False)}
    selected_label = st.selectbox("Pilih Dataset", list(dataset_options.keys()), key="dataset_history_select")
    selected_id = dataset_options[selected_label]
    record = load_dataset_by_id(selected_id)

    if record is None:
        st.error("Dataset tidak ditemukan.")
        return

    with card_container():
        section_header("Detail Dataset", record["name"])
        interactive_table(record["data"].rename(columns={"Revenue": "Omzet"}), key=f"dataset_detail_{selected_id}", page_size=10)

        col_analysis, col_activate, col_download, col_delete, col_spacer = st.columns([1.4, 1.4, 1.3, 1.6, 4], gap=None)
        with col_analysis:
            if st.button("Analisis Dataset", key=f"analyze_dataset_{selected_id}"):
                if use_dataset_for_analysis(selected_id): st.success("Dataset dipilih untuk analisis tanpa mengubah Dataset Aktif Dashboard.")
        with col_activate:
            if st.button("Aktifkan Dataset", key=f"activate_dataset_{selected_id}"):
                if activate_dataset(selected_id):
                    st.success("Dataset berhasil dijadikan Dataset Aktif Dashboard.")
                    st.rerun()
        with col_download:
            st.download_button("Download CSV", data=record["data"].to_csv(index=False).encode("utf-8"), file_name=f"dataset_{selected_id}.csv", mime="text/csv", key=f"download_dataset_{selected_id}")
        with col_delete:
            if st.session_state.role == "owner":
                confirm_delete = st.checkbox("Konfirmasi hapus", key=f"confirm_delete_dataset_{selected_id}")
                if st.button("Hapus Dataset", key=f"delete_dataset_{selected_id}", disabled=not confirm_delete):
                    if delete_dataset_history(selected_id):
                        st.success("Dataset berhasil dihapus.")
                        st.rerun()


# ============================================================
# RIWAYAT CLUSTERING
# ============================================================

def clustering_history_page():
    top_bar("Riwayat Hasil Clustering", "Buka, download, dan kelola hasil clustering terdahulu.")
    history_df = get_clustering_history()

    if history_df.empty:
        st.info("Belum ada riwayat hasil clustering.")
        return

    display_df = history_df.rename(columns={"id": "ID", "clustered_at": "Tanggal Clustering", "dataset_name": "Dataset", "clustered_by": "Pengguna", "k": "Nilai K", "silhouette": "Silhouette Score", "dbi": "Davies-Bouldin Index"})
    with card_container():
        section_header("Daftar Riwayat", "Daftar hasil proses clustering yang telah disimpan.")
        interactive_table(display_df[["ID", "Tanggal Clustering", "Dataset", "Pengguna", "Nilai K", "Silhouette Score", "Davies-Bouldin Index"]], key="clustering_history_table", page_size=10, default_sort="Tanggal Clustering")

    history_options = {f"#{row.id} - {row.dataset_name} | k={row.k} | {row.clustered_at}": row.id for row in history_df.itertuples(index=False)}
    selected_label = st.selectbox("Pilih data yang ingin dilihat", ["Pilih data"] + list(history_options.keys()), key="clustering_history_select")

    if selected_label == "Pilih data": return
    record = load_clustering_history_by_id(history_options[selected_label])

    if record is None:
        st.warning("Data riwayat tidak ditemukan.")
        return

    with card_container():
        section_header(f"Hasil Clustering #{record['id']}", f"{record['dataset_name']} - {record['clustered_at']}")
        interactive_table(record["df_result"].rename(columns={"Revenue": "Omzet", "Revenue_Per_Transaksi": "Omzet per Transaksi"}), key=f"clustering_history_detail_{record['id']}", page_size=10, default_sort="Omzet")
        col_download, col_action, col_space = st.columns([1.3, 2.0, 3.2], gap="small")
        with col_download:
            st.download_button("Download Hasil CSV", data=record["df_result"].to_csv(index=False).encode("utf-8"), file_name=f"hasil_clustering_{record['id']}.csv", mime="text/csv", key=f"download_history_{record['id']}")
        with col_action:
            if st.session_state.role == "owner":
                confirm_key = f"confirm_delete_history_{record['id']}"
                col_confirm, col_delete = st.columns([1.2, 1], gap="small")
                with col_confirm: confirm_delete = st.checkbox("Konfirmasi hapus", key=confirm_key)
                with col_delete:
                    if st.button("Hapus Riwayat", key=f"delete_history_{record['id']}", disabled=not confirm_delete):
                        if delete_clustering_history(record["id"]):
                            st.success("Riwayat clustering berhasil dihapus.")
                            st.rerun()


# ============================================================
# USER MANAGEMENT PAGE
# ============================================================

def user_management_page():
    top_bar("Manajemen User", "Owner dapat menambahkan akun admin baru dan menghapus pengguna.")

    if st.session_state.role != "owner":
        st.error("Halaman ini hanya dapat diakses oleh owner.")
        return

    with card_container():
        section_header("Tambah User Admin", "Owner dapat menambahkan akun baru dengan role admin.")
        with st.form("add_admin_form"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Simpan")
            if submit:
                if new_username.strip() == "" or new_password.strip() == "": st.error("Username dan password tidak boleh kosong.")
                else:
                    success = add_user(new_username, new_password, "admin")
                    if success: st.success("User admin berhasil ditambahkan.")
                    else: st.error("Username sudah digunakan.")

    with card_container():
        section_header("Daftar User", "Daftar pengguna yang tersimpan dalam database.")
        df_users = get_all_users()
        show_table(df_users)
        
        st.markdown("### Hapus User")
        user_options = {f"{row.username} ({row.role})": row.id for row in df_users.itertuples(index=False)}
        selected_user = st.selectbox("Pilih pengguna yang akan dihapus", list(user_options.keys()))
        
        if st.button("Hapus Pengguna"):
            if delete_user(user_options[selected_user]):
                st.success(f"Pengguna {selected_user} berhasil dihapus.")
                st.rerun()
            else:
                st.error("Gagal menghapus pengguna.")


# ============================================================
# SIDEBAR MENU ROUTING
# ============================================================

def sidebar_menu():
    role_badge = "badge-owner" if st.session_state.role == "owner" else "badge-admin"
    safe_username = safe_html(st.session_state.username)
    safe_role = safe_html(str(st.session_state.role).upper())

    st.sidebar.markdown(f"""
    <div class="sidebar-brand">
        <div class="sidebar-brand-icon">
            <span class="material-symbols-rounded">monitoring</span>
        </div>
        <div>
            <div class="sidebar-brand-title">TOKO SJB</div>
            <div class="sidebar-brand-subtitle">K-Means Dashboard BI</div>
        </div>
    </div>
    <div class="user-box">
        <div class="user-avatar">
            <span class="material-symbols-rounded">person</span>
            <span class="online-indicator"></span>
        </div>
        <div class="user-details">
            <div class="user-caption">Logged in as</div>
            <div class="user-name">{safe_username}</div>
            <span class="{role_badge}">{safe_role}</span>
        </div>
    </div>
    <div class="sidebar-section-label">Navigation</div>
    """, unsafe_allow_html=True)

    menus = [
        ("Dashboard", "Dashboard"),
        ("Clustering", "Clustering"),
        ("Dataset History", "Riwayat Dataset"),
        ("Clustering History", "Riwayat Clustering")
    ]

    if st.session_state.role == "owner":
        menus.insert(2, ("Insights", "Insight"))
        menus.append(("User Management", "Manajemen User"))

    menu_labels = [display_name for display_name, route_name in menus]
    menu_names = [route_name for display_name, route_name in menus]

    selected_label = st.sidebar.radio("Navigasi", menu_labels, label_visibility="collapsed", key="main_sidebar_navigation")
    selected_name = menu_names[menu_labels.index(selected_label)]

    st.sidebar.markdown('<div class="account-divider"></div><div class="sidebar-section-label">Account</div>', unsafe_allow_html=True)

    if st.sidebar.button("Logout", key="sidebar_logout_button"):
        st.session_state.login_status = False
        st.session_state.username = None
        st.session_state.role = None
        st.session_state.df_selected = None
        st.session_state.df_product = None
        st.session_state.analysis_df_selected = None
        st.session_state.analysis_dataset_id = None
        st.session_state.analysis_dataset_name = None
        reset_analysis_results()
        st.rerun()

    return selected_name


# ============================================================
# MAIN APP
# ============================================================

if not st.session_state.login_status:
    login_page()
else:
    page = sidebar_menu()

    if page == "Dashboard": dashboard_page()
    elif page == "Clustering": upload_page()
    elif page == "Insight": insight_page()
    elif page == "Riwayat Dataset": dataset_history_page()
    elif page == "Riwayat Clustering": clustering_history_page()
    elif page == "Manajemen User": user_management_page()