# DASHBOARD TOKO SEPATU JAKARTA BARAT

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

# ============================================================
# WARNA GRAFIK DASHBOARD
# ============================================================

COLOR_BLUE = "#3b82f6"
COLOR_TEAL = "#14b8a6"
COLOR_PURPLE = "#a855f7"
COLOR_GREEN = "#22c55e"
COLOR_YELLOW = "#facc15"
COLOR_RED = "#ef4444"
COLOR_ORANGE = "#fb923c"

CHART_COLORS = [
    COLOR_BLUE,
    COLOR_TEAL,
    COLOR_PURPLE,
    COLOR_GREEN,
    COLOR_YELLOW,
    COLOR_ORANGE,
    COLOR_RED,
]
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


def dashboard_page(get_active_selected_data_filtered, aggregate_product_data, show_plotly, card_container, section_header, metric_card, top_bar):
    top_bar("Dashboard Overview", "Ringkasan kondisi penjualan dari Dataset Aktif saat ini.")

    df_selected, sumber_data = get_active_selected_data_filtered()
    if df_selected is None or df_selected.empty:
        st.error("Data tidak tersedia atau tidak dapat diproses.")
        return
    
    st.markdown(f'<span class="badge badge-green">Dataset Aktif: {safe_html(sumber_data)}</span>', unsafe_allow_html=True)

    if "Date" in df_selected.columns:

            df_selected = df_selected.copy()

            df_selected["Date"] = pd.to_datetime(
                df_selected["Date"],
                errors="coerce"
            )

            valid_dates = df_selected["Date"].dropna()

            if not valid_dates.empty:

                min_date = valid_dates.min().date()
                max_date = valid_dates.max().date()

                col_mulai, col_akhir = st.columns(2)

                # Mempertahankan tanggal pilihan selama masih valid
                current_start = st.session_state.get(
                    "tanggal_mulai_filter", min_date
                )

                current_end = st.session_state.get(
                    "tanggal_akhir_filter", max_date
                )

                if (
                    current_start is None
                    or current_start < min_date
                    or current_start > max_date
                ):
                    st.session_state["tanggal_mulai_filter"] = min_date

                if (
                    current_end is None
                    or current_end < min_date
                    or current_end > max_date
                ):
                    st.session_state["tanggal_akhir_filter"] = max_date

                with col_mulai:
                    tanggal_mulai = st.date_input(
                        "Tanggal Mulai",
                        value=min_date,
                        min_value=min_date,
                        max_value=max_date,
                        key="tanggal_mulai_filter"
                    )

                with col_akhir:
                    tanggal_akhir = st.date_input(
                        "Tanggal Akhir",
                        value=max_date,
                        min_value=min_date,
                        max_value=max_date,
                        key="tanggal_akhir_filter"
                    )

                if tanggal_mulai > tanggal_akhir:
                    st.warning(
                        "Tanggal mulai tidak boleh melebihi tanggal akhir."
                    )
                    return

                df_selected = df_selected[
                    (df_selected["Date"].dt.date >= tanggal_mulai)
                    &
                    (df_selected["Date"].dt.date <= tanggal_akhir)
                ].copy()

                st.caption(
                    f"Periode: {tanggal_mulai:%d/%m/%Y} "
                    f"- {tanggal_akhir:%d/%m/%Y}"
                )

                if df_selected.empty:
                    st.info(
                        "Tidak ada transaksi pada periode yang dipilih."
                    )
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
