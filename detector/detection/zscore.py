import numpy as np

def check(value: float, hist: list[float], threshold: float, consecutive:int=1) -> bool:
    if len(hist) < 10: return False
    m, s = np.mean(hist), np.std(hist) or 1.0
    z = (value - m) / s
    return z > threshold
