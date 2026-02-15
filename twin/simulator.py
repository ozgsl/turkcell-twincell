import numpy as np
import pandas as pd

# Sabitler (istasyon başına farklılaştırılabilir)
DEFAULT_BASELINE_W = 700.0
DEFAULT_DYN_W_MAX = 600.0

def _daily_profile(hours_index: pd.DatetimeIndex, capacity_mbps: float, phase_shift: float = 0.0, noise_scale: float = 0.05) -> np.ndarray:
    """Basit günlük trafik profili (sinüs tabanlı) + gürültü."""
    hour = hours_index.hour.values.astype(float)
    # Sabah ve akşam tepe saatlerini yaklaşıkla
    base = 0.25
    morning = 0.35 * (np.sin(2 * np.pi * (hour - 8 + phase_shift) / 24.0) + 1) / 2.0
    evening = 0.40 * (np.sin(2 * np.pi * (hour - 18 + phase_shift) / 24.0) + 1) / 2.0
    factor = base + morning + evening  # 0.25 - 1.0 arası
    demand = capacity_mbps * factor
    noise = np.random.normal(0.0, noise_scale * capacity_mbps, size=len(hours_index))
    demand = np.clip(demand + noise, a_min=0.05 * capacity_mbps, a_max=1.2 * capacity_mbps)
    return demand

def _compute_qos(utilization: np.ndarray) -> np.ndarray:
    """Basit QoS skoru: yüksek dolulukta ceza uygula."""
    qos = 100.0 - np.clip((utilization - 0.85) / 0.15, 0, 1) * 30.0  # 85% üstü max -30 puan
    qos += np.random.normal(0.0, 0.8, size=len(utilization))  # küçük varyasyon
    return np.clip(qos, 0, 100)

def _compute_energy_w(u: np.ndarray, baseline_w: float, dyn_w_max: float) -> np.ndarray:
    """Enerji modeli: P = P0 + Pdyn * u^1.3"""
    return baseline_w + dyn_w_max * np.power(np.clip(u, 0, 1), 1.3)

def generate_synthetic_data(n_bs: int = 3, hours: int = 72, seed: int | None = None) -> dict[str, pd.DataFrame]:
    """n_bs adet baz istasyonu için saatlik sentetik zaman serileri üret."""
    if seed is not None:
        np.random.seed(seed)

    now = pd.Timestamp.now(tz="UTC").floor("H")
    time_idx = pd.date_range(end=now, periods=hours, freq="H")

    out: dict[str, pd.DataFrame] = {}
    for i in range(n_bs):
        bs_id = f"BS-{i+1}"
        capacity = 600.0 + i * 50.0  # Mb/s
        baseline_w = DEFAULT_BASELINE_W + i * 20.0
        dyn_w_max = DEFAULT_DYN_W_MAX

        traffic = _daily_profile(time_idx, capacity_mbps=capacity, phase_shift=i * 2.0, noise_scale=0.06)
        utilization = np.clip(traffic / capacity, 0, 1)
        energy_w = _compute_energy_w(utilization, baseline_w, dyn_w_max)
        qos = _compute_qos(utilization)

        df = pd.DataFrame(
            {
                "time": time_idx,
                "traffic_mbps": traffic,
                "utilization": utilization,
                "energy_w": energy_w,
                "qos": qos,
                "capacity_mbps": capacity,
                "baseline_w": baseline_w,
                "dyn_w_max": dyn_w_max,
            }
        )
        out[bs_id] = df

    return out

def apply_scenario(df: pd.DataFrame, scenario: str, params: dict) -> pd.DataFrame:
    """Seçilen senaryoyu uygula ve yeni seri üret."""
    cap = float(df["capacity_mbps"].iloc[0])
    baseline_w = float(df["baseline_w"].iloc[0])
    dyn_w_max = float(df["dyn_w_max"].iloc[0])

    if scenario == "Enerji Tasarruf Modu":
        t = float(params.get("tasarruf_yuzde", 0.15))
        cap_eff = cap * (1.0 - 0.30 * t)  # tasarruf arttıkça küçük kapasite düşüşü
        baseline_eff = baseline_w * (1.0 - 0.40 * t)
        dyn_eff = dyn_w_max * (1.0 - 0.60 * t)

        traffic = df["traffic_mbps"].values
        u_new = np.clip(traffic / cap_eff, 0, 1)
        energy_new = _compute_energy_w(u_new, baseline_eff, dyn_eff)
        qos_new = _compute_qos(u_new) - 2.0 * np.clip((u_new - 0.85) / 0.15, 0, 1)  # yüksek yükte ilave küçük ceza
        qos_new = np.clip(qos_new, 0, 100)

        df_out = df.copy()
        df_out["utilization"] = u_new
        df_out["energy_w"] = energy_new
        df_out["qos"] = qos_new
        df_out["capacity_mbps"] = cap_eff
        return df_out

    if scenario == "Komşuya Yük Aktarma":
        x = float(params.get("offload_yuzde", 0.15))
        traffic_new = df["traffic_mbps"].values * (1.0 - x)
        u_new = np.clip(traffic_new / cap, 0, 1)
        energy_new = _compute_energy_w(u_new, baseline_w, dyn_w_max)
        # Daha düşük doluluk QoS'u iyileştirir, küçük bir artı puan ekleyelim (maks +2)
        qos_new = np.clip(_compute_qos(u_new) + 2.0 * x / 0.30, 0, 100)

        df_out = df.copy()
        df_out["traffic_mbps"] = traffic_new
        df_out["utilization"] = u_new
        df_out["energy_w"] = energy_new
        df_out["qos"] = qos_new
        return df_out

    # Referans ya da tanımsız → aynen döndür
    return df

def kpis(df: pd.DataFrame) -> dict:
    """Temel KPI'ları hesapla."""
    # Enerji: saatlik numuneler → toplam kWh
    energy_kwh = df["energy_w"].sum() / 1000.0
    # Trafik: Mb/s → GB/saat dönüşümü: GB = Mbps * 3600 / 8000
    traffic_gb = float((df["traffic_mbps"].sum() * 3600.0) / 8000.0)
    avg_power_w = float(df["energy_w"].mean())
    avg_qos = float(df["qos"].mean())
    energy_per_gb_whgb = (energy_kwh * 1000.0 / traffic_gb) if traffic_gb > 0 else np.nan

    return {
        "avg_power_w": avg_power_w,
        "energy_kwh": energy_kwh,
        "traffic_gb": traffic_gb,
        "energy_per_gb_whgb": energy_per_gb_whgb,
        "avg_qos": avg_qos,
    }

def forecast_traffic(series: pd.Series, steps: int = 24, seasonal_period: int = 24) -> pd.Series:
    """Basit mevsimsel-naif tahmin: son 24 saati ileriye kopyala."""
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) >= seasonal_period:
        last = s.iloc[-seasonal_period:].values
        rep = int(np.ceil(steps / seasonal_period))
        values = np.tile(last, rep)[:steps]
    else:
        values = np.full(steps, s.iloc[-1] if len(s) else 0.0)
    return pd.Series(values)
