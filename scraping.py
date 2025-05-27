import requests
import schedule
import time
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables dari .env
load_dotenv()

# Koneksi ke MongoDB Atlas
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['Db_garam']
collection = db['berita_garam']

# Daftar endpoint berita
endpoints = [
    "https://api-berita-indonesia.vercel.app/tribun/kesehatan/",
    "https://api-berita-indonesia.vercel.app/republika/terbaru/",
    "https://api-berita-indonesia.vercel.app/merdeka/sehat/",
    "https://api-berita-indonesia.vercel.app/merdeka/jateng/",
    "https://api-berita-indonesia.vercel.app/cnn/gayaHidup/",
    "https://api-berita-indonesia.vercel.app/antara/terbaru/",
    "https://api-berita-indonesia.vercel.app/tribun/terbaru/",
    "https://api-berita-indonesia.vercel.app/tempo/dunia/",
]

# Fungsi scraping dan simpan
def scrap_dan_simpan():
    print(f"[{datetime.now()}] Mulai scraping...")

    # Hapus data lama
    deleted = collection.delete_many({})
    print(f"{deleted.deleted_count} data lama dihapus.")

    for endpoint in endpoints:
        try:
            res = requests.get(endpoint)
            res.raise_for_status()
            data = res.json()

            for article in data['data']['posts']:
                berita = {
                    "judul": article['title'],
                    "link": article['link'],
                    "thumbnail": article.get('thumbnail', ''),
                    "description": article.get('description', ''),
                    "pubDate": article.get('pubDate', ''),
                    "source": endpoint.split('/')[3],
                    "tanggal_scrap": datetime.now()
                }
                collection.insert_one(berita)
                print(f"Disimpan: {article['title']}")
        except Exception as e:
            print(f"Gagal ambil dari {endpoint}: {e}")

    print("Scraping selesai.\n")

# Jadwal scraping setiap 2 menit
schedule.every(2).minutes.do(scrap_dan_simpan)

print("Scheduler aktif. Tekan Ctrl+C untuk menghentikan.")

while True:
    schedule.run_pending()
    time.sleep(1)
