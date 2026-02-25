import streamlit as st
import requests
from datetime import datetime

# 1. Mobil Uyumlu Sayfa Ayarları
st.set_page_config(
    page_title="LRF Master", 
    page_icon="🎣", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Telefon ekranı için özel görsel düzenleme
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; }
    .stButton>button { width: 100%; border-radius: 20px; }
    .main { background-color: #fafafa; }
    </style>
    """, unsafe_allow_index=True)

st.title("🎣 LRF Master: İstanbul")

# 2. Tüm Meralar (Tek Liste)
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
    "İskorpit": "Kırmızı/Turuncu kokulu silikon. Yavaş aksiyon."
}

# Seçim Alanları
secilen_mera = st.selectbox("📍 Mera Seçin:", list(MERALAR.keys()))
hedef_balik = st.selectbox("🐟 Hedef Balık:", list(BALIK_REHBERI.keys()))

@st.cache_data(ttl=900)
def get_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,is_day,wind_speed_10m,surface_pressure&daily=sunrise,sunset&timezone=auto"
    return requests.get(url).json()

try:
    m = MERALAR[secilen_mera]
    w = get_weather(m['lat'], m['lon'])
    c = w['current']

    # LRF Algoritması
    score = 70
    if c['wind_speed_10m'] > 12: score -= 35
    if c['is_day'] == 0: score += 20
    score = min(100, max(0, score))

    # Mobil Gösterim Kartları
    col1, col2 = st.columns(2)
    with col1:
        st.metric("AV ŞANSI", f"%{score}")
    with col2:
        st.metric("RÜZGAR", f"{c['wind_speed_10m']} km/s")

    if score > 70: st.success("🎯 Şartlar harika, rastgele!")
    elif score > 45: st.warning("⚖️ Biraz çaba gerekebilir.")
    else: st.error("🏠 Hava şu an LRF'yi zorluyor.")

    st.markdown(f"**💡 Öneri:** {BALIK_REHBERI[hedef_balik]}")
    st.info(f"🌅 Gün Doğumu: {w['daily']['sunrise'][0][-5:]} | 🌇 Gün Batımı: {w['daily']['sunset'][0][-5:]}")

except Exception:
    st.error("Veri alınamadı, interneti kontrol et.")
