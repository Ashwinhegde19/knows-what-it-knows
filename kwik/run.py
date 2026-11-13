"""Run one check for one model and one thinking mode. Saves one JSON line per question, raw replies included.

    python -m kwik.run calibration --model IFM/K2-Horizon-3.7B --mode think --runs 3
    python -m kwik.run abstention  --model IFM/K2-Horizon-3.7B --mode think --runs 3
    python -m kwik.run pushback    --model IFM/K2-Horizon-3.7B --mode think   # needs calibration run 1

Reruns skip questions already done without an error, so a crash costs nothing.
"""
import argparse
import asyncio
import csv
import json
import os
import random
import zlib
from pathlib import Path

from kwik import prompts
from kwik.models import MODELS, chat, client_for, slug
from kwik.parse import matches_gold, parse_final, parse_mc

ROOT = Path(__file__).resolve().parents[1]
RAW = Path(os.environ.get("KWIK_RAW", ROOT / "results" / "raw"))
LETTERS = "ABCD"


def load_csv(name: str) -> list[dict]:
    with open(ROOT / "data" / name, newline="") as f:
        return list(csv.DictReader(f))


def out_path(task: str, model: str, mode: str, run: int) -> Path:
    p = RAW / task / f"{slug(model)}__{mode}__run{run}.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def done_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    ids = set()
    for line in path.read_text().splitlines():
        r = json.loads(line)
        if not r.get("error"):
            ids.add(r["key"])
    return ids


def append(path: Path, row: dict, lock: asyncio.Lock):
    async def _w():
        async with lock:
            with path.open("a") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return _w()


async def run_calibration(model, mode, runs, limit, conc):
    items = load_csv("factual_200.csv")[:limit]
    client, sem, lock = client_for(model), asyncio.Semaphore(conc), asyncio.Lock()
    for run in range(1, runs + 1):
        path = out_path("calibration", model, mode, run)
        skip = done_ids(path)

        async def one(q):
            async with sem:
                msg = [{"role": "user", "content": prompts.CALIBRATION.format(**q)}]
                r = await chat(client, model, mode, msg, seed=run * 100000 + int(q["id"][1:]))
            p = parse_mc(r["visible"])
            row = {"key": q["id"], "id": q["id"], "run": run, "model": model, "mode": mode,
                   "category": q["category"], "gold": q["answer"], **p,
                   "correct": p["answer"] == q["answer"] if p["answer"] else None, **r}
            await append(path, row, lock)

        todo = [q for q in items if q["id"] not in skip]
        print(f"calibration {slug(model)} {mode} run{run}: {len(todo)} to do", flush=True)
        await asyncio.gather(*(one(q) for q in todo))


async def run_abstention(model, mode, runs, limit, conc):
    items = load_csv("unanswerable_50.csv")[:limit] + load_csv("answerable_50.csv")[:limit]
    client, sem, lock = client_for(model), asyncio.Semaphore(conc), asyncio.Lock()
    for run in range(1, runs + 1):
        path = out_path("abstention", model, mode, run)
        skip = done_ids(path)

        async def one(q, cond):
            tmpl = prompts.ABSTENTION_PLAIN if cond == "plain" else prompts.ABSTENTION_PENALTY
            async with sem:
                msg = [{"role": "user", "content": tmpl.format(question=q["question"])}]
                r = await chat(client, model, mode, msg, seed=run * 100000 + zlib.crc32(q["id"].encode()) % 99991)
            p = parse_final(r["visible"])
            answerable = q["kind"] == "answerable_trivia"
            aliases = q.get("gold_aliases", "").split(" || ") if answerable else []
            correct = (not p["abstained"]) and matches_gold(p["final"], aliases) if answerable else None
            row = {"key": f"{q['id']}|{cond}", "id": q["id"], "kind": q["kind"], "answerable": answerable,
                   "condition": cond, "run": run, "model": model, "mode": mode, **p, "correct": correct, **r}
            await append(path, row, lock)

        todo = [(q, c) for q in items for c in ("plain", "penalty") if f"{q['id']}|{c}" not in skip]
        print(f"abstention {slug(model)} {mode} run{run}: {len(todo)} to do", flush=True)
        await asyncio.gather(*(one(q, c) for q, c in todo))


async def run_pushback(model, mode, limit, conc):
    calib = out_path("calibration", model, mode, 1)
    if not calib.exists():
        raise SystemExit(f"needs {calib} first")
    first = {}
    for line in calib.read_text().splitlines():
        r = json.loads(line)
        if not r.get("error") and r["answer"]:
            first[r["id"]] = r
    items = [q for q in load_csv("factual_200.csv")[:limit] if q["id"] in first]
    client, sem, lock = client_for(model), asyncio.Semaphore(conc), asyncio.Lock()
    path = out_path("pushback", model, mode, 1)
    skip = done_ids(path)

    async def one(q):
        start = first[q["id"]]
        right = start["answer"] == q["answer"]
        if right:  # push toward a wrong letter, chosen with a fixed seed
            wrong = [L for L in LETTERS if L != q["answer"]]
            target = random.Random(f"{q['id']}-target").choice(wrong)
        else:      # push toward the right letter
            target = q["answer"]
        messages = [{"role": "user", "content": prompts.CALIBRATION.format(**q)},
                    {"role": "assistant", "content": start["visible"], "reasoning_content": ""}]
        steps, flipped_at = [], None
        async with sem:
            for i, (name, text) in enumerate(prompts.PUSHBACK):
                messages.append({"role": "user", "content": text.format(target=target, category=q["category"])})
                r = await chat(client, model, mode, messages, seed=900000 + i * 1000 + int(q["id"][1:]))
                p = parse_mc(r["visible"])
                # Earlier turns carry only the visible answer. K2 Horizon's template requires a thinking
                # field on every assistant turn, so an empty one is sent for all models alike.
                messages.append({"role": "assistant", "content": r["visible"], "reasoning_content": ""})
                steps.append({"step": i, "name": name, **p, **r})
                if r["error"]:
                    break
                if p["answer"] and p["answer"] != start["answer"]:
                    flipped_at = i
                    break
        last = steps[-1]
        row = {"key": q["id"], "id": q["id"], "model": model, "mode": mode, "category": q["category"],
               "gold": q["answer"], "start_answer": start["answer"], "start_confidence": start["confidence"],
               "start_correct": right, "target": target, "flipped_at": flipped_at,
               "flipped_to": last["answer"] if flipped_at is not None else None,
               "error": last["error"], "steps": steps}
        await append(path, row, lock)

    todo = [q for q in items if q["id"] not in skip]
    print(f"pushback {slug(model)} {mode}: {len(todo)} to do", flush=True)
    await asyncio.gather(*(one(q) for q in todo))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task", choices=["calibration", "abstention", "pushback"])
    ap.add_argument("--model", required=True, choices=list(MODELS))
    ap.add_argument("--mode", required=True, choices=["think", "nothink"])
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--limit", type=int, default=10_000, help="first N questions only (for quick checks)")
    ap.add_argument("--concurrency", type=int, default=48)
    a = ap.parse_args()
    if a.task == "calibration":
        asyncio.run(run_calibration(a.model, a.mode, a.runs, a.limit, a.concurrency))
    elif a.task == "abstention":
        asyncio.run(run_abstention(a.model, a.mode, a.runs, a.limit, a.concurrency))
    else:
        asyncio.run(run_pushback(a.model, a.mode, a.limit, a.concurrency))


if __name__ == "__main__":
    main()
