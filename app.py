import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 1. Sayfa Tasarımı ve Profesyonel Tema
st.set_page_config(page_title="LRF Master Pro Dashboard", page_icon="🎣", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .metric-card {
        background-color: #161b22;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #30363d;
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-label { color: #8b949e; font-size: 14px; font-weight: bold; margin-bottom: 5px; }
    .metric-value { color: #58a6ff; font-size: 24px; font-weight: bold; }
    .status-active { color: #238636; font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)

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

st.title("🎣 LRF Master: Profesyonel Av Dashboard")

# Yan Menü / Üst Seçim
secilen_mera = st.selectbox("📍 Analiz Edilecek Bölgeyi Seçin", list(MERALAR.keys()))
lat, lon = MERALAR[secilen_mera]['lat'], MERALAR[secilen_mera]['lon']

@st.cache_data(ttl=600)
def fetch_pro_data(lat, lon):
    try:
        w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,surface_pressure,wind_speed_10m,wind_direction_10m&daily=sunrise,sunset,uv_index_max&timezone=auto"
        m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height,wave_direction,wave_period"
        return requests.get(w_url).json(), requests.get(m_url).json()
    except: return None, None

w, m = fetch_pro_data(lat, lon)

if w and "current" in w:
    cw, dw, cm = w["current"], w["daily"], m.get("current", {})

    # Profesyonel Skorlama (Örneklerdeki gibi dengeli)
    score = 50
    if cw['wind_speed_10m'] < 12: score += 20
    if cm.get('wave_height', 0) < 0.4: score += 15
    if 1010 < cw['surface_pressure'] < 1020: score += 10
    score = min(94, score) # %100 gerçekçi değil, tavan çektik

    # --- ÜST PANEL: ÖZET METRİKLER ---
    col1, col2, col3, col4 = st.columns(4)
    
    metrics = [
        ("🎯 AKTİVİTE", f"%{score}", "Yüksek" if score > 70 else "Orta"),
        ("🌡️ SICAKLIK", f"{cw['temperature_2m']}°C", f"His: {cw['apparent_temperature']}°C"),
        ("💨 RÜZGAR", f"{cw['wind_speed_10m']} km/s", f"Yön: {cw['wind_direction_10m']}°"),
        ("🌊 DALGA", f"{cm.get('wave_height', '0.2')} m", f"Periyot: {cm.get('wave_period', '-')}s")
    ]

    for col, (label, value, sub) in zip([col1, col2, col3, col4], metrics):
        with col:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                    <div class="status-active">{sub}</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # --- ORTA PANEL: HARİTA VE SOLUNAR ---
    c_left, c_right = st.columns([1.5, 1])

    with c_left:
        st.markdown("### 🗺️ Mera Konumu")
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=14)

    with c_right:
        st.markdown("### 🌕 Solunar & Çizelge")
        st.info(f"📏 **Tahmini Derinlik:** {'0.5m - 2m (Yüzey)' if cw['is_day'] == 0 else '3m - 6m (Dip)'}")
        st.write(f"📉 **Basınç:** {cw['surface_pressure']} hPa")
        st.write(f"💧 **Nem:** %{cw['relative_humidity_2m']}")
        st.write(f"🌅 **Gün Doğumu:** {dw['sunrise'][0][-5:]}")
        st.write(f"🌇 **Gün Batımı:** {dw['sunset'][0][-5:]}")
        st.write(f"☀️ **UV İndeksi:** {dw['uv_index_max'][0]}")
        
        # Dinamik Öneri
        if cw['surface_pressure'] > 1018:
            st.success("✅ Yüksek Basınç: Balık iştahlı olabilir, hareketli sahteler dene.")
        else:
            st.warning("⚠️ Basınç Değişimi: Balık nazlı olabilir, kokulu silikonlara geç.")

    # --- ALT PANEL: EK BİLGİLER ---
    st.markdown("---")
    st.caption("Veriler Open-Meteo Marine ve Astronomy servisleri tarafından anlık sağlanmaktadır.")

else:
    st.error("Veri alınamadı. Lütfen internet bağlantınızı veya API durumunu kontrol edin.")
