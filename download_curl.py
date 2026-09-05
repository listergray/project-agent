import os, json, urllib.request, urllib.parse

MIRROR = "https://hf-mirror.com"
BASE = os.path.join(os.path.dirname(__file__), "data", "models")
REPOS = {
    "bge-small-zh-v1.5": "BAAI/bge-small-zh-v1.5",
    "bge-reranker-v2-m3": "BAAI/bge-reranker-v2-m3",
}


def download(repo, local_name):
    local = os.path.join(BASE, local_name)
    os.makedirs(local, exist_ok=True)
    api = f"{MIRROR}/api/models/{repo}"
    req_api = urllib.request.Request(api, headers={"User-Agent": "curl/8"})
    with urllib.request.urlopen(req_api, timeout=30) as r:
        data = json.load(r)
    siblings = [s["rfilename"] for s in data.get("siblings", [])]
    for fname in siblings:
        # 跳过 README 与图片类非必需文件（加速；不影响加载）
        low = fname.lower()
        if low.endswith((".png", ".jpg", ".jpeg", ".md")):
            print("SKIP", fname, flush=True)
            continue
        url = f"{MIRROR}/{repo}/resolve/main/{urllib.parse.quote(fname)}"
        dst = os.path.join(local, fname)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        print("GET", fname, flush=True)
        req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
        with urllib.request.urlopen(req, timeout=600) as resp, open(dst, "wb") as f:
            while True:
                chunk = resp.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
        print("  ->", os.path.getsize(dst), "bytes", flush=True)
    print("DONE", repo, flush=True)


for local_name, repo in REPOS.items():
    download(repo, local_name)
print("ALL_LOCAL_DONE", flush=True)
