
import ast
import builtins
import re
import shutil
import symtable
from pathlib import Path

# ============================================================
# 1. KONFIGURASI
# ============================================================

app = Path("app.py")
output = Path("views/other_pages.py")
backup = Path("app_backup_tahap12.py")

names = (
    "upload_page",
    "insight_page",
    "dataset_history_page",
    "clustering_history_page",
    "user_management_page",
)

source = app.read_text(encoding="utf-8")
tree = ast.parse(source)
lines = source.splitlines(keepends=True)

functions = {
    n.name: n
    for n in tree.body
    if isinstance(n, ast.FunctionDef)
    and n.name in names
}

# ============================================================
# 2. PEMERIKSAAN KEAMANAN
# ============================================================

if set(functions) != set(names):
    raise RuntimeError(
        "Ada fungsi halaman yang tidak ditemukan."
    )

if backup.exists():
    raise RuntimeError(
        "Backup Tahap 12 sudah ada. Proses dibatalkan."
    )

if output.exists() and output.read_text(
    encoding="utf-8"
).strip():
    raise RuntimeError(
        "other_pages.py sudah berisi kode."
    )

if "from views import other_pages" in source:
    raise RuntimeError(
        "Halaman sudah pernah dihubungkan."
    )

# ============================================================
# 3. IDENTIFIKASI DEPENDENSI
# ============================================================

globals_available = set()

for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        globals_available.add(node.name)

    elif isinstance(node, ast.Import):
        globals_available.update(
            a.asname or a.name.split(".")[0]
            for a in node.names
        )

    elif isinstance(node, ast.ImportFrom):
        globals_available.update(
            a.asname or a.name
            for a in node.names
        )

    elif isinstance(node, (ast.Assign, ast.AnnAssign)):
        targets = (
            node.targets
            if isinstance(node, ast.Assign)
            else [node.target]
        )

        for target in targets:
            globals_available.update(
                x.id
                for x in ast.walk(target)
                if isinstance(x, ast.Name)
            )

builtins_set = set(dir(builtins))

exports = []
removed = set()
routes = {}

# ============================================================
# 4. MEMINDAHKAN LIMA FUNGSI
# ============================================================

for name in names:
    node = functions[name]

    original = ast.get_source_segment(
        source, node
    )

    scope = symtable.symtable(
        original,
        name + ".py",
        "exec"
    ).get_children()[0]

    deps = sorted(
        symbol.get_name()
        for symbol in scope.get_symbols()
        if symbol.is_global()
        and symbol.is_referenced()
        and symbol.get_name() not in builtins_set
    )

    missing = set(deps) - globals_available

    if missing:
        raise RuntimeError(
            f"{name}: dependensi tidak ditemukan: "
            f"{sorted(missing)}"
        )

    old_def = f"def {name}():"

    if not original.startswith(old_def):
        raise RuntimeError(
            f"Struktur {name} tidak sesuai."
        )

    new_def = (
        f"def {name}(*, {', '.join(deps)}):"
        if deps else old_def
    )

    exports.append(
        original.replace(old_def, new_def, 1)
    )

    removed.update(
        range(node.lineno, node.end_lineno + 1)
    )

    routes[name] = (
        f"other_pages.{name}("
        + ", ".join(f"{d}={d}" for d in deps)
        + ")"
    )

# ============================================================
# 5. MEMBUAT FILE HALAMAN
# ============================================================

new_module = (
    "# HALAMAN APLIKASI SJB\n\n\n"
    + "\n\n\n".join(exports)
    + "\n"
)

remaining = "".join(
    line
    for i, line in enumerate(lines, 1)
    if i not in removed
)

# ============================================================
# 6. MEMPERBARUI ROUTING APP.PY
# ============================================================

for name in names:
    pattern = re.compile(
        r"(?m)^(\s*(?:if|elif) page == "
        r"[^\n:]+:\s*)"
        + re.escape(name)
        + r"\(\)\s*$"
    )

    remaining, count = pattern.subn(
        lambda match: match.group(1) + routes[name],
        remaining
    )

    if count != 1:
        raise RuntimeError(
            f"Routing {name} tidak ditemukan tepat satu kali."
        )

imports = [
    n for n in tree.body
    if isinstance(n, (ast.Import, ast.ImportFrom))
]

if not imports:
    raise RuntimeError(
        "Bagian import tidak ditemukan."
    )

last_import_line = max(
    n.end_lineno for n in imports
)

remaining_lines = remaining.splitlines(
    keepends=True
)

remaining_lines.insert(
    last_import_line,
    "from views import other_pages\n"
)

remaining = "".join(remaining_lines)

# ============================================================
# 7. VALIDASI SEBELUM MENYIMPAN
# ============================================================

ast.parse(remaining)
ast.parse(new_module)

new_app_tree = ast.parse(remaining)
new_page_tree = ast.parse(new_module)

app_functions = {
    n.name
    for n in new_app_tree.body
    if isinstance(n, ast.FunctionDef)
}

page_functions = {
    n.name
    for n in new_page_tree.body
    if isinstance(n, ast.FunctionDef)
}

if set(names) & app_functions:
    raise RuntimeError(
        "Masih ada fungsi halaman lama di app.py."
    )

if not set(names) <= page_functions:
    raise RuntimeError(
        "Ada fungsi yang tidak berhasil dipindahkan."
    )

# ============================================================
# 8. BACKUP DAN SIMPAN
# ============================================================

output.parent.mkdir(
    parents=True,
    exist_ok=True
)

shutil.copy2(app, backup)

output.write_text(
    new_module,
    encoding="utf-8"
)

app.write_text(
    remaining,
    encoding="utf-8"
)

print("BERHASIL: 5 halaman dipindahkan.")
print("Lokasi: views/other_pages.py")
print("Backup:", backup)
print("SINTAKS: VALID")
