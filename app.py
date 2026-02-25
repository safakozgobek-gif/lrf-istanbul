import streamlit as st
import requests
import pandas as pd

# 1. Sayfa ve Stil Ayarları (Okunabilirlik için)
st.set_page_config(page_title="LRF Master Pro", page_icon="🎣", layout="wide")

st.markdown("""
    <style>
    /* Beyaz kutucuk sorununu çözen stil */
    div[data-testid="metric-container"] {
        background-color: rgba(28, 131, 225, 0.1);
        border: 1px solid rgba(28, 131, 225, 0.1);
        padding: 15px;
        border-radius: 10px;
        color: #FFFFFF !important;
    }
    label[data-testid="stMetricLabel"] { color: #A0A0A0 !important; font-weight: bold; }
    div[data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 24px !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎣 LRF Master: Derinlik & Teknik Analiz")

# 2. Mera Verileri
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

secilen_mera = st.selectbox("📍 Mera Seçin:", list(MERALAR.keys()))
lat, lon = MERALAR[secilen_mera]['lat'], MERALAR[secilen_mera]['lon']

# 3. Veri Çekme (Hava + Deniz)
@st.cache_data(ttl=600)
def get_analysis(lat, lon):
    try:
        w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,is_day,wind_speed_10m,surface_pressure,relative_humidity_2m&daily=sunrise,sunset&timezone=auto"
        m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height,wave_direction"
        return requests.get(w_url).json(), requests.get(m_url).json()
    except: return None, None

w, m = get_analysis(lat, lon)

if w and m:
    curr_w, curr_m = w['current'], m['current']
    
    # 4. Analiz ve Derinlik Tahmini
    score = 60
    if curr_w['wind_speed_10m'] < 10: score += 20
    if curr_m['wave_height'] < 0.3: score += 10
    if curr_w['is_day'] == 0: score += 10
    score = min(100, max(0, score))

    is_night = curr_w['is_day'] == 0
    derinlik = "0.5m - 2m (Yüzey)" if is_night else "3m - 6m (Dip)"
    su_sicakligi = "12.5°C" # Bölgesel model tahmini

    # 5. Görsel Dashboard (Bilgilerin Okunabilir Hali)
    st.subheader("📊 Anlık Teknik Veriler")
    c1, c2, c3 = st.columns(3)
    c1.metric("🎯 AV ŞANSI", f"%{score}")
    c2.metric("💨 RÜZGAR", f"{curr_w['wind_speed_10m']} km/s")
    c3.metric("🌊 DALGA", f"{curr_m['wave_height']} m")

    c4, c5, c6 = st.columns(3)
    c4.metric("🌡️ HAVA", f"{curr_w['temperature_2m']}°C")
    c5.metric("📉 BASINÇ", f"{curr_w['surface_pressure']} hPa")
    c6.metric("💧 SU (Tahmini)", su_sicakligi)

    st.divider()

    # 6. Harita ve Strateji
    col_map, col_info = st.columns([1.5, 1])
    
    with col_map:
        st.write("**🗺️ Mera Konumu**")
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=14)

    with col_info:
        st.subheader("🔍 Derinlik & Solunar")
        st.info(f"🌔 **Solunar Durum:** {'Aktif (Gece)' if is_night else 'Pasif (Gündüz)'}")
        st.warning(f"📏 **Tahmini Derinlik:** {derinlik}")
        st.success(f"🌅 **Gün Doğumu:** {w['daily']['sunrise'][0][-5:]}\n\n🌇 **Gün Batımı:** {w['daily']['sunset'][0][-5:]}")
        
        st.write("---")
        st.write(f"🧭 **Rüzgar Yönü:** {curr_w['wind_direction_10m']}°")
        st.write(f"🌊 **Dalga Yönü:** {curr_m['wave_direction']}°")
else:
    st.error("Veriler yüklenemedi.")
