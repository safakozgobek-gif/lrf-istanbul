import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 1. Dashboard Ayarları
st.set_page_config(page_title="LRF Master Pro", page_icon="🎣", layout="wide")

st.markdown("""
    <style>
    .metric-card { background-color: #161b22; padding: 15px; border-radius: 12px; border: 1px solid #30363d; text-align: center; }
    .target-card { background-color: #0d1117; padding: 15px; border-radius: 10px; border-bottom: 3px solid #58a6ff; text-align: center; margin-bottom: 10px; }
    .target-score { color: #58a6ff; font-size: 24px; font-weight: bold; }
    .lrf-advice { background-color: #1c2128; padding: 20px; border-radius: 10px; border: 1px dashed #444c56; margin-top: 15px; line-height: 1.6; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎣 LRF Master: İstanbul Teknik Terminal")

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

secilen_mera = st.selectbox("📍 Analiz Edilecek Mera:", list(MERALAR.keys()))
lat = MERALAR[secilen_mera]['lat']
lon = MERALAR[secilen_mera]['lon']

@st.cache_data(ttl=600)
def get_weather_data(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,is_day,surface_pressure,wind_speed_10m&hourly=surface_pressure,wind_speed_10m&daily=sunrise,sunset&timezone=Europe%2FIstanbul&forecast_days=1"
        m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height&hourly=wave_height&timezone=Europe%2FIstanbul"
        w_res = requests.get(url).json()
        m_res = requests.get(m_url).json()
        return w_res, m_res
    except:
        return None, None

w_data, m_data = get_weather_data(lat, lon)

if w_data and "current" in w_data:
    cw = w_data["current"]
    mw = m_data.get("current", {"wave_height": 0.2})
    
    # Basınç Trendi Hesaplama
    current_h = datetime.now().hour
    p_prev = w_data['hourly']['surface_pressure'][max(0, current_h-3)]
    p_diff = cw['surface_pressure'] - p_prev
    trend_msg = "Yükseliyor (Olumlu)" if p_diff > 0.3 else "Düşüyor (Nazlı)" if p_diff < -0.3 else "Stabil"

    # Gelişmiş Dinamik Puanlama
    def get_dynamic_score(fish, wind, wave, press, is_day, p_trend):
        s = 40
        if wind > 16: s -= 30
        elif wind < 10: s += 15
        if wave < 0.3: s += 10
        if 1011 < press < 1016: s += 15
        if p_trend > 0: s += 5
        
        # Balık Spesifik
        if fish == "Eşkina" or fish == "İskorpit":
            if is_day == 1: return 10
            s += 25
        if fish == "Zargana" and is_day == 0: return 5
        if fish == "İstavrit" and is_day == 0: s += 15
        
        return min(94, max(5, s))

    # --- ÜST PANEL ---
    cols = st.columns(4)
    c_data = [("💨 RÜZGAR", f"{cw['wind_speed_10m']} km/h"), ("📉 BASINÇ", f"{cw['surface_pressure']} hPa"), 
              ("🌊 DALGA", f"{mw['wave_height']} m"), ("🌡️ HAVA", f"{cw['temperature_2m']}°C")]
    for i, col in enumerate(cols):
        with col:
            st.markdown(f'<div class="metric-card"><div style="color:#8b949e; font-size:12px;">{c_data[i][0]}</div><div style="color:#ffffff; font-size:20px; font-weight:bold;">{c_data[i][1]}</div></div>', unsafe_allow_html=True)

    # --- HEDEF BALIKLAR ---
    st.markdown("---")
    st.subheader("🎯 Hedef Balık Aktivitesi")
    targets = ["İstavrit", "Eşkina", "İskorpit", "İspari", "Zargana", "Mırmır"]
    f_cols = st.columns(3)
    for i, f in enumerate(targets):
        fs = get_dynamic_score(f, cw['wind_speed_10m'], mw['wave_height'], cw['surface_pressure'], cw['is_day'], p_diff)
        with f_cols[i % 3]:
            st.markdown(f'<div class="target-card"><div style="color:#8b949e; font-size:13px;">{f}</div><div class="target-score">%{fs}</div></div>', unsafe_allow_html=True)

    # --- LRF EKSPERTİZ ---
    st.markdown(f"""<div class="lrf-advice">
        <b>🔍 LRF Teknik Analiz Raporu</b><br>
        <b>Derinlik:</b> {'Yüzey (0.5 - 1.5m)' if cw['is_day'] == 0 else 'Dip (3.0 - 6.0m)'}<br>
        <b>Basınç Trendi:</b> {trend_msg} ({p_diff:.1f} hPa değişim)<br>
        <b>Worm Tavsiyesi:</b> {'Glow / UV Pembe Silikon' if cw['is_day'] == 0 else 'Doğal Kum / Karides Rengi'}<br>
        <b>Aksiyon:</b> {'Yavaş 'shake' aksiyonu' if mw['wave_height'] < 0.3 else 'Sert 'darting' aksiyonu'}
    </div>""", unsafe_allow_html=True)

    # --- 24 SAATLİK GRAFİK ---
    st.markdown("### ⏰ 24 Saatlik Değişim Tahmini (TR Saati)")
    t_list = [datetime.fromisoformat(t).strftime('%H:00') for t in w_data['hourly']['time'][:24]]
    s_list = [get_dynamic_score("İstavrit", w_data['hourly']['wind_speed_10m'][i], 0.2, w_data['hourly']['surface_pressure'][i], 1 if 6 < i < 19 else 0, 0) for i in range(24)]
    st.line_chart(pd.DataFrame({"Saat": t_list, "Aktivite": s_list}).set_index("Saat"), height=250)

    st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=14)
else:
    st.error("Veri bağlantı hatası. Lütfen sayfayı yenileyin.")
