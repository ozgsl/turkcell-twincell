from __future__ import annotations
import pandas as pd
import numpy as np
from .simulator import forecast_traffic

def _hour_ranges(mask: np.ndarray, start_time: pd.Timestamp) -> list[str]:
    """True olan saat aralıklarını insan okunur aralıklara çevir (ör. 01:00-04:00)."""
    ranges: list[str] = []
    i = 0
    n = len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j + 1 < n and mask[j + 1]:
                j += 1
            t0 = (start_time + pd.Timedelta(hours=i + 1)).tz_localize(None)
            t1 = (start_time + pd.Timedelta(hours=j + 2)).tz_localize(None)
            ranges.append(f"{t0.strftime('%H:%M')}–{t1.strftime('%H:%M')}")
            i = j + 1
        else:
            i += 1
    return ranges

def recommend_actions(traffic_series: pd.Series, capacity_mbps: float, steps: int = 24) -> list[dict]:
    """
    Basit kural tabanlı öneriler:
    - Düşük yük (<35%): Enerji tasarruf modunu aç
    - Tepe (>85%): Komşuya %10–20 yük aktar
    """
    recs: list[dict] = []
    if capacity_mbps <= 0:
        return recs

    # Tahmini 24 saat ileri
    fc = forecast_traffic(traffic_series, steps=steps, seasonal_period=24)
    start_time = pd.Timestamp.now().floor("H")

    u = np.clip(fc.values / capacity_mbps, 0, 1)
    low_mask = u < 0.35
    peak_mask = u > 0.85

    # Düşük yük saatleri → tasarruf
    if low_mask.sum() >= 2:
        ranges = _hour_ranges(low_mask, start_time)
        if ranges:
            recs.append(
                {
                    "Zaman Aralığı": ", ".join(ranges[:3]) + ("..." if len(ranges) > 3 else ""),
                    "Aksiyon": "Enerji tasarruf modunu etkinleştir (TX güç/taşıyıcı azaltımı)",
                    "Beklenen Etki": "Dinamik güçte %10–25 azalma; QoS etkisi yok veya ihmalî",
                }
            )

    # Tepe saatleri → offload
    if peak_mask.sum() >= 1:
        ranges = _hour_ranges(peak_mask, start_time)
        if ranges:
            recs.append(
                {
                    "Zaman Aralığı": ", ".join(ranges[:3]) + ("..." if len(ranges) > 3 else ""),
                    "Aksiyon": "Komşu hücrelere %10–20 yük aktar (eNodeB/gNodeB parametreleri)",
                    "Beklenen Etki": "Tepe saat QoS +5–10 puan; enerji küçük artı/eksi (yük dengesi)",
                }
            )

    # Genel gece önerisi (çok düşük ortalama)
    avg_u = float(u.mean())
    if avg_u < 0.25:
        recs.append(
            {
                "Zaman Aralığı": "Gece (yaklaşık 01:00–05:00)",
                "Aksiyon": "Düşük yükte taşıyıcı/anten kapanı (MIMO derecesini azalt)",
                "Beklenen Etki": "Saat başına ~0.1–0.3 kWh tasarruf; QoS etkisi sınırlı",
            }
        )

    return recs
