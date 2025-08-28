import time, requests, yaml, math
from collections import deque
import numpy as np
from prometheus_client import start_http_server, Counter, Gauge

# metrics exported
ANOMALIES = Counter('detector_anomalies_total','anomalies detected')
ACTIONS_SENT = Counter('detector_actions_sent_total','actions sent to actuator')

def query_range(prom_url, query, start_ts, end_ts, step):
    params = {'query': query, 'start': start_ts, 'end': end_ts, 'step': step}
    r = requests.get(prom_url + "/api/v1/query_range", params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    if data['status'] != 'success': 
        return []
    # assume a single vector/time-series -> we reduce by summing points per timestamp if needed
    # simplified: take first result, calculate values
    res = data['data']['result']
    if not res:
        return []
    # merge results by timestamp: sum across series if multiple series (e.g., per pod)
    # build dict timestamp->value sum
    tsmap = {}
    for series in res:
        for ts, val in series['values']:
            tsmap[ts] = tsmap.get(ts, 0.0) + float(val)
    # return sorted values
    items = sorted((float(k), v) for k,v in tsmap.items())
    return items

def instant_query(prom_url, query):
    r = requests.get(prom_url + "/api/v1/query", params={'query': query}, timeout=5)
    r.raise_for_status()
    d = r.json()
    if d['status'] != 'success': return None
    res = d['data']['result']
    if not res: return 0.0
    # sum all series values
    s=0.0
    for series in res:
        val = float(series['value'][1])
        s += val
    return s

class MetricState:
    def __init__(self, name, config, baseline_mean=0.0, baseline_std=1.0, window_size=8):
        self.name = name
        self.config = config
        self.window = deque(maxlen=window_size)
        self.baseline_mean = baseline_mean
        self.baseline_std = baseline_std
        self.consecutive = 0

def bootstrap_baseline(prom_url, promql, baseline_window, step):
    end = time.time()
    start = end - baseline_window
    samples = query_range(prom_url, promql, start, end, step)
    if not samples:
        return 0.0, 1.0
    vals = [v for ts,v in samples]
    mean = float(np.mean(vals))
    std = float(np.std(vals)) if np.std(vals) > 0 else 1.0
    return mean, std

def run_detector(config):
    prom = config['prometheus']['url']
    poll = config.get('poll_interval_seconds', 15)
    baseline_window = config.get('baseline_window_seconds', 3600)
    metrics_cfg = config['metrics']
    states = {}
    # bootstrap
    for m in metrics_cfg:
        mean,std = bootstrap_baseline(prom, m['promql'], baseline_window, poll)
        states[m['name']] = MetricState(m['name'], m, baseline_mean=mean, baseline_std=std)
        print(f"[bootstrap] {m['name']} mean={mean:.3f} std={std:.3f}")
    # start prometheus /metrics on 9100 for scraping
    start_http_server(9100)
    while True:
        for m in metrics_cfg:
            name = m['name']
            promql = m['promql']
            val = instant_query(prom, promql)
            if val is None:
                val = 0.0
            st = states[name]
            st.window.append(val)
            # zscore check vs baseline
            z = 0.0
            if st.baseline_std > 0:
                z = abs((val - st.baseline_mean) / st.baseline_std)
            triggered = False
            det = m['detection']
            if det.get('method') == 'zscore':
                if z >= det.get('threshold', 3.0):
                    triggered = True
            elif det.get('method') == 'slope':
                # simple slope: linear regression on window
                arr = np.array(st.window)
                if len(arr) >= 3:
                    x = np.arange(len(arr))
                    A = np.vstack([x, np.ones(len(x))]).T
                    slope, _ = np.linalg.lstsq(A, arr, rcond=None)[0]
                    if slope >= det.get('slope_threshold', 0.1):
                        triggered = True
            # consecutive logic
            if triggered:
                st.consecutive += 1
            else:
                st.consecutive = 0
            if st.consecutive >= det.get('consecutive', 1):
                ANOMALIES.inc()
                print(f"[ANOMALY] metric={name} val={val} z={z:.2f} consecutive={st.consecutive}")
                # send action
                action = det.get('action', 'restart_pod')
                payload = {
                    'metric': name,
                    'value': val,
                    'zscore': z,
                    'action': action,
                    'details': {'promql': promql}
                }
                if not config.get('dry_run', True):
                    try:
                        r = requests.post(config['actuator_endpoint'], json=payload, timeout=5)
                        r.raise_for_status()
                        ACTIONS_SENT.inc()
                        print("[sent] to actuator:", payload)
                    except Exception as e:
                        print("actuator call fail:", e)
                else:
                    print("dry_run enabled — not calling actuator. payload:", payload)
                # reset consecutive to avoid repeated calls until cooldown handled by actuator
                st.consecutive = 0
        time.sleep(poll)

if __name__ == "__main__":
    import sys, os
    cfg = yaml.safe_load(open(sys.argv[1])) if len(sys.argv) > 1 else yaml.safe_load(open('detector-config.yaml'))
    run_detector(cfg)
