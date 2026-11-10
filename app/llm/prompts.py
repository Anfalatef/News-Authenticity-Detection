from __future__ import annotations


PROMPT_VERSION = "v1"
PROMPT_VERSION_AR = "v2"
PIPELINE_VERSION = "v1"


def _contexts_to_block(contexts: list[dict]) -> str:
    lines = []
    for i, c in enumerate(contexts, start=1):
        lines.append(
            f"[{i}] source={c.get('source','')} title={c.get('title','')} url={c.get('url','')}\n"
            f"chunk={c.get('chunk_text','')}\n"
        )
    return "\n".join(lines).strip()


def build_veracity_prompt(
    user_text: str,
    contexts: list[dict],
    language: str | None = None,
) -> list[dict[str, str]]:
    evidence = _contexts_to_block(contexts)
    reasons_language = "English"
    if language == "ar":
        reasons_language = "Arabic"
    return [
        {
            "role": "system",
            "content": (
                "You are a fact-checking assistant. "
                "If the input is not a news claim or news text, return JSON error NOT_NEWS and do not analyze."
                "Given a user claim/news text and retrieved evidence snippets, "
                "decide whether the claim is Real, Fake, or Unclear. "
                "Return a short JSON with: label, confidence (0-100), reasons (bullets), evidence_urls. "
                f"Write reasons in {reasons_language}. "
                "Keep label strictly one of: Real, Fake, Unclear."
            ),
        },
        {"role": "user", "content": f"CLAIM:\n{user_text}\n\nEVIDENCE:\n{evidence}"},
    ]


def build_bias_prompt(user_text: str, contexts: list[dict]) -> list[dict[str, str]]:
    evidence = _contexts_to_block(contexts)
    return [
        {
            "role": "system",
            "content": (
                "You are a bias analysis assistant. "
                "Detect bias in the user text (political/ideological/religious/ethnic/gender/hate/incitement). "
                "Return a short JSON with: has_bias (true/false), types, severity (1-5), "
                "If input is not news text, return JSON error NOT_NEWS."
                "quotes (exact snippets), neutral_rewrite."
            ),
        },
        {"role": "user", "content": f"TEXT:\n{user_text}\n\nCONTEXT:\n{evidence}"},
    ]
