"""
Edge tarafında çalışan karar destek servisi
"""

def edge_decision(traffic_forecast):
    if traffic_forecast < 0.6:
        return "ECO_MODE"
    return "NORMAL_MODE"
