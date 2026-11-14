import pandas as pd
import pymysql
import hashlib
import hmac
import os
import io
import json

from database.connection import get_connection

PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 600_000

def hash_password(password):
    password_bytes = password.encode("utf-8")
    salt = os.urandom(16)
    derived_key = hashlib.pbkdf2_hmac("sha256", password_bytes, salt, PASSWORD_ITERATIONS)
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${salt.hex()}${derived_key.hex()}"

def verify_password(password, stored_password):
    if not stored_password: return False
    password = password.strip()
    if stored_password.startswith(f"{PASSWORD_SCHEME}$"):
        try:
            _, iteration_text, salt_hex, expected_hash = stored_password.split("$", 3)
            iterations = int(iteration_text)
            salt = bytes.fromhex(salt_hex)
            calculated_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations).hex()
            return hmac.compare_digest(calculated_hash, expected_hash)
        except (ValueError, TypeError):
            return False
    legacy_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy_hash, stored_password)

def password_needs_upgrade(stored_password):
    return not str(stored_password).startswith(f"{PASSWORD_SCHEME}$")


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Memastikan empat tabel tersedia di MySQL
    tabel = [
        "users",
        "sales_data",
        "datasets",
        "clustering_history"
    ]

    cursor.execute("SHOW TABLES")
    tabel_tersedia = {row[0] for row in cursor.fetchall()}

    for nama_tabel in tabel:
        if nama_tabel not in tabel_tersedia:
            cursor.close()
            conn.close()
            raise RuntimeError(
                f"Tabel {nama_tabel} belum tersedia di MySQL."
            )

    cursor.close()
    conn.close()

def login_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Mencari akun berdasarkan username
        cursor.execute(
            "SELECT id, username, password, role FROM users WHERE username=%s",
            (username.strip(),)
        )

        user_row = cursor.fetchone()

        # Memeriksa apakah akun dan password sesuai
        if user_row is None or not verify_password(password, user_row[2]):
            return None

        # Memperbarui format hash password lama jika diperlukan
        if password_needs_upgrade(user_row[2]):
            cursor.execute(
                "UPDATE users SET password=%s WHERE id=%s",
                (hash_password(password.strip()), user_row[0])
            )
            conn.commit()

        # Mengembalikan data pengguna
        return (user_row[0], user_row[1], user_row[3])

    finally:
        cursor.close()
        conn.close()


def add_user(username, password, role):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            (username.strip(), hash_password(password.strip()), role)
        )

        conn.commit()
        return True

    except pymysql.err.IntegrityError:
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()



def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT id, username, role FROM users ORDER BY id ASC"
        )

        data = cursor.fetchall()

        df_users = pd.DataFrame(
            data,
            columns=["id", "username", "role"]
        )

        return df_users

    finally:
        cursor.close()
        conn.close()


def delete_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM users WHERE id=%s",
            (int(user_id),)
        )

        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted

    except pymysql.MySQLError:
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()
def save_sales_data_to_db(df_selected):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Menghapus transaksi sebelumnya
        cursor.execute("DELETE FROM sales_data")

        # Menyalin dataset agar data asli tidak berubah
        data_to_save = df_selected.copy()

        # Memastikan kolom opsional tersedia
        if "Date" not in data_to_save.columns:
            data_to_save["Date"] = None

        if "Order Status" not in data_to_save.columns:
            data_to_save["Order Status"] = None

        if "Regency and City" not in data_to_save.columns:
            data_to_save["Regency and City"] = None

        if "Province" not in data_to_save.columns:
            data_to_save["Province"] = None

        if "Payment Method" not in data_to_save.columns:
            data_to_save["Payment Method"] = None

        records = []

        for p_name, qty, ord_id, rev, d_val, s_val, city, province, pay_method in data_to_save[
            [
                "Product Name",
                "Quantity",
                "Order",
                "Revenue",
                "Date",
                "Order Status",
                "Regency and City",
                "Province",
                "Payment Method"
            ]
        ].itertuples(index=False, name=None):

            records.append((
                str(p_name),
                float(qty),
                str(ord_id),
                float(rev),
                str(d_val) if pd.notna(d_val) else None,
                str(s_val) if pd.notna(s_val) else None,
                str(city) if pd.notna(city) else None,
                str(province) if pd.notna(province) else None,
                str(pay_method) if pd.notna(pay_method) else None
            ))

        # Menyimpan transaksi ke MySQL
        cursor.executemany(
            """
            INSERT INTO sales_data (
                product_name,
                quantity,
                orders,
                revenue,
                date,
                order_status,
                regency_and_city,
                province,
                payment_method
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            records
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


def load_sales_data_from_db():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM sales_data")

        data = cursor.fetchall()
        columns = [col[0] for col in cursor.description]

        df = pd.DataFrame(data, columns=columns)

    finally:
        cursor.close()
        conn.close()

    if df.empty: return None

    df = df.rename(columns={
        "product_name": "Product Name", "quantity": "Quantity", "orders": "Order",
        "revenue": "Revenue", "date": "Date", "order_status": "Order Status",
        "regency_and_city": "Regency and City", "province": "Province", "payment_method": "Payment Method" 
    })
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["Revenue"] = pd.to_numeric(df["Revenue"], errors="coerce")
    if "Date" in df.columns: df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    needed_cols = ["Product Name", "Quantity", "Order", "Revenue"]
    if "Date" in df.columns and df["Date"].notna().any(): needed_cols.append("Date")
    if "Order Status" in df.columns: needed_cols.append("Order Status")
    if "Regency and City" in df.columns: needed_cols.append("Regency and City")
    if "Province" in df.columns: needed_cols.append("Province")
    if "Payment Method" in df.columns: needed_cols.append("Payment Method")

    return df[needed_cols]


def clear_sales_data_db():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM sales_data")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def dataframe_to_json(df):
    return df.to_json(orient="table", date_format="iso", force_ascii=False)

def dataframe_from_json(data_json):
    if not data_json: return pd.DataFrame()
    return pd.read_json(io.StringIO(data_json), orient="table")


def save_dataset_history(df_selected, dataset_name, uploaded_by, make_active=False):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Menonaktifkan dataset lama jika dataset baru dipilih aktif
        if make_active:
            cursor.execute("UPDATE datasets SET is_active=0")

        # Menyimpan riwayat dataset baru ke MySQL
        cursor.execute(
            """
            INSERT INTO datasets (
                name, uploaded_by, is_active, data_json
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                str(dataset_name),
                str(uploaded_by),
                1 if make_active else 0,
                dataframe_to_json(df_selected)
            )
        )

        # Mengambil ID dataset yang baru disimpan
        dataset_id = cursor.lastrowid

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()

    # Memperbarui transaksi jika dataset menjadi aktif
    if make_active:
        save_sales_data_to_db(df_selected)

    return dataset_id



def get_dataset_history():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                id,
                name,
                uploaded_at,
                uploaded_by,
                is_active
            FROM datasets
            ORDER BY uploaded_at DESC, id DESC
        """)

        data = cursor.fetchall()

        columns = [col[0] for col in cursor.description]

        df = pd.DataFrame(data, columns=columns)

        return df

    finally:
        cursor.close()
        conn.close()



def load_dataset_by_id(dataset_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, name, uploaded_at, uploaded_by,
                   is_active, data_json
            FROM datasets
            WHERE id=%s
            """,
            (int(dataset_id),)
        )

        row = cursor.fetchone()

    finally:
        cursor.close()
        conn.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "uploaded_at": row[2],
        "uploaded_by": row[3],
        "is_active": bool(row[4]),
        "data": dataframe_from_json(row[5])
    }


def get_active_dataset_record():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, name, uploaded_at, uploaded_by, data_json
            FROM datasets
            WHERE is_active = 1
            ORDER BY id DESC
            LIMIT 1
        """)

        row = cursor.fetchone()

    finally:
        cursor.close()
        conn.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "uploaded_at": row[2],
        "uploaded_by": row[3],
        "data": dataframe_from_json(row[4])
    }



def get_active_dataset_metadata():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, name, uploaded_at, uploaded_by
            FROM datasets
            WHERE is_active = 1
            ORDER BY id DESC
            LIMIT 1
        """)

        row = cursor.fetchone()

    finally:
        cursor.close()
        conn.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "uploaded_at": row[2],
        "uploaded_by": row[3]
    }

def save_clustering_history(result, dataset_id, dataset_name, clustered_by):
    df_result = result["df_result"]

    insight_items, recommendation_items = build_clustering_insight(
        df_result, result["k"]
    )

    insight = json.dumps(insight_items, ensure_ascii=False)
    recommendation = json.dumps(recommendation_items, ensure_ascii=False)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO clustering_history (
                dataset_id,
                dataset_name,
                clustered_by,
                k,
                silhouette,
                dbi,
                result_json,
                centroid_json,
                insight,
                recommendation
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                int(dataset_id) if dataset_id is not None else None,
                str(dataset_name),
                str(clustered_by),
                int(result["k"]),
                float(result["silhouette"]),
                float(result["dbi"]),
                dataframe_to_json(result["df_result"]),
                dataframe_to_json(result["centroid_df"]),
                insight,
                recommendation
            )
        )

        history_id = cursor.lastrowid
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()

    return history_id



def get_clustering_history():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                id,
                clustered_at,
                dataset_id,
                dataset_name,
                clustered_by,
                k,
                silhouette,
                dbi
            FROM clustering_history
            ORDER BY clustered_at DESC, id DESC
        """)

        data = cursor.fetchall()
        columns = [col[0] for col in cursor.description]

        df = pd.DataFrame(data, columns=columns)

        return df

    finally:
        cursor.close()
        conn.close()



def load_clustering_history_by_id(history_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                id, clustered_at, dataset_id, dataset_name,
                clustered_by, k, silhouette, dbi,
                result_json, centroid_json, insight, recommendation
            FROM clustering_history
            WHERE id=%s
            """,
            (int(history_id),)
        )

        row = cursor.fetchone()

    finally:
        cursor.close()
        conn.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "clustered_at": row[1],
        "dataset_id": row[2],
        "dataset_name": row[3],
        "clustered_by": row[4],
        "k": row[5],
        "silhouette": row[6],
        "dbi": row[7],
        "df_result": dataframe_from_json(row[8]),
        "centroid_df": dataframe_from_json(row[9]),
        "insight": row[10] or "-",
        "recommendation": row[11] or "-"
    }



def load_latest_clustering_for_dataset(dataset_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if dataset_id is None:
            cursor.execute("""
                SELECT id
                FROM clustering_history
                WHERE dataset_id IS NULL
                  AND dataset_name = 'Data Default k-means.xlsx'
                ORDER BY clustered_at DESC, id DESC
                LIMIT 1
            """)
        else:
            cursor.execute(
                """
                SELECT id
                FROM clustering_history
                WHERE dataset_id = %s
                ORDER BY clustered_at DESC, id DESC
                LIMIT 1
                """,
                (int(dataset_id),)
            )

        row = cursor.fetchone()

    finally:
        cursor.close()
        conn.close()

    return load_clustering_history_by_id(row[0]) if row else None



def delete_clustering_history(history_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM clustering_history WHERE id=%s",
            (int(history_id),)
        )

        deleted = cursor.rowcount > 0

        conn.commit()
        return deleted

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()

# Kategori diurutkan dari skor performa penjualan tertinggi ke terendah.
# Konfigurasi label cluster
CLUSTER_LABELS = {
    2: ["Cluster Tinggi", "Cluster Rendah"],
    3: ["Cluster Tinggi", "Cluster Sedang", "Cluster Rendah"],
    4: ["Cluster Sangat Tinggi", "Cluster Tinggi", "Cluster Sedang", "Cluster Rendah"],
    5: ["Cluster Sangat Tinggi", "Cluster Tinggi", "Cluster Sedang", "Cluster Rendah", "Cluster Sangat Rendah"],
    6: ["Cluster Sangat Tinggi", "Cluster Tinggi", "Cluster Menengah Atas", "Cluster Menengah Bawah", "Cluster Rendah", "Cluster Sangat Rendah"],
}

def get_cluster_order(k):
    return CLUSTER_LABELS.get(int(k), [])

def buat_rekomendasi(kategori):
    rekomendasi = {
        "Cluster Sangat Tinggi": "Produk dengan performa relatif paling tinggi. Prioritaskan ketersediaan stok, pantau permintaan, dan pertahankan strategi penjualan yang efektif.",
        "Cluster Tinggi": "Produk berkinerja relatif tinggi. Jaga stok dan pertahankan promosi yang efektif untuk menjaga performa penjualan.",
        "Cluster Menengah Atas": "Produk berada di kelompok menengah atas. Uji promosi terarah dan optimalkan tampilan produk untuk meningkatkan penjualan.",
        "Cluster Sedang": "Produk dengan performa menengah. Evaluasi harga, promosi, dan tampilan produk untuk mendorong peningkatan penjualan.",
        "Cluster Menengah Bawah": "Produk berada di kelompok menengah bawah. Tinjau harga, foto produk, dan strategi pemasaran; lakukan uji perbaikan secara bertahap.",
        "Cluster Rendah": "Produk berkinerja relatif rendah. Evaluasi penyebab penjualan rendah dan pertimbangkan diskon atau bundling yang terukur.",
        "Cluster Sangat Rendah": "Produk dengan performa relatif paling rendah. Prioritaskan evaluasi produk dan efisiensi stok sebelum memutuskan promosi atau penambahan persediaan.",
    }
    return rekomendasi.get(kategori, "Lakukan analisis lanjutan terhadap performa produk.")

def format_rupiah(value):
    try: return f"Rp {float(value):,.0f}".replace(",", ".")
    except Exception: return "Rp 0"

def format_number(value):
    try: return f"{int(value):,}".replace(",", ".")
    except Exception: return "0"

def build_clustering_insight(df_result, k):
    insights = []
    cluster_summary = df_result.groupby("Kategori_Cluster").agg(
        Jumlah_Produk=("Product Name", "nunique"),
        Total_Quantity=("Quantity", "sum"),
        Total_Transaksi=("Order", "sum"),
        Total_Revenue=("Revenue", "sum")
    ).reset_index()
    order = get_cluster_order(k)
    cluster_summary["urutan"] = cluster_summary["Kategori_Cluster"].map({name: i for i, name in enumerate(order)})
    cluster_summary = cluster_summary.sort_values("urutan")
    for row in cluster_summary.itertuples(index=False):
        insights.append(f"{row.Kategori_Cluster} berisi {int(row.Jumlah_Produk)} produk, quantity {format_number(row.Total_Quantity)}, total transaksi {format_number(row.Total_Transaksi)}, dan omzet {format_rupiah(row.Total_Revenue)}.")
    recommendations = [buat_rekomendasi(name) for name in order if name in df_result["Kategori_Cluster"].values]
    insights.append("Nama kategori menunjukkan peringkat performa relatif antar-cluster dalam dataset ini, bukan perbandingan terhadap tahun sebelumnya.")
    return insights, recommendations


def set_active_dataset(dataset_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Menonaktifkan semua dataset
        cursor.execute(
            "UPDATE datasets SET is_active=0"
        )

        # Mengaktifkan dataset yang dipilih
        cursor.execute(
            "UPDATE datasets SET is_active=1 WHERE id=%s",
            (int(dataset_id),)
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()

def delete_dataset_by_id(dataset_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM datasets WHERE id=%s",
            (int(dataset_id),)
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()
