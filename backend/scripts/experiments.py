"""Run the report's experiments and export the results (syllabus: evaluation of generated text).

    cd backend && source .venv/bin/activate
    python scripts/experiments.py              # run missing experiments, then export
    python scripts/experiments.py --export     # only export what is already in the database
    python scripts/experiments.py --images     # also illustrate every experiment story (costs image credits)

Plan: data/experiment_plan.json (3 ideas x 6 variants = 18 stories, about 24 Gemini calls).
Already-finished runs are reused, so the script can be stopped and restarted safely.

Outputs (all under data/):
    experiments/results.csv         one row per story with every metric
    experiments/summary.json        averages by strategy and by temperature, plus findings (used by the report and slides)
    experiments/charts/*.png        charts for the report
    samples/*.json                  full generated stories with their prompts, settings and metrics
"""
import argparse
import csv
import json
import re
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db import SessionLocal, init_db  # noqa: E402
from app.models import Story  # noqa: E402
from app.providers.llm import ProviderError, ProviderRateLimited, get_llm  # noqa: E402
from app.schemas import GenerateRequest  # noqa: E402
from app.services.image_worker import render_story_images  # noqa: E402
from app.services.story_service import generate_story, idea_key  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
OUT = DATA / "experiments"
SAMPLES = DATA / "samples"
STRATEGY_NAMES = {"direct": "Direct", "interview": "Interview Pattern", "cot": "Chain-of-Thought", "tot": "Tree-of-Thought"}
METRICS = ["distinct_1", "distinct_2", "brief_coverage", "character_presence", "length_ratio", "structure_score",
           "word_count", "llm_calls", "latency_ms"]
HUMAN = ["coherence", "creativity", "adherence", "character_consistency"]


def request_for(idea: dict, variant: dict, sampling: dict) -> GenerateRequest:
    return GenerateRequest(
        idea=idea["idea"], plot=idea["plot"], strategy=variant["strategy"],
        sampling={**sampling, "temperature": variant["temperature"]},
    )


def find_existing(db, req: GenerateRequest, provider: str):
    q = select(Story).where(Story.idea_key == idea_key(req), Story.strategy == req.strategy, Story.provider == provider)
    for s in db.scalars(q.order_by(Story.created_at)).all():
        if abs(s.sampling.get("temperature", -1) - req.sampling.temperature) < 1e-6:
            return s
    return None


def run(plan: dict, with_images: bool, allow_demo: bool) -> list[int]:
    llm = get_llm()
    if llm.name == "mock" and not allow_demo:
        sys.exit("Demo mode: set GEMINI_API_KEY in backend/.env (LLM_PROVIDER=auto) so results come from the real model.")
    ids, total = [], len(plan["ideas"]) * len(plan["variants"])
    n = 0
    for idea in plan["ideas"]:
        for variant in plan["variants"]:
            n += 1
            req = request_for(idea, variant, plan["sampling"])
            label = f"[{n}/{total}] {idea['title']} · {STRATEGY_NAMES[req.strategy]} · T={req.sampling.temperature}"
            db = SessionLocal()
            try:
                existing = find_existing(db, req, llm.name)
                if existing:
                    print(f"{label}: already done (story #{existing.id})")
                    ids.append(existing.id)
                    continue
                for attempt in range(4):
                    try:
                        story = generate_story(db, llm, req)
                        break
                    except ProviderRateLimited:
                        wait = 60 * (attempt + 1)
                        print(f"{label}: rate limited, waiting {wait} s")
                        time.sleep(wait)
                    except ProviderError as exc:
                        print(f"{label}: {exc} (attempt {attempt + 1}/4)")
                        time.sleep(5)
                else:
                    print(f"{label}: FAILED, skipped. Run the script again later to retry.")
                    continue
                if not with_images:
                    for sc in story.scenes:
                        sc.status, sc.error = "failed", "Not illustrated during the experiment run. Use Retry images to draw them."
                    db.commit()
                print(f"{label}: done (story #{story.id}, {round(sum(r.latency_ms for r in story.runs) / 1000, 1)} s)")
                ids.append(story.id)
            finally:
                db.close()
            if with_images:
                render_story_images(story.id)
            time.sleep(2)  # stay friendly with free-tier rate limits
    return ids


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower().replace("é", "e")).strip("-")


def mean(values):
    vals = [v for v in values if v is not None]
    return round(statistics.mean(vals), 3) if vals else None


def export(plan: dict) -> dict:
    db = SessionLocal()
    title_by_key = {}
    for idea in plan["ideas"]:
        for variant in plan["variants"]:
            title_by_key[idea_key(request_for(idea, variant, plan["sampling"]))] = idea["title"]
    stories = [s for s in db.scalars(select(Story).order_by(Story.created_at)).all() if s.idea_key in title_by_key]
    planned = {(v["strategy"], v["temperature"]) for v in plan["variants"]}
    stories = [s for s in stories if (s.strategy, s.sampling.get("temperature")) in planned]
    # keep the first run of each (idea, strategy, temperature, provider)
    seen, rows, picked = set(), [], []
    for s in stories:
        k = (s.idea_key, s.strategy, s.sampling.get("temperature"), s.provider)
        if k in seen:
            continue
        seen.add(k)
        picked.append(s)
    live = [s for s in picked if s.provider != "mock"]
    use = live or picked  # demo rows only when nothing live exists (builders then mark the output as a preview)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "charts").mkdir(exist_ok=True)
    SAMPLES.mkdir(parents=True, exist_ok=True)
    for old in SAMPLES.glob("*.json"):
        old.unlink()

    for s in use:
        m = s.metrics or {}
        hr = s.human_rating or {}
        row = {"story_id": s.id, "idea": title_by_key[s.idea_key], "title": s.title, "strategy": s.strategy,
               "strategy_name": STRATEGY_NAMES[s.strategy], "temperature": s.sampling.get("temperature"),
               "top_p": s.sampling.get("top_p"), "top_k": s.sampling.get("top_k"), "provider": s.provider, "model": s.model}
        row.update({k: m.get(k) for k in METRICS})
        row.update({f"human_{k}": hr.get(k) for k in HUMAN})
        row["human_avg"] = mean([hr.get(k) for k in HUMAN]) if hr else None
        rows.append(row)
        sample = {
            "title": s.title, "idea": s.idea, "plot": s.plot, "sampling": s.sampling, "strategy": s.strategy,
            "provider": s.provider, "model": s.model, "created_at": s.created_at.isoformat(),
            "prompts": [{"step": r.step, "prompt": r.prompt, "latency_ms": r.latency_ms} for r in s.runs],
            "intermediate_steps": s.artifacts, "output": s.output, "metrics": s.metrics, "human_rating": s.human_rating,
            "scenes": [{"index": sc.index, "caption": sc.caption, "image_prompt": sc.image_prompt} for sc in s.scenes],
        }
        name = f"{slug(title_by_key[s.idea_key])}__{s.strategy}__t{s.sampling.get('temperature')}.json"
        (SAMPLES / name).write_text(json.dumps(sample, indent=2, ensure_ascii=False), encoding="utf-8")
    db.close()

    if not rows:
        sys.exit("No experiment stories found. Run without --export first.")
    with open(OUT / "results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    base_t = 0.9
    by_strategy = {}
    for st in STRATEGY_NAMES:
        rs = [r for r in rows if r["strategy"] == st and r["temperature"] == base_t]
        if rs:
            by_strategy[st] = {k: mean([r[k] for r in rs]) for k in METRICS + ["human_avg"]} | {"n": len(rs)}
    by_temperature = {}
    for t in sorted({r["temperature"] for r in rows if r["strategy"] == "direct"}):
        rs = [r for r in rows if r["strategy"] == "direct" and r["temperature"] == t]
        by_temperature[str(t)] = {k: mean([r[k] for r in rs]) for k in METRICS + ["human_avg"]} | {"n": len(rs)}

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "demo": not live,
        "model": rows[0]["model"], "provider": rows[0]["provider"],
        "ideas": [i["title"] for i in plan["ideas"]], "design": plan["description"],
        "runs": len(rows), "llm_calls": sum(r["llm_calls"] or 0 for r in rows),
        "human_rated": sum(1 for r in rows if r["human_avg"] is not None),
        "by_strategy": by_strategy, "by_temperature": by_temperature,
        "findings": findings(by_strategy, by_temperature),
        "rows": rows,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    charts(by_strategy, by_temperature)
    print(f"Exported {len(rows)} runs to {OUT} and {SAMPLES}" + (" (DEMO data: not for the report)" if not live else ""))
    return summary


def findings(by_s: dict, by_t: dict) -> list[str]:
    """Plain-language observations computed from the numbers (no hand-written claims).

    Differences smaller than NOISE are reported as "about the same": with one run per setting they are within run-to-run noise.
    """
    NOISE_D2, NOISE_PCT = 0.01, 0.03
    out = []
    names = STRATEGY_NAMES

    def best(metric, high=True):
        vals = [(k, v[metric]) for k, v in by_s.items() if v.get(metric) is not None]
        return (max if high else min)(vals, key=lambda x: x[1]) if vals else None

    def change(a, b, noise):
        if abs(b - a) < noise:
            return "stayed about the same"
        return "rose" if b > a else "fell"

    if len(by_t) >= 2:
        ts = sorted(by_t, key=float)
        lo, hi = by_t[ts[0]], by_t[ts[-1]]
        if lo.get("distinct_2") is not None and hi.get("distinct_2") is not None:
            d2 = [by_t[t]["distinct_2"] for t in ts if by_t[t].get("distinct_2") is not None]
            trend = change(lo["distinct_2"], hi["distinct_2"], NOISE_D2)
            out.append(f"Temperature (direct prompting, T={ts[0]} to T={ts[-1]}): Distinct-2 {trend} "
                       f"({lo['distinct_2']:.3f} to {hi['distinct_2']:.3f}; range {min(d2):.3f}-{max(d2):.3f} across all three).")
        if lo.get("brief_coverage") is not None and hi.get("brief_coverage") is not None:
            trend = change(lo["brief_coverage"], hi["brief_coverage"], NOISE_PCT)
            out.append(f"Brief coverage {trend} with temperature: {lo['brief_coverage'] * 100:.0f}% at T={ts[0]} and "
                       f"{hi['brief_coverage'] * 100:.0f}% at T={ts[-1]}.")
    cov = best("brief_coverage")
    if cov and "direct" in by_s and by_s["direct"].get("brief_coverage") is not None and cov[0] != "direct":
        base = by_s["direct"]["brief_coverage"]
        out.append(f"{names[cov[0]]} gave the highest brief coverage at T=0.9: {cov[1] * 100:.0f}% versus "
                   f"{base * 100:.0f}% for direct prompting (+{round(cov[1] * 100) - round(base * 100)} points).")
    elif cov:
        out.append(f"Highest brief coverage at T=0.9: {names[cov[0]]} ({cov[1] * 100:.0f}%).")
    d2 = [v["distinct_2"] for v in by_s.values() if v.get("distinct_2") is not None]
    if d2:
        if max(d2) - min(d2) < NOISE_D2:
            out.append(f"Lexical diversity was similar for all strategies (Distinct-2 {min(d2):.3f}-{max(d2):.3f}).")
        else:
            b = best("distinct_2")
            tied = [names[k] for k, v in by_s.items() if v.get("distinct_2") is not None and abs(v["distinct_2"] - b[1]) < 0.001]
            out.append(f"Highest Distinct-2 (diversity) at T=0.9: {' and '.join(tied)} ({b[1]:.3f}).")
    b = best("character_presence")
    if b:
        out.append(f"Highest character presence (consistency proxy) at T=0.9: {names[b[0]]} ({b[1] * 100:.0f}%).")
    lr = {k: v["length_ratio"] for k, v in by_s.items() if v.get("length_ratio") is not None}
    if lr and max(lr.values()) < 0.95:
        lo_k, hi_k = min(lr, key=lr.get), max(lr, key=lr.get)
        out.append(f"Every strategy wrote less than the requested length (length ratio {lr[lo_k]:.2f} for {names[lo_k]} "
                   f"to {lr[hi_k]:.2f} for {names[hi_k]}).")
    lat = {k: v["latency_ms"] for k, v in by_s.items() if v.get("latency_ms")}
    if "direct" in lat and "tot" in lat:
        out.append(f"Tree-of-Thought needs 2 model calls and took {lat['tot'] / lat['direct']:.1f}x the generation time of "
                   f"direct prompting ({lat['tot'] / 1000:.1f} s vs {lat['direct'] / 1000:.1f} s on average).")
    s = [v["structure_score"] for v in by_s.values() if v.get("structure_score") is not None]
    if s:
        out.append(f"Average structure score across strategies was {statistics.mean(s) * 100:.0f}% "
                   "(6 beats, 4 scenes and the requested number of chapters).")
    return out


def charts(by_s: dict, by_t: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = ["#4C1D95", "#8B5CF6", "#C4B5FD", "#B7791F"]
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

    if by_s:
        keys = list(by_s)
        metrics = [("distinct_2", "Distinct-2"), ("brief_coverage", "Brief coverage"),
                   ("character_presence", "Character presence"), ("structure_score", "Structure")]
        fig, ax = plt.subplots(figsize=(8, 4), dpi=200)
        width = 0.8 / len(keys)
        for i, k in enumerate(keys):
            vals = [by_s[k].get(m) or 0 for m, _ in metrics]
            bars = ax.bar([x + i * width for x in range(len(metrics))], vals, width, label=STRATEGY_NAMES[k], color=colors[i % 4])
            ax.bar_label(bars, fmt="%.2f", fontsize=7, padding=2)
        ax.set_xticks([x + width * (len(keys) - 1) / 2 for x in range(len(metrics))], [l for _, l in metrics])
        ax.set_ylim(0, 1.15)
        ax.set_ylabel("Score (0–1)")
        ax.set_title("Automatic metrics by prompting strategy (T = 0.9)")
        ax.legend(frameon=False, ncol=4, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.1))
        fig.tight_layout()
        fig.savefig(OUT / "charts" / "strategy_metrics.png", facecolor="white")
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(6, 3.4), dpi=200)
        vals = [(by_s[k].get("latency_ms") or 0) / 1000 for k in keys]
        bars = ax.bar([STRATEGY_NAMES[k] for k in keys], vals, color=colors[: len(keys)])
        ax.bar_label(bars, labels=[f"{v:.1f} s\n{int(by_s[k].get('llm_calls') or 0)} call(s)" for v, k in zip(vals, keys)], fontsize=8, padding=2)
        ax.set_ylabel("Seconds")
        ax.set_ylim(0, max(vals + [1]) * 1.35)
        ax.set_title("Average generation time by strategy")
        fig.tight_layout()
        fig.savefig(OUT / "charts" / "strategy_latency.png", facecolor="white")
        plt.close(fig)

    if by_t:
        ts = sorted(by_t, key=float)
        fig, ax = plt.subplots(figsize=(6, 3.4), dpi=200)
        for metric, label, c in [("distinct_2", "Distinct-2", colors[0]), ("distinct_1", "Distinct-1", colors[1]),
                                 ("brief_coverage", "Brief coverage", colors[3])]:
            ys = [by_t[t].get(metric) for t in ts]
            ax.plot([float(t) for t in ts], ys, marker="o", color=c, label=label)
            for x, y in zip(ts, ys):
                if y is not None:
                    ax.annotate(f"{y:.2f}", (float(x), y), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=7)
        ax.set_xlabel("Temperature")
        ax.set_ylabel("Score (0–1)")
        ax.set_ylim(0, 1.1)
        ax.set_title("Effect of temperature (direct prompting)")
        ax.legend(frameon=False, fontsize=8)
        fig.tight_layout()
        fig.savefig(OUT / "charts" / "temperature_effect.png", facecolor="white")
        plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--export", action="store_true", help="only export existing results")
    ap.add_argument("--images", action="store_true", help="also illustrate experiment stories")
    ap.add_argument("--allow-demo", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args()
    plan = json.loads((DATA / "experiment_plan.json").read_text(encoding="utf-8"))
    init_db()
    print(f"Text model: {get_settings().effective_llm} · {get_settings().gemini_model}")
    if not args.export:
        run(plan, args.images, args.allow_demo)
    export(plan)


if __name__ == "__main__":
    main()
