"""Serve one eval model from the kwik-models volume with vLLM on Modal.

    KWIK_MODEL=IFM/K2-Horizon-3.7B modal serve scripts/modal_serve.py     # dev, dies with Ctrl-C
    KWIK_MODEL=IFM/K2-Horizon-3.7B modal deploy scripts/modal_serve.py    # persistent URL

Prints an OpenAI-compatible base URL (…/v1). Inspect AI talks to it with
    --model openai/<served name> -M base_url=<url>/v1 -M api_key=EMPTY

Pre-sprint infrastructure; contains no eval logic.
"""
import os
import subprocess

import modal

VOLUME_NAME = "kwik-models"
MODEL = os.environ.get("KWIK_MODEL", "IFM/K2-Horizon-3.7B")
GPU = os.environ.get("KWIK_GPU", "L40S")          # 48 GB; fine for every model here up to 7B
MAX_MODEL_LEN = os.environ.get("KWIK_MAX_LEN", "65536")
PORT = 8000

# Per-model vLLM flags, from each model card's recommended serve command.
MODEL_FLAGS = {
    "IFM/K2-Horizon-3.7B": ["--trust-remote-code", "--dtype", "bfloat16", "--reasoning-parser", "k2_horizon"],
    "IFM/K2-Horizon-7B":   ["--trust-remote-code", "--dtype", "bfloat16", "--reasoning-parser", "k2_horizon"],
    "openbmb/MiniCPM5-2B": ["--trust-remote-code", "--dtype", "bfloat16", "--reasoning-parser", "deepseek_r1"],  # <think>…</think> blocks
    "Qwen/Qwen3.5-4B":     ["--reasoning-parser", "qwen3", "--language-model-only"],
}
if MODEL not in MODEL_FLAGS:
    raise SystemExit(f"unknown model {MODEL}; add it to MODEL_FLAGS")

app = modal.App("kwik-vllm-" + MODEL.split("/")[-1].lower())
vol = modal.Volume.from_name(VOLUME_NAME)
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("vllm==0.33.0", "huggingface_hub[hf_transfer]")
    .env({
        "HF_HUB_OFFLINE": "1",
        "KWIK_MODEL": MODEL,
        "KWIK_FLAGS": " ".join(MODEL_FLAGS[MODEL]),
        "KWIK_MAX_LEN": MAX_MODEL_LEN,
    })
)


@app.function(
    image=image,
    gpu=GPU,
    volumes={"/models": vol},
    timeout=6 * 3600,
    scaledown_window=5 * 60,      # shut the GPU down 5 min after the last request
)
@modal.concurrent(max_inputs=64)
@modal.web_server(port=PORT, startup_timeout=20 * 60)
def serve():
    model = os.environ["KWIK_MODEL"]
    cmd = [
        "vllm", "serve", f"/models/{model}",
        "--served-model-name", model,
        "--host", "0.0.0.0", "--port", str(PORT),
        "--max-model-len", os.environ["KWIK_MAX_LEN"],
        "--gpu-memory-utilization", "0.90",
        "--enable-prefix-caching",
        *os.environ["KWIK_FLAGS"].split(),
    ]
    print("launching:", " ".join(cmd), flush=True)
    subprocess.Popen(cmd)
