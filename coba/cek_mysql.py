
import pymysql
from getpass import getpass

# Meminta password MySQL
password_mysql = getpass("Masukkan password MySQL: ")

# Membuat koneksi ke database MySQL
conn = pymysql.connect(
    host="localhost",
    user="root",
    password=password_mysql,
    database="sjb_database",
    port=3306
)

print("Koneksi ke MySQL berhasil!")

# Memeriksa nama database yang digunakan
cursor = conn.cursor()
cursor.execute("SELECT DATABASE()")

nama_database = cursor.fetchone()[0]
print("Database aktif:", nama_database)

# Menutup koneksi
cursor.close()
conn.close()
