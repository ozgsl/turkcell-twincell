"""
TWINCELL Digital Twin - Baz İstasyonu Durum Modeli
"""

class BaseStationState:
    def __init__(self, station_id, traffic_load, energy_consumption, qos_score):
        self.station_id = station_id
        self.traffic_load = traffic_load
        self.energy_consumption = energy_consumption
        self.qos_score = qos_score

    def to_dict(self):
        return {
            "station_id": self.station_id,
            "traffic_load": self.traffic_load,
            "energy_consumption": self.energy_consumption,
            "qos_score": self.qos_score
        }
