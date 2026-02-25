import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# 1. Dashboard Tasarımı
st.set_page_config(page_title="LRF Pro Terminal", page_icon="🎣", layout="wide")

st.markdown("""
    <style>
    .metric-container {
        background-color: #1a1c23;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #2d2f39;
        text-align: center;
    }
    .metric-title { color: #8a8d97; font-size: 12px; font-weight: bold; }
    .metric-value { color: #ffffff; font-size: 20px; font-weight: bold; margin: 5px 0; }
    .metric-desc { color: #00d4ff; font-size: 11px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎣 LRF Master: Profesyonel Analiz")

MERALAR = {
    "Kadıköy (Moda)": {"lat": 40.9780, "lon": 29.0220},
    "Üsküdar Sahil": {"lat": 41.0540, "lon": 29.0550},
    "Caddebostan": {"lat": 40.9620, "lon": 29.0650},
    "Dragos": {"lat": 40.8985, "lon": 29.1620},
    "Maltepe": {"lat": 40.9165, "lon": 29.1315},
    "Kartal": {"lat": 40.8870, "lon": 29.1865},
    "Sarayburnu": {"lat": 41.0150, "lon": 28.9850},
    "Tarabya": {"lat": 41.1350, "lon": 29.0580},
    "Yeşilköy": {"lat": 40.9550, "lon": 28.8250}
}

secilen_mera = st.selectbox("📍 Mera Seçin:", list(MERALAR.keys()))
lat, lon = MERALAR[secilen_mera]['lat'], MERALAR[secilen_mera]['lon']

@st.cache_data(ttl=900)
def get_pro_weather(lat, lon):
    # Hem anlık hem 24 saatlik tahmin verilerini çekiyoruz
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,is_day,surface_pressure,wind_speed_10m&hourly=temperature_2m,surface_pressure,wind_speed_10m&daily=sunrise,sunset&timezone=auto&forecast_days=1"
    m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height&hourly=wave_height"
    return requests.get(url).json(), requests.get(m_url).json()

w, m = get_pro_weather(lat, lon)

if w and "current" in w:
    cw = w["current"]
    hourly = w["hourly"]
    
    # --- PROFESYONEL PUANLAMA ALGORİTMASI ---
    def calculate_score(wind, wave, press, is_day):
        score = 50
        if wind < 10: score += 15
        elif wind > 18: score -= 30
        if wave < 0.3: score += 10
        elif wave > 0.6: score -= 20
        # Basınç dengesi (En kritik yer: 1013 hPa idealdir)
        if 1011 < press < 1015: score += 15
        if is_day == 0: score += 10
        return min(95, max(5, score))

    anlik_skor = calculate_score(cw['wind_speed_10m'], m['current']['wave_height'], cw['surface_pressure'], cw['is_day'])

    # --- ÜST PANEL (WIDGETLAR) ---
    st.markdown("### 📊 Teknik Özet")
    cols = st.columns(4)
    data = [
        ("AKTİVİTE", f"%{anlik_skor}", "Stabil" if 1010 < cw['surface_pressure'] < 1015 else "Değişken"),
        ("RÜZGAR", f"{cw['wind_speed_10m']} km/s", f"Nem: %{cw['relative_humidity_2m']}"),
        ("BASINÇ", f"{cw['surface_pressure']} hPa", "İdeal" if 1012 < cw['surface_pressure'] < 1016 else "Riskli"),
        ("DALGA", f"{m['current']['wave_height']} m", "LRF Uygun")
    ]
    
    for i, col in enumerate(cols):
        with col:
            st.markdown(f"""<div class="metric-container">
                <div class="metric-title">{data[i][0]}</div>
                <div class="metric-value">{data[i][1]}</div>
                <div class="metric-desc">{data[i][2]}</div>
            </div>""", unsafe_allow_html=True)

    # --- 24 SAATLİK TAHMİN GRAFİĞİ ---
    st.markdown("---")
    st.subheader("⏰ 24 Saatlik Av Tahmini")
    
    # Saatlik verileri işle
    forecast_data = []
    current_hour = datetime.now().hour
    for i in range(current_hour, current_hour + 24):
        idx = i % 24
        h_wind = hourly['wind_speed_10m'][idx]
        h_press = hourly['surface_pressure'][idx]
        # Basit bir gece/gündüz tahmini (18-06 arası gece)
        h_is_day = 1 if 6 < idx < 19 else 0
        h_score = calculate_score(h_wind, 0.2, h_press, h_is_day)
        forecast_data.append({"Saat": f"{idx}:00", "Av Şansı": h_score})
    
    df_forecast = pd.DataFrame(forecast_data)
    st.line_chart(df_forecast.set_index("Saat"), height=250)

    # --- HARİTA VE DETAY ---
    st.markdown("---")
    l_col, r_col = st.columns([1.5, 1])
    with l_col:
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=14)
    with r_col:
        st.info(f"🌔 **Derinlik:** {'Yüzey (Işık/Gece)' if cw['is_day'] == 0 else 'Dip (Baskı/Gündüz)'}")
        st.write(f"🌅 Gün Doğumu: {w['daily']['sunrise'][0][-5:]}")
        st.write(f"🌇 Gün Batımı: {w['daily']['sunset'][0][-5:]}")

else:
    st.error("Veri merkeziyle bağlantı kesildi.")
