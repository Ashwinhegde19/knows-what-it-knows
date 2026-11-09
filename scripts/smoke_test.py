"""One request against a running modal_serve endpoint, to prove the stack works.

    python scripts/smoke_test.py <base_url> <model> [reasoning_kwarg=value]

Examples:
    python scripts/smoke_test.py https://…modal.run IFM/K2-Horizon-3.7B reasoning_effort=high
    python scripts/smoke_test.py https://…modal.run Qwen/Qwen3.5-4B enable_thinking=false

Pre-sprint infrastructure; contains no eval logic.
"""
import sys
import time

from openai import OpenAI

base_url, model = sys.argv[1].rstrip("/") + "/v1", sys.argv[2]
kwargs = {}
for kv in sys.argv[3:]:
    k, v = kv.split("=", 1)
    kwargs[k] = {"true": True, "false": False}.get(v.lower(), v)

client = OpenAI(base_url=base_url, api_key="EMPTY")
t0 = time.time()
r = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "What is the capital of Australia? Answer in one sentence."}],
    max_tokens=4096,
    temperature=1.0,
    top_p=0.95,
    extra_body={"chat_template_kwargs": kwargs} if kwargs else None,
)
m = r.choices[0].message
print(f"--- {model} | {time.time() - t0:.1f}s | finish={r.choices[0].finish_reason} | "
      f"prompt={r.usage.prompt_tokens} completion={r.usage.completion_tokens}")
reasoning = getattr(m, "reasoning_content", None) or getattr(m, "reasoning", None)
print("reasoning:", (reasoning or "")[:400].replace("\n", " "), "…" if reasoning and len(reasoning) > 400 else "")
print("answer:", (m.content or "").strip()[:400])
