import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 1. Sayfa Ayarları
st.set_page_config(page_title="LRF Master Pro v3", page_icon="🎣", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #f8f9fa; padding: 10px; border-radius: 10px; border: 1px solid #dee2e6; }
    [data-testid="stMetricValue"] { font-size: 20px !important; }
    .status-box { padding: 15px; border-radius: 10px; margin-bottom: 10px; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎣 LRF Master: Derinlik & Teknik Analiz")

# 2. Mera Koordinatları
MERALAR = {
    "Kadıköy (Moda)": {"lat": 40.9780, "lon": 29.0220},
    "Üsküdar Sahil": {"lat": 41.0540, "lon": 29.0550},
    "Caddebostan": {"lat": 40.9620, "lon": 29.0650},
    "Dragos": {"lat": 40.8985, "lon": 29.1620},
    "Maltepe Dolgu": {"lat": 40.9165, "lon": 29.1315},
    "Kartal Sahil": {"lat": 40.8870, "lon": 29.1865},
    "Pendik Marina": {"lat": 40.8755, "lon": 29.2315},
    "Sarayburnu": {"lat": 41.0150, "lon": 28.9850},
    "Tarabya": {"lat": 41.1350, "lon": 29.0580},
    "Yeşilköy": {"lat": 40.9550, "lon": 28.8250}
}

# 3. Veri Çekme Motoru
@st.cache_data(ttl=600)
def get_full_analysis(lat, lon):
    try:
        w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,is_day,wind_speed_10m,wind_direction_10m,surface_pressure,relative_humidity_2m&daily=sunrise,sunset&timezone=auto"
        m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height,wave_direction"
        w = requests.get(w_url).json()
        m = requests.get(m_url).json()
        return w, m
    except: return None, None

secilen_mera = st.selectbox("📍 Mera Seçin:", list(MERALAR.keys()))
lat, lon = MERALAR[secilen_mera]['lat'], MERALAR[secilen_mera]['lon']
w, m = get_full_analysis(lat, lon)

if w and m:
    curr_w, curr_m = w['current'], m['current']
    
    # 4. Derinlik Tahmin Algoritması
    # Işık ve sıcaklığa göre balığın olduğu katman
    if curr_w['is_day'] == 0:
        derinlik_tahmini = "Yüzey ve Orta Su (0.5m - 2m)"
        katman_tavsiyesi = "Balıklar beslenmek için yüzeye yakın. Glow silikonlarla yüzey taraması yap."
    else:
        derinlik_tahmini = "Dip ve Kaya Altı (3m - 6m)"
        katman_tavsiyesi = "Işıktan kaçan balık dipte. Ağır jighead ile dipte zıplatma yap."

    # Av Şansı Hesaplama
    score = 50
    if curr_w['wind_speed_10m'] < 10: score += 20
    if curr_m['wave_height'] < 0.3: score += 15
    if 1012 <= curr_w['surface_pressure'] <= 1018: score += 15
    score = min(100, max(0, score))

    # 5. Dashboard Tasarımı
    st.markdown("### 📊 Anlık Teknik Veriler")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🎯 AV ŞANSI", f"%{score}")
    c2.metric("💨 RÜZGAR", f"{curr_w['wind_speed_10m']} km/s")
    c3.metric("🌊 DALGA", f"{curr_m['wave_height']} m")
    c4.metric("🌡️ HAVA", f"{curr_w['temperature_2m']}°C")

    st.divider()

    # Alt Panel
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("🔍 Derinlik & Katman Analizi")
        st.warning(f"**Tahmini Derinlik:** {derinlik_tahmini}")
        st.info(f"**Strateji:** {katman_tavsiyesi}")
        
        # Ek Bilgiler Tablosu
        st.write("---")
        st.write(f"📉 **Basınç:** {curr_w['surface_pressure']} hPa")
        st.write(f"🧭 **Rüzgar Yönü:** {curr_w['wind_direction_10m']}°")
        st.write(f"🌇 **Gün Batımı:** {w['daily']['sunset'][0][-5:]}")

    with col_right:
        st.write("**📍 Mera Konumu**")
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=14)

else:
    st.error("Veriler alınamadı.")
