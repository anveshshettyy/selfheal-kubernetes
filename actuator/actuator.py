#!/usr/bin/env python3
# actuator/actuator.py
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import time, threading
from kubernetes import client, config
from prometheus_client import start_http_server, Counter, Gauge

# metrics
ACTIONS = Counter('actuator_actions_total','actions executed')
LAST_ACTION = Gauge('actuator_last_action_timestamp','last action timestamp')

# load kube config (in-cluster preferred)
try:
    config.load_incluster_config()
except:
    config.load_kube_config()

apps = client.AppsV1Api()
core = client.CoreV1Api()

# simple in-memory cooldown store
cooldown_store = {}

# policy: how much to scale on scale_up
SCALE_STEP = 2
COOLDOWN = 300  # seconds

class ActionRequest(BaseModel):
    metric: str
    value: float
    zscore: float = None
    action: str
    details: dict = {}

app = FastAPI()

def can_take(target_key):
    now = time.time()
    last = cooldown_store.get(target_key, 0)
    return (now - last) > COOLDOWN

def record_action(target_key):
    cooldown_store[target_key] = time.time()
    LAST_ACTION.set(time.time())

@app.post("/action")
async def do_action(req: ActionRequest):
    # map action
    action = req.action
    target_key = "selfheal-api"  # could be refined per-pod if detector sends pod
    if not can_take(target_key):
        raise HTTPException(status_code=429, detail="In cooldown")
    if action == 'scale_up':
        # scale deployment
        ns = 'selfheal'
        name = 'selfheal-api'
        # fetch current
        dep = apps.read_namespaced_deployment(name, ns)
        cur = dep.spec.replicas or 1
        new = cur + SCALE_STEP
        body = {'spec': {'replicas': new}}
        apps.patch_namespaced_deployment(name, ns, body)
        record_action(target_key)
        ACTIONS.inc()
        return {"status":"scaled","from":cur,"to":new}
    elif action == 'restart_pod':
        # choose a pod to delete
        pods = core.list_namespaced_pod('selfheal', label_selector='app=selfheal-api')
        if not pods.items:
            raise HTTPException(status_code=404, detail="no pods found")
        target = pods.items[0].metadata.name
        core.delete_namespaced_pod(target, 'selfheal', grace_period_seconds=0)
        record_action(target_key)
        ACTIONS.inc()
        return {"status":"deleted_pod","pod":target}
    elif action == 'rollout_restart':
        ns='selfheal'; name='selfheal-api'
        # patch annotation to trigger rollout
        body = {"spec":{"template":{"metadata":{"annotations":{"selfheal/restartedAt": str(int(time.time()))}}}}}
        apps.patch_namespaced_deployment(name,ns,body)
        record_action(target_key)
        ACTIONS.inc()
        return {"status":"rolled","deployment":name}
    else:
        raise HTTPException(status_code=400, detail="unknown action")

if __name__ == "__main__":
    start_http_server(9200)  # metrics for actuator
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
