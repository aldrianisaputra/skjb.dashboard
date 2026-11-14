import streamlit as st
import pandas as pd
import numpy as np
# mengintegrasi dari sqlite3 ke mysql
import re
import html
from contextlib import contextmanager


# import config.py
# import database.connection sebagai db_conn
from database.connection import get_connection
# import database.repository sebagai db_repo
from database.repository import init_db, login_user, add_user, get_all_users, delete_user, save_sales_data_to_db, load_sales_data_from_db, clear_sales_data_db, save_dataset_history, get_dataset_history, load_dataset_by_id, get_active_dataset_record, get_active_dataset_metadata, get_clustering_history, load_clustering_history_by_id, delete_clustering_history, get_cluster_order, set_active_dataset, delete_dataset_by_id
from processing.data_loader import (
    get_default_data,
    load_uploaded_file,
    normalize_column_key,
    clean_column_names,
    COLUMN_CANDIDATE_GROUPS
)

from processing.clustering import build_data_signature, run_clustering

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
from views import other_pages
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


# ============================================================
# INSIGHT PAGE (Owner only)
# ============================================================



# ============================================================
# RIWAYAT DATASET
# ============================================================



# ============================================================
# RIWAYAT CLUSTERING
# ============================================================



# ============================================================
# USER MANAGEMENT PAGE
# ============================================================



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
    elif page == "Clustering": other_pages.upload_page(aggregate_product_data=aggregate_product_data, build_clustering_report_html=build_clustering_report_html, card_container=card_container, get_active_selected_data=get_active_selected_data, get_cluster_order=get_cluster_order, load_uploaded_file=load_uploaded_file, preprocess_data=preprocess_data, reset_analysis_results=reset_analysis_results, reset_date_filter_state=reset_date_filter_state, run_clustering=run_clustering, save_dataset_history=save_dataset_history, section_header=section_header, st=st, top_bar=top_bar)
    elif page == "Insight": other_pages.insight_page(format_number=format_number, format_rupiah=format_rupiah, get_cluster_order=get_cluster_order, get_valid_clustering_result=get_valid_clustering_result, safe_html=safe_html, st=st, top_bar=top_bar)
    elif page == "Riwayat Dataset": other_pages.dataset_history_page(activate_dataset=activate_dataset, card_container=card_container, clear_sales_data_db=clear_sales_data_db, delete_dataset_history=delete_dataset_history, get_active_dataset_record=get_active_dataset_record, get_connection=get_connection, get_dataset_history=get_dataset_history, interactive_table=interactive_table, load_dataset_by_id=load_dataset_by_id, reset_analysis_results=reset_analysis_results, reset_date_filter_state=reset_date_filter_state, section_header=section_header, st=st, top_bar=top_bar, use_dataset_for_analysis=use_dataset_for_analysis)
    elif page == "Riwayat Clustering": other_pages.clustering_history_page(card_container=card_container, delete_clustering_history=delete_clustering_history, get_clustering_history=get_clustering_history, interactive_table=interactive_table, load_clustering_history_by_id=load_clustering_history_by_id, section_header=section_header, st=st, top_bar=top_bar)
    elif page == "Manajemen User": other_pages.user_management_page(add_user=add_user, card_container=card_container, delete_user=delete_user, get_all_users=get_all_users, section_header=section_header, show_table=show_table, st=st, top_bar=top_bar)