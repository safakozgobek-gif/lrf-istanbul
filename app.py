import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 1. Stil ve Dashboard Ayarları
st.set_page_config(page_title="LRF Master: Target Edition", page_icon="🎣", layout="wide")

st.markdown("""
    <style>
    .metric-card { background-color: #161b22; padding: 12px; border-radius: 10px; border: 1px solid #30363d; text-align: center; }
    .metric-label { color: #8b949e; font-size: 12px; font-weight: bold; }
    .metric-value { color: #58a6ff; font-size: 18px; font-weight: bold; }
    .target-card { background-color: #0d1117; padding: 15px; border-radius: 10px; border: 1px solid #238636; text-align: center; margin-bottom: 10px; }
    .target-name { color: #ffffff; font-weight: bold; font-size: 16px; }
    .target-score { color: #238636; font-size: 20px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎣 LRF Master: Hedef Balık Analizi")

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
def get_fishing_data(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,is_day,surface_pressure,wind_speed_10m&hourly=surface_pressure&daily=sunrise,sunset&timezone=Europe%2FIstanbul&forecast_days=1"
    m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height&timezone=Europe%2FIstanbul"
    return requests.get(url).json(), requests.get(m_url).json()

w, m = get_fishing_data(lat, lon)

if w and "current" in w:
    cw, mw = w["current"], m["current"]
    
    # --- BASINÇ TRENDİ ---
    current_hour = datetime.now().hour
    prev_press = w['hourly']['surface_pressure'][max(0, current_hour-3)]
    press_diff = cw['surface_pressure'] - prev_press
    
    # --- BALIK BAZLI PUANLAMA MOTORU ---
    def calculate_fish_score(fish_type, wind, wave, press, is_day, p_diff):
        score = 50
        if fish_type == "İstavrit":
            if wind < 15: score += 20
            if is_day == 0: score += 15
        elif fish_type == "Eşkina":
            if wind < 8: score += 25
            if wave < 0.2: score += 20
            if is_day == 0: score += 30
            else: score -= 40 # Gündüz Eşkina zordur
        elif fish_type == "Mırmır":
            if 1012 < press < 1016: score += 20
            if wave < 0.4: score += 15
            if p_diff > 0: score += 10
        elif fish_type == "Levrek":
            if 8 < wind < 20: score += 15 # Az dalgalı sever
            if wave > 0.4: score += 15
            if p_diff < 0: score += 10 # Alçalan basınç iştah açar
        return min(95, max(5, score))

    # --- ÜST PANEL: TEKNİK VERİLER ---
    cols = st.columns(4)
    data = [("💨 RÜZGAR", f"{cw['wind_speed_10m']} km/h"), ("📉 BASINÇ", f"{cw['surface_pressure']} hPa"), 
            ("🌊 DALGA", f"{mw['wave_height']} m"), ("🌡️ HAVA", f"{cw['temperature_2m']}°C")]
    for i, col in enumerate(cols):
        with col:
            st.markdown(f'<div class="metric-card"><div class="metric-label">{data[i][0]}</div><div class="metric-value">{data[i][1]}</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # --- HEDEF BALIK SKORLARI ---
    st.subheader("🎯 Hedef Balık Aktivite Tahmini")
    f_cols = st.columns(4)
    targets = ["İstavrit", "Eşkina", "Mırmır", "Levrek"]
    
    for i, fish in enumerate(targets):
        f_score = calculate_fish_score(fish, cw['wind_speed_10m'], mw['wave_height'], cw['surface_pressure'], cw['is_day'], press_diff)
        with f_cols[i]:
            st.markdown(f"""<div class="target-card">
                <div class="target-name">{fish}</div>
                <div class="target-score">%{f_score}</div>
                <div style="color:#8b949e; font-size:11px;">Aktivite Durumu</div>
            </div>""", unsafe_allow_html=True)

    # --- DETAYLI ANALİZ VE TAKTİK ---
    st.markdown("---")
    l_col, r_col = st.columns([1, 1])
    
    with l_col:
        st.subheader("🕵️ Profesyonel Değerlendirme")
        if cw['is_day'] == 0:
            st.success("GECE PERİYODU: Balıklar kıyıya yanaştı. Yüzey ve orta su (0.5m-1.5m) taraması yap.")
        else:
            st.warning("GÜNDÜZ PERİYODU: Balık derinde ve taş altlarında. 3m-6m derinlik, dip aksiyonu şart.")
        
        st.info(f"💡 **Taktik:** { 'Basınç yükseliyor, balık hareketli. Glow silikon dene.' if press_diff > 0 else 'Basınç düşüyor, balık nazlı. Kokulu worm ve ağır aksiyon kullan.' }")

    with r_col:
        st.write("**📍 Mera Görünümü**")
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=14)

else:
    st.error("Veri alınamadı, lütfen sayfayı yenileyin.")
