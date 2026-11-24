"""Prompt-engineering strategies (syllabus unit: Prompt Engineering).

Each strategy is a list of steps; each step is one LLM call whose prompt is stored in generation_runs,
so the Prompt Lab can show exactly what was sent.

direct     one prompt containing all conditions
interview  Interview Pattern: the model first asks itself the questions a writer would ask, answers them
           from the brief, then writes from that Q&A
cot        Chain-of-Thought-style structured prompting: the model must output a visible plan
           (world -> characters -> arc) before the story fields
tot        Tree-of-Thought-style: generate 3 plot branches, score each on criteria, select the best, then write
"""
from ..schemas import IdeaInput, PlotParameters

STRATEGIES = {
    "direct": {
        "label": "Direct prompting",
        "steps": ["write"],
        "description": "A single prompt with all the conditions. The baseline for comparisons.",
    },
    "interview": {
        "label": "Interview Pattern",
        "steps": ["interview", "write"],
        "description": "The model first asks and answers clarifying questions about the brief, then writes from that Q&A.",
    },
    "cot": {
        "label": "Chain-of-Thought (structured)",
        "steps": ["write"],
        "description": "The model must write an explicit plan (world, characters, arc) before the story itself.",
    },
    "tot": {
        "label": "Tree-of-Thought (branch & select)",
        "steps": ["branches", "write"],
        "description": "Three plot branches are generated and scored; the best one is expanded into the story.",
    },
}

SYSTEM = (
    "You are StoryForge, a manga story writer. Always reply with a single valid JSON object that follows the "
    "requested schema exactly. No markdown, no commentary outside the JSON."
)

STORY_SCHEMA = """{
  "title": string,
  "logline": string (2-3 sentence teaser),
  "characters": [{"name": string, "role": "protagonist"|"ally"|"rival"|"villain"|"mentor"|"other",
                  "visual_description": string (hair, eyes, outfit; reused for every image)}]  (3-5 items),
  "relationships": [{"source": name, "target": name, "label": short string like "ALLY", "CONFLICT"}],
  "beats": [{"name": one of "Inciting Incident","Call to Action","Rising Conflict","Midpoint Turn","Climax","Resolution",
             "summary": one sentence}]  (exactly 6, in that order),
  "chapters": [{"title": short title WITHOUT "Chapter" or a number, "text": string}],
  "scenes": [{"caption": short string, "image_prompt": visual description of one key moment, no dialogue}]  (exactly 4)
}"""


def _level(value: int, low: str, mid: str, high: str) -> str:
    return low if value < 34 else mid if value < 67 else high


def length_targets(length: int) -> tuple[int, int]:
    """Story-length slider -> (chapters, words per chapter)."""
    chapters = 3 if length < 34 else 4 if length < 67 else 5
    words = 150 + length * 3  # ~150-450 words per chapter
    return chapters, words


def brief(idea: IdeaInput, plot: PlotParameters) -> str:
    """Conditional generation: user inputs and sliders become explicit conditions in the prompt."""
    chapters, words = length_targets(plot.length)
    lines = [
        f"Protagonist: {idea.protagonist}",
        f"Goal: {idea.goal}",
        f"Genre: {idea.genre}",
    ]
    if idea.world_rule:
        lines.append(f"World rule (must matter to the plot): {idea.world_rule}")
    if idea.ending_twist:
        lines.append(f"Ending twist (reveal near the climax, set it up earlier): {idea.ending_twist}")
    lines += [
        f"Tone: {_level(plot.tone, 'dark and grim', 'bittersweet', 'light and hopeful')} ({plot.tone}/100 toward light)",
        f"Conflict level: {_level(plot.conflict, 'low', 'moderate', 'high')} ({plot.conflict}/100)",
        f"Romance: {_level(plot.romance, 'none or minimal', 'a subplot', 'central')} ({plot.romance}/100)",
        f"Action intensity: {_level(plot.action, 'low', 'moderate', 'intense battles')} ({plot.action}/100)",
        f"Length: {chapters} chapters of about {words} words each",
    ]
    return "STORY BRIEF\n" + "\n".join(f"- {l}" for l in lines)


def interview_prompt(story_brief: str) -> str:
    return (
        f"{story_brief}\n\nBefore writing, act as an editor interviewing the author. Ask the 5 most important "
        "questions needed to write this story well (motivation, stakes, the world rule's cost, the rival, how the "
        "twist is foreshadowed), then answer each one yourself, consistent with the brief.\n"
        'Return JSON: {"questions": [{"q": string, "a": string}]}'
    )


def branches_prompt(story_brief: str) -> str:
    return (
        f"{story_brief}\n\nPropose 3 clearly different plot branches for this story. Score each from 1-10 on "
        "originality, coherence and fit_to_brief, then choose the best one.\n"
        'Return JSON: {"branches": [{"id": "A"|"B"|"C", "premise": string, '
        '"scores": {"originality": int, "coherence": int, "fit_to_brief": int}}], '
        '"selected": "A"|"B"|"C", "reason": string}'
    )


def write_prompt(strategy: str, story_brief: str, artifacts: dict) -> str:
    parts = [story_brief]
    if strategy == "interview" and artifacts.get("interview"):
        qa = "\n".join(f"Q: {x['q']}\nA: {x['a']}" for x in artifacts["interview"]["questions"])
        parts.append(f"EDITOR INTERVIEW (use these answers):\n{qa}")
    if strategy == "tot" and artifacts.get("branches"):
        b = artifacts["branches"]
        chosen = next((x for x in b["branches"] if x["id"] == b["selected"]), b["branches"][0])
        parts.append(f"SELECTED PLOT BRANCH ({chosen['id']}): {chosen['premise']}")

    schema = STORY_SCHEMA
    if strategy == "cot":
        parts.append(
            "Work in explicit stages. First fill the \"plan\" field: (1) the world and how its rule works, "
            "(2) each character's motivation, (3) the arc across the six beats and where the twist is foreshadowed. "
            "Then write the story so it follows your plan."
        )
        schema = schema.replace("{\n", '{\n  "plan": {"world": string, "characters": string, "arc": string},\n', 1)

    parts.append(f"Write the story. Return JSON with this schema:\n{schema}")
    return "\n\n".join(parts)
