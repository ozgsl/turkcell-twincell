"""
Dijital ikiz simülasyon çalıştırıcısı
"""

from simulation.energy_model import calculate_energy_consumption
from simulation.qos_model import calculate_qos

def simulate_step(traffic_load):
    energy = calculate_energy_consumption(traffic_load)
    qos = calculate_qos(traffic_load)
    return energy, qos
