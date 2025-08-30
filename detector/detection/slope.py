import numpy as np

def check(series: list[float], slope_threshold: float) -> bool:
    if len(series) < 6: return False
    x = np.arange(len(series))
    m = np.polyfit(x, series, 1)[0]
    return m > slope_threshold
