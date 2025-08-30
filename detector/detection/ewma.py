import numpy as np

def ewma(arr, alpha):
    out = []
    s = arr[0]
    for x in arr: s = alpha * x + (1 - alpha) * s; out.append(s)
    return np.array(out)

def check(value: float, hist: list[float], z_threshold: float, span_seconds:int, step:int) -> bool:
    if len(hist) < 10: return False
    alpha = 2/(1 + max(2, span_seconds//step))
    sm = ewma(hist, alpha)
    m, s = sm.mean(), sm.std() or 1.0
    z = (value - m) / s
    return z > z_threshold
