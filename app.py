import streamlit as st
import requests
import pandas as pd

# 1. Sayfa ve Görünüm Ayarları
st.set_page_config(page_title="LRF Master Pro", page_icon="🎣", layout="wide")

st.markdown("""
    <style>
    /* Okunabilirlik için karanlık tema ve belirgin yazılar */
    .stMetric {
        background-color: #1e1e1e !important;
        border: 1px solid #3e3e3e !important;
        padding: 10px;
        border-radius: 10px;
    }
    [data-testid="stMetricLabel"] { color: #00d4ff !important; font-weight: bold; }
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎣 LRF Master Pro: İstanbul")

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

secilen_mera = st.selectbox("📍 Analiz İçin Mera Seçin:", list(MERALAR.keys()))
lat, lon = MERALAR[secilen_mera]['lat'], MERALAR[secilen_mera]['lon']

# 3. Güvenli Veri Çekme Fonksiyonu
@st.cache_data(ttl=600)
def get_safe_data(lat, lon):
    try:
        w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,is_day,wind_speed_10m,wind_direction_10m,surface_pressure&daily=sunrise,sunset&timezone=auto"
        m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height,wave_direction"
        w_res = requests.get(w_url).json()
        m_res = requests.get(m_url).json()
        return w_res, m_res
    except:
        return None, None

w_data, m_data = get_safe_data(lat, lon)

if w_data and "current" in w_data:
    c_w = w_data["current"]
    c_m = m_data.get("current", {"wave_height": 0.0, "wave_direction": 0})
    
    # 4. Puanlama ve Derinlik
    score = 65
    if c_w.get('wind_speed_10m', 20) < 12: score += 15
    if c_m.get('wave_height', 1.0) < 0.4: score += 10
    if c_w.get('is_day') == 0: score += 10
    score = min(100, max(0, score))

    # 5. Dashboard (Okunabilir Panel)
    st.subheader("📊 Teknik Göstergeler")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🎯 AV ŞANSI", f"%{score}")
    col2.metric("💨 RÜZGAR", f"{c_w.get('wind_speed_10m', 'N/A')} km/s")
    col3.metric("🌊 DALGA", f"{c_m.get('wave_height', 'N/A')} m")
    col4.metric("🌡️ HAVA", f"{c_w.get('temperature_2m', 'N/A')}°C")

    st.divider()

    # 6. Harita ve Detaylar
    m_col, d_col = st.columns([1.5, 1])
    
    with m_col:
        st.write("**🗺️ Bölge Haritası**")
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=14)

    with d_col:
        st.subheader("🔍 Derinlik & Solunar")
        is_night = c_w.get('is_day') == 0
        st.info(f"🌔 **Durum:** {'Gece (Aktif)' if is_night else 'Gündüz (Pasif)'}")
        st.warning(f"📏 **Derinlik:** {'0.5m-2m (Yüzey)' if is_night else '3m-6m (Dip)'}")
        
        # Ek Bilgiler (Hata vermemesi için güvenli çekim)
        st.write(f"📉 **Basınç:** {c_w.get('surface_pressure', 'N/A')} hPa")
        st.write(f"🧭 **Rüzgar Yönü:** {c_w.get('wind_direction_10m', 'N/A')}°")
        st.write(f"🌇 **Gün Batımı:** {w_data['daily']['sunset'][0][-5:]}")

else:
    st.error("Hava durumu servisi şu an yanıt vermiyor. Lütfen birkaç dakika sonra tekrar deneyin.")
