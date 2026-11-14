
import ast
from pathlib import Path

app_path = Path("app.py")
styles_path = Path("utils/styles.py")

source = app_path.read_text(encoding="utf-8")
tree = ast.parse(source)

css = None

for node in tree.body:
    if not isinstance(node, ast.Expr):
        continue

    call = node.value

    if not isinstance(call, ast.Call):
        continue

    if not isinstance(call.func, ast.Attribute):
        continue

    if call.func.attr != "markdown":
        continue

    if not call.args:
        continue

    first_arg = call.args[0]

    if isinstance(first_arg, ast.Constant):
        value = first_arg.value

        if isinstance(value, str):
            if value.strip().startswith("<style>"):
                css = value
                break

if css is None:
    raise RuntimeError("CSS utama tidak ditemukan.")

styles_path.parent.mkdir(
    parents=True,
    exist_ok=True
)

if styles_path.exists() and styles_path.stat().st_size > 0:
    raise RuntimeError(
        "styles.py sudah berisi kode. "
        "Proses dibatalkan agar tidak menimpa file."
    )

styles_code = (
    "import streamlit as st\n\n\n"
    "def inject_main_css():\n"
    f"    st.markdown({css!r}, unsafe_allow_html=True)\n"
)

styles_path.write_text(
    styles_code,
    encoding="utf-8"
)

print("CSS utama berhasil disalin ke utils/styles.py")
print(f"Jumlah karakter CSS: {len(css)}")
print("File app.py tidak diubah.")
