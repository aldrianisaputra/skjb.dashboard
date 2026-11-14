
import pandas as pd
import streamlit as st

from processing.clustering import run_clustering

# Data contoh untuk pengujian
df_test = pd.DataFrame({
    "Product Name": [
        "Sepatu A", "Sepatu B", "Sepatu C",
        "Sepatu D", "Sepatu E", "Sepatu F"
    ],
    "Quantity": [2, 3, 10, 12, 30, 35],
    "Order": [1, 2, 8, 9, 25, 28],
    "Revenue": [
        200000, 300000, 1000000,
        1200000, 3000000, 3500000
    ]
})

# Jalankan clustering tanpa menyimpan history
berhasil = run_clustering(
    df_product=df_test,
    k=3,
    dataset_id=None,
    dataset_name="Data Pengujian",
    save_history=False
)

if berhasil:
    result = st.session_state.clustering_result

    print("\n=== HASIL CLUSTERING ===")
    print(result["df_result"][
        ["Product Name", "Cluster", "Kategori_Cluster"]
    ])

    print("\n=== HASIL EVALUASI ===")
    print("Silhouette:", result["silhouette"])
    print("Davies-Bouldin Index:", result["dbi"])

    print("\n=== CENTROID ===")
    print(result["centroid_df"])

    print("\nPENGUJIAN K-MEANS BERHASIL!")
else:
    print("PENGUJIAN K-MEANS GAGAL!")
