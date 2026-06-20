"""Emit the steelman chatbot prompt for each eval case (the rules-summary preamble
+ the case scenario), ready to paste into ChatGPT or feed to an API YOU control.

This does NOT call any API. It writes ``eval/chatbot_prompts.txt`` (one prompt per
case, separated) and prints them. Per the eval doc, run C/D cases 3× and record
whether the answer is identical across runs (consistency is itself a finding).

    python eval/chatbot_prompts.py
"""

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(_BACKEND))

from cases import CASES, PREAMBLE, Case  # noqa: E402


def build_prompt(case: Case) -> str:
    """The verbatim steelman preamble with this case's scenario substituted in."""
    return f"{PREAMBLE}\n\nCASE: {case.scenario_text}"


def main() -> None:
    blocks: list[str] = []
    for case in CASES:
        runs = " (run 3×)" if case.category in ("C", "D") else ""
        blocks.append(
            f"================ {case.id} [{case.category}]{runs} ================\n"
            f"{build_prompt(case)}\n"
        )
    text = "\n".join(blocks)

    out = Path(__file__).resolve().parent / "chatbot_prompts.txt"
    out.write_text(text, encoding="utf-8")
    print(text)
    print(f"\nWrote {len(CASES)} prompts to {out.relative_to(Path(__file__).resolve().parent.parent)}")


if __name__ == "__main__":
    main()
