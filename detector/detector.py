import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pathlib


import time, yaml, collections
# from models import RootCfg
# from prom import Prom
# from state import Cooldowns, Budgets
# from utils import LOG, ANOMALIES, ACTIONS, VALUES
# from detection import zscore, slope as slope_mod, ewma as ewma_mod, window as window_mod
# from actions import k8s as k8s_act, http as http_act
# from prometheus_client import start_http_server

from .models import RootCfg
from .prom import Prom
from .state import Cooldowns, Budgets
from .utils import LOG, ANOMALIES, ACTIONS, VALUES
from .detection import zscore, slope as slope_mod, ewma as ewma_mod, window as window_mod
from .actions import k8s as k8s_act, http as http_act
from prometheus_client import start_http_server

def main():
    cfg_path = pathlib.Path(__file__).parent / "detector-config.yaml"
    cfg = RootCfg(**yaml.safe_load(open(cfg_path)))
    start_http_server(9103)
    prom = Prom(cfg.prometheus["url"])
    cooldowns = Cooldowns(cfg.cooldown_seconds)
    budgets = Budgets(cfg.budgets.get("global_actions_per_hour",9999),
                      cfg.budgets.get("per_target_per_hour",9999))

    # rings store last N values for slope/ewma; also streaks for window_threshold
    ring = collections.defaultdict(lambda: collections.deque(maxlen=120))
    streak = collections.defaultdict(int)
    inhibit_until = {}

    step = cfg.poll_interval_seconds

    while True:
        tnow = time.time()

        # check inhibitions
        for inh in cfg.inhibit:
            met = inh["when_metric"]
            if inhibit_until.get(met,0) > tnow: pass

        for m in cfg.metrics:
            try:
                value = prom.instant(m.promql)
                LOG.info("metric %s = %s", m.name, value)
                VALUES.labels(m.name).set(value)
                ring[m.name].append(value)

                fired = False
                d = m.detection

                if d.method == "zscore":
                    fired = zscore.check(value, list(ring[m.name]), d.threshold, d.consecutive)
                elif d.method == "slope":
                    fired = slope_mod.check(list(ring[m.name]), d.slope_threshold)
                elif d.method == "ewma_zscore":
                    fired = ewma_mod.check(value, list(ring[m.name]), d.z_threshold, d.span_seconds, step)
                elif d.method == "window_threshold":
                    streak[m.name] = streak[m.name] + step if (d.gt is not None and value > d.gt) else 0
                    fired = window_mod.check(value, d.gt, d.for_seconds, streak[m.name])

                if not fired:
                    continue

                # inhibition gate
                inhibited = False
                for inh in cfg.inhibit:
                    if m.name == inh.get("when_metric"):
                        inhibit_until[m.name] = tnow + inh["suppress_actions_for_seconds"]
                        inhibited = True
                if inhibited:
                    LOG.warning("Inhibited by %s", m.name)
                    continue

                # cooldown
                target_key = f"{m.action.type}:{m.action.target.namespace}:{m.action.target.name or m.action.target.selector or 'NA'}"
                if not cooldowns.allow(target_key):
                    LOG.info("Cooldown active for %s", target_key); continue

                # budget
                if not budgets.allow(target_key):
                    LOG.warning("Budget exceeded for %s", target_key); continue

                ANOMALIES.labels(m.name).inc()

                if cfg.dry_run:
                    LOG.warning("[dry-run] Would act: %s on %s", m.action.type, target_key)
                    continue

                ok, msg = execute_action(m.action.type, m.action.target, cfg)
                ACTIONS.labels(m.action.type, target_key).inc()
                LOG.warning("Action %s => %s | %s", m.action.type, "OK" if ok else "FAIL", msg)

            except Exception as e:
                LOG.exception("metric %s failed: %s", m.name, e)

        time.sleep(step)

def execute_action(action_type, target, cfg):
    t = target.dict()
    if action_type == "restart_pod":
        return k8s_act.restart_pod(t["namespace"], t["selector"])
    if action_type == "rollout_restart":
        return k8s_act.rollout_restart(t["namespace"], t["name"])
    if action_type == "scale_deployment":
        return k8s_act.scale_deployment(t["namespace"], t["name"], t["factor"], t["max"])
    if action_type == "scale_up":
        return k8s_act.scale_deployment(t["namespace"], t["name"], 2, t.get("max",10))
    if action_type == "http_post":
        ep = cfg.actuator["endpoint"].rstrip("/")
        tok = cfg.actuator.get("tokens",{}).get("default")
        return http_act.post(f"{ep}/task", {"target":t}, tok)
    if action_type == "defer":
        return True, "deferred by policy"
    return False, f"unknown action {action_type}"

if __name__ == "__main__":
    main()
