import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 1. Dashboard ve Tema Ayarları
st.set_page_config(page_title="LRF Master Pro Terminal", page_icon="🎣", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    .metric-card { background-color: #161b22; padding: 15px; border-radius: 12px; border: 1px solid #30363d; text-align: center; }
    .target-card { background-color: #0d1117; padding: 15px; border-radius: 10px; border-bottom: 3px solid #58a6ff; text-align: center; margin-bottom: 10px; }
    .target-score { color: #58a6ff; font-size: 24px; font-weight: bold; }
    .lrf-advice-box { background-color: #1c2128; padding: 20px; border-radius: 10px; border: 1px dashed #444c56; margin-top: 15px; color: #adbac7; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎣 LRF Master: İstanbul Teknik Terminal")

# 2. Meralar ve Koordinatlar
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
lat, lon = MERALAR[secilen_mera]['lat'], MERALAR[secilen_mera]['lon']

# 3. Veri Çekme Motoru
@st.cache_data(ttl=600)
def get_clean_data(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,is_day,surface_pressure,wind_speed_10m&hourly=surface_pressure,wind_speed_10m&daily=sunrise,sunset&timezone=Europe%2FIstanbul&forecast_days=1"
        m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height&hourly=wave_height&timezone=Europe%2FIstanbul"
        w = requests.get(url).json()
        m = requests.get(m_url).json()
        return w, m
    except: return None, None

w, m = get_clean_data(lat, lon)

if w and "current" in w:
    cw = w["current"]
    # Basınç Trendi (Hata payını sıfıra indiren yöntem)
    p_diff = cw['surface_pressure'] - w['hourly']['surface_pressure'][0]
    trend_txt = "Yükseliyor (Pozitif)" if p_diff > 0.3 else "Düşüyor (Nazlı)" if p_diff < -0.3 else "Stabil"

    # Dinamik İstatistik Algoritması (Türlere Göre)
    def calc_dynamic_stat(fish, wind, press, is_day, p_trend):
        s = 40
        if wind > 16: s -= 35
        elif wind < 10: s += 20
        if 1012 < press < 1016: s += 15
        if p_trend > 0: s += 10
        
        # Tür Spesifik Mantık
        if fish in ["Eşkina", "İskorpit"] and is_day == 1: return 8
        if fish == "Zargana" and is_day == 0: return 4
        if fish == "İspari" and is_day == 1: s += 15
        if fish == "İstavrit" and is_day == 0: s += 20
        return min(94, max(5, s))

    # --- ÜST PANEL: TEKNİK BİLGİLER ---
    st.markdown("### 📊 Anlık Göstergeler")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="metric-card"><div style="color:#8b949e; font-size:12px;">💨 RÜZGAR</div><div style="color:#ffffff; font-size:20px; font-weight:bold;">{cw["wind_speed_10m"]} km/h</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div style="color:#8b949e; font-size:12px;">📉 BASINÇ</div><div style="color:#ffffff; font-size:20px; font-weight:bold;">{cw["surface_pressure"]} hPa</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div style="color:#8b949e; font-size:12px;">🌊 DALGA</div><div style="color:#ffffff; font-size:20px; font-weight:bold;">{m["current"]["wave_height"]} m</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div style="color:#8b949e; font-size:12px;">🌡️ HAVA</div><div style="color:#ffffff; font-size:20px; font-weight:bold;">{cw["temperature_2m"]}°C</div></div>', unsafe_allow_html=True)

    # --- HEDEF BALIKLAR ---
    st.markdown("---")
    st.subheader("🎯 İstanbul Hedef Balık Aktivitesi")
    targets = ["İstavrit", "Eşkina", "İskorpit", "İspari", "Zargana", "Mırmır"]
    rows = st.columns(3)
    for i, t in enumerate(targets):
        ts = calc_dynamic_stat(t, cw['wind_speed_10m'], cw['surface_pressure'], cw['is_day'], p_diff)
        with rows[i % 3]:
            st.markdown(f'<div class="target-card"><div style="color:#8b949e; font-size:13px;">{t}</div><div class="target-score">%{ts}</div></div>', unsafe_allow_html=True)

    # --- LRF EKSPERTİZ VE AKSİYON ---
    st.markdown(f"""<div class="lrf-advice-box">
        <b>🕵️ LRF Ekspertiz Raporu</b><br>
        <b>Derinlik:</b> {'Yüzey (0.5 - 1.5m) - Işık Hattı' if cw['is_day'] == 0 else 'Dip (3.0 - 6.0m) - Taş Altı'}<br>
        <b>Basınç Trendi:</b> {trend_txt} ({p_diff:.1f} hPa değişim)<br>
        <b>Worm Tavsiyesi:</b> {'Glow / UV Pembe Silikon' if cw['is_day'] == 0 else 'Doğal Karides / Kum Rengi'}<br>
        <b>Aksiyon:</b> {'Yavaş "shake" / Titreşim' if m['current']['wave_height'] < 0.3 else 'Sert "darting" / Zıplatma'}
    </div>""", unsafe_allow_html=True)

    # --- SAATLİK GRAFİK ---
    st.markdown("### ⏰ 24 Saatlik Aktivite Grafiği (TR)")
    time_list = [datetime.fromisoformat(x).strftime('%H:00') for x in w['hourly']['time'][:24]]
    # Genel bir istatistik eğrisi (İstavrit bazlı)
    stat_list = [calc_dynamic_stat("İstavrit", w['hourly']['wind_speed_10m'][j], w['hourly']['surface_pressure'][j], 1 if 6 < j < 19 else 0, 0) for j in range(24)]
    st.line_chart(pd.DataFrame({"Saat": time_list, "Skor": stat_list}).set_index("Saat"), height=200)

    st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=14)
else:
    st.error("Veri bağlantısı kurulamadı. Lütfen internetinizi kontrol edip sayfayı yenileyin.")
