import json, urllib.request, ssl
# login as admin
body = json.dumps({"username":"admin","password":"admin123","code":"","uuid":""}).encode()
req = urllib.request.Request("http://127.0.0.1:8088/login", data=body, headers={"Content-Type":"application/json"}, method="POST")
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        login = json.loads(r.read().decode())
    print("login", login.get("code"), list(login.keys()), "msg", login.get("msg"))
    token = login.get("token")
    if not token:
        print(login)
        raise SystemExit(1)
    req2 = urllib.request.Request("http://127.0.0.1:8088/getRouters", headers={"Authorization":"Bearer "+token})
    with urllib.request.urlopen(req2, timeout=15) as r:
        routers = json.loads(r.read().decode())
    print("routers code", routers.get("code"), "count", len(routers.get("data") or []))
    for item in (routers.get("data") or []):
        meta = item.get("meta") or {}
        print("-", item.get("path"), meta.get("title"), "hidden=", item.get("hidden"), "children=", len(item.get("children") or []))
    req3 = urllib.request.Request("http://127.0.0.1:8088/getInfo", headers={"Authorization":"Bearer "+token})
    with urllib.request.urlopen(req3, timeout=15) as r:
        info = json.loads(r.read().decode())
    user = info.get("user") or {}
    print("userId", user.get("userId"), "userName", user.get("userName"), "roles", info.get("roles"), "perms sample", list(info.get("permissions") or [])[:5])
except Exception as e:
    print("ERR", type(e).__name__, e)
