import os

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_DISABLE_XET"] = "1"
from huggingface_hub import snapshot_download

MODELS = [
    "BAAI/bge-small-zh-v1.5",
    "BAAI/bge-reranker-v2-m3",
]
CACHE = os.path.join(os.path.dirname(__file__), "data", "models")

for m in MODELS:
    print(f"=== downloading {m} ===", flush=True)
    p = snapshot_download(repo_id=m, cache_dir=CACHE)
    print("DONE", m, "->", p, flush=True)
print("ALL_DOWNLOADS_COMPLETE", flush=True)
