import hashlib
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score

from database.repository import (
    get_active_dataset_metadata,
    save_clustering_history,
    get_cluster_order,
    buat_rekomendasi,
)

def build_data_signature(df_product):
    if df_product is None or df_product.empty:
        return None

    df_signature = (
        df_product[
            ["Product Name", "Quantity", "Order", "Revenue"]
        ]
        .copy()
        .sort_values("Product Name")
        .reset_index(drop=True)
    )

    hashed_values = pd.util.hash_pandas_object(
        df_signature,
        index=False
    ).values.tobytes()

    return hashlib.sha256(hashed_values).hexdigest()


def validate_clustering_input(df_product, k):
    if df_product is None or df_product.empty:
        return False, "Data produk tidak tersedia untuk clustering."

    required_columns = ["Quantity", "Order", "Revenue"]

    if any(col not in df_product.columns for col in required_columns):
        return False, "Kolom Quantity, Order, dan Revenue harus tersedia."

    features = df_product[required_columns].apply(
        pd.to_numeric, errors="coerce"
    )

    if features.isna().any().any() or not np.isfinite(features.to_numpy()).all():
        return False, "Data clustering mengandung nilai kosong atau tidak valid."

    num_samples = len(features)
    num_unique = len(features.drop_duplicates())

    if num_samples < 3:
        return False, "Minimal diperlukan 3 produk untuk menjalankan clustering."

    if k < 2:
        return False, "Jumlah cluster minimal adalah 2."

    if k >= num_samples:
        return False, "Jumlah cluster harus lebih kecil daripada jumlah produk."

    if k > num_unique:
        return False, "Jumlah cluster melebihi jumlah kombinasi data yang unik."

    return True, ""



import streamlit as st


def run_clustering(
    df_product,
    k,
    dataset_id=None,
    dataset_name=None,
    save_history=True
):
    is_valid, validation_message = validate_clustering_input(
        df_product, k
    )

    if not is_valid:
        st.error(validation_message)
        return False

    st.session_state.clustering_result = None

    features = df_product[
        ["Quantity", "Order", "Revenue"]
    ].astype(float)

    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    try:
        kmeans = KMeans(
            n_clusters=k,
            random_state=42,
            n_init=10
        )

        df_result = df_product.copy()
        df_result["Cluster"] = kmeans.fit_predict(
            features_scaled
        )

    except ValueError as error:
        st.error(
            f"Proses K-Means tidak dapat dijalankan: {error}"
        )
        return False

    unique_labels = np.unique(df_result["Cluster"])

    if (
        len(unique_labels) < 2
        or len(unique_labels) != k
        or len(unique_labels) >= len(df_result)
    ):
        st.error(
            "Gagal membentuk cluster yang valid. "
            "Kurangi nilai k atau gunakan data yang lebih bervariasi."
        )
        return False

    scaled_df = pd.DataFrame(
        features_scaled,
        columns=[
            "Quantity_scaled",
            "Order_scaled",
            "Revenue_scaled"
        ]
    )

    scaled_df["Cluster"] = df_result["Cluster"].values

    cluster_score = (
        scaled_df.groupby("Cluster")
        .mean()
        .reset_index()
    )

    cluster_score["Skor"] = (
        cluster_score["Quantity_scaled"]
        + cluster_score["Order_scaled"]
        + cluster_score["Revenue_scaled"]
    )

    cluster_score = (
        cluster_score.sort_values(
            "Skor", ascending=False
        ).reset_index(drop=True)
    )

    ordered_labels = get_cluster_order(k)

    label_mapping = {
        row["Cluster"]: ordered_labels[i]
        for i, row in cluster_score.iterrows()
    }

    df_result["Kategori_Cluster"] = (
        df_result["Cluster"].map(label_mapping)
    )

    df_result["Rekomendasi"] = (
        df_result["Kategori_Cluster"].apply(
            buat_rekomendasi
        )
    )

    try:
        silhouette = silhouette_score(
            features_scaled,
            df_result["Cluster"]
        )

        dbi = davies_bouldin_score(
            features_scaled,
            df_result["Cluster"]
        )

    except ValueError as error:
        st.error(
            f"Metrik evaluasi clustering tidak dapat dihitung: {error}"
        )
        return False

    centroid_original = scaler.inverse_transform(
        kmeans.cluster_centers_
    )

    centroid_df = pd.DataFrame(
        centroid_original,
        columns=["Quantity", "Order", "Revenue"]
    )

    centroid_df["Cluster"] = range(k)

    centroid_df["Kategori_Cluster"] = (
        centroid_df["Cluster"].map(label_mapping)
    )

    if dataset_id is None:
        active_metadata = get_active_dataset_metadata()

        if active_metadata is not None:
            dataset_id = active_metadata["id"]
            dataset_name = active_metadata["name"]

    if not dataset_name:
        dataset_name = "Data Default k-means.xlsx"

    st.session_state.clustering_result = {
        "df_result": df_result,
        "centroid_df": centroid_df,
        "silhouette": silhouette,
        "dbi": dbi,
        "k": k,
        "dataset_id": dataset_id,
        "dataset_name": dataset_name,
        "data_signature": build_data_signature(
            df_product
        )
    }

    if save_history:
        history_id = save_clustering_history(
            st.session_state.clustering_result,
            dataset_id,
            dataset_name,
            st.session_state.get("username") or "system"
        )

        st.session_state.clustering_result[
            "history_id"
        ] = history_id

    return True
