"""Run the detective with Databricks or explicitly replay a saved transcript."""

import argparse
import json
from pathlib import Path
from scripts.detective import investigate


def main():
    """Persist every model response; replay requires exact prompt matching."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", default="databricks-gpt-oss-120b")
    parser.add_argument("--max-steps", type=int, default=24)
    parser.add_argument(
        "--replay", help="JSON list of {prompt, response}; no live model calls"
    )
    args = parser.parse_args()
    case = json.loads(Path(args.case).read_text(encoding="utf-8"))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    calls = []
    if args.replay:
        saved = iter(json.loads(Path(args.replay).read_text(encoding="utf-8")))

        def model(prompt):
            item = next(saved)
            if item["prompt"] != prompt:
                raise ValueError("Replay prompt mismatch; case or code changed")
            return item["response"]

    else:
        from scripts.databricks_llm import DatabricksChatLLM

        model = DatabricksChatLLM(args.model, max_tokens=8000)

    def tracked(prompt):
        response = model(prompt)
        calls.append({"prompt": prompt, "response": response})
        output.with_suffix(".calls.json").write_text(
            json.dumps(calls, indent=2) + "\n", encoding="utf-8"
        )
        return response

    def persist(result):
        result = {
            **result,
            "model": args.model,
            "execution": "REPLAY" if args.replay else "LIVE",
            "max_steps": args.max_steps,
        }
        temp = output.with_suffix(".tmp")
        temp.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        temp.replace(output)

    investigate(case, tracked, max_steps=args.max_steps, persist=persist)


if __name__ == "__main__":
    main()
