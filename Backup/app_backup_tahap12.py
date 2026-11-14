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
    build_clustering_report_html,
    safe_html,
)
from views.dashboard import dashboard_page
from utils.styles import (
    inject_main_css,
    inject_login_css,
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
inject_main_css()


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



# ============================================================
# DASHBOARD PAGE
# ============================================================



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

    if page == "Dashboard": dashboard_page(get_active_selected_data_filtered, aggregate_product_data, show_plotly, card_container, section_header, metric_card, top_bar)
    elif page == "Clustering": upload_page()
    elif page == "Insight": insight_page()
    elif page == "Riwayat Dataset": dataset_history_page()
    elif page == "Riwayat Clustering": clustering_history_page()
    elif page == "Manajemen User": user_management_page()