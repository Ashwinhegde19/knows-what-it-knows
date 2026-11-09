"""Download the eval models into a Modal volume once, so GPU runs never wait on
Hugging Face. CPU-only. Usage:  modal run scripts/modal_download.py

Pre-sprint infrastructure; contains no eval logic.
"""
import modal

VOLUME_NAME = "kwik-models"
MODELS = [
    "IFM/K2-Horizon-3.7B",
    "IFM/K2-Horizon-7B",
    "openbmb/MiniCPM5-2B",
    "Qwen/Qwen3.5-4B",
]
SKIP = ["*.gguf", "*.bin", "*.pth", "*.onnx", "*.msgpack", "consolidated*", "original/*"]

app = modal.App("kwik-download")
vol = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("huggingface_hub[hf_transfer]==1.4.1")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)


@app.function(image=image, volumes={"/models": vol}, cpu=4, timeout=3 * 3600)
def download(repo_id: str) -> str:
    import os
    from huggingface_hub import snapshot_download

    target = f"/models/{repo_id}"
    snapshot_download(repo_id, local_dir=target, ignore_patterns=SKIP)
    vol.commit()
    size_gb = sum(
        os.path.getsize(os.path.join(d, f))
        for d, _, fs in os.walk(target) for f in fs
    ) / 1e9
    return f"{repo_id}: {size_gb:.1f} GB"


@app.local_entrypoint()
def main():
    for line in download.map(MODELS):
        print(line)
