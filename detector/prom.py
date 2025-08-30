import requests, time

class Prom:
    def __init__(self, base):
        self.base = base.rstrip('/')

    def instant(self, q):
        r = requests.get(f"{self.base}/api/v1/query", params={"query": q}, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data["status"] != "success": raise RuntimeError(data)
        result = data["data"]["result"]
        if not result: return 0.0
        # assume scalar-ish sum; pick first value
        v = float(result[0]["value"][1])
        return v
