"""
Baz istasyonu enerji tüketim modeli (ilk versiyon)
"""

def calculate_energy_consumption(traffic_load, base_power=100, load_factor=0.5):
    """
    traffic_load: 0-1 arası normalize trafik
    """
    return base_power + (traffic_load * base_power * load_factor)
