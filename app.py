import streamlit as st
import requests
import pandas as pd

# 1. Sayfa Ayarları
st.set_page_config(page_title="LRF Master Pro", page_icon="🎣", layout="wide")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 26px; color: #1E88E5; }
    .stSelectbox label { font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎣 LRF Master: İstanbul Pro")

# 2. Mera Verileri
MERALAR = {
    "Kadıköy (Moda)": {"lat": 40.9780, "lon": 29.0220, "tip": "Kayalık/Derin"},
    "Üsküdar Sahil": {"lat": 41.0540, "lon": 29.0550, "tip": "Akıntılı/Derin"},
    "Caddebostan": {"lat": 40.9620, "lon": 29.0650, "tip": "Sığ/Kumluk"},
    "Dragos": {"lat": 40.8985, "lon": 29.1620, "tip": "Sığ/Kayalık"},
    "Maltepe Dolgu": {"lat": 40.9165, "lon": 29.1315, "tip": "Karma Yapı"},
    "Kartal Sahil": {"lat": 40.8870, "lon": 29.1865, "tip": "Derin Kayalık"},
    "Pendik Marina": {"lat": 40.8755, "lon": 29.2315, "tip": "Liman/Derin"},
    "Sarayburnu": {"lat": 41.0150, "lon": 28.9850, "tip": "Akıntılı/Eşkina"},
    "Beşiktaş": {"lat": 41.0470, "lon": 29.0250, "tip": "Akıntılı/İstavrit"},
    "Tarabya": {"lat": 41.1350, "lon": 29.0580, "tip": "Boğaz/Derin"},
    "Yeşilköy": {"lat": 40.9550, "lon": 28.8250, "tip": "Sığ/Mırmır"}
}

BALIK_REHBERI = {
    "İstavrit": "Pembe/Beyaz UV silikon. 0.8g-1.5g jighead.",
    "Eşkina": "Glow iri silikon. Dipte yavaş zıplatma.",
    "Mırmır": "Kum kurdu rengi. Dipte yavaş sürütme.",
    "Levrek": "Beyaz maket balık veya 7cm silikon.",
    "İskorpit": "Kırmızı/Turuncu kokulu silikon."
}

# Arayüz Düzeni
col_main, col_map = st.columns([1, 1.2])

with col_main:
    secilen_mera = st.selectbox("📍 Mera Seçin:", list(MERALAR.keys()))
    hedef_balik = st.selectbox("🐟 Hedef Balık:", list(BALIK_REHBERI.keys()))

    @st.cache_data(ttl=600)
    def get_weather(lat, lon):
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,is_day,wind_speed_10m,surface_pressure&daily=sunrise,sunset&timezone=auto"
            return requests.get(url).json()
        except: return None

    w = get_weather(MERALAR[secilen_mera]['lat'], MERALAR[secilen_mera]['lon'])

    if w:
        c = w['current']
        # Olasılık Algoritması (Rüzgar ve Basınç Etkisi)
        score = 65
        if c['wind_speed_10m'] < 10: score += 15
        elif c['wind_speed_10m'] > 18: score -= 40
        
        if c['is_day'] == 0: score += 15 # Gece LRF bonusu
        
        score = min(100, max(0, score))

        # Metrikler
        m1, m2 = st.columns(2)
        m1.metric("AV ŞANSI", f"%{score}")
        m2.metric("RÜZGAR", f"{c['wind_speed_10m']} km/s")

        st.info(f"💡 **Taktik:** {BALIK_REHBERI[hedef_balik]}")
        st.write(f"🌅 Gün Doğumu: {w['daily']['sunrise'][0][-5:]} | 🌇 Gün Batımı: {w['daily']['sunset'][0][-5:]}")

# Harita Bölümü
with col_map:
    st.write(f"🗺️ **{secilen_mera} Konumu**")
    map_data = pd.DataFrame({'lat': [MERALAR[secilen_mera]['lat']], 'lon': [MERALAR[secilen_mera]['lon']]})
    st.map(map_data, zoom=13)
