"""Quick check of how often the endpoint returns an empty or unusable answer.

    python -m scripts.probe_model --model databricks-gpt-oss-120b --n 6

Sends the detective's first-step prompt for CHG-001 n times through the same
adapter the agent uses and reports usable replies. Takes about a minute.
"""

import argparse
import json

from scripts.databricks_llm import DatabricksChatLLM
from scripts.detective import _object, parse_command
from scripts.export_case import export_case


def first_prompt(case):
    captured = []

    def capture(prompt):
        captured.append(prompt)
        raise RuntimeError("captured")

    from scripts.detective import investigate

    try:
        investigate(case, capture, max_steps=1)
    except RuntimeError:
        pass
    return captured[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="databricks-gpt-oss-120b")
    parser.add_argument("--n", type=int, default=6)
    parser.add_argument("--change-id", default="CHG-001")
    args = parser.parse_args()
    prompt = first_prompt(export_case(args.change_id))
    llm = DatabricksChatLLM(args.model, max_tokens=8000)
    usable = 0
    for i in range(args.n):
        text = llm(prompt)
        try:
            action, _ = parse_command(_object(text))
            usable += 1
            print(f"{i + 1}: OK action={action}")
        except Exception as exc:
            print(
                f"{i + 1}: FAIL {type(exc).__name__}: {str(exc)[:80]} | {text[:120]!r}"
            )
    print(
        json.dumps(
            {
                "usable": usable,
                "of": args.n,
                "empty_attempts_retried": getattr(llm, "empty_answers", 0),
            }
        )
    )


if __name__ == "__main__":
    main()
