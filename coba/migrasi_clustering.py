
import sqlite3
import pymysql
import os
from getpass import getpass
from datetime import datetime

# Lokasi database SQLite lama
APP_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB = os.path.join(APP_DIR, "database_kmeans.db")

# Koneksi SQLite
sqlite_conn = sqlite3.connect(SQLITE_DB)
sqlite_cursor = sqlite_conn.cursor()

# Koneksi MySQL
mysql_conn = pymysql.connect(
    host="localhost",
    port=3306,
    user="root",
    password=getpass("Masukkan password MySQL: "),
    database="sjb_database",
    charset="utf8mb4",
    autocommit=False
)
mysql_cursor = mysql_conn.cursor()

try:
    # Mengambil seluruh riwayat clustering dari SQLite
    sqlite_cursor.execute("""
        SELECT
            id, clustered_at, dataset_id, dataset_name,
            clustered_by, k, silhouette, dbi,
            result_json, centroid_json, insight, recommendation
        FROM clustering_history
        ORDER BY id
    """)

    data_sqlite = sqlite_cursor.fetchall()

    print("Jumlah riwayat SQLite:", len(data_sqlite))

    # Memastikan tabel MySQL masih kosong
    mysql_cursor.execute(
        "SELECT COUNT(*) FROM clustering_history"
    )

    if mysql_cursor.fetchone()[0] != 0:
        raise RuntimeError(
            "Tabel clustering_history MySQL tidak kosong. "
            "Migrasi dibatalkan."
        )

    # Mengubah tanggal teks menjadi datetime
    data_migrasi = []

    for row in data_sqlite:
        row = list(row)
        row[1] = datetime.fromisoformat(row[1])
        data_migrasi.append(tuple(row))

    # Menyalin data ke MySQL
    if data_migrasi:
        mysql_cursor.executemany("""
            INSERT INTO clustering_history (
                id, clustered_at, dataset_id, dataset_name,
                clustered_by, k, silhouette, dbi,
                result_json, centroid_json, insight, recommendation
            )
            VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
        """, data_migrasi)

    # Memeriksa jumlah data sebelum disimpan
    mysql_cursor.execute(
        "SELECT COUNT(*) FROM clustering_history"
    )

    jumlah_mysql = mysql_cursor.fetchone()[0]

    if jumlah_mysql != len(data_sqlite):
        raise RuntimeError(
            "Jumlah riwayat SQLite dan MySQL berbeda!"
        )

    mysql_conn.commit()

    print("Jumlah riwayat MySQL:", jumlah_mysql)
    print("Migrasi clustering_history berhasil!")

except Exception:
    mysql_conn.rollback()
    raise

finally:
    sqlite_cursor.close()
    sqlite_conn.close()
    mysql_cursor.close()
    mysql_conn.close()
