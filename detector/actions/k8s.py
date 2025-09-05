import subprocess, json

def _kubectl(args:list[str]):
    cp = subprocess.run(["kubectl"] + args, capture_output=True, text=True, check=False)
    return cp.returncode, cp.stdout, cp.stderr

def restart_pod(namespace:str, selector:str):
    code,out,err = _kubectl(["-n", namespace, "delete", "pod", "-l", selector, "--grace-period=0", "--force"])
    return code==0, out or err

def rollout_restart(namespace:str, name:str):
    code,out,err = _kubectl(["-n", namespace, "rollout", "restart", f"deploy/{name}"])
    return code==0, out or err

def scale_deployment(namespace:str, name:str, factor:int, max_replicas:int):
    # read current replicas
    code,out,err = _kubectl(["-n", namespace, "get", "deploy", name, "-o", "json"])
    if code!=0: return False, err
    obj = json.loads(out)
    cur = int(obj["spec"]["replicas"])
    new = min(cur*factor, max_replicas)
    if new == cur: return True, f"replicas unchanged at {cur}"
    code,out,err = _kubectl(["-n", namespace, "scale", f"deploy/{name}", f"--replicas={new}"])
    return code==0, out or err

def scale_down(namespace: str, name: str, min_replicas: int = 1):
    # read current replicas
    code, out, err = _kubectl(["-n", namespace, "get", "deploy", name, "-o", "json"])
    if code != 0:
        return False, err
    obj = json.loads(out)
    cur = int(obj["spec"]["replicas"])
    new = max(min_replicas, cur // 2)  # reduce by half but not below min_replicas
    if new == cur:
        return True, f"replicas unchanged at {cur}"
    code, out, err = _kubectl(["-n", namespace, "scale", f"deploy/{name}", f"--replicas={new}"])
    return code == 0, out or err
