
import sqlite3
import pymysql
import os
from getpass import getpass

# Menentukan lokasi database SQLite lama
APP_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB = os.path.join(APP_DIR, "database_kmeans.db")

# Menghubungkan ke SQLite
sqlite_conn = sqlite3.connect(SQLITE_DB)
sqlite_cursor = sqlite_conn.cursor()

# Menghubungkan ke MySQL
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
    # Mengambil seluruh transaksi dari SQLite
    sqlite_cursor.execute("""
        SELECT
            id, product_name, quantity, orders, revenue,
            date, order_status, regency_and_city,
            province, payment_method
        FROM sales_data
    """)

    sales = sqlite_cursor.fetchall()

    print("Jumlah transaksi SQLite:", len(sales))

    # Memastikan tabel MySQL masih kosong
    mysql_cursor.execute("SELECT COUNT(*) FROM sales_data")
    jumlah_mysql = mysql_cursor.fetchone()[0]

    if jumlah_mysql != 0:
        raise RuntimeError(
            "Tabel sales_data MySQL tidak kosong. Migrasi dibatalkan."
        )

    # Memindahkan transaksi ke MySQL
    if sales:
        mysql_cursor.executemany("""
            INSERT INTO sales_data (
                id, product_name, quantity, orders, revenue,
                date, order_status, regency_and_city,
                province, payment_method
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, sales)

    # Memeriksa jumlah data sebelum disimpan
    mysql_cursor.execute("SELECT COUNT(*) FROM sales_data")
    hasil_mysql = mysql_cursor.fetchone()[0]

    if hasil_mysql != len(sales):
        raise RuntimeError(
            "Jumlah data SQLite dan MySQL berbeda!"
        )

    mysql_conn.commit()

    print("Jumlah transaksi MySQL:", hasil_mysql)
    print("Migrasi sales_data berhasil!")

except Exception:
    mysql_conn.rollback()
    raise

finally:
    sqlite_cursor.close()
    sqlite_conn.close()
    mysql_cursor.close()
    mysql_conn.close()
