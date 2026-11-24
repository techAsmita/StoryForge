// Builds submission/PPT_XX.pptx (10 slides) from docs/project_info.json and data/experiments/summary.json.
//   cd docs && npm install && node build_ppt.mjs
// Layout follows the course sample: institute strip and logo on every slide, "Submitted by" title slide,
// problem and objectives, challenges, and speaker notes labelled with who presents each slide.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import pptxgen from "pptxgenjs";
import JSZip from "jszip";

const DOCS = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(DOCS, "..");
const INFO = JSON.parse(fs.readFileSync(path.join(DOCS, "project_info.json"), "utf8"));
const SUMMARY_PATH = path.join(ROOT, "data", "experiments", "summary.json");
if (!fs.existsSync(SUMMARY_PATH)) {
  console.error("No experiment results yet. Run: cd backend && python scripts/experiments.py");
  process.exit(1);
}
const SUM = JSON.parse(fs.readFileSync(SUMMARY_PATH, "utf8"));
// Image model named from backend/.env (only IMAGE_PROVIDER / OPENAI_IMAGE_MODEL are read, never keys).
const envVal = (name, def) => {
  const f = path.join(ROOT, "backend", ".env");
  if (!fs.existsSync(f)) return def;
  const line = fs.readFileSync(f, "utf8").split(/\r?\n/).find((l) => l.trim().startsWith(`${name}=`));
  return line ? (line.split("=").slice(1).join("=").split("#")[0].trim() || def) : def;
};
const IMG = envVal("IMAGE_PROVIDER", "pollinations") === "openai" ? `OpenAI ${envVal("OPENAI_IMAGE_MODEL", "gpt-image-2")}` : "Flux via Pollinations.ai";
const A = (...p) => path.join(DOCS, "assets", ...p);
const officialLogo = A("thapar_logo_official.png");
const hasOfficial = fs.existsSync(officialLogo);

// Palette: one dominant violet, light lavender surfaces, a single gold accent.
const C = { violet: "4C1D95", violet2: "7C3AED", lav: "F1ECFB", lav2: "E4DAF8", ink: "1F1B2E", muted: "6B6680", gold: "B7791F", white: "FFFFFF", line: "D9D2EA", red: "C41230" };
const HEAD = "Cambria", BODY = "Calibri";
const NAMES = { direct: "Direct", interview: "Interview Pattern", cot: "Chain-of-Thought", tot: "Tree-of-Thought" };
const [M1, M2, M3] = INFO.members.map((m) => m.name); // presenters; edit the speaker labels below if you split it differently
const SPEAKER = { intro: M3, middle: M1, results: M2 };

// Image size (PNG or JPEG) so screenshots keep their aspect ratio.
function imgSize(file) {
  const b = fs.readFileSync(file);
  if (b.readUInt32BE(0) === 0x89504e47) return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
  let i = 2;
  while (i < b.length) {
    const marker = b[i + 1], len = b.readUInt16BE(i + 2);
    if (marker >= 0xc0 && marker <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(marker)) return { w: b.readUInt16BE(i + 7), h: b.readUInt16BE(i + 5) };
    i += 2 + len;
  }
  throw new Error(`Unknown image size: ${file}`);
}
// Fresh captures from take_screenshots.py are preferred; older captures are the fallback.
const screen = (fresh, old) => {
  const f = path.join(DOCS, "screenshots", `desktop-${fresh}.png`);
  return fs.existsSync(f) ? f : A("screens", old);
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
pres.title = `${INFO.short_title} - ${INFO.course_code}`;
pres.author = INFO.members.map((m) => m.name).join(", ");
pres.theme = { headFontFace: HEAD, bodyFontFace: BODY };

const logoObjects = hasOfficial
  ? [{ image: { path: officialLogo, x: 11.15, y: 0.14, w: 1.6, h: 1.6 * imgSize(officialLogo).h / imgSize(officialLogo).w } }]
  : [{ image: { path: A("thapar_mark.png"), x: 12.3, y: 0.14, w: 0.42, h: 0.58 } }];
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.white },
  objects: [
    { text: { text: "THAPAR INSTITUTE OF ENGINEERING & TECHNOLOGY  •  DEPT OF CSE",
      options: { x: 0.6, y: 0.2, w: 9, h: 0.28, fontFace: BODY, fontSize: 10, bold: true, color: C.violet, charSpacing: 1, margin: 0 } } },
    { line: { x: 0.6, y: 1.32, w: 12.13, h: 0, line: { color: C.line, width: 1 } } },
    ...logoObjects,
    { text: { text: `${INFO.course_code} ${INFO.course_name} · Group ${INFO.group_no} · ${INFO.short_title}`,
      options: { x: 0.6, y: 7.0, w: 8, h: 0.3, fontFace: BODY, fontSize: 10, color: C.muted, margin: 0 } } },
  ],
  slideNumber: { x: 12.3, y: 7.0, w: 0.5, h: 0.3, fontFace: BODY, fontSize: 10, color: C.muted, align: "right" },
});
pres.defineSlideMaster({ title: "TITLE", background: { color: C.white }, objects: [] });

function slideWithTitle(title, speaker, notes) {
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText(title, { x: 0.6, y: 0.5, w: 10.4, h: 0.75, fontFace: HEAD, fontSize: 30, bold: true, color: C.ink, margin: 0, valign: "middle", isTextBox: true });
  s.addNotes(`[SPEAKER: ${speaker}]\n${notes}`);
  return s;
}
const card = (s, x, y, w, h, fill = C.lav) =>
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: fill }, line: { color: fill } });
const outline = (s, x, y, w, h) =>
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: C.white }, line: { color: C.line, width: 1 } });
const circleNum = (s, x, y, n, d = 0.5) => {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: C.violet }, line: { color: C.violet } });
  s.addText(String(n), { x, y, w: d, h: d, fontFace: BODY, fontSize: 16, bold: true, color: C.white, align: "center", valign: "middle", margin: 0, isTextBox: true });
};
const imgFit = (s, file, x, y, w, h) => s.addImage({ path: file, x, y, w, h, sizing: { type: "contain", w, h } });
// Screenshot in a lavender frame, width w; fits inside maxH if given. Returns the height used.
const shot = (s, file, x, y, w, maxH = 99) => {
  const { w: iw, h: ih } = imgSize(file);
  let h = w * ih / iw;
  if (h > maxH) { w = maxH * iw / ih; h = maxH; }
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x - 0.06, y: y - 0.06, w: w + 0.12, h: h + 0.12, rectRadius: 0.1, fill: { color: C.lav2 }, line: { color: C.lav2 } });
  s.addImage({ path: file, x, y, w, h });
  return h;
};
const bullets = (items) => items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1 } }));
const fmt = (v, pct = false, d = 2) => (v === null || v === undefined ? "–" : pct ? `${Math.round(v * 100)}%` : v.toFixed(d));
const preview = (s) => SUM.demo && s.addText("PREVIEW · demo data · rebuild after running experiments in live mode",
  { x: 0.6, y: 6.6, w: 12.1, h: 0.3, fontFace: BODY, fontSize: 11, bold: true, color: "C0392B", margin: 0, isTextBox: true });

// 1 · Title -------------------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: "TITLE" });
  if (hasOfficial) {
    const { w, h } = imgSize(officialLogo);
    imgFit(s, officialLogo, 5.67, 0.35, 2.0, 2.0 * h / w);
  } else {
    s.addImage({ path: A("thapar_mark.png"), x: 6.33, y: 0.35, w: 0.68, h: 0.94 });
    s.addText([{ text: "THAPAR INSTITUTE", options: { bold: true, color: C.red, fontSize: 16, breakLine: true } },
      { text: "OF ENGINEERING & TECHNOLOGY  ·  (Deemed to be University)", options: { color: C.muted, fontSize: 10 } }],
      { x: 3.67, y: 1.35, w: 6, h: 0.6, fontFace: HEAD, align: "center", margin: 0, isTextBox: true });
  }
  s.addText("StoryForge: A Multimodal Story Generation Studio", { x: 0.8, y: 2.3, w: 11.73, h: 0.85, fontFace: HEAD, fontSize: 36, bold: true, color: C.ink, align: "center", margin: 0, isTextBox: true });
  s.addText(INFO.subtitle, { x: 0.8, y: 3.15, w: 11.73, h: 0.45, fontFace: BODY, fontSize: 17, color: C.violet, align: "center", margin: 0, isTextBox: true });
  s.addText(`${INFO.course_code} ${INFO.course_name}  ·  Project Presentation`, { x: 0.8, y: 3.6, w: 11.73, h: 0.35, fontFace: BODY, fontSize: 13, italic: true, color: C.muted, align: "center", margin: 0, isTextBox: true });
  s.addText("SUBMITTED BY", { x: 0.8, y: 4.3, w: 11.73, h: 0.3, fontFace: BODY, fontSize: 11, bold: true, color: C.muted, charSpacing: 2, align: "center", margin: 0, isTextBox: true });
  s.addText(`Group No. ${INFO.group_no}  ·  ${INFO.batch}`, { x: 0.8, y: 4.6, w: 11.73, h: 0.35, fontFace: BODY, fontSize: 15, bold: true, color: C.ink, align: "center", margin: 0, isTextBox: true });
  s.addText(INFO.members.map((m) => `${m.name} (${m.roll})`).join("    •    "), { x: 0.8, y: 4.95, w: 11.73, h: 0.4, fontFace: BODY, fontSize: 15, color: C.ink, align: "center", margin: 0, isTextBox: true });
  s.addText([{ text: "Under the guidance of  ", options: { color: C.muted } }, { text: INFO.supervisor, options: { bold: true, color: C.ink } }],
    { x: 0.8, y: 5.55, w: 11.73, h: 0.35, fontFace: BODY, fontSize: 15, align: "center", margin: 0, isTextBox: true });
  s.addText([{ text: INFO.department, options: { bold: true, breakLine: true } }, { text: "Thapar Institute of Engineering and Technology (Deemed to be University), Patiala" }],
    { x: 0.8, y: 6.2, w: 11.73, h: 0.6, fontFace: BODY, fontSize: 12, color: C.violet, align: "center", margin: 0, isTextBox: true });
  s.addNotes(`[SPEAKER: ${SPEAKER.intro}]\nGood morning, sir. We are Group ${INFO.group_no}: ${INFO.members.map((m) => m.name).join(", ")}. Our project is StoryForge, a multimodal story generation studio. It turns a short story idea into a structured, illustrated story, and it lets us study how conditioning, prompting and sampling change what a generative model produces. I will cover the problem and how the project maps to the syllabus, ${SPEAKER.middle} will explain the system and the prompting strategies, and ${SPEAKER.results} will cover images, the application and our results.`);
}

// 2 · Problem & objectives ------------------------------------------------------------------------
{
  const s = slideWithTitle("Problem statement and objectives", SPEAKER.intro,
    "Most story generators are a black box: you type an idea and get text, with no view of the prompt, the settings or any measure of quality, and images are drawn separately so characters change between pictures. We set five objectives that map directly to the course: conditional generation, prompt engineering, sampling control, multimodal generation and evaluation.");
  card(s, 0.6, 1.6, 5.95, 5.0);
  s.addText("The problem", { x: 0.95, y: 1.8, w: 5.3, h: 0.45, fontFace: HEAD, fontSize: 20, bold: true, color: C.red, margin: 0, isTextBox: true });
  s.addText([
    { text: "Hidden process: ", options: { bold: true } }, { text: "you see the story, never the prompt, the settings or the reasoning", options: { breakLine: true } },
    { text: "No comparison: ", options: { bold: true } }, { text: "Chain-of-Thought or Tree-of-Thought are rarely compared on the same idea", options: { breakLine: true } },
    { text: "No measurement: ", options: { bold: true } }, { text: "quality is judged by impression; nothing is stored to compare", options: { breakLine: true } },
    { text: "Disconnected images: ", options: { bold: true } }, { text: "pictures are made separately, so characters change look" },
  ].map((r, i) => (i % 2 === 0 ? { ...r, options: { ...r.options, bullet: true } } : r)),
  { x: 0.95, y: 2.4, w: 5.3, h: 4.0, fontFace: BODY, fontSize: 15, color: C.ink, margin: 0, paraSpaceAfter: 10, valign: "top", isTextBox: true });
  outline(s, 6.78, 1.6, 5.95, 5.0);
  s.addText("Our objectives", { x: 7.13, y: 1.8, w: 5.3, h: 0.45, fontFace: HEAD, fontSize: 20, bold: true, color: C.violet, margin: 0, isTextBox: true });
  const obj = [["Conditional generation", "idea and plot dials become explicit prompt conditions"],
    ["Prompt engineering", "compare Direct, Interview, Chain-of-Thought, Tree-of-Thought"],
    ["Sampling control", "temperature, top-k and top-p, measured"],
    ["Multimodal", "LLM scene prompts drive a text-to-image model"],
    ["Evaluation", "explainable metrics, human ratings, an experiment"]];
  obj.forEach(([h, t], i) => {
    const y = 2.45 + i * 0.82;
    circleNum(s, 7.13, y + 0.05, i + 1, 0.45);
    s.addText([{ text: h, options: { bold: true, breakLine: true } }, { text: t, options: { color: C.muted, fontSize: 13 } }],
      { x: 7.78, y, w: 4.75, h: 0.72, fontFace: BODY, fontSize: 15, color: C.ink, margin: 0, valign: "top", isTextBox: true });
  });
}

// 3 · Syllabus ----------------------------------------------------------------------------------
{
  const s = slideWithTitle("Built around the UCS748 syllabus", SPEAKER.intro,
    "Each syllabus topic is a feature you can see in the application. Stories are written by a pretrained Transformer LLM; the user's inputs become conditions; we control and compare sampling; four prompting strategies including the Interview Pattern, Chain-of-Thought and Tree-of-Thought; a text-to-image model for the storyboard; and evaluation metrics. I'll now hand over to " + SPEAKER.middle + " for the system design.");
  const rows = [
    ["Large language models", "Stories are written by Gemini, a pretrained Transformer LLM"],
    ["Conditional text generation", "Idea fields and plot dials become explicit conditions in the prompt"],
    ["Sampling strategies", "Temperature, Top-K and Top-P are controlled and compared"],
    ["Prompt engineering", "Direct, Interview Pattern, Chain-of-Thought, Tree-of-Thought"],
    ["Image & multimodal generation", "LLM-written scene prompts drive a text-to-image model"],
    ["Evaluation metrics", "Diversity, brief coverage, consistency, structure + human ratings"],
  ];
  const head = (t) => ({ text: t, options: { bold: true, color: C.white, fill: { color: C.violet }, fontSize: 15 } });
  s.addTable([[head("Syllabus topic"), head("Where it appears in StoryForge")],
    ...rows.map(([a, b], i) => [{ text: a, options: { bold: true, fill: { color: i % 2 ? C.white : C.lav } } }, { text: b, options: { fill: { color: i % 2 ? C.white : C.lav } } }])],
  { x: 0.6, y: 1.65, w: 12.13, colW: [3.9, 8.23], fontFace: BODY, fontSize: 15, color: C.ink, border: { type: "solid", pt: 0.75, color: C.line }, rowH: 0.64, valign: "middle", margin: [0.06, 0.15, 0.06, 0.15] });
}

// 4 · Architecture ------------------------------------------------------------------------------
{
  const s = slideWithTitle("How it works", SPEAKER.middle,
    "Thank you. This is the architecture. The React interface sends the idea and settings to our FastAPI backend. The prompt builder turns them into a structured brief and runs the chosen strategy against Gemini. The model returns the story as JSON, which we validate, score and save in PostgreSQL, including every prompt and model call. A background worker then sends the four scene descriptions to the image model and saves the panels. The gold boxes are the external pretrained models; everything else is our code.");
  imgFit(s, A("architecture.png"), 1.1, 1.5, 11.1, 5.3);
}

// 5 · Controlling generation --------------------------------------------------------------------
{
  const s = slideWithTitle("Steering the model: conditions and sampling", SPEAKER.middle,
    "There are two separate controls. Conditions change what we ask: the protagonist, goal, world rule, twist and the dials are written into the prompt, and the 0 to 100 dials are turned into words. Sampling changes how the model picks each next token. Temperature divides the logits before the softmax: low is safe and repetitive, high is more varied. Top-K keeps only the 40 most likely tokens, and Top-P keeps the smallest set covering 95 percent of the probability.");
  card(s, 0.6, 1.6, 5.4, 5.0);
  s.addText("Conditional generation", { x: 0.9, y: 1.8, w: 4.9, h: 0.45, fontFace: HEAD, fontSize: 20, bold: true, color: C.violet, margin: 0, isTextBox: true });
  s.addText([
    { text: "Inputs become a written story brief:", options: { breakLine: true } },
    { text: "Protagonist, goal and genre", options: { bullet: true, breakLine: true } },
    { text: "World rule that must matter to the plot", options: { bullet: true, breakLine: true } },
    { text: "Ending twist, set up before the climax", options: { bullet: true, breakLine: true } },
    { text: "Dials 0–100 turned into words: tone 30 → “dark and grim”, length 60 → 4 chapters × ~330 words", options: { bullet: true } },
  ], { x: 0.9, y: 2.35, w: 4.9, h: 3.9, fontFace: BODY, fontSize: 15, color: C.ink, margin: 0, paraSpaceAfter: 6, valign: "top", isTextBox: true });
  const items = [["Temperature", "0.3 · 0.9 · 1.5", "p = softmax(z / T). Low = safe, high = varied."],
    ["Top-K", "40", "Only the 40 most likely next tokens can be chosen."],
    ["Top-P", "0.95", "Smallest set of tokens covering 95% of probability."]];
  items.forEach(([h, v, t], i) => {
    const y = 1.6 + i * 1.7;
    outline(s, 6.4, y, 6.33, 1.5);
    s.addText(v, { x: 6.6, y: y + 0.2, w: 2.3, h: 1.1, fontFace: HEAD, fontSize: 28, bold: true, color: C.violet, valign: "middle", margin: 0, isTextBox: true });
    s.addText([{ text: h, options: { bold: true, fontSize: 17, color: C.ink, breakLine: true } }, { text: t, options: { fontSize: 13, color: C.muted } }],
      { x: 9.0, y: y + 0.15, w: 3.55, h: 1.2, fontFace: BODY, valign: "middle", margin: 0, isTextBox: true });
  });
}

// 6 · Prompting strategies ----------------------------------------------------------------------
{
  const s = slideWithTitle("Four prompt-engineering strategies", SPEAKER.middle,
    "Same idea, four ways of asking. Direct is the baseline: one prompt with every condition. The Interview Pattern first makes the model ask and answer five editor questions, then write from that Q and A. Chain-of-Thought makes the model write a visible plan before the story. Tree-of-Thought generates three plot branches, scores them and expands the best. We only use visible intermediate outputs, which are all shown in the Prompt Lab tab. Over to " + SPEAKER.results + ".");
  const st = [["Direct", "1 call", "One prompt with every condition. The baseline."],
    ["Interview Pattern", "2 calls", "The model asks and answers 5 editor questions, then writes from the answers."],
    ["Chain-of-Thought", "1 call", "The model must write a visible plan (world, characters, arc) before the story."],
    ["Tree-of-Thought", "2 calls", "3 plot branches are scored for originality, coherence and fit; the best is written."]];
  st.forEach(([h, calls, t], i) => {
    const x = 0.6 + (i % 2) * 6.18, y = 1.6 + Math.floor(i / 2) * 2.55;
    card(s, x, y, 5.95, 2.3);
    circleNum(s, x + 0.3, y + 0.3, i + 1, 0.55);
    s.addText(h, { x: x + 1.05, y: y + 0.28, w: 3.4, h: 0.6, fontFace: HEAD, fontSize: 20, bold: true, color: C.ink, valign: "middle", margin: 0, isTextBox: true });
    s.addText(calls, { x: x + 4.45, y: y + 0.33, w: 1.25, h: 0.5, fontFace: BODY, fontSize: 13, bold: true, color: C.gold, align: "right", valign: "middle", margin: 0, isTextBox: true });
    s.addText(t, { x: x + 0.35, y: y + 1.05, w: 5.3, h: 1.05, fontFace: BODY, fontSize: 15, color: C.ink, valign: "top", margin: 0, isTextBox: true });
  });
}

// 7 · Multimodal ---------------------------------------------------------------------------------
{
  const s = slideWithTitle("From words to pictures", SPEAKER.results,
    `Thank you. The language model and the image model work as a team. Gemini writes four key scenes and a visual description of every character. Each scene becomes an image prompt for ${IMG}. The image model has no memory between pictures, so we add the same character sheet to every prompt to keep characters consistent. We use a diffusion-family model rather than a GAN because diffusion models follow free-text prompts much better.`);
  shot(s, screen("story", "story_hero.jpg"), 0.66, 1.66, 6.3, 4.9);
  const pts = [["The LLM writes the scene prompts", "4 key moments + a visual description of every character."],
    ["The image model draws them", `${IMG} (diffusion family), called from the backend.`],
    ["Consistency trick", "The same character sheet is added to every panel's prompt."],
    ["Why diffusion, not GANs", "Diffusion models follow free-text prompts well; GANs are harder to condition on text."]];
  pts.forEach(([h, t], i) => {
    const y = 1.65 + i * 1.22;
    circleNum(s, 7.45, y + 0.1, i + 1, 0.45);
    s.addText([{ text: h, options: { bold: true, fontSize: 16, color: C.ink, breakLine: true } }, { text: t, options: { fontSize: 13.5, color: C.muted } }],
      { x: 8.1, y, w: 4.63, h: 1.1, fontFace: BODY, valign: "top", margin: 0, isTextBox: true });
  });
}

// 8 · The application ----------------------------------------------------------------------------
{
  const s = slideWithTitle("The application", SPEAKER.results,
    "The application has four pages. Create is where stories are made. Library keeps every story with its prompts and scores. Explore gives starter ideas and explains the techniques, and Settings stores generation defaults. Every story opens with four tabs: Story, Scenes, Prompt Lab and Evaluation. The layout works on desktop, tablet and phone. (Switch to the live demo here if time allows.)");
  const h1 = shot(s, screen("library", "library.jpg"), 0.66, 1.66, 5.9, 3.7);
  shot(s, screen("explore", "explore_ideas.jpg"), 6.83, 1.66, 5.9, 3.7);
  const cy = 1.66 + h1 + 0.15;
  s.addText("Library: every story with its scenes, prompts and scores", { x: 0.6, y: cy, w: 5.95, h: 0.3, fontFace: BODY, fontSize: 11, italic: true, color: C.muted, margin: 0, isTextBox: true });
  s.addText("Explore: starter ideas with AI-generated cover art", { x: 6.78, y: cy, w: 5.95, h: 0.3, fontFace: BODY, fontSize: 11, italic: true, color: C.muted, margin: 0, isTextBox: true });
  const py = Math.min(cy + 0.6, 6.25);
  ["Create", "Library", "Explore", "Settings"].forEach((t, i) => {
    const x = 0.6 + i * 1.55;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: py, w: 1.4, h: 0.5, rectRadius: 0.25, fill: { color: i === 0 ? C.violet : C.lav }, line: { color: i === 0 ? C.violet : C.lav } });
    s.addText(t, { x, y: py, w: 1.4, h: 0.5, fontFace: BODY, fontSize: 14, bold: true, color: i === 0 ? C.white : C.violet, align: "center", valign: "middle", margin: 0, isTextBox: true });
  });
  s.addText("Story tabs: Story · Scenes · Prompt Lab · Evaluation", { x: 6.9, y: py, w: 5.83, h: 0.5, fontFace: BODY, fontSize: 14, color: C.ink, valign: "middle", margin: 0, isTextBox: true });
}

// 9 · Results ------------------------------------------------------------------------------------
{
  const bs = SUM.by_strategy, keys = Object.keys(bs);
  const bestCov = keys.reduce((a, b) => ((bs[b].brief_coverage ?? 0) > (bs[a].brief_coverage ?? 0) ? b : a), keys[0]);
  const s = slideWithTitle("What the experiments showed", SPEAKER.results,
    `We ran ${SUM.runs} live generations: ${SUM.ideas.length} story ideas, each with all four strategies at temperature 0.9 and with direct prompting at 0.3 and 1.5. ` +
    `On the left, brief coverage, our adherence measure, was highest for ${NAMES[bestCov]} at ${fmt(bs[bestCov].brief_coverage, true)}, against ${fmt(bs.direct?.brief_coverage, true)} for direct prompting. Diversity, measured by Distinct-2, was similar for all strategies. ` +
    `On the right, temperature changed Distinct-2 very little in this range. Tree-of-Thought took about ${((bs.tot?.latency_ms ?? 0) / (bs.direct?.latency_ms || 1)).toFixed(1)} times as long as direct prompting because it makes two calls. All stories had a fully valid structure. These are simple, explainable proxies over one run per setting, so we read them as tendencies.`);
  const axis = { catAxisLabelColor: C.muted, valAxisLabelColor: C.muted, catAxisLabelFontFace: BODY, valAxisLabelFontFace: BODY,
    catAxisLabelFontSize: 11, valAxisLabelFontSize: 10, valGridLine: { color: "E6E1F0", size: 0.5 }, catGridLine: { style: "none" },
    dataLabelColor: C.ink, dataLabelFontSize: 10, dataLabelFontFace: BODY, titleFontFace: BODY, titleFontSize: 14, titleColor: C.ink,
    legendFontFace: BODY, legendFontSize: 11, legendColor: C.ink, valAxisMinVal: 0, valAxisMaxVal: 1, valAxisMajorUnit: 0.25 };
  s.addChart(pres.charts.BAR, [
    { name: "Distinct-2 (diversity)", labels: keys.map((k) => NAMES[k]), values: keys.map((k) => bs[k].distinct_2 ?? 0) },
    { name: "Brief coverage (adherence)", labels: keys.map((k) => NAMES[k]), values: keys.map((k) => bs[k].brief_coverage ?? 0) },
  ], { x: 0.6, y: 1.5, w: 6.3, h: 3.6, barDir: "col", chartColors: [C.violet, C.gold], showValue: true, dataLabelFormatCode: "0.00",
    dataLabelPosition: "outEnd", showTitle: true, title: "By strategy (T = 0.9)", showLegend: true, legendPos: "b", ...axis });
  const ts = Object.keys(SUM.by_temperature).sort((a, b) => a - b);
  s.addChart(pres.charts.LINE, [
    { name: "Distinct-2", labels: ts.map((t) => `T = ${t}`), values: ts.map((t) => SUM.by_temperature[t].distinct_2 ?? 0) },
    { name: "Brief coverage", labels: ts.map((t) => `T = ${t}`), values: ts.map((t) => SUM.by_temperature[t].brief_coverage ?? 0) },
  ], { x: 7.1, y: 1.5, w: 5.63, h: 3.6, chartColors: [C.violet, C.gold], lineSize: 2.5, lineDataSymbol: "circle", lineDataSymbolSize: 8,
    showValue: true, dataLabelFormatCode: "0.00", dataLabelPosition: "t", showTitle: true, title: "Effect of temperature (Direct)", showLegend: true, legendPos: "b", ...axis });
  const picked = SUM.findings.filter((t) => /highest brief coverage|^Temperature \(|Tree-of-Thought needs/i.test(t));
  const f = (picked.length ? picked : SUM.findings).slice(0, 3);
  s.addText(bullets(f), { x: 0.6, y: 5.3, w: 12.13, h: 1.3, fontFace: BODY, fontSize: 14, color: C.ink, margin: 0, paraSpaceAfter: 4, valign: "top", isTextBox: true });
  preview(s);
}

// 10 · Challenges, conclusion and repository ------------------------------------------------------
{
  const s = slideWithTitle("Challenges, conclusion and code", SPEAKER.intro,
    "To conclude. The main challenges were Gemini's 503 high-demand errors during the experiment, which we handled with retries and a resumable experiment script; making the JSON output reliable enough to drive the image pipeline; image API rate limits and cost; and keeping characters consistent across panels. We built a working end-to-end generative AI studio that makes conditioning, sampling, prompting and multimodal generation visible and measurable. The models are pretrained and the metrics are proxies; next steps are fine-tuning a small open model, semantic metrics such as CLIPScore, and a larger experiment. The code is on GitHub. Thank you, we are happy to take questions.");
  const cols = [["Challenges we solved", C.red, ["Gemini 503 “high demand”: retries + resumable experiments", "Reliable JSON output to drive the image pipeline", "Image rate limits and cost: background worker", "Character consistency: shared character sheet"]],
    ["What we achieved", C.violet, ["End-to-end studio: idea → story → storyboard → scores", "All course concepts visible in one app", `A live experiment of ${SUM.runs} generations`]],
    ["Future work", C.gold, ["Fine-tune a small open model (LoRA)", "Semantic metrics and CLIPScore", "More runs per setting, text-to-speech"]]];
  cols.forEach(([h, col, items], i) => {
    const x = 0.6 + i * 4.11;
    if (i === 1) card(s, x, 1.6, 3.91, 3.75); else outline(s, x, 1.6, 3.91, 3.75);
    s.addText(h, { x: x + 0.25, y: 1.75, w: 3.45, h: 0.45, fontFace: HEAD, fontSize: 18, bold: true, color: col, margin: 0, isTextBox: true });
    s.addText(bullets(items), { x: x + 0.25, y: 2.3, w: 3.45, h: 2.95, fontFace: BODY, fontSize: 14, color: C.ink, margin: 0, paraSpaceAfter: 8, valign: "top", isTextBox: true });
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 5.6, w: 12.13, h: 1.1, rectRadius: 0.12, fill: { color: C.violet }, line: { color: C.violet } });
  s.addText([{ text: "PROJECT CODE REPOSITORY", options: { fontSize: 11, bold: true, color: C.lav2, charSpacing: 2, breakLine: true } },
    { text: INFO.github_url, options: { fontSize: 22, bold: true, color: C.white, hyperlink: { url: INFO.github_url } } }],
  { x: 0.6, y: 5.6, w: 12.13, h: 1.1, fontFace: BODY, align: "center", valign: "middle", margin: 0, isTextBox: true });
}

const outDir = path.join(ROOT, "submission");
fs.mkdirSync(outDir, { recursive: true });
const file = path.join(outDir, `PPT_${INFO.group_no}.pptx`);
await pres.writeFile({ fileName: file });
// Drop ZIP folder entries: some cloud viewers (Drive/OneDrive) fail to open decks that contain them.
const src = await JSZip.loadAsync(fs.readFileSync(file));
const clean = new JSZip();
for (const [name, entry] of Object.entries(src.files)) {
  if (!entry.dir) clean.file(name, await entry.async("nodebuffer"), { createFolders: false });
}
fs.writeFileSync(file, await clean.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
console.log(`Saved ${file}${SUM.demo ? "  (PREVIEW: demo data)" : ""}`);
