"""
QoS (Hizmet Kalitesi) hesaplama modeli
"""

def calculate_qos(traffic_load, capacity=1.0):
    if traffic_load <= capacity:
        return 1.0
    return max(0.0, 1 - (traffic_load - capacity))
