# TWINCELL – Dijital İkiz Dashboard (MVP)

Bu proje, 5G baz istasyonları için dijital ikiz yaklaşımıyla senaryo simülasyonu, kısa vadeli trafik tahmini ve enerji/QoS analizini sağlayan Streamlit tabanlı bir MVP'dir.

## Özellikler
- Sentetik veri ile birden fazla baz istasyonu simülasyonu
- Senaryolar:
  - Referans
  - Enerji Tasarruf Modu (TX güç/taşıyıcı azaltımı etkisi)
  - Komşuya Yük Aktarma (offload)
- KPI'lar: Ortalama Güç, Toplam Enerji, Toplam Trafik, Enerji/GB, Ortalama QoS
- 24 saatlik mevsimsel-naif trafik tahmini
- Basit öneri motoru (düşük-yük ve tepe saatlerde aksiyon önerileri)

## Kurulum
Önkoşullar: Python 3.10+ (öneri: 3.11), pip
