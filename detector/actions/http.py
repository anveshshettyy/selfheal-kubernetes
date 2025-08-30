import requests

def post(url:str, payload:dict, token:str|None=None):
    headers={}
    if token: headers["Authorization"]=f"Bearer {token}"
    r = requests.post(url, json=payload, headers=headers, timeout=5)
    return r.ok, f"{r.status_code} {r.text}"
