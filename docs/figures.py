"""Static figures shared by the report and the slides (architecture and generation pipeline)."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

VIOLET, LAVENDER, INK, MUTED, GOLD = "#4C1D95", "#EDE7FB", "#1F1B2E", "#6B6680", "#B7791F"


def _box(ax, x, y, w, h, title, sub="", fill=LAVENDER, edge=VIOLET):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc=fill, ec=edge, lw=1.4))
    ax.text(x + w / 2, y + h / 2 + (0.13 if sub else 0), title, ha="center", va="center",
            fontsize=10.5, fontweight="bold", color=INK)
    if sub:
        ax.text(x + w / 2, y + h / 2 - 0.2, sub, ha="center", va="center", fontsize=8.2, color=MUTED)


def _arrow(ax, p1, p2, label="", color=VIOLET, rad=0.0):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=13, lw=1.4, color=color,
                                 connectionstyle=f"arc3,rad={rad}"))
    if label:
        ax.text((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2 + 0.14, label, ha="center", fontsize=7.8, color=MUTED)


def architecture(path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(11.6, 5.6), dpi=200)
    ax.set_xlim(0, 11.6)
    ax.set_ylim(0, 5.6)
    ax.axis("off")
    L, B, M, R, W = 0.1, 3.0, 5.9, 9.1, 2.2   # column x positions and box width

    _box(ax, L, 2.3, 2.0, 1.0, "React UI", "4 pages + workspace", fill="#FFFFFF")
    _box(ax, B, 2.3, 2.0, 1.0, "FastAPI backend", "REST API + validation", fill="#FFFFFF")
    _box(ax, B, 0.55, 2.0, 1.0, "PostgreSQL", "stories · runs · scenes", fill="#FFFFFF")
    _box(ax, M, 4.0, W, 1.0, "Prompt builder", "conditions + 4 strategies")
    _box(ax, M, 2.3, W, 1.0, "Story JSON", "chapters · beats · scenes")
    _box(ax, M, 0.55, W, 1.0, "Image worker", "scene + character sheet")
    _box(ax, R, 4.0, W, 1.0, "Gemini LLM", "pretrained Transformer", fill="#F6F1E4", edge=GOLD)
    _box(ax, R, 2.3, W, 1.0, "Evaluation", "distinct-n · coverage · ...")
    _box(ax, R, 0.55, W, 1.0, "Image model", "OpenAI gpt-image / Flux", fill="#F6F1E4", edge=GOLD)

    _arrow(ax, (L + 2.0, 2.8), (B, 2.8))
    ax.text((L + 2.0 + B) / 2, 3.0, "idea +\nsettings", ha="center", fontsize=7.8, color=MUTED)
    _arrow(ax, (B + 1.0, 3.3), (M, 4.5), rad=-0.25)
    _arrow(ax, (M + W, 4.5), (R, 4.5))
    ax.text((M + W + R) / 2, 4.62, "prompt", ha="center", fontsize=7.8, color=MUTED)
    _arrow(ax, (R + 0.6, 4.0), (M + W - 0.4, 3.3), rad=0.0)
    ax.text(R + 0.7, 3.62, "JSON text", ha="left", fontsize=7.8, color=MUTED)
    _arrow(ax, (M + W, 2.65), (R, 2.65))
    ax.text((M + W + R) / 2, 2.4, "metrics", ha="center", fontsize=7.8, color=MUTED)
    _arrow(ax, (M, 2.8), (B + 2.0, 2.8))
    _arrow(ax, (M + W / 2, 2.3), (M + W / 2, 1.55))
    ax.text(M + W / 2 + 0.08, 1.9, "4 scene prompts", fontsize=7.8, color=MUTED)
    _arrow(ax, (M + W, 1.2), (R, 1.2))
    _arrow(ax, (R, 0.85), (M + W, 0.85))
    ax.text((M + W + R) / 2, 1.3, "prompt", ha="center", fontsize=7.8, color=MUTED)
    ax.text((M + W + R) / 2, 0.6, "image", ha="center", fontsize=7.8, color=MUTED)
    _arrow(ax, (M, 1.05), (B + 2.0, 1.05))
    ax.text((M + B + 2.0) / 2, 1.17, "save", ha="center", fontsize=7.8, color=MUTED)
    _arrow(ax, (B + 1.0, 1.55), (B + 1.0, 2.3))
    ax.text(B + 1.08, 1.9, "store / read", fontsize=7.8, color=MUTED)
    ax.text(R + W / 2, 5.3, "External pretrained models", ha="center", fontsize=8.5, color=GOLD, fontweight="bold")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def strategy_pipelines(path: Path) -> Path:
    rows = [
        ("Direct", ["Brief", "Write story"]),
        ("Interview Pattern", ["Brief", "Editor Q&A (5 questions)", "Write from Q&A"]),
        ("Chain-of-Thought", ["Brief", "Visible plan (world, cast, arc)", "Write story"]),
        ("Tree-of-Thought", ["Brief", "3 plot branches", "Score & select", "Write chosen branch"]),
    ]
    fig, ax = plt.subplots(figsize=(11, 4.2), dpi=200)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 4.2)
    ax.axis("off")
    for i, (name, steps) in enumerate(rows):
        y = 3.45 - i * 1.0
        ax.text(0.1, y + 0.3, name, fontsize=10.5, fontweight="bold", color=INK, va="center")
        x = 2.4
        width = (8.4 - 0.25 * (len(steps) - 1)) / len(steps)
        for j, st in enumerate(steps):
            last = j == len(steps) - 1
            _box(ax, x, y, width, 0.6, "", fill=VIOLET if last else LAVENDER)
            ax.text(x + width / 2, y + 0.3, st, ha="center", va="center", fontsize=8.6,
                    color="white" if last else INK, fontweight="bold" if last else "normal")
            if not last:
                _arrow(ax, (x + width, y + 0.3), (x + width + 0.25, y + 0.3))
            x += width + 0.25
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


if __name__ == "__main__":
    out = Path(__file__).parent / "assets"
    print(architecture(out / "architecture.png"))
    print(strategy_pipelines(out / "strategies.png"))
