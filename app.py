"""
TWINCELL Dashboard - MVP
Streamlit tabanlı dijital ikiz simülasyon arayüzü
"""

import streamlit as st
import pandas as pd
import numpy as np

from twin.simulator import (
    generate_synthetic_data,
    apply_scenario,
    kpis,
    forecast_traffic,
)
from twin.optimizer import recommend_actions

st.set_page_config(
    page_title="TWINCELL Dijital İkiz",
    page_icon="📡",
    layout="wide",
)

st.title("📡 TWINCELL Dijital İkiz Dashboard")
st.caption("5G Baz İstasyonları için Edge tabanlı senaryo simülasyonu, kısa vadeli tahmin ve enerji/QoS optimizasyonu")

# ------------------------------
# Sidebar - Kontroller
# ------------------------------
st.sidebar.header("Ayarlar")

seed = st.sidebar.number_input("Rastgele tohum", min_value=0, value=42, step=1)
hours = st.sidebar.slider("Simülasyon süresi (saat)", min_value=24, max_value=168, value=72, step=24)
n_bs = st.sidebar.slider("Baz istasyonu sayısı", min_value=1, max_value=5, value=3, step=1)

@st.cache_data(show_spinner=False)
def load_data_cached(n_bs: int, hours: int, seed: int):
    return generate_synthetic_data(n_bs=n_bs, hours=hours, seed=seed)

data = load_data_cached(n_bs, hours, int(seed))
bs_list = sorted(list(data.keys()))

selected_bs = st.sidebar.selectbox("Baz istasyonu seçin", bs_list, index=0)

scenario = st.sidebar.selectbox(
    "Senaryo",
    ["Referans", "Enerji Tasarruf Modu", "Komşuya Yük Aktarma"],
    index=0,
)

params = {}
if scenario == "Enerji Tasarruf Modu":
    params["tasarruf_yuzde"] = st.sidebar.slider("Tasarruf (%)", 5, 30, 15, step=1) / 100.0
elif scenario == "Komşuya Yük Aktarma":
    params["offload_yuzde"] = st.sidebar.slider("Komşuya aktarım (%)", 5, 30, 15, step=1) / 100.0

# ------------------------------
# Veri & Senaryo
# ------------------------------
df_base = data[selected_bs].copy()
capacity = float(df_base["capacity_mbps"].iloc[0])

df_scn = apply_scenario(df_base.copy(), scenario, params)

base_kpi = kpis(df_base)
scn_kpi = kpis(df_scn)

# ------------------------------
# KPI Kartları
# ------------------------------
st.subheader(f"📍 {selected_bs} - Ana Göstergeler")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric(
    "Ortalama Güç (W)",
    f"{base_kpi['avg_power_w']:.0f}",
    delta=f"{(scn_kpi['avg_power_w'] - base_kpi['avg_power_w']):+.0f} W"
)
col2.metric(
    "Toplam Enerji (kWh)",
    f"{base_kpi['energy_kwh']:.2f}",
    delta=f"{(scn_kpi['energy_kwh'] - base_kpi['energy_kwh']):+.2f} kWh"
)
col3.metric(
    "Toplam Trafik (GB)",
    f"{base_kpi['traffic_gb']:.1f}",
    delta=f"{(scn_kpi['traffic_gb'] - base_kpi['traffic_gb']):+.1f} GB"
)
col4.metric(
    "Enerji / GB (Wh/GB)",
    f"{base_kpi['energy_per_gb_whgb']:.1f}",
    delta=f"{(scn_kpi['energy_per_gb_whgb'] - base_kpi['energy_per_gb_whgb']):+.1f} Wh/GB"
)
col5.metric(
    "Ortalama QoS (%)",
    f"{base_kpi['avg_qos']:.1f}",
    delta=f"{(scn_kpi['avg_qos'] - base_kpi['avg_qos']):+.1f} puan"
)

st.divider()

# ------------------------------
# Grafikler
# ------------------------------
tab_ts, tab_fc, tab_rec = st.tabs(["Zaman Serileri", "Kısa Vadeli Tahmin", "Öneriler"])

with tab_ts:
    st.subheader("Trafik (Mb/s)")
    plot_tr = pd.DataFrame(
        {
            "Referans": df_base.set_index("time")["traffic_mbps"],
            "Senaryo": df_scn.set_index("time")["traffic_mbps"],
        }
    )
    st.line_chart(plot_tr)

    st.subheader("Enerji (W)")
    plot_en = pd.DataFrame(
        {
            "Referans": df_base.set_index("time")["energy_w"],
            "Senaryo": df_scn.set_index("time")["energy_w"],
        }
    )
    st.line_chart(plot_en)

    st.subheader("QoS (%)")
    plot_q = pd.DataFrame(
        {
            "Referans": df_base.set_index("time")["qos"],
            "Senaryo": df_scn.set_index("time")["qos"],
        }
    )
    st.line_chart(plot_q)

with tab_fc:
    st.subheader("24 Saatlik Trafik Tahmini")
    steps = 24
    fc_values = forecast_traffic(df_base["traffic_mbps"], steps=steps, seasonal_period=24)
    last_time = pd.to_datetime(df_base["time"].iloc[-1])
    fc_index = pd.date_range(start=last_time + pd.Timedelta(hours=1), periods=steps, freq="H")
    fc_series = pd.Series(fc_values.values, index=fc_index, name="Tahmin")

    recent_hours = min(48, len(df_base))
    recent_series = df_base.set_index("time")["traffic_mbps"].iloc[-recent_hours:]
    fc_plot = pd.concat([recent_series.rename("Gerçekleşen"), fc_series], axis=1)
    st.line_chart(fc_plot)

with tab_rec:
    st.subheader("Aksiyon Önerileri")
    recs = recommend_actions(df_base["traffic_mbps"], capacity_mbps=capacity)
    if len(recs) == 0:
        st.success("Şimdilik ek aksiyon gerekmiyor. Yük profili dengeli görünüyor.")
    else:
        st.dataframe(pd.DataFrame(recs))

st.caption("Not: Bu bir MVP’dir; üretim ortamı için model kalibrasyonu ve gerçek saha verisi entegrasyonu önerilir.")
