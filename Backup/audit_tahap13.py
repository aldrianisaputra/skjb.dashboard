
import ast
from pathlib import Path

# ============================================================
# AUDIT TAHAP 13 - APP.PY
# ============================================================

app = Path("app.py")

source = app.read_text(encoding="utf-8")
tree = ast.parse(source)

functions = [
    node for node in tree.body
    if isinstance(node, ast.FunctionDef)
]

imports = [
    node for node in tree.body
    if isinstance(node, (ast.Import, ast.ImportFrom))
]

# ============================================================
# 1. INFORMASI UMUM
# ============================================================

print("=" * 55)
print("AUDIT APP.PY - TAHAP 13")
print("=" * 55)

print("Total baris:", len(source.splitlines()))
print("Jumlah fungsi:", len(functions))
print("Jumlah blok import:", len(imports))

# ============================================================
# 2. DAFTAR FUNGSI YANG MASIH ADA
# ============================================================

print("\n=== FUNGSI DI APP.PY ===")

for node in functions:
    print(
        f"{node.name}: "
        f"baris {node.lineno}-{node.end_lineno}"
    )

# ============================================================
# 3. CEK DUPLIKASI FUNGSI
# ============================================================

print("\n=== DUPLIKASI FUNGSI ===")

names = [node.name for node in functions]

duplicates = sorted({
    name for name in names
    if names.count(name) > 1
})

if duplicates:
    for name in duplicates:
        print("DUPLIKAT:", name)
else:
    print("Tidak ada duplikasi fungsi.")

# ============================================================
# 4. PERIKSA IMPORT YANG BERPOTENSI TIDAK DIGUNAKAN
# ============================================================

print("\n=== KANDIDAT IMPORT TIDAK DIGUNAKAN ===")

loaded_names = {
    node.id
    for node in ast.walk(tree)
    if isinstance(node, ast.Name)
    and isinstance(node.ctx, ast.Load)
}

unused = []

for node in imports:
    if isinstance(node, ast.Import):
        for alias in node.names:
            name = alias.asname or alias.name.split(".")[0]
            if name not in loaded_names:
                unused.append(name)

    elif isinstance(node, ast.ImportFrom):
        for alias in node.names:
            if alias.name == "*":
                continue

            name = alias.asname or alias.name

            if name not in loaded_names:
                unused.append(name)

if unused:
    for name in sorted(set(unused)):
        print("PERIKSA:", name)
else:
    print("Tidak ada kandidat.")

# ============================================================
# 5. VERIFIKASI HALAMAN SUDAH DIPINDAHKAN
# ============================================================

print("\n=== PEMERIKSAAN HALAMAN ===")

pages = [
    "dashboard_page",
    "upload_page",
    "insight_page",
    "dataset_history_page",
    "clustering_history_page",
    "user_management_page",
]

for name in pages:
    if name in names:
        print(name, ": MASIH DI APP.PY")
    else:
        print(name, ": SUDAH TIDAK DI APP.PY")

print("\nAUDIT SELESAI - TIDAK ADA FILE YANG DIUBAH")
    