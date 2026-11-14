import streamlit as st
import pandas as pd
import os
import io
import re
import zipfile
import posixpath
import xml.etree.ElementTree as ET

from collections import defaultdict
from config import DEFAULT_FILE

def _source_to_bytes(source):
    if isinstance(source, (bytes, bytearray)): return bytes(source)
    with open(source, "rb") as file: return file.read()
    
XLSX_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
XLSX_DOCUMENT_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

def _normalize_xlsx_archive_path(target):
    target = str(target).replace("\\", "/")
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join("xl", target))

def _excel_column_to_index(column_letters):
    col_idx = 0
    for char in str(column_letters).upper(): col_idx = (col_idx * 26 + (ord(char) - ord("A") + 1))
    return col_idx - 1

def _make_unique_headers(header_values):
    headers = []
    occurrence = {}
    for idx, val in enumerate(header_values):
        base_name = f"Unnamed: {idx}" if val is None or str(val).strip() == "" else str(val).strip()
        count = occurrence.get(base_name, 0)
        unique_name = base_name if count == 0 else f"{base_name}.{count}"
        occurrence[base_name] = count + 1
        headers.append(unique_name)
    return headers

def _read_xlsx_shared_strings(zip_file):
    shared_strings_path = "xl/sharedStrings.xml"
    if shared_strings_path not in zip_file.namelist(): return []
    root = ET.fromstring(zip_file.read(shared_strings_path))
    shared_strings = []
    for string_item in root.findall(f"{{{XLSX_MAIN_NS}}}si"):
        text_parts = [t.text or "" for t in string_item.iter(f"{{{XLSX_MAIN_NS}}}t")]
        shared_strings.append("".join(text_parts))
    return shared_strings

def _read_xlsx_cell_value(cell, shared_strings):
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        text_parts = [t.text or "" for t in cell.iter(f"{{{XLSX_MAIN_NS}}}t")]
        return "".join(text_parts)
    value_node = cell.find(f"{{{XLSX_MAIN_NS}}}v")
    if value_node is None:
        text_parts = [t.text or "" for t in cell.iter(f"{{{XLSX_MAIN_NS}}}t")]
        return "".join(text_parts) if text_parts else None
    raw_value = value_node.text or ""
    if cell_type == "s":
        try: return shared_strings[int(raw_value)]
        except (ValueError, IndexError): return raw_value
    if cell_type in {"str", "e"}: return raw_value
    if cell_type == "b": return raw_value == "1"
    try:
        numeric_value = float(raw_value)
        if numeric_value.is_integer(): return int(numeric_value)
        return numeric_value
    except (TypeError, ValueError): return raw_value

@st.cache_data(show_spinner=False, max_entries=8)
def read_excel_xml_matrices(file_bytes):
    worksheets = {}
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zip_file:
            workbook_root = ET.fromstring(zip_file.read("xl/workbook.xml"))
            relationship_root = ET.fromstring(zip_file.read("xl/_rels/workbook.xml.rels"))
            relationship_map = {}
            for rel in relationship_root:
                r_id = rel.attrib.get("Id")
                r_target = rel.attrib.get("Target")
                if r_id and r_target: relationship_map[r_id] = _normalize_xlsx_archive_path(r_target)
            shared_strings = _read_xlsx_shared_strings(zip_file)
            sheets_element = workbook_root.find(f"{{{XLSX_MAIN_NS}}}sheets")
            if sheets_element is None: return worksheets
            for sheet_element in sheets_element:
                sheet_name = sheet_element.attrib.get("name")
                r_id = sheet_element.attrib.get(f"{{{XLSX_DOCUMENT_REL_NS}}}id")
                ws_path = relationship_map.get(r_id)
                if not sheet_name or not ws_path or ws_path not in zip_file.namelist(): continue
                worksheet_root = ET.fromstring(zip_file.read(ws_path))
                row_values = defaultdict(dict)
                max_row = 0
                max_col = -1
                for cell in worksheet_root.iter(f"{{{XLSX_MAIN_NS}}}c"):
                    ref = cell.attrib.get("r", "")
                    match = re.match(r"([A-Z]+)(\d+)$", ref)
                    if match is None: continue
                    c_letters = match.group(1)
                    r_num = int(match.group(2))
                    c_idx = _excel_column_to_index(c_letters)
                    row_values[r_num][c_idx] = _read_xlsx_cell_value(cell, shared_strings)
                    max_row = max(max_row, r_num)
                    max_col = max(max_col, c_idx)
                if max_row == 0 or max_col < 0: continue
                matrix = []
                for r_num in range(1, max_row + 1):
                    row = [None] * (max_col + 1)
                    for c_idx, val in row_values.get(r_num, {}).items(): row[c_idx] = val
                    matrix.append(row)
                worksheets[sheet_name] = matrix
    except Exception: return {}
    return worksheets

@st.cache_data(show_spinner=False, max_entries=16)
def _cached_excel_sheet_names(file_bytes):
    try: return list(pd.ExcelFile(io.BytesIO(file_bytes)).sheet_names)
    except Exception: return []

@st.cache_data(show_spinner=False, max_entries=16)
def _cached_read_excel_raw(file_bytes, sheet_name):
    return pd.read_excel(
        io.BytesIO(file_bytes),
        sheet_name=sheet_name,
        header=None,
        dtype=object
    )

def dataframe_from_raw_excel(raw_dataframe, header_row):
    if raw_dataframe is None or raw_dataframe.empty or header_row < 0 or header_row >= len(raw_dataframe): return None
    headers = _make_unique_headers(raw_dataframe.iloc[header_row].tolist())
    dataframe = raw_dataframe.iloc[header_row + 1:].copy()
    dataframe.columns = headers
    return clean_loaded_dataframe(dataframe.reset_index(drop=True))

def dataframe_from_excel_matrix(matrix, header_row):
    if matrix is None or len(matrix) <= header_row or header_row < 0: return None
    header_values = matrix[header_row]
    if not header_values: return None
    headers = _make_unique_headers(header_values)
    data_rows = matrix[header_row + 1:]
    if not data_rows: return None
    return clean_loaded_dataframe(pd.DataFrame(data_rows, columns=headers))

def read_excel_sales_source(source, source_label):
    try: file_bytes = _source_to_bytes(source)
    except Exception as error:
        st.error(f"{source_label} tidak dapat dibuka: {error}")
        return None

    sheet_names = _cached_excel_sheet_names(file_bytes)
    if not sheet_names:
        xml_worksheets = read_excel_xml_matrices(file_bytes)
        sheet_names = list(xml_worksheets.keys())
    if not sheet_names:
        st.error(f"Tidak ada sheet yang dapat dibaca dari {source_label}.")
        return None

    def is_order_sku_sheet(sheet_name):
        ns = normalize_column_key(sheet_name).replace(" ", "")
        return ns == "orderskulist" or "ordersku" in ns or "skuorder" in ns

    order_sku_sheet = next((s for s in sheet_names if is_order_sku_sheet(s)), None)
    ordered_sheets = []
    if order_sku_sheet is not None: ordered_sheets.append(order_sku_sheet)
    ordered_sheets.extend(s for s in sheet_names if s != order_sku_sheet)

    inspected_candidates = []
    valid_candidates = []

    def evaluate_candidate(candidate_df, sheet_name, header_row, sheet_index, reader_type):
        candidate_df = clean_loaded_dataframe(candidate_df)
        if candidate_df is None or candidate_df.empty: return None
        score, req_count, opt_count = score_sales_dataframe(candidate_df)
        if sheet_name == order_sku_sheet: score += 500
        score += max(0, 40 - header_row) + max(0, 10 - sheet_index)
        if reader_type == "xml" and len(candidate_df.columns) > 1: score += 100
        candidate_record = (score, opt_count, sheet_name, header_row, reader_type, candidate_df)
        inspected_candidates.append((req_count, score, sheet_name, header_row, reader_type, candidate_df))
        if req_count == len(REQUIRED_COLUMN_GROUPS):
            valid_candidates.append(candidate_record)
            return candidate_record
        return None

    def return_candidate(candidate_record):
        st.session_state["last_excel_reader_info"] = {"sheet": candidate_record[2], "header_row": candidate_record[3] + 1, "reader": candidate_record[4], "source": source_label}
        return candidate_record[5]

    for sheet_index, sheet_name in enumerate(ordered_sheets):
        try: raw_dataframe = _cached_read_excel_raw(file_bytes, sheet_name)
        except Exception: continue
        for header_row in range(min(30, len(raw_dataframe))):
            valid_candidate = evaluate_candidate(dataframe_from_raw_excel(raw_dataframe, header_row), sheet_name, header_row, sheet_index, "pandas")
            if valid_candidate is not None and sheet_name == order_sku_sheet: return return_candidate(valid_candidate)
            if valid_candidate is not None: break

    if valid_candidates:
        valid_candidates.sort(key=lambda item: (item[0], item[1], len(item[5].columns)), reverse=True)
        return return_candidate(valid_candidates[0])

    xml_worksheets = read_excel_xml_matrices(file_bytes)
    for sheet_index, sheet_name in enumerate(ordered_sheets):
        matrix = xml_worksheets.get(sheet_name)
        if matrix is None: continue
        for header_row in range(min(30, len(matrix))):
            valid_candidate = evaluate_candidate(dataframe_from_excel_matrix(matrix, header_row), sheet_name, header_row, sheet_index, "xml")
            if valid_candidate is not None: return return_candidate(valid_candidate)

    if inspected_candidates:
        inspected_candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        best = inspected_candidates[0]
        detected = detect_sales_columns(best[5])
        missing = [g for g in REQUIRED_COLUMN_GROUPS if detected.get(g) is None]
        group_labels = {"product": "Product Name", "quantity": "Quantity", "order": "Order ID", "revenue": "SKU Subtotal After Discount"}
        missing_labels = [group_labels[g] for g in missing]
        best_cols = ", ".join(str(c) for c in best[5].columns)
        st.error(f"{source_label} belum dapat dipetakan sebagai data transaksi.")
        st.warning("Kolom yang belum dikenali: " + ", ".join(missing_labels))
        st.info(f"Sheet terbaik: {best[2]}, header baris {best[3] + 1}, pembacaan: {best[4]}. Kolom ditemukan: {best_cols}")
    else:
        st.error(f"Tidak ada sheet yang dapat dibaca dari {source_label}.")
    return None

@st.cache_data(show_spinner=False, max_entries=16)
def _cached_read_csv_raw(file_bytes, encoding, separator):
    kwargs = {"encoding": encoding, "header": None, "on_bad_lines": "skip", "dtype": object}
    if separator is None: kwargs.update({"sep": None, "engine": "python"})
    else: kwargs.update({"sep": separator})
    return pd.read_csv(io.BytesIO(file_bytes), **kwargs)

def read_csv_sales_source(source, source_label):
    try: file_bytes = _source_to_bytes(source)
    except Exception as error:
        st.error(f"{source_label} tidak dapat dibuka: {error}")
        return None

    inspected_candidates = []
    for encoding in ["utf-8-sig", "utf-8", "cp1252", "latin1"]:
        for separator in [None, ",", ";", "\t", "|"]:
            try: raw_dataframe = _cached_read_csv_raw(file_bytes, encoding, separator)
            except Exception: continue
            for header_row in range(min(6, len(raw_dataframe))):
                candidate_df = dataframe_from_raw_excel(raw_dataframe, header_row)
                if candidate_df is None or candidate_df.empty: continue
                score, req_count, opt_count = score_sales_dataframe(candidate_df)
                score += max(0, 10 - header_row)
                inspected_candidates.append((req_count, score, separator, header_row, candidate_df))
                if req_count == len(REQUIRED_COLUMN_GROUPS): return candidate_df

    if inspected_candidates:
        inspected_candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        best = inspected_candidates[0]
        st.error(f"{source_label} belum memiliki struktur yang sama dengan Data Default k-means.xlsx.")
        st.info(f"Kolom terbaik yang berhasil dibaca: {', '.join(str(c) for c in best[4].columns)}")
    else:
        st.error(f"{source_label} tidak dapat dibaca sebagai file CSV.")
    return None


def load_sales_data_source(source, file_name, source_label):
    lower_name = str(file_name).lower()
    if lower_name.endswith(".xlsx"): return read_excel_sales_source(source, source_label)
    if lower_name.endswith(".csv"): return read_csv_sales_source(source, source_label)
    st.error("Format file tidak didukung. Gunakan CSV atau Excel .xlsx.")
    return None

def get_default_data():
    if not os.path.exists(DEFAULT_FILE):
        st.error("File default k-means.xlsx tidak ditemukan. Pastikan file berada satu folder dengan app.py.")
        return pd.DataFrame()
    df = load_sales_data_source(DEFAULT_FILE, os.path.basename(DEFAULT_FILE), "Data Default k-means.xlsx")
    return df if df is not None else pd.DataFrame()

def load_uploaded_file(uploaded_file):
    return load_sales_data_source(uploaded_file.getvalue(), uploaded_file.name, f"File upload {uploaded_file.name}")

def normalize_column_key(column_name):
    text = str(column_name).replace("\ufeff", " ").replace("\n", " ").replace("\r", " ").replace("\t", " ")
    return " ".join(re.sub(r"[^0-9a-zA-Z]+", " ", text).lower().strip().split())


def clean_column_names(df):
    df = df.copy()
    df.columns = [
        " ".join(
            str(c)
            .replace("\ufeff", " ")
            .replace("\n", " ")
            .replace("\r", " ")
            .replace("\t", " ")
            .strip()
            .split()
        )
        for c in df.columns
    ]
    return df


def clean_loaded_dataframe(df):
    if df is None:
        return None

    df = clean_column_names(df).dropna(
        axis=0, how="all"
    ).dropna(
        axis=1, how="all"
    )

    removable_columns = [
        col for col in df.columns
        if normalize_column_key(col).startswith("unnamed")
        and df[col].isna().all()
    ]

    if removable_columns:
        df = df.drop(columns=removable_columns)

    return df

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
