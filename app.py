import streamlit as st
import plotly.express as px
from pymongo import MongoClient
import pandas as pd
from urllib.parse import urlparse
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os

# --- Load variabel lingkungan ---
load_dotenv()

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="Analisis Kandungan Garam", layout="wide", page_icon="🏓")
st.title("🏓 Analisis Kandungan Garam")

# --- Koneksi ke MongoDB Atlas ---
@st.cache_resource
def load_data():
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        st.error("❌ MONGO_URI tidak ditemukan. Pastikan sudah disetel di .env.")
        st.stop()
    
    client = MongoClient(mongo_uri)
    db = client['Db_garam']
    collection = db['berita_garam']
    data = list(collection.find())
    return pd.DataFrame(data)

df = load_data()

if df.empty:
    st.warning("⚠ Tidak ada data artikel yang tersedia di database.")
    st.stop()

# --- Preprocessing ---
df = df.rename(columns={'judul': 'title', 'link': 'url', 'pubDate': 'date'})
df['parsed_date'] = pd.to_datetime(df['date'], errors='coerce')
df['domain'] = df['url'].apply(lambda x: urlparse(x).netloc if pd.notnull(x) else 'Unknown')

# --- Sidebar / Filter Controls di Atas ---
st.markdown("## 🔍 Filter Artikel")
col_a, col_b = st.columns([1, 2])
with col_a:
    domains = sorted(df['domain'].unique().tolist())
    selected_domains = st.multiselect("Pilih Domain:", options=domains, default=domains)
with col_b:
    min_date = df['parsed_date'].min().date()
    max_date = df['parsed_date'].max().date()
    date_range = st.date_input("Rentang Tanggal:", [min_date, max_date])

# --- Validasi Filter ---
if not date_range or len(date_range) != 2:
    st.warning("❗ Silakan pilih rentang tanggal yang valid.")
    st.stop()

start_date, end_date = date_range
mask = (
    df['domain'].isin(selected_domains) &
    (df['parsed_date'].dt.date.between(start_date, end_date))
)
df_filtered = df.loc[mask]

# --- Statistik Setelah Filter ---
st.markdown("### 📊 Statistik Artikel Terfilter")
col1, col2, col3 = st.columns(3)
col1.metric("📝 Total Artikel", len(df_filtered))
col2.metric("🌐 Domain Terpilih", len(selected_domains))
col3.metric("⏳ Rentang Tanggal", f"{start_date} hingga {end_date}")

# --- Tabel Artikel ---
st.markdown("### 📋 Daftar Artikel")
st.dataframe(
    df_filtered[['title', 'parsed_date', 'url']].rename(columns={'parsed_date': 'date'}),
    use_container_width=True
)

# --- Visualisasi: Artikel per Tanggal ---
st.markdown("### 📈 Artikel per Tanggal")
if not df_filtered.empty and df_filtered['parsed_date'].notnull().any():
    date_counts = df_filtered.groupby(df_filtered['parsed_date'].dt.date).size().reset_index(name='count')
    date_counts.columns = ['parsed_date', 'count']
    fig1 = px.area(date_counts, x='parsed_date', y='count', title='Distribusi Artikel per Tanggal')
    fig1.update_layout(xaxis_title='Tanggal', yaxis_title='Jumlah Artikel', plot_bgcolor='white')
    st.plotly_chart(fig1, use_container_width=True)
else:
    st.info("Tidak ada data untuk visualisasi tanggal.")

# --- Visualisasi: Proporsi Artikel per Domain ---
st.markdown("### 🌍 Proporsi Artikel per Domain")
if not df_filtered.empty:
    domain_counts = df_filtered['domain'].value_counts().reset_index()
    domain_counts.columns = ['domain', 'count']
    fig2 = px.pie(domain_counts, names='domain', values='count', title='Proporsi Domain')
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Tidak ada data untuk visualisasi domain.")

# --- Word Cloud Judul ---
st.markdown("### ☁️ Word Cloud Judul Artikel")
if not df_filtered['title'].dropna().empty:
    text = " ".join(df_filtered['title'].tolist())
    wc = WordCloud(width=800, height=400, background_color='white').generate(text)
    fig_wc, ax_wc = plt.subplots(figsize=(12, 6))
    ax_wc.imshow(wc, interpolation='bilinear')
    ax_wc.axis('off')
    st.pyplot(fig_wc)
else:
    st.info("Tidak ada judul untuk Word Cloud setelah filter.")
