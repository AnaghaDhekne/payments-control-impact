"""Serve the client-facing experience (app/web) as a Databricks App.

    python app/server.py            # http://localhost:8000

Databricks Apps set DATABRICKS_APP_PORT; locally PORT or 8000 is used. Only the
Python standard library is needed to serve the pages. POST /api/ask forwards a
question to the existing project assistant (app/qa.py), which uses the
workspace model endpoint; if that is not reachable, the reply says so.
"""

from __future__ import annotations

import json
import os
import sys
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "app" / "web"
sys.path.insert(0, str(ROOT))


def results_summary() -> str:
    """The figures the experience shows, as plain text for the assistant."""
    e = json.loads((WEB / "data" / "experience.json").read_text())
    p, prov = e["portfolio"], e["provenance"]
    return (
        f"Held-out test ({p['changes']} synthetic changes, version {prov['version']}, job {prov['job']}, {prov['date']}): "
        f"{p['key_affected']} affected key-control instances; current check found {p['check_found_key']}; "
        f"agent recommended {p['agent_found_key']} of the {p['key_misses']} the check missed ({100 * p['recovery']:.1f}%); "
        f"{p['key_routed']} routed for human review; {p['key_silent']} not surfaced. "
        f"New recommendations right: {p['new_right']} of {p['new_total']}. "
        f"Review items: {p['check_items']} from the check, {p['added_items']} added "
        f"({p['added_affected']} genuinely affected, {p['added_unaffected']} unaffected). "
        f"Consistency over 5 runs: {100 * p['consistency']['agreement']:.0f}% of {p['consistency']['pairs']} key decisions (target 95%). "
        "Routing to a person is not a completed review; reviewer time, real-data accuracy and costs were not measured."
    )


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        if self.path.startswith("/data/"):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, fmt, *args):  # quieter logs
        sys.stderr.write("%s %s\n" % (self.command, self.path))

    def do_GET(self):
        if self.path == "/healthz":
            return self._json({"ok": True})
        if self.path.split("?")[0] == "/summary.pdf":
            return self._summary_pdf()
        return super().do_GET()

    def _summary_pdf(self):
        """The one-page summary, built from the same exported figures."""
        try:
            from app import onepager

            e = json.loads((WEB / "data" / "experience.json").read_text())
            p = e["portfolio"]
            h = {
                "key_misses": p["key_misses"],
                "key_recovered": p["agent_found_key"],
                "key_miss_recovery": p["recovery"],
                "new_control_precision": p["precision"],
                "avoidable_review_items_per_case": p["added_unaffected"] / p["changes"],
            }
            data = onepager.build(h, p["consistency"], "2026-10-19")
        except Exception as exc:  # fpdf2 not installed
            return self._json(
                {"error": f"Summary unavailable ({type(exc).__name__})"},
                HTTPStatus.SERVICE_UNAVAILABLE,
            )
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/pdf")
        self.send_header(
            "Content-Disposition",
            'attachment; filename="control-impact-poc-summary.pdf"',
        )
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path.rstrip("/") != "/api/ask":
            return self._json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(min(n, 20000)) or b"{}")
            question = str(body.get("question", "")).strip()[:1000]
        except (ValueError, json.JSONDecodeError):
            return self._json(
                {"error": 'Send JSON: {"question": "..."}'}, HTTPStatus.BAD_REQUEST
            )
        if not question:
            return self._json({"error": "Ask a question."}, HTTPStatus.BAD_REQUEST)
        try:
            from app import qa

            answer = qa.ask(question, [], results_summary())
            return self._json({"answer": answer})
        except Exception as exc:  # endpoint missing, not permitted, or no SDK locally
            return self._json(
                {
                    "answer": "The model endpoint could not be reached from here "
                    f"({type(exc).__name__}). The Results and Limits pages in the evidence room "
                    "answer the common questions."
                }
            )

    def _json(self, obj, status=HTTPStatus.OK):
        data = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    port = int(os.environ.get("DATABRICKS_APP_PORT") or os.environ.get("PORT") or 8000)
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Control Impact Detective on http://0.0.0.0:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
