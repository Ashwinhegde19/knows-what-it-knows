"""The models, their thinking switches, and one streaming chat call with retries."""
import asyncio
import os
import re
import time

import httpx
from openai import AsyncOpenAI

# Thinking on/off is passed through the chat template, the way each model card documents it.
MODELS = {
    "IFM/K2-Horizon-3.7B": {"think": {"reasoning_effort": "high"}, "nothink": {"reasoning_effort": "low"}},
    "IFM/K2-Horizon-7B": {"think": {"reasoning_effort": "high"}, "nothink": {"reasoning_effort": "low"}},
    "openbmb/MiniCPM5-2B": {"think": {"enable_thinking": True}, "nothink": {"enable_thinking": False}},
    "Qwen/Qwen3.5-4B": {"think": {"enable_thinking": True}, "nothink": {"enable_thinking": False}},
}

# Each developer's recommended sampling, from the model cards (checked 13 Nov 2026):
#   K2 Horizon: temperature 1.0, top_p 0.95, reasoning_effort high, at least 32,768 output tokens.
#   MiniCPM5:   temperature 1.0, top_p 0.95, min_p 0.0.
#   Qwen3.5:    thinking "general tasks" temperature 1.0, top_p 0.95, top_k 20, presence_penalty 1.5;
#               non-thinking "general tasks" temperature 0.7, top_p 0.8, top_k 20, presence_penalty 1.5.
# A shared temperature of 0.6 made Qwen3.5 loop in pilots, so each model runs as its makers advise.
SAMPLING = {
    "IFM/K2-Horizon-3.7B": {m: {"temperature": 1.0, "top_p": 0.95} for m in ("think", "nothink")},
    "IFM/K2-Horizon-7B": {m: {"temperature": 1.0, "top_p": 0.95} for m in ("think", "nothink")},
    "openbmb/MiniCPM5-2B": {m: {"temperature": 1.0, "top_p": 0.95, "min_p": 0.0} for m in ("think", "nothink")},
    "Qwen/Qwen3.5-4B": {
        "think": {"temperature": 1.0, "top_p": 0.95, "top_k": 20, "min_p": 0.0, "presence_penalty": 1.5},
        "nothink": {"temperature": 0.7, "top_p": 0.8, "top_k": 20, "min_p": 0.0, "presence_penalty": 1.5},
    },
}
MAX_TOKENS = 32768

# K2 Horizon 7B at low effort sometimes opens <ifm|think_faster> but closes with </ifm|think>, so the
# server's reasoning parser files the whole reply as thinking. The visible part is recovered after the
# last closing tag, and every recovery is flagged.
_CLOSE = re.compile(r"</(?:ifm\|think(?:_fast|_faster)?|think)>")


def visible_text(content: str, reasoning: str) -> tuple[str, bool]:
    if content.strip():
        return content, False
    hits = list(_CLOSE.finditer(reasoning or ""))
    if hits:
        return reasoning[hits[-1].end():], True
    return content, False


def slug(model: str) -> str:
    return model.split("/")[-1].lower()


def base_url(model: str) -> str:
    """Deployed app URL (modal deploy). Modal turns dots into dashes in the host name."""
    override = os.environ.get("KWIK_BASE_URL")
    if override:
        return override.rstrip("/")
    return f"https://myredmi4ktv--kwik-vllm-{slug(model).replace('.', '-')}-serve.us-east.modal.run/v1"


def client_for(model: str) -> AsyncOpenAI:
    return AsyncOpenAI(base_url=base_url(model), api_key="EMPTY",
                       timeout=httpx.Timeout(900.0, connect=60.0), max_retries=0)


def _reasoning_piece(delta) -> str:
    for name in ("reasoning_content", "reasoning"):
        v = getattr(delta, name, None)
        if v is None and getattr(delta, "model_extra", None):
            v = delta.model_extra.get(name)
        if v:
            return v
    return ""


async def chat(client: AsyncOpenAI, model: str, mode: str, messages: list[dict],
               seed: int | None = None, attempts: int = 6) -> dict:
    """Stream one chat completion. Streaming keeps Modal's 150 s request limit from cutting long thinking."""
    s = SAMPLING[model][mode]
    last_err = None
    for attempt in range(attempts):
        t0 = time.time()
        content, reasoning, usage, finish = [], [], None, None
        try:
            stream = await client.chat.completions.create(
                model=model, messages=messages, max_tokens=MAX_TOKENS, seed=seed, stream=True,
                stream_options={"include_usage": True},
                temperature=s["temperature"], top_p=s["top_p"], presence_penalty=s.get("presence_penalty", 0.0),
                extra_body={"chat_template_kwargs": MODELS[model][mode],
                            **{k: s[k] for k in ("top_k", "min_p") if k in s}},
            )
            async for chunk in stream:
                if chunk.usage:
                    usage = chunk.usage
                if not chunk.choices:
                    continue
                ch = chunk.choices[0]
                if ch.delta:
                    if ch.delta.content:
                        content.append(ch.delta.content)
                    r = _reasoning_piece(ch.delta)
                    if r:
                        reasoning.append(r)
                if ch.finish_reason:
                    finish = ch.finish_reason
            raw_content, raw_reasoning = "".join(content), "".join(reasoning)
            visible, recovered = visible_text(raw_content, raw_reasoning)
            return {
                "visible": visible, "visible_recovered": recovered,
                "content": raw_content, "reasoning": raw_reasoning, "finish_reason": finish,
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "seconds": round(time.time() - t0, 2), "attempts": attempt + 1, "error": None,
            }
        except Exception as e:  # network, 5xx, cold start
            last_err = f"{type(e).__name__}: {str(e)[:300]}"
            await asyncio.sleep(min(60, 5 * 2 ** attempt))
    return {"visible": "", "visible_recovered": False, "content": "", "reasoning": "", "finish_reason": None, "prompt_tokens": None,
            "completion_tokens": None, "seconds": None, "attempts": attempts, "error": last_err}
