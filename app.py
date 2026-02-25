import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 1. Sayfa Ayarları
st.set_page_config(page_title="LRF Pro Analyzer", page_icon="🎣", layout="wide")

st.markdown("""
    <style>
    .metric-card { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #007BFF; }
    [data-testid="stMetricValue"] { font-size: 22px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎣 LRF Master Pro: Teknik Veri Paneli")

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

# 3. Veri Çekme (Hava + Deniz + Astronomi)
@st.cache_data(ttl=900)
def get_extended_data(lat, lon):
    try:
        # Hava ve Genel
        w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,is_day,wind_speed_10m,wind_direction_10m,surface_pressure,relative_humidity_2m&daily=sunrise,sunset&timezone=auto"
        # Denizcilik (Dalga)
        m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height,wave_direction"
        
        w = requests.get(w_url).json()
        m = requests.get(m_url).json()
        return w, m
    except: return None, None

secilen_mera = st.selectbox("📍 Analiz Edilecek Merayı Seçin:", list(MERALAR.keys()))
lat, lon = MERALAR[secilen_mera]['lat'], MERALAR[secilen_mera]['lon']
w, m = get_extended_data(lat, lon)

if w and m:
    curr_w = w['current']
    curr_m = m['current']
    
    # 4. Gelişmiş Skorlama (Solunar ve Deniz Şartları)
    score = 55
    if curr_w['wind_speed_10m'] < 12: score += 15
    if curr_m['wave_height'] < 0.4: score += 15
    if curr_w['is_day'] == 0: score += 10 # Gece avantajı
    if 1010 < curr_w['surface_pressure'] < 1020: score += 10 # Basınç dengesi
    
    score = min(100, max(0, score))

    # 5. Kullanıcı Bilgi Paneli (Dashboard)
    st.subheader(f"📊 {secilen_mera} Anlık Teknik Veriler")
    
    # Birinci Satır: Temel Göstergeler
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🎯 AV ŞANSI", f"%{score}")
    col2.metric("💨 RÜZGAR", f"{curr_w['wind_speed_10m']} km/s")
    col3.metric("🌊 DALGA", f"{curr_m['wave_height']} m")
    col4.metric("🌡️ SICAKLIK", f"{curr_w['temperature_2m']}°C")

    # İkinci Satır: Detaylı Bilgiler
    st.markdown("---")
    d1, d2, d3, d4 = st.columns(4)
    d1.write(f"🧭 **Rüzgar Yönü:** {curr_w['wind_direction_10m']}°")
    d2.write(f"📉 **Basınç:** {curr_w['surface_pressure']} hPa")
    d3.write(f"💧 **Nem:** %{curr_w['relative_humidity_2m']}")
    d4.write(f"🌓 **Periyot:** {'GECE' if curr_w['is_day'] == 0 else 'GÜNDÜZ'}")

    # 6. Harita ve Solunar Zamanları
    st.markdown("---")
    m_col, s_col = st.columns([1.5, 1])
    
    with m_col:
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=13)
        
    with s_col:
        st.success("☀️ **Solunar ve Günlük Döngü**")
        st.write(f"🌅 **Gün Doğumu:** {w['daily']['sunrise'][0][-5:]}")
        st.write(f"🌇 **Gün Batımı:** {w['daily']['sunset'][0][-5:]}")
        st.write(f"🌊 **Dalga Yönü:** {curr_m['wave_direction']}°")
        
        # Dinamik Tavsiye Kutusu
        st.info("💡 **Günün Tavsiyesi**")
        if curr_w['surface_pressure'] < 1005:
            st.write("Düşük Basınç: Balık derine çekilmiş olabilir, dip taraması yap.")
        elif curr_m['wave_height'] > 0.5:
            st.write("Dalgalı Deniz: Aksiyonu yüksek, ses çıkaran sahteler seç.")
        else:
            st.write("Sakin Su: Doğal renkler ve yavaş aksiyon ile avlan.")

else:
    st.error("Veri bağlantısı kurulamadı.")
