
import sqlite3
import pymysql
import os
from getpass import getpass
from datetime import datetime

# Lokasi database SQLite
APP_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB = os.path.join(APP_DIR, "database_kmeans.db")

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
    # Mengambil seluruh riwayat dataset dari SQLite
    sqlite_cursor.execute("""
        SELECT id, name, uploaded_at, uploaded_by,
               is_active, data_json
        FROM datasets
        ORDER BY id
    """)

    datasets = sqlite_cursor.fetchall()

    print("Jumlah dataset SQLite:", len(datasets))

    # Memastikan tabel tujuan masih kosong
    mysql_cursor.execute("SELECT COUNT(*) FROM datasets")

    if mysql_cursor.fetchone()[0] != 0:
        raise RuntimeError(
            "Tabel datasets MySQL sudah berisi data. Migrasi dibatalkan."
        )

    # Mengubah tanggal teks SQLite menjadi datetime Python
    data_migrasi = []

    for id_, name, uploaded_at, uploaded_by, is_active, data_json in datasets:
        tanggal = datetime.fromisoformat(uploaded_at)

        data_migrasi.append((
            id_,
            name,
            tanggal,
            uploaded_by,
            is_active,
            data_json
        ))

    # Memindahkan data ke MySQL
    if data_migrasi:
        mysql_cursor.executemany("""
            INSERT INTO datasets (
                id, name, uploaded_at, uploaded_by,
                is_active, data_json
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, data_migrasi)

    # Memeriksa jumlah baris sebelum commit
    mysql_cursor.execute("SELECT COUNT(*) FROM datasets")
    jumlah_mysql = mysql_cursor.fetchone()[0]

    if jumlah_mysql != len(datasets):
        raise RuntimeError(
            "Jumlah dataset SQLite dan MySQL tidak sama!"
        )

    mysql_conn.commit()

    print("Jumlah dataset MySQL:", jumlah_mysql)
    print("Migrasi tabel datasets berhasil!")

except Exception:
    mysql_conn.rollback()
    raise

finally:
    sqlite_cursor.close()
    sqlite_conn.close()
    mysql_cursor.close()
    mysql_conn.close()
