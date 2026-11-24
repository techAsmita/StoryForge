"""Build submission/Report_XX.pdf (Thapar-style project report).

    python docs/build_report.py

Reads docs/project_info.json (names, group, GitHub link) and the experiment results in data/experiments/
(run backend/scripts/experiments.py first). If the results came from demo mode the PDF is stamped PREVIEW.
"""
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate, PageBreak,
                                PageTemplate, Paragraph, Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
DOCS, ASSETS, DATA = ROOT / "docs", ROOT / "docs" / "assets", ROOT / "data"
INFO = json.loads((DOCS / "project_info.json").read_text(encoding="utf-8"))
SUMMARY_PATH = DATA / "experiments" / "summary.json"

for style, file in [("Serif", "Regular"), ("Serif-Bold", "Bold"), ("Serif-Italic", "Italic"), ("Serif-BoldItalic", "BoldItalic")]:
    pdfmetrics.registerFont(TTFont(style, str(ASSETS / "fonts" / f"LiberationSerif-{file}.ttf")))
pdfmetrics.registerFontFamily("Serif", normal="Serif", bold="Serif-Bold", italic="Serif-Italic", boldItalic="Serif-BoldItalic")

RED, VIOLET, GREY = colors.HexColor("#C41230"), colors.HexColor("#4C1D95"), colors.HexColor("#555555")
LIGHT = colors.HexColor("#EFEAF9")

S = {
    "body": ParagraphStyle("body", fontName="Serif", fontSize=12, leading=18, alignment=TA_JUSTIFY, spaceAfter=8),
    "bullet": ParagraphStyle("bullet", fontName="Serif", fontSize=12, leading=17, alignment=TA_LEFT, leftIndent=18,
                             bulletIndent=6, spaceAfter=3),
    "h1": ParagraphStyle("h1", fontName="Serif-Bold", fontSize=15, leading=20, alignment=TA_LEFT, spaceAfter=10, spaceBefore=16, keepWithNext=1),
    "h1c": ParagraphStyle("h1c", fontName="Serif-Bold", fontSize=15, leading=20, alignment=TA_CENTER, spaceAfter=12, spaceBefore=4),
    "h2": ParagraphStyle("h2", fontName="Serif-Bold", fontSize=13, leading=18, spaceBefore=10, spaceAfter=6, keepWithNext=1),
    "h3": ParagraphStyle("h3", fontName="Serif-BoldItalic", fontSize=12, leading=16, spaceBefore=6, spaceAfter=4),
    "caption": ParagraphStyle("caption", fontName="Serif-Italic", fontSize=10, leading=13, alignment=TA_CENTER, spaceBefore=4, spaceAfter=12, textColor=GREY),
    "cell": ParagraphStyle("cell", fontName="Serif", fontSize=10, leading=13),
    "cellb": ParagraphStyle("cellb", fontName="Serif-Bold", fontSize=10, leading=13),
    "center": ParagraphStyle("center", fontName="Serif", fontSize=12, leading=18, alignment=TA_CENTER),
    "ref": ParagraphStyle("ref", fontName="Serif", fontSize=11, leading=15, leftIndent=24, firstLineIndent=-24, spaceAfter=5),
    "code": ParagraphStyle("code", fontName="Courier", fontSize=8.2, leading=10.5, textColor=colors.HexColor("#222222")),
}

FIG = {"n": 0}


def _env_value(name, default=""):
    """Read one non-secret setting from backend/.env (never the API keys)."""
    env = ROOT / "backend" / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith(f"{name}="):
                return line.split("=", 1)[1].split("#")[0].strip() or default
    return default


_PROVIDER = _env_value("IMAGE_PROVIDER", "pollinations")
if _PROVIDER == "openai":
    IMG_SHORT = f"OpenAI {_env_value('OPENAI_IMAGE_MODEL', 'gpt-image-2')}"
    IMG_LONG = (f"{IMG_SHORT}, {_env_value('OPENAI_IMAGE_QUALITY', 'medium')} quality [21] "
                "(Flux via Pollinations.ai as a free alternative)")
else:
    IMG_SHORT = "Flux via Pollinations.ai"
    IMG_LONG = "Flux, an open diffusion-family model, via Pollinations.ai [21] (OpenAI gpt-image-2 also supported)"
TAB = {"n": 0}


# ---------------------------------------------------------------- page decoration
class ReportDoc(BaseDocTemplate):
    def __init__(self, path, demo):
        super().__init__(str(path), pagesize=A4, leftMargin=2.6 * cm, rightMargin=2.3 * cm, topMargin=2.4 * cm,
                         bottomMargin=2.3 * cm, title=f"{INFO['short_title']} - Project Report",
                         author=", ".join(m["name"] for m in INFO["members"]), subject=f"{INFO['course_code']} {INFO['course_name']}")
        self.demo = demo
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="f")
        self.addPageTemplates([PageTemplate("title", [frame], onPage=self._border),
                               PageTemplate("main", [frame], onPage=self._numbered)])

    def _border(self, canv, doc):
        if not self.demo:
            return
        canv.saveState()
        w, h = A4
        canv.setFont("Serif-Bold", 40)
        canv.setFillColor(colors.Color(0.85, 0.2, 0.2, alpha=0.12))
        canv.translate(w / 2, h / 2)
        canv.rotate(40)
        canv.drawCentredString(0, 0, "PREVIEW - DEMO DATA")
        canv.restoreState()

    def _numbered(self, canv, doc):
        self._border(canv, doc)
        canv.saveState()
        canv.setFont("Serif", 10)
        canv.setFillColor(GREY)
        canv.drawRightString(A4[0] - 2.0 * cm, 1.75 * cm, str(doc.page))
        canv.drawString(2.0 * cm, 1.75 * cm, f"{INFO['course_code']} · {INFO['short_title']}")
        canv.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and hasattr(flowable, "toc_level"):
            self.notify("TOCEntry", (flowable.toc_level, flowable.getPlainText(), self.page))


def H1(text):
    p = Paragraph(text, S["h1"])
    p.toc_level = 0
    return p


def H2(text):
    p = Paragraph(text, S["h2"])
    p.toc_level = 1
    return p


def P(text):
    return Paragraph(text, S["body"])


def B(items):
    return [Paragraph(i, S["bullet"], bulletText="•") for i in items]


def figure(path, caption, width_cm=15.5):
    from PIL import Image as PILImage

    with PILImage.open(path) as im:
        w, h = im.size
    width = width_cm * cm
    height = width * h / w
    if height > 15 * cm:
        height, width = 15 * cm, 15 * cm * w / h
    FIG["n"] += 1
    return KeepTogether([Image(str(path), width=width, height=height),
                         Paragraph(f"Figure {FIG['n']}: {caption}", S["caption"])])


def table(rows, widths, caption=None, header=True):
    data = [[Paragraph(str(c), S["cellb" if header and i == 0 else "cell"]) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1 if header else 0)
    style = [("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
             ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), LIGHT))
    t.setStyle(TableStyle(style))
    out = [t]
    if caption:
        TAB["n"] += 1
        out.append(Paragraph(f"Table {TAB['n']}: {caption}", S["caption"]))
    return KeepTogether(out)


# ---------------------------------------------------------------- sections
# Layout follows the format used in the course samples: title page, abstract, then
# 1. Introduction, 2. Methodology, 3. Results, 4. Discussion, 5. Conclusion (with the code link), references, appendix.
NAMES = {"direct": "Direct", "interview": "Interview Pattern", "cot": "Chain-of-Thought", "tot": "Tree-of-Thought"}


SHOTS = DOCS / "screenshots"  # fresh captures from docs/take_screenshots.py (preferred)


def screen(new, old):
    """Use docs/screenshots/desktop-<new>.png when it exists, else the older capture in docs/assets/screens/."""
    fresh = SHOTS / f"desktop-{new}.png"
    return fresh if fresh.exists() else ASSETS / "screens" / old


def _ratio(path):
    from PIL import Image as PILImage

    with PILImage.open(path) as im:
        return im.size[1] / im.size[0]


def title_page():
    c = S["center"]
    big = ParagraphStyle("big", parent=c, fontName="Serif-Bold", fontSize=19, leading=25)
    bold = ParagraphStyle("bold", parent=c, fontName="Serif-Bold", fontSize=12.5, leading=18)
    inst = ParagraphStyle("inst", parent=c, fontName="Serif-Bold", fontSize=17, leading=20, textColor=RED)
    inst2 = ParagraphStyle("inst2", parent=c, fontName="Serif", fontSize=10.5, leading=13, textColor=GREY)
    logo = ASSETS / "thapar_logo_official.png"
    flow = [Spacer(1, 1.2 * cm),
            Paragraph(INFO["project_title"].upper(), big), Spacer(1, 0.3 * cm),
            Paragraph(f"<i>Project report, {INFO['course_code']} {INFO['course_name']}</i>", c), Spacer(1, 1.0 * cm)]
    if logo.exists():
        flow += [Image(str(logo), width=5.5 * cm, height=5.5 * cm * _ratio(logo))]
    else:
        mark = ASSETS / "thapar_mark.png"
        flow += [Image(str(mark), width=1.8 * cm, height=1.8 * cm * _ratio(mark)), Spacer(1, 0.15 * cm),
                 Paragraph("THAPAR INSTITUTE", inst), Paragraph("OF ENGINEERING &amp; TECHNOLOGY", inst2),
                 Paragraph("(Deemed to be University)", inst2)]
    flow += [Spacer(1, 1.1 * cm), Paragraph("Submitted by:-", bold), Paragraph(f"Group No. {INFO['group_no']}", bold)]
    flow += [Paragraph(f"{m['name']} — Roll No. {m['roll']}", bold) for m in INFO["members"]]
    flow += [Spacer(1, 1.1 * cm), Paragraph("Under the Guidance of", bold), Paragraph(INFO["supervisor"], c),
             Spacer(1, 1.6 * cm), Paragraph(INFO["department"], bold),
             Paragraph("Thapar Institute of Engineering and Technology (Deemed to be University)", bold),
             Paragraph("Patiala, Punjab, India", bold), Spacer(1, 0.3 * cm), Paragraph(INFO["month_year"], c),
             NextPageTemplate("main"), PageBreak()]
    return flow


def abstract(summary):
    bs = summary["by_strategy"]
    best = max(bs, key=lambda k: bs[k]["brief_coverage"] or 0)
    result = ""
    if not summary["demo"] and best != "direct":
        result = (f" In a controlled experiment of {summary['runs']} live generations over {len(summary['ideas'])} story ideas, "
                  f"the {NAMES[best]} strategy gave the highest adherence to the brief ({bs[best]['brief_coverage'] * 100:.0f}% "
                  f"brief coverage versus {bs['direct']['brief_coverage'] * 100:.0f}% for direct prompting), while every strategy "
                  "returned a fully valid story structure.")
    elif summary["demo"]:
        result = " (Preview built from demo data.)"
    return [Paragraph("ABSTRACT", S["h1"]),
            P("Large language models can write fluent stories, but how a story turns out depends heavily on how the model is "
              "asked and how its output is sampled. StoryForge is a web application that turns a short story idea into an "
              "illustrated, structured story and makes those choices visible and measurable."),
            P("A user describes a protagonist, an objective, a genre, a tone, an optional world rule and an ending twist, and "
              "sets plot dials for conflict, romance, action and length. These inputs become explicit conditions in the prompt "
              "(conditional generation). The story is generated by a pretrained Transformer language model (Google Gemini) with "
              "one of four prompt-engineering strategies taught in the course: direct prompting, the Interview Pattern, "
              "Chain-of-Thought-style planning and Tree-of-Thought-style branching and selection. Temperature, top-k and top-p "
              "are passed to the model so their effect can be studied. The model returns a structured story (chapters, "
              "characters, relationships, six episode beats and four scene descriptions); the scene descriptions, combined "
              "with a shared character sheet, are rendered by a text-to-image model into a four-panel storyboard (multimodal "
              "generation)."),
            P("Every prompt, parameter, output and timing is stored in PostgreSQL. A reference-free evaluation module computes "
              "Distinct-1/2, brief coverage, character presence, length ratio and a structure score, and supports human "
              f"ratings.{result} The project demonstrates, in one working end-to-end system, the syllabus topics of LLMs, "
              "conditional text generation, sampling, prompt engineering, image generation, multimodal generation and evaluation."),
            Paragraph("<b>Keywords:</b> generative AI, large language models, conditional text generation, prompt engineering, "
                      "chain-of-thought, tree-of-thought, sampling, text-to-image, diffusion models, evaluation", S["body"])]


def numbered(items):
    return [Paragraph(f"<b>{h}:</b> {t}", S["bullet"], bulletText=f"{i}.") for i, (h, t) in enumerate(items, 1)]


def chapter_intro():
    syllabus = [["Syllabus unit", "Concept", "Where it appears in StoryForge"],
                ["Generative AI models", "Large language models, Transformer, attention, pre-training",
                 "Story text is produced by Gemini, a pretrained Transformer LLM (Section 2.1)."],
                ["Text generation with LLMs", "Conditional text generation",
                 "Idea fields, genre, tone and plot dials become explicit conditions in a structured brief."],
                ["Text generation with LLMs", "Sampling strategies",
                 "Temperature, top-k and top-p are sent to the model; a temperature sweep measures their effect."],
                ["Text generation with LLMs", "Evaluation metrics",
                 "Distinct-1/2, brief coverage, character presence, length ratio, structure score, human ratings."],
                ["Image generation", "Text-to-image generation; GANs vs newer approaches",
                 "Scene prompts are rendered by a text-to-image model; GANs and diffusion are compared (Table 2)."],
                ["Beyond text and images", "Combining LLMs with other generative models",
                 "The LLM writes scene prompts and a character sheet that drive the image model (storyboard)."],
                ["Prompt engineering", "Interview Pattern, Chain-of-Thought, Tree-of-Thought",
                 "Four selectable strategies; every prompt and intermediate step is shown in the Prompt Lab."]]
    return [H1("1. INTRODUCTION"),
            H2("1.1 Background"),
            P("Generative AI systems create new content (text, images, audio and code) rather than only classifying existing "
              "data. Large language models (LLMs) based on the Transformer [1] now write coherent long-form text, and "
              "diffusion models [12, 13] produce high-quality images from text. Encoder models such as BERT [2] are "
              "pre-trained to understand text, while decoder-only models such as GPT-2 [3] and GPT-3 [4] are pre-trained to "
              "predict the next token and can then be steered with prompts alone, which is the paradigm StoryForge uses."),
            P("How the next token is chosen matters as much as the model itself. Greedy decoding tends to produce repetitive "
              "text in open-ended tasks; top-k sampling [6] and nucleus (top-p) sampling [5] reduce this degeneration, and "
              "temperature controls how adventurous the output is. Prompting techniques add a second layer of control: "
              "Chain-of-Thought [7] asks the model for intermediate steps, Tree of Thoughts [8] generates and selects between "
              "candidate thoughts, prompt patterns such as the Interview Pattern [9] make the model gather missing details "
              "first, and planning a storyline before writing improves story coherence [18]. For images, GANs [11] were "
              "displaced for text-to-image work by diffusion models [12, 13] conditioned on text embeddings [14, 15]. "
              "Creative text has no single correct answer, so reference-based metrics such as BLEU [19] and ROUGE [20] fit "
              "poorly; diversity measures such as Distinct-n [10] and human judgement are used instead."),
            H2("1.2 Problem Statement"),
            P("Story generators and student projects built on LLMs commonly share four limitations:"),
            *numbered([("Hidden generation process", "the user types an idea and receives text, with no view of the prompt, "
                        "the decoding settings or the intermediate steps, so it is impossible to learn why one output is "
                        "better than another."),
                       ("No comparison of techniques", "prompting techniques such as Chain-of-Thought or Tree-of-Thought are "
                        "used, if at all, in isolation and are never compared on the same idea."),
                       ("No measurement", "outputs are judged by impression only; there are no reproducible metrics or "
                        "stored runs to compare."),
                       ("Disconnected images", "illustrations, when present, are generated independently of the story, so "
                        "characters change appearance from panel to panel.")]),
            H2("1.3 Objectives"),
            *numbered([("Conditional generation", "convert a structured story idea and plot dials into explicit conditions "
                        "for a pretrained LLM."),
                       ("Prompt engineering", "implement and compare Direct, Interview Pattern, Chain-of-Thought and "
                        "Tree-of-Thought prompting, with every prompt and intermediate step stored and viewable."),
                       ("Sampling control", "expose temperature, top-k and top-p and measure their effect."),
                       ("Multimodal generation", "combine the LLM with a text-to-image model to produce a consistent "
                        "four-panel storyboard."),
                       ("Evaluation", "score every story with explainable automatic metrics and human ratings, and report "
                        "a controlled experiment.")]),
            H2("1.4 Scope of the Project"),
            *B([f"<b>Models:</b> pretrained models used through APIs (Gemini for text, {IMG_SHORT} for images); "
                "training or fine-tuning models is out of scope (Section 4.3).",
                "<b>Execution:</b> a full-stack web application (React, FastAPI, PostgreSQL) that runs locally on a laptop.",
                "<b>Measurement:</b> reference-free automatic metrics plus human ratings; a controlled experiment over three "
                "story ideas of different genres.",
                "<b>Curriculum alignment:</b> each UCS748 topic maps to a visible feature of the application (Table 1)."]),
            table(syllabus, [3.3, 4.4, 8.3], "Mapping of the UCS748 syllabus to StoryForge")]


def chapter_method():
    gan = [["Aspect", "GANs [11]", "Diffusion / modern text-to-image [12, 13]"],
           ["Training", "Generator vs discriminator (adversarial game); can be unstable, mode collapse",
            "Learns to denoise; stable likelihood-style objective"],
           ["Text conditioning", "Possible (conditional GANs) but limited for open-ended prompts",
            "Natural: denoiser is conditioned on text embeddings (e.g. CLIP/T5)"],
           ["Sampling speed", "One forward pass: very fast", "Many denoising steps: slower (reduced by latent space, fewer steps)"],
           ["Diversity", "Lower (mode collapse risk)", "High, controllable with guidance and seeds"],
           ["Use in StoryForge", "Not used: free-text scene prompts need strong text conditioning",
            f"Used via API ({IMG_SHORT})"]]
    metrics = [["Metric", "Definition", "What it indicates"],
               ["Distinct-1 / Distinct-2", "unique unigrams (bigrams) ÷ total unigrams (bigrams) [10]", "Lexical diversity; repetition lowers it"],
               ["Brief coverage", "content words of the brief found in the story ÷ content words in the brief",
                "Prompt adherence (lexical proxy; paraphrases are not counted)"],
               ["Character presence", "average share of chapters mentioning each named character", "Character consistency (proxy)"],
               ["Length ratio", "words written ÷ words requested", "Whether the length condition was followed (1.0 = exact)"],
               ["Structure score", "share of checks passed: 6 beats, 4 scenes, requested chapter count", "Schema adherence of the structured output"],
               ["Human rating", "1–5 for coherence, creativity, adherence and character consistency", "Qualitative judgement"]]
    stack = [["Layer", "Technology", "Role"],
             ["Front end", "React 19, Vite, Tailwind CSS, React Router", "Create, Library, Explore and Settings pages; story workspace"],
             ["Back end", "Python 3.12, FastAPI, Pydantic", "REST API, validation, generation pipeline, background image jobs"],
             ["Database", "PostgreSQL, SQLAlchemy 2", "Stories, every LLM call, scenes, settings"],
             ["Text model", "Google Gemini (gemini-3.5-flash-lite) via google-genai [17]", "Story generation with temperature, top-k and top-p"],
             ["Image model", IMG_LONG, "Storyboard panels and interface artwork"],
             ["Testing", "pytest (10 API and provider tests)", "Strategies, validation, library, settings, image providers"]]
    responsive = SHOTS / "responsive.png"
    return [H1("2. METHODOLOGY"),
            H2("2.1 Generative AI Concepts Used"),
            P("<b>Transformer language model.</b> A Transformer LLM converts text into tokens, embeds them, and passes them "
              "through stacked self-attention and feed-forward layers. Self-attention computes, for each token, a weighted mix "
              "of all other tokens: Attention(Q, K, V) = softmax(QK<super>T</super> / √d<sub>k</sub>) V [1]. The model is "
              "pre-trained to predict the next token, P(w<sub>1</sub>…w<sub>T</sub>) = Π P(w<sub>t</sub> | w<sub>1</sub>…"
              "w<sub>t−1</sub>), and is later instruction-tuned. StoryForge uses such a model through the Gemini API and does "
              "not modify its weights."),
            P("<b>Conditional generation.</b> The application models p(story | conditions). The conditions are written into a "
              "<i>story brief</i>: protagonist, objective, genre, world rule (which must matter to the plot), ending twist "
              "(revealed near the climax and foreshadowed earlier), tone, conflict, romance, action intensity and length. The "
              "0–100 dials are mapped to words (for example tone 30 becomes “dark and grim”, length 60 becomes four chapters of "
              "about 330 words). These dials change the prompt, not the decoder."),
            P("<b>Sampling.</b> At each step the model produces logits z<sub>i</sub>. With temperature T the sampling "
              "probability is p<sub>i</sub> = exp(z<sub>i</sub>/T) / Σ<sub>j</sub> exp(z<sub>j</sub>/T). T below 1 sharpens the "
              "distribution (safer, more repetitive text); T above 1 flattens it. Top-k keeps only the k most likely tokens; "
              "top-p keeps the smallest set whose probabilities sum to p [5]. StoryForge sends all three with every request "
              "and stores them with every story."),
            P("<b>Image generation.</b> StoryForge needs images from free-text scene descriptions, so strong text "
              "conditioning matters more than single-pass speed. Table 2 compares GANs with the diffusion-based approach "
              "behind modern text-to-image models."),
            table(gan, [3.2, 6.0, 6.8], "GANs compared with diffusion-based text-to-image generation"),
            H2("2.2 Proposed System and Architecture"),
            P("StoryForge is a three-tier web application (Figure 1). The React front end collects the idea and settings; the "
              "FastAPI back end builds the prompt, calls the language model, validates the JSON output, computes metrics, "
              "stores everything in PostgreSQL and schedules image generation in the background."),
            figure(ASSETS / "architecture.png", "System architecture of StoryForge"),
            H2("2.3 Generation Workflow"),
            *numbered([("Input", "the user fills the idea form and plot dials, and chooses a strategy and sampling values."),
                       ("Prompting", "the back end builds the structured brief and runs the selected strategy, making one or "
                        "two LLM calls; each call is stored with its prompt, parameters, raw output and latency."),
                       ("Validation", "the model returns JSON (title, logline, characters, relationships, six beats, chapters, "
                        "four scenes); a missing field produces a clear error instead of a broken story."),
                       ("Evaluation", "the automatic metrics are computed and saved with the story."),
                       ("Illustration", "a background worker renders the four storyboard panels one by one, saves them and "
                        "updates their status; the interface refreshes automatically.")]),
            H2("2.4 Prompt Engineering Strategies"),
            P("Four strategies are implemented (Figure 2). <b>Direct</b> sends one prompt with all conditions and is the "
              "baseline. <b>Interview Pattern</b> first makes the model ask and answer five editor questions (motivation, "
              "stakes, the world rule, the rival and foreshadowing), then writes from that Q&amp;A. <b>Chain-of-Thought</b> "
              "requires a visible plan of the world, characters and arc before the story. <b>Tree-of-Thought</b> generates "
              "three plot branches, scores each for originality, coherence and fit, and expands the best one. Hidden model "
              "reasoning is never requested; only explicit, inspectable intermediate outputs are used."),
            figure(ASSETS / "strategies.png", "The four prompt-engineering strategies (dark box = final writing call)"),
            H2("2.5 Multimodal Image Pipeline"),
            P("The LLM returns four scene descriptions and a visual description of every character. For each panel the image "
              "prompt is: scene description + the full character sheet + a shared style instruction. The image model has no "
              "memory between panels, so repeating the same character sheet in every prompt is what keeps characters "
              "visually consistent."),
            H2("2.6 Evaluation Metrics"),
            P("Creative stories have no single correct answer, so StoryForge uses reference-free metrics that are simple to "
              "explain and verify (Table 3), with human ratings stored separately. Runs of the same idea and plot dials share "
              "an <i>idea key</i>, so runs that differ only in strategy or temperature can be compared directly."),
            table(metrics, [3.3, 6.7, 6.0], "Evaluation metrics"),
            KeepTogether([H2("2.7 Implementation"), table(stack, [2.6, 6.4, 7.0], "Technology stack")]),
            P("The interface has four pages. <b>Create</b> holds the idea form and creative workspace (Figure 3). Each story "
              "opens in a workspace with four tabs: <b>Story</b> (storyboard, beats and chapters, Figure 4), <b>Scenes</b>, "
              "<b>Prompt Lab</b> (exact prompts and intermediate steps) and <b>Evaluation</b> (metrics, human rating and run "
              "comparison). <b>Library</b> stores all stories (Figure 5); <b>Explore</b> and <b>Settings</b> hold starter "
              "ideas and generation defaults. The layout is responsive on desktop, tablet and phone"
              + (" (Figure 6)." if (SHOTS / "responsive.png").exists() else ".")),
            figure(screen("create", "create.jpg"), "Create page: idea form and creative workspace", 14),
            figure(screen("story", "storyboard.jpg"), "Story tab of a live generation: storyboard and episode beats", 14),
            figure(screen("library", "library.jpg"), "Library of generated stories", 14)] + (
            [figure(responsive, "The same interface on desktop, tablet and phone", 15)] if responsive.exists() else [])


def fmt(v, pct=False, digits=3):
    if v is None:
        return "–"
    return f"{v * 100:.0f}%" if pct else f"{v:.{digits}f}"


def chapter_results(summary):
    bs, bt = summary["by_strategy"], summary["by_temperature"]
    strat_rows = [["Strategy", "Distinct-2", "Brief coverage", "Character presence", "Length ratio", "Structure", "LLM calls", "Time (s)"]]
    for k, v in bs.items():
        strat_rows.append([NAMES[k], fmt(v["distinct_2"]), fmt(v["brief_coverage"], True), fmt(v["character_presence"], True),
                           fmt(v["length_ratio"], digits=2), fmt(v["structure_score"], True), fmt(v["llm_calls"], digits=0),
                           fmt((v["latency_ms"] or 0) / 1000, digits=1)])
    temp_rows = [["Temperature", "Distinct-1", "Distinct-2", "Brief coverage", "Character presence", "Length ratio"]]
    for t, v in sorted(bt.items(), key=lambda x: float(x[0])):
        temp_rows.append([t, fmt(v["distinct_1"]), fmt(v["distinct_2"]), fmt(v["brief_coverage"], True),
                          fmt(v["character_presence"], True), fmt(v["length_ratio"], digits=2)])
    charts = DATA / "experiments" / "charts"
    flow = [H1("3. RESULTS"),
            H2("3.1 Experimental Setup"),
            P(f"{summary['design']} The experiment covered {len(summary['ideas'])} story ideas of different genres "
              f"({', '.join(summary['ideas'])}), giving {summary['runs']} generations and {summary['llm_calls']} model calls "
              f"with {summary['model']}. Plot dials were fixed per idea, so only the strategy or the temperature changed "
              "between compared runs. Every run is listed in Appendix B."),
            Paragraph("The experiment is reproduced with <font face='Courier'>backend/scripts/experiments.py</font>.",
                      ParagraphStyle("left", parent=S["body"], alignment=TA_LEFT))]
    if summary["demo"]:
        flow.append(P("<b>Note:</b> this preview was built from demo-mode template text. The numbers below only show that the "
                      "pipeline works and must be regenerated in live mode before submission."))
    flow += [H2("3.2 Comparison of Prompting Strategies"),
             table(strat_rows, [3.0, 1.8, 1.9, 2.0, 1.6, 2.0, 1.6, 1.6], "Average metrics by strategy at temperature 0.9"),
             figure(charts / "strategy_metrics.png", "Automatic metrics by prompting strategy", 14.5),
             figure(charts / "strategy_latency.png", "Average generation time and number of model calls by strategy", 10.5),
             KeepTogether([H2("3.3 Effect of Temperature"),
                           table(temp_rows, [2.8, 2.3, 2.3, 2.6, 3.1, 2.5], "Direct prompting at three temperatures")]),
             figure(charts / "temperature_effect.png", "Diversity and brief coverage as temperature increases", 10.5),
             H2("3.4 Key Findings")]
    flow += B(summary["findings"])
    if summary["human_rated"]:
        hum = [["Strategy", "Human average (1–5)", "Rated runs"]]
        for k, v in bs.items():
            hum.append([NAMES[k], fmt(v.get("human_avg"), digits=1), str(sum(1 for r in summary["rows"]
                        if r["strategy"] == k and r["temperature"] == 0.9 and r["human_avg"] is not None))])
        flow += [H2("3.5 Human Evaluation"),
                 P(f"{summary['human_rated']} stories were rated by the team on coherence, creativity, adherence to the brief "
                   "and character consistency (1 to 5) in the Evaluation tab."),
                 table(hum, [5, 5, 4], "Average human rating by strategy (temperature 0.9)")]
    return flow


def analysis(summary):
    """Discussion points written from the numbers, so they stay true if the experiment is re-run."""
    bs, bt = summary["by_strategy"], summary["by_temperature"]
    get = lambda k, m: (bs.get(k) or {}).get(m)  # noqa: E731
    pts = []
    cov = {k: v["brief_coverage"] for k, v in bs.items() if v.get("brief_coverage") is not None}
    if "direct" in cov and len(cov) > 1:
        best = max(cov, key=cov.get)
        others = ", ".join(f"{NAMES[k]} {cov[k] * 100:.0f}%" for k in cov if k not in ("direct", best))
        if best != "direct":
            pts.append(("Asking before writing helps adherence",
                        f"{NAMES[best]} reached {cov[best] * 100:.0f}% brief coverage against {cov['direct'] * 100:.0f}% for "
                        f"direct prompting ({others}). Its first call makes the model state the motivation, stakes, world "
                        "rule and foreshadowing explicitly, and the writing call then works from those answers, so more of "
                        "the brief's own terms likely reach the story. The gain comes at the cost of a second model call."))
        else:
            pts.append(("Direct prompting already follows the brief",
                        f"Direct prompting gave the highest brief coverage ({cov['direct'] * 100:.0f}%; {others})."))
    lr = {k: v["length_ratio"] for k, v in bs.items() if v.get("length_ratio") is not None}
    if lr and max(lr.values()) < 0.95 and min(lr, key=lr.get) == "direct":
        lo, hi = min(lr, key=lr.get), max(lr, key=lr.get)
        pts.append(("The model under-writes, planning reduces it",
                    f"No strategy reached the requested length (length ratio {lr[lo]:.2f} for {NAMES[lo]} to {lr[hi]:.2f} "
                    f"for {NAMES[hi]}). Instruction-tuned models tend to be concise even when a word count is given; "
                    "strategies that first produce a plan or Q&amp;A had more material to expand and wrote longer stories."))
    if len(bt) >= 2:
        ts = sorted(bt, key=float)
        d2 = [bt[t]["distinct_2"] for t in ts if bt[t].get("distinct_2") is not None]
        if d2 and max(d2) - min(d2) < 0.01:
            pts.append(("Temperature had a small effect on diversity",
                        f"Distinct-2 stayed between {min(d2):.3f} and {max(d2):.3f} from T={ts[0]} to T={ts[-1]}. With "
                        "top-p 0.95 and top-k 40 held fixed, the candidate pool is already truncated before sampling, so "
                        "temperature mostly reorders probabilities inside that pool; a story-length text is also varied at "
                        "the bigram level regardless. A difference this small is within run-to-run noise for one run per "
                        "setting, so a larger sweep (or more extreme values) would be needed to measure the effect."))
        elif d2:
            pts.append(("Temperature changed diversity",
                        f"Distinct-2 moved from {d2[0]:.3f} at T={ts[0]} to {d2[-1]:.3f} at T={ts[-1]}, consistent with "
                        "temperature flattening the next-token distribution."))
    s = [v["structure_score"] for v in bs.values() if v.get("structure_score") is not None]
    if s and min(s) == 1.0:
        pts.append(("Structured output was fully reliable",
                    f"All {summary['runs']} generations returned valid JSON with six beats, four scenes and the requested "
                    "number of chapters. Requesting JSON output and validating required keys on the server made the "
                    "multimodal pipeline dependable: every story had four scene prompts ready for the image model."))
    lat = {k: v.get("latency_ms") for k, v in bs.items() if v.get("latency_ms")}
    if "direct" in lat and "tot" in lat:
        pts.append(("Reasoning strategies cost time",
                    f"Tree-of-Thought took {lat['tot'] / lat['direct']:.1f}x as long as direct prompting "
                    f"({lat['tot'] / 1000:.1f} s vs {lat['direct'] / 1000:.1f} s) because it makes two calls and the first "
                    "produces three full plot branches. Its benefit is a visible choice between alternatives in the Prompt "
                    "Lab rather than a large change in the automatic scores."))
    return numbered(pts)


def chapter_discussion(summary):
    return [H1("4. DISCUSSION"),
            H2("4.1 Analysis of Results"),
            *analysis(summary),
            P("All differences come from one run per setting over three ideas, so they indicate tendencies rather than "
              "statistically significant effects (Section 4.3)."),
            H2("4.2 Challenges Faced"),
            *numbered([("Model availability", "during the experiment Gemini repeatedly returned 503 “high demand” errors. "
                        "The experiment script retries with back-off and is resumable: finished runs are detected by their "
                        "idea key and skipped, so failed runs can be re-tried later without repeating work. Earlier, the "
                        "first model chosen was retired for new API keys (404), so the model name was made configurable."),
                       ("Reliable structured output", "a story is only useful to the image pipeline if it has every field. "
                        "JSON output mode plus server-side validation of required keys turned malformed responses into clear "
                        "errors instead of broken stories."),
                       ("Image rate limits and cost", "the free image service allows roughly one image every 46 seconds and "
                        "the paid service charges per image. Images are therefore rendered by a background worker, paced per "
                        "provider and retried up to three times, while the story is shown immediately."),
                       ("Character consistency across panels", "the image model has no memory between calls; repeating one "
                        "character sheet in every panel prompt reduced drift between panels."),
                       ("Responsive interface", "multi-column grids overflowed on phones; layouts were rebuilt to collapse "
                        "to a single column and were tested on desktop, tablet and phone sizes.")]),
            H2("4.3 Limitations"),
            *B(["The language and image models are pretrained and accessed through APIs; no model was trained or fine-tuned.",
                "The automatic metrics are lexical proxies. They cannot judge plot quality, and brief coverage misses paraphrases.",
                "The experiment is small (three ideas, one run per setting); sampling is random, so single-run differences are noisy.",
                "Characters can still drift between panels despite the shared character sheet.",
                "Free API tiers impose rate limits and the paid image tier has a per-image cost."]),
            H2("4.4 Future Improvements"),
            *numbered([("Fine-tuning", "fine-tune a small open model (for example with LoRA on a story dataset) and compare "
                        "it with the API model."),
                       ("Semantic metrics", "embedding similarity between brief and story, and CLIPScore [16] for image-text "
                        "alignment."),
                       ("Larger experiment", "repeat each setting several times with fixed seeds and report means with "
                        "confidence intervals."),
                       ("Consistency and audio", "reference-image conditioning for characters, and text-to-speech narration "
                        "to extend the multimodal pipeline.")])]


def chapter_conclusion(summary):
    url = INFO["github_url"]
    return [H1("5. CONCLUSION"),
            P("StoryForge shows the core ideas of the UCS748 course working together in one system. Structured user inputs "
              "become explicit conditions for a pretrained Transformer LLM; four prompt-engineering strategies change how the "
              "story is planned; sampling parameters control how the next token is chosen; and a second generative model "
              "turns LLM-written scene descriptions into a consistent storyboard. Because every prompt, parameter and output "
              "is stored, the effect of each choice can be inspected and measured rather than guessed."),
            P(f"The controlled experiment of {summary['runs']} generations showed that strategies with an explicit "
              "intermediate step make the model's planning visible and, for the Interview Pattern, improved adherence to the "
              "brief, at the cost of extra calls and time, while the structured output stayed fully reliable across all runs. "
              "The project gives a working, explainable blueprint for studying conditional, controllable and multimodal "
              "generation with pretrained models."),
            Spacer(1, 0.2 * cm),
            P(f"<b>Link to the code:</b> <link href='{url}' color='blue'>{url}</link>")]


def references():
    refs = [
        "A. Vaswani et al., “Attention Is All You Need,” in Advances in Neural Information Processing Systems (NeurIPS), 2017.",
        "J. Devlin, M.-W. Chang, K. Lee and K. Toutanova, “BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding,” in Proc. NAACL-HLT, 2019.",
        "A. Radford, J. Wu, R. Child, D. Luan, D. Amodei and I. Sutskever, “Language Models are Unsupervised Multitask Learners,” OpenAI, 2019.",
        "T. Brown et al., “Language Models are Few-Shot Learners,” in Advances in Neural Information Processing Systems (NeurIPS), 2020.",
        "A. Holtzman, J. Buys, L. Du, M. Forbes and Y. Choi, “The Curious Case of Neural Text Degeneration,” in Proc. ICLR, 2020.",
        "A. Fan, M. Lewis and Y. Dauphin, “Hierarchical Neural Story Generation,” in Proc. ACL, 2018.",
        "J. Wei et al., “Chain-of-Thought Prompting Elicits Reasoning in Large Language Models,” in Advances in Neural Information Processing Systems (NeurIPS), 2022.",
        "S. Yao et al., “Tree of Thoughts: Deliberate Problem Solving with Large Language Models,” in Advances in Neural Information Processing Systems (NeurIPS), 2023.",
        "J. White et al., “A Prompt Pattern Catalog to Enhance Prompt Engineering with ChatGPT,” arXiv:2302.11382, 2023.",
        "J. Li, M. Galley, C. Brockett, J. Gao and B. Dolan, “A Diversity-Promoting Objective Function for Neural Conversation Models,” in Proc. NAACL-HLT, 2016.",
        "I. Goodfellow et al., “Generative Adversarial Nets,” in Advances in Neural Information Processing Systems (NeurIPS), 2014.",
        "J. Ho, A. Jain and P. Abbeel, “Denoising Diffusion Probabilistic Models,” in Advances in Neural Information Processing Systems (NeurIPS), 2020.",
        "R. Rombach, A. Blattmann, D. Lorenz, P. Esser and B. Ommer, “High-Resolution Image Synthesis with Latent Diffusion Models,” in Proc. CVPR, 2022.",
        "A. Ramesh, P. Dhariwal, A. Nichol, C. Chu and M. Chen, “Hierarchical Text-Conditional Image Generation with CLIP Latents,” arXiv:2204.06125, 2022.",
        "A. Radford et al., “Learning Transferable Visual Models From Natural Language Supervision,” in Proc. ICML, 2021.",
        "J. Hessel, A. Holtzman, M. Forbes, R. Le Bras and Y. Choi, “CLIPScore: A Reference-free Evaluation Metric for Image Captioning,” in Proc. EMNLP, 2021.",
        "Google, “Gemini API documentation,” ai.google.dev, accessed November 2026.",
        "L. Yao, N. Peng, R. Weischedel, K. Knight, D. Zhao and R. Yan, “Plan-and-Write: Towards Better Automatic Storytelling,” in Proc. AAAI, 2019.",
        "K. Papineni, S. Roukos, T. Ward and W.-J. Zhu, “BLEU: a Method for Automatic Evaluation of Machine Translation,” in Proc. ACL, 2002.",
        "C.-Y. Lin, “ROUGE: A Package for Automatic Evaluation of Summaries,” in Text Summarization Branches Out (ACL Workshop), 2004.",
        "Pollinations.ai, “API documentation,” pollinations.ai, accessed November 2026; OpenAI, “Image generation API documentation,” developers.openai.com, accessed November 2026.",
    ]
    return [H1("REFERENCES")] + [Paragraph(f"[{i}] {r}", S["ref"]) for i, r in enumerate(refs, 1)]


def appendix(summary):
    setup = [["Step", "Command / action"],
             ["1. Database", "In pgAdmin, run separately: CREATE USER storyforge WITH PASSWORD 'storyforge'; then CREATE DATABASE storyforge OWNER storyforge;"],
             ["2. Keys", "Copy backend/.env.example to backend/.env; add GEMINI_API_KEY (free at aistudio.google.com); choose IMAGE_PROVIDER."],
             ["3. Back end", "cd backend; python3.12 -m venv .venv; source .venv/bin/activate; pip install -r requirements.txt; uvicorn app.main:app --reload"],
             ["4. Front end", "cd frontend; npm install; npm run dev; open http://localhost:5173"],
             ["5. Tests", "cd backend; pytest (10 tests)"],
             ["6. Experiments", "cd backend; python scripts/experiments.py"]]
    files = [["Path", "Purpose"],
             ["backend/app/prompts/strategies.py", "Story brief and the prompts of the four strategies"],
             ["backend/app/providers/llm.py", "Gemini provider (sampling parameters, JSON output, retries) and offline demo provider"],
             ["backend/app/providers/images.py", "Image prompts; OpenAI and Pollinations providers"],
             ["backend/app/services/story_service.py", "Runs a strategy, validates the output, stores runs and scenes"],
             ["backend/app/services/image_worker.py", "Background rendering of storyboard panels with retries"],
             ["backend/app/services/evaluation.py", "Automatic metrics"],
             ["backend/app/routers/stories.py", "REST API (generate, library, rating, related runs, settings)"],
             ["backend/scripts/experiments.py", "Experiment plan runner; exports results, charts and samples"],
             ["frontend/src/", "React pages (Create, Library, Explore, Settings) and workspace tabs"],
             ["data/", "Experiment plan, results.csv, summary.json, charts and generated sample stories"],
             ["docs/", "Builders for this report and the slides, figures and screenshots"]]
    run_rows = [["Idea", "Strategy", "T", "Title generated", "D-2", "Cov.", "Chars", "Words"]]
    for r in summary["rows"]:
        run_rows.append([r["idea"], NAMES[r["strategy"]], r["temperature"], r["title"], fmt(r["distinct_2"], digits=2),
                         fmt(r["brief_coverage"], True), fmt(r["character_presence"], True), r["word_count"]])
    flow = [H1("APPENDIX"),
            H2("Appendix A: Repository Structure and Setup"),
            table(files, [6.2, 9.8], "Main files"),
            table(setup, [3.0, 13.0], "Setup steps (runs locally; API keys stay in backend/.env, which is not committed)"),
            KeepTogether([H2("Appendix B: All Experiment Runs"),
                          table(run_rows, [2.8, 3.0, 1.0, 4.0, 1.1, 1.2, 1.4, 1.5],
                                "Every experiment run (D-2 = Distinct-2, Cov. = brief coverage, Chars = character presence)")])]
    samples = sorted((DATA / "samples").glob("*__tot__t0.9.json"))
    if samples:
        s = json.loads(samples[0].read_text(encoding="utf-8"))
        prompt = s["prompts"][0]["prompt"]
        excerpt = (s["output"]["chapters"][0]["text"][:900] + "…") if s["output"].get("chapters") else ""
        esc = lambda t: t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")  # noqa: E731
        flow += [H2("Appendix C: Example Prompt and Output"),
                 P(f"First Tree-of-Thought prompt (branch generation) for “{s['idea']['protagonist']}”, exactly as sent to the model:"),
                 Table([[Paragraph(esc(prompt), S["code"])]], colWidths=[16 * cm],
                       style=[("BOX", (0, 0), (-1, -1), 0.5, colors.grey), ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F7F7"))]),
                 Spacer(1, 0.4 * cm),
                 P(f"Opening of Chapter 1 of the resulting story, “{s['title']}”:"),
                 Paragraph(f"<i>{esc(excerpt)}</i>", S["body"])]
    return flow


def main():
    if not SUMMARY_PATH.exists():
        raise SystemExit("No experiment results yet. Run: cd backend && python scripts/experiments.py")
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    out_dir = ROOT / "submission"
    out_dir.mkdir(exist_ok=True)
    path = out_dir / f"Report_{INFO['group_no']}.pdf"
    doc = ReportDoc(path, summary["demo"])
    story = (title_page() + abstract(summary) + chapter_intro() + chapter_method() + chapter_results(summary)
             + chapter_discussion(summary) + chapter_conclusion(summary) + references() + appendix(summary))
    FIG["n"] = TAB["n"] = 0
    doc.multiBuild(story)
    print(f"Saved {path}" + ("  (PREVIEW: demo data)" if summary["demo"] else ""))


if __name__ == "__main__":
    main()
