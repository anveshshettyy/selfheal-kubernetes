import time, collections, json, os
from typing import Dict

class Cooldowns:
    def __init__(self, seconds:int):
        self.seconds = seconds
        self.last: Dict[str, float] = {}

    def allow(self, key:str)->bool:
        now = time.time()
        if key not in self.last or (now - self.last[key]) >= self.seconds:
            self.last[key] = now
            return True
        return False

class Budgets:
    def __init__(self, global_per_hour:int, per_target_per_hour:int):
        self.global_window = collections.deque()
        self.per_target: Dict[str, collections.deque] = {}
        self.gph = global_per_hour
        self.tph = per_target_per_hour

    def _prune(self, dq):
        cutoff = time.time() - 3600
        while dq and dq[0] < cutoff:
            dq.popleft()

    def allow(self, target_key:str)->bool:
        now = time.time()
        self._prune(self.global_window)
        dq = self.per_target.setdefault(target_key, collections.deque())
        self._prune(dq)
        if len(self.global_window) >= self.gph: return False
        if len(dq) >= self.tph: return False
        self.global_window.append(now); dq.append(now)
        return True
