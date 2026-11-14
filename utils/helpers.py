import html
import pandas as pd
import numpy as np


def format_rupiah(value):
    try:
        return f"Rp {float(value):,.0f}".replace(",", ".")
    except Exception:
        return "Rp 0"


def format_number(value):
    try:
        return f"{int(value):,}".replace(",", ".")
    except Exception:
        return "0"


def format_table_value(value):
    if pd.isna(value):
        return ""

    if isinstance(value, pd.Timestamp):
        return value.strftime("%d/%m/%Y")

    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}".replace(",", ".")

    if isinstance(value, (float, np.floating)):
        if abs(value) >= 1000:
            return f"{value:,.0f}".replace(",", ".")
        return f"{value:,.2f}".replace(",", ".")

    return str(value)

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