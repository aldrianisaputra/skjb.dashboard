
import sqlite3
import pymysql
import os
from getpass import getpass

# Koneksi database SQLite lama
sqlite_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "database_kmeans.db"
)
sqlite_conn = sqlite3.connect(sqlite_path)
sqlite_cursor = sqlite_conn.cursor()

# Koneksi database MySQL baru
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
    # Mengambil data akun dari SQLite
    sqlite_cursor.execute(
        "SELECT id, username, password, role FROM users"
    )
    users = sqlite_cursor.fetchall()

    print("Jumlah pengguna SQLite:", len(users))

    # Memastikan tabel MySQL masih kosong
    mysql_cursor.execute("SELECT COUNT(*) FROM users")

    if mysql_cursor.fetchone()[0] != 0:
        raise RuntimeError(
            "Tabel users MySQL tidak kosong. Migrasi dibatalkan."
        )

    # Memindahkan akun ke MySQL
    mysql_cursor.executemany(
        """
        INSERT INTO users (id, username, password, role)
        VALUES (%s, %s, %s, %s)
        """,
        users
    )

    mysql_conn.commit()
    print("Migrasi tabel users berhasil!")

except Exception:
    mysql_conn.rollback()
    raise

finally:
    sqlite_cursor.close()
    sqlite_conn.close()
    mysql_cursor.close()
    mysql_conn.close()
