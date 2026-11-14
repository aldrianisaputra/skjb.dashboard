
import pymysql
import os

# Konfigurasi sesuai app.py
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_DATABASE = "sjb_database"

def get_connection():
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=os.environ["SJB_MYSQL_PASSWORD"],
        database=MYSQL_DATABASE,
        charset="utf8mb4",
        autocommit=False
    )

conn = get_connection()
cursor = conn.cursor()

try:
    cursor.execute("SELECT DATABASE()")
    print("Database aktif:", cursor.fetchone()[0])

    cursor.execute("SELECT COUNT(*) FROM users")
    print("Jumlah pengguna:", cursor.fetchone()[0])

    print("Pengujian koneksi berhasil!")

finally:
    cursor.close()
    conn.close()
