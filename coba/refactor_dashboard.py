
import ast
import shutil
from pathlib import Path

# ============================================================
# 1. MEMBACA FILE APLIKASI
# ============================================================

app = Path("app.py")
view = Path("views/dashboard.py")

source = app.read_text(encoding="utf-8")
tree = ast.parse(source)
lines = source.splitlines(keepends=True)

names = {"dashboard_page", "show_province_map"}

functions = {
    node.name: node
    for node in tree.body
    if isinstance(node, ast.FunctionDef)
    and node.name in names
}

if names != functions.keys():
    raise RuntimeError(
        "Fungsi Dashboard tidak ditemukan lengkap."
    )

if "from views.dashboard import dashboard_page" in source:
    raise RuntimeError(
        "Dashboard sudah pernah dihubungkan."
    )

# ============================================================
# 2. MEMERIKSA FILE TUJUAN
# ============================================================

if view.exists():
    existing = view.read_text(encoding="utf-8")

    if existing.strip():
        if "def aggregate_product_data(" not in existing:
            raise RuntimeError(
                "dashboard.py sudah berisi kode lain."
            )

# ============================================================
# 3. MEMBUAT BACKUP
# ============================================================

backup = Path(
    "app_backup_sebelum_tahap11_otomatis.py"
)

if backup.exists():
    raise RuntimeError(
        "File backup sudah ada. Proses dibatalkan."
    )

shutil.copy2(app, backup)

if view.exists() and view.stat().st_size:
    shutil.copy2(
        view,
        Path("views/dashboard_backup_tahap11.py")
    )

# ============================================================
# 4. MENGAMBIL KONSTANTA WARNA DASHBOARD
# ============================================================

colors = {
    "COLOR_GREEN",
    "COLOR_YELLOW",
    "COLOR_RED",
    "CHART_COLORS",
}

assignments = []

for node in tree.body:
    if isinstance(node, ast.Assign):
        if any(
            isinstance(target, ast.Name)
            and target.id in colors
            for target in node.targets
        ):
            assignments.append(
                ast.get_source_segment(source, node)
            )

if len(assignments) != 4:
    raise RuntimeError(
        "Konstanta warna Dashboard tidak lengkap."
    )

# ============================================================
# 5. MENGAMBIL FUNGSI DASHBOARD ASLI
# ============================================================

map_src = ast.get_source_segment(
    source,
    functions["show_province_map"]
)

dash_src = ast.get_source_segment(
    source,
    functions["dashboard_page"]
)

callbacks = (
    "get_active_selected_data_filtered",
    "aggregate_product_data",
    "show_plotly",
    "card_container",
    "section_header",
    "metric_card",
    "top_bar",
)

old_head = "def dashboard_page():"

if dash_src.count(old_head) != 1:
    raise RuntimeError(
        "Struktur fungsi Dashboard tidak cocok."
    )

dash_src = dash_src.replace(
    old_head,
    "def dashboard_page("
    + ", ".join(callbacks)
    + "):",
    1,
)

# ============================================================
# 6. MEMBUAT MODUL DASHBOARD
# ============================================================

header = '''# DASHBOARD TOKO SEPATU JAKARTA BARAT

import os
import json
import pandas as pd
import plotly.express as px
import streamlit as st

from config import APP_DIR

from database.repository import (
    load_latest_clustering_for_dataset,
    get_cluster_order,
)

from utils.helpers import (
    format_rupiah,
    format_number,
    safe_html,
)

'''

view.parent.mkdir(
    parents=True,
    exist_ok=True
)

view.write_text(
    header
    + "\n\n".join(assignments)
    + "\n\n\n"
    + map_src
    + "\n\n\n"
    + dash_src
    + "\n",
    encoding="utf-8",
)

# ============================================================
# 7. MEMPERBARUI APP.PY
# ============================================================

remove_lines = set()

for node in functions.values():
    remove_lines.update(
        range(node.lineno, node.end_lineno + 1)
    )

remaining = "".join(
    line
    for i, line in enumerate(lines, 1)
    if i not in remove_lines
)

import_stmt = (
    "from views.dashboard import dashboard_page\n"
)

anchor = "from utils.styles import ("

if anchor not in remaining:
    raise RuntimeError(
        "Lokasi import tidak ditemukan."
    )

remaining = remaining.replace(
    anchor,
    import_stmt + anchor,
    1,
)

old_route = (
    'if page == "Dashboard": dashboard_page()'
)

new_route = (
    'if page == "Dashboard": dashboard_page('
    + ", ".join(callbacks)
    + ")"
)

if remaining.count(old_route) != 1:
    raise RuntimeError(
        "Pemanggilan Dashboard tidak cocok."
    )

remaining = remaining.replace(
    old_route,
    new_route,
    1,
)

# ============================================================
# 8. VALIDASI DAN SIMPAN
# ============================================================

ast.parse(
    view.read_text(encoding="utf-8")
)

ast.parse(remaining)

app.write_text(
    remaining,
    encoding="utf-8",
)

print("BERHASIL: Dashboard dipindahkan.")
print("Lokasi: views/dashboard.py")
print("Backup:", backup)
print("Fungsi pendukung tetap aman di app.py")
