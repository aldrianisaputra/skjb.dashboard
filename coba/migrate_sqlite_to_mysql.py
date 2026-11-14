
import sqlite3
from pathlib import Path

from database.connection import get_connection

SQLITE_PATH = Path("database_kmeans.db").resolve()

TABLES = [
    "users",
    "sales_data",
    "datasets",
    "clustering_history",
]

EXPECTED_COLUMNS = {
    "users": [
        "id", "username", "password", "role"
    ],
    "sales_data": [
        "id", "product_name", "quantity", "orders",
        "revenue", "date", "order_status",
        "regency_and_city", "province", "payment_method"
    ],
    "datasets": [
        "id", "name", "uploaded_at", "uploaded_by",
        "is_active", "data_json"
    ],
    "clustering_history": [
        "id", "clustered_at", "dataset_id",
        "dataset_name", "clustered_by", "k",
        "silhouette", "dbi", "result_json",
        "centroid_json", "insight", "recommendation"
    ],
}


def migrate():
    if not SQLITE_PATH.is_file():
        raise FileNotFoundError(SQLITE_PATH)

    sqlite_conn = sqlite3.connect(
        SQLITE_PATH.as_uri() + "?mode=ro",
        uri=True
    )
    sqlite_conn.row_factory = sqlite3.Row

    mysql_conn = None

    try:
        mysql_conn = get_connection()

        with mysql_conn.cursor() as cursor:
            cursor.execute("SELECT DATABASE()")
            database_name = cursor.fetchone()[0]

            if database_name != "sjb_database":
                raise RuntimeError(
                    f"Database tujuan tidak sesuai: {database_name}"
                )

            # Validasi struktur dan pastikan tabel tujuan kosong
            for table in TABLES:
                expected = set(EXPECTED_COLUMNS[table])

                sqlite_columns = {
                    row["name"]
                    for row in sqlite_conn.execute(
                        f"PRAGMA table_info(`{table}`)"
                    )
                }

                cursor.execute(f"SHOW COLUMNS FROM `{table}`")
                mysql_columns = {
                    row[0] for row in cursor.fetchall()
                }

                if sqlite_columns != expected:
                    raise RuntimeError(
                        f"Struktur SQLite {table} tidak sesuai."
                    )

                if mysql_columns != expected:
                    raise RuntimeError(
                        f"Struktur MySQL {table} tidak sesuai."
                    )

                cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                if cursor.fetchone()[0] != 0:
                    raise RuntimeError(
                        f"Tabel MySQL {table} tidak kosong. "
                        "Migrasi dibatalkan agar data tidak tertimpa."
                    )

            print("Validasi berhasil. Memulai migrasi...")

            mysql_conn.begin()

            for table in TABLES:
                columns = EXPECTED_COLUMNS[table]
                quoted_columns = ", ".join(
                    f"`{column}`" for column in columns
                )
                placeholders = ", ".join(
                    ["%s"] * len(columns)
                )

                sql = (
                    f"INSERT INTO `{table}` ({quoted_columns}) "
                    f"VALUES ({placeholders})"
                )

                rows = sqlite_conn.execute(
                    f"SELECT {quoted_columns} FROM `{table}`"
                ).fetchall()

                # Ambil ID dataset yang benar-benar tersedia
                valid_dataset_ids = {
                    row[0]
                    for row in sqlite_conn.execute(
                        "SELECT id FROM datasets"
                    ).fetchall()
                }

                data = []

                for row in rows:
                    values = []

                    for column in columns:
                        value = row[column]

                        # Mengonversi Order ID menjadi teks
                        if table == "sales_data" and column == "orders":
                            if value is not None:
                                value = str(int(value))

                        # Memperbaiki relasi dataset yang sudah tidak tersedia
                        if table == "clustering_history" and column == "dataset_id":
                            if value is not None and value not in valid_dataset_ids:
                                print(
                                    f"History ID {row['id']}: "
                                    f"dataset_id {value} tidak ditemukan, "
                                    f"diubah menjadi NULL"
                                )
                                value = None

                        values.append(value)

                    data.append(tuple(values))

                if data:
                    cursor.executemany(sql, data)

                cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                mysql_count = cursor.fetchone()[0]

                if mysql_count != len(data):
                    raise RuntimeError(
                        f"Jumlah data {table} tidak cocok."
                    )

                print(
                    f"{table}: {mysql_count} data berhasil disalin"
                )

            # Menyimpan seluruh perubahan sekaligus
            mysql_conn.commit()

            print("\nMIGRASI BERHASIL!")
            print("Semua data telah dipindahkan ke MySQL.")

    except Exception:
        if mysql_conn is not None:
            mysql_conn.rollback()
        print("Migrasi gagal. Transaksi dibatalkan.")
        raise

    finally:
        sqlite_conn.close()
        if mysql_conn is not None:
            mysql_conn.close()


if __name__ == "__main__":
    migrate()
