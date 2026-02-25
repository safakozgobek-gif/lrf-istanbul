import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 1. Dashboard Tasarımı
st.set_page_config(page_title="LRF Master: Real-Time Stats", page_icon="🎣", layout="wide")

st.markdown("""
    <style>
    .metric-card { background-color: #0d1117; padding: 15px; border-radius: 12px; border: 1px solid #30363d; text-align: center; }
    .target-card { background-color: #161b22; padding: 15px; border-radius: 10px; border-bottom: 3px solid #58a6ff; text-align: center; margin-bottom: 10px; }
    .target-score { color: #58a6ff; font-size: 24px; font-weight: bold; }
    .lrf-advice { background-color: #1c2128; padding: 15px; border-radius: 10px; border: 1px dashed #444c56; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎣 LRF Master: Dinamik İstatistik Terminali")

MERALAR = {
    "Kadıköy (Moda)": {"lat": 40.9780, "lon": 29.0220, "expo": "SW"},
    "Üsküdar Sahil": {"lat": 41.0540, "lon": 29.0550, "expo": "W"},
    "Caddebostan": {"lat": 40.9620, "lon": 29.0650, "expo": "S"},
    "Dragos": {"lat": 40.8985, "lon": 29.1620, "expo": "S"},
    "Maltepe": {"lat": 40.9165, "lon": 29.1315, "expo": "S"},
    "Kartal": {"lat": 40.8870, "lon": 29.1865, "expo": "S"},
    "Sarayburnu": {"lat": 41.0150, "lon": 28.9850, "expo": "NE"},
    "Tarabya": {"lat": 41.1350, "lon": 29.0580, "expo": "NE"},
    "Yeşilköy": {"lat": 40.9550, "lon": 28.8250, "expo": "SW"}
}

secilen_mera = st.selectbox("📍 Analiz Edilecek Mera:", list(MERALAR.keys()))
m_info = MERALAR[secilen_mera]

@st.cache_data(ttl=600)
def get_dynamic_data(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,is_day,surface_pressure,wind_speed_10m,wind_direction_10m&hourly=surface_pressure,wind_speed_10m&daily=sunrise,sunset&timezone=Europe%2FIstanbul&forecast_days=1"
    m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height,wave_direction&hourly=wave_height&timezone=Europe%2FIstanbul"
    return requests.get(url).json(), requests.get(m_url).json()

w, m = get_dynamic_data(m_info['lat'], m_info['lon'])

if w and "current" in w:
    cw, mw = w["current"], m["current"]
    curr_h = datetime.now().hour
    # Basınç Trendi (Son 3 saatlik değişim hızı)
    p_diff = cw['surface_pressure'] - w['hourly']['surface_pressure'][max(0, curr_h-3)]
    
    # --- GELİŞMİŞ DİNAMİK PUANLAMA ---
    def get_dynamic_fish_score(type, wind, wave, press, is_day, p_trend, w_dir):
        # Temel Başlangıç (Zayıf Fikir Eleme Mantığı)
        s = 35 
        
        # 1. Rüzgar Cezası: LRF'de 15 km/h üstü rüzgar "Zayıf Fikir"dir.
        if wind > 15: s -= 25
        elif wind < 8: s += 20
        
        # 2. Basınç Trendi: Hızlı düşüş balığı kilitler.
        if p_trend < -0.8: s -= 20
        elif 1012 < press < 1015: s += 15
        
        # 3. Solunar ve Tür Spesifik
        if type == "İstavrit":
            if is_day == 0: s += 25
            if wind < 12: s += 10
        elif type == "Eşkina":
            if is_day == 1: return 8 # Gündüz imkansız
            if wind < 6 and wave < 0.2: s += 40
        elif type == "İskorpit":
            if is_day == 0: s += 30
            s += 10 if wind < 10 else -10
        elif type == "Zargana":
            if is_day == 0: return 4 # Gece imkansız
            if wind < 10 and wave < 0.3: s += 35
        elif type == "İspari":
            if is_day == 1: s += 20
            if wave < 0.4: s += 15
        elif type == "Mırmır":
            if 1011 < press < 1015 and p_trend >= 0: s += 30
        
        return min(94, max(5, s))

    # --- DASHBOARD ---
    st.markdown("### 📊 Anlık İstatistikler")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">💨 RÜZGAR</div><div class="metric-value">{cw["wind_speed_10m"]} km/h</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">📉 BASINÇ</div><div class="metric-value">{cw["surface_pressure"]} hPa</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-label">🌊 DALGA</div><div class="metric-value">{mw["wave_height"]} m</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-label">💧 NEM</div><div class="metric-value">%{cw["relative_humidity_2m"]}</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    
    # --- BALIK ANALİZİ ---
    st.subheader("🎯 Hedef Odaklı Aktivite")
    targets = ["İstavrit", "Eşkina", "İskorpit", "İspari", "Zargana", "Mırmır"]
    cols = st.columns(3)
    for i, f in enumerate(targets):
        fs = get_dynamic_fish_score(f, cw['wind_speed_10m'], mw['wave_height'], cw['surface_pressure'], cw['is_day'], p_diff, cw['wind_direction_10m'])
        with cols[i % 3]:
            st.markdown(f'<div class="target-card"><div class="target-name">{f}</div><div class="target-score">%{fs}</div></div>', unsafe_allow_html=True)

    # --- REALİST DEĞERLENDİRME ---
    st.markdown("### 🕵️ LRF Ekspertiz Raporu")
    st.markdown(f"""<div class="lrf-advice">
        <b>Derinlik:</b> {'0.5 - 1.5m (Yüzey Aktif)' if cw['is_day'] == 0 else '3.0 - 6.0m (Dip Baskı)'}<br>
        <b>Basınç Analizi:</b> {trend_text := "Dengeli ve Olumlu" if p_diff >= 0 else "Düşüşte (Balık Nazlı)"}<br>
        <b>Worm Tavsiyesi:</b> {'Glow/Parlak Renkler' if cw['is_day'] == 0 else 'Doğal/Şeffaf Tonlar'}<br>
        <b>Aksiyon:</b> {'Hafif Titreşim' if mw['wave_height'] < 0.3 else 'Sert Darting'}
    </div>""", unsafe_allow_html=True)

    # --- 24 SAATLİK TAHMİN ---
    st.markdown("### ⏰ 24 Saatlik Değişim Grafiği")
    t_list = [datetime.fromisoformat(t).strftime('%H:00') for t in w['hourly']['time'][:24]]
    # İstavrit üzerinden genel bir aktivite tahmini
    s_list = [get_dynamic_fish_score("İstavrit", w['hourly']['wind_speed_10m'][i], 0.2, w['hourly']['surface_pressure'][i], 1 if 6 < i < 19 else 0, 0, 0) for i in range(24)]
    st.line_chart(pd.DataFrame({"Saat": t_list, "Aktivite": s_list}).set_index("Saat"), height=250)
