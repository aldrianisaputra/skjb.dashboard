
import ast
import shutil
from pathlib import Path

# ============================================================
# TAHAP 13 - CLEANUP IMPORT APP.PY
# ============================================================

app = Path("app.py")
backup = Path("app_backup_tahap13.py")

source = app.read_text(encoding="utf-8")
tree = ast.parse(source)

# Import yang terdeteksi sebagai kandidat tidak digunakan
candidates = {
    "APP_DIR",
    "DEFAULT_FILE",
    "ET",
    "KMeans",
    "MYSQL_DATABASE",
    "MYSQL_HOST",
    "MYSQL_PORT",
    "MYSQL_USER",
    "StandardScaler",
    "buat_rekomendasi",
    "build_clustering_insight",
    "csv",
    "dataframe_from_json",
    "dataframe_to_json",
    "davies_bouldin_score",
    "defaultdict",
    "go",
    "hashlib",
    "hmac",
    "io",
    "json",
    "load_latest_clustering_for_dataset",
    "os",
    "posixpath",
    "px",
    "pymysql",
    "save_clustering_history",
    "silhouette_score",
    "validate_clustering_input",
    "zipfile",
}

# ============================================================
# 1. PENGECEKAN REFERENSI
# ============================================================

used_names = {
    node.id
    for node in ast.walk(tree)
    if isinstance(node, ast.Name)
    and isinstance(node.ctx, ast.Load)
}

lines = source.splitlines(keepends=True)
replacements = []
removed = []

# ============================================================
# 2. FILTER IMPORT
# ============================================================

for node in tree.body:

    if not isinstance(
        node, (ast.Import, ast.ImportFrom)
    ):
        continue

    kept_aliases = []

    for alias in node.names:

        if isinstance(node, ast.Import):
            name = (
                alias.asname
                or alias.name.split(".")[0]
            )
        else:
            name = alias.asname or alias.name

        if (
            name in candidates
            and name not in used_names
        ):
            removed.append(name)
        else:
            kept_aliases.append(alias)

    if len(kept_aliases) == len(node.names):
        continue

    if kept_aliases:
        if isinstance(node, ast.Import):
            new_node = ast.Import(
                names=kept_aliases
            )
        else:
            new_node = ast.ImportFrom(
                module=node.module,
                names=kept_aliases,
                level=node.level
            )

        replacement = ast.unparse(new_node) + "\n"
    else:
        replacement = ""

    replacements.append(
        (node.lineno, node.end_lineno, replacement)
    )

# ============================================================
# 3. MEMBUAT KODE BARU
# ============================================================

for start, end, replacement in sorted(
    replacements,
    reverse=True
):
    lines[start - 1:end] = [replacement]

new_source = "".join(lines)

# ============================================================
# 4. VALIDASI
# ============================================================

new_tree = ast.parse(new_source)

def non_import_nodes(tree):
    return [
        ast.dump(node, include_attributes=False)
        for node in tree.body
        if not isinstance(
            node, (ast.Import, ast.ImportFrom)
        )
    ]

if non_import_nodes(tree) != non_import_nodes(new_tree):
    raise RuntimeError(
        "Ada perubahan di luar import. "
        "Proses dibatalkan."
    )

compile(new_source, "app.py", "exec")

# ============================================================
# 5. BACKUP DAN SIMPAN
# ============================================================

if backup.exists():
    raise RuntimeError(
        "Backup Tahap 13 sudah ada. "
        "Proses dibatalkan agar backup lama aman."
    )

shutil.copy2(app, backup)

app.write_text(
    new_source,
    encoding="utf-8"
)

print("=" * 50)
print("CLEANUP TAHAP 13 BERHASIL")
print("=" * 50)

print("\nImport yang dibersihkan:")

for name in sorted(set(removed)):
    print("-", name)

print("\nJumlah import dibersihkan:", len(removed))
print("Backup:", backup)
print("Sintaks Python: VALID")
print("Kode di luar import: TIDAK BERUBAH")
