"""
What-if senaryo motoru
"""

def run_scenario(state, traffic_modifier):
    new_traffic = state.traffic_load * traffic_modifier
    return new_traffic
