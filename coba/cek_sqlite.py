import sqlite3

# Menghubungkan Python dengan SQLite
conn = sqlite3.connect("database_kmeans.db")

cursor = conn.cursor()

# Daftar tabel yang akan diperiksa
tabel = [
    "users",
    "sales_data",
    "datasets",
    "clustering_history"
]

# Menghitung jumlah data setiap tabel
for nama_tabel in tabel:
    cursor.execute(f"SELECT COUNT(*) FROM {nama_tabel}")
    jumlah = cursor.fetchone()[0]

    print(f"{nama_tabel}: {jumlah} data")

# Menutup koneksi database
conn.close()