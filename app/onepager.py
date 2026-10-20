"""A one-page PDF summary of the results, for executives to keep or forward."""

from __future__ import annotations

from fpdf import FPDF

INK = (27, 36, 48)
MUTED = (91, 102, 117)
BLUE = (47, 111, 174)
GREEN = (46, 148, 104)
GREY = (195, 202, 211)
# The dashboard's colours, so the page and the PDF read the same way.
CHECK = (94, 149, 217)
AGENT = (69, 73, 176)
REVIEW = (184, 90, 130)
RISK = (194, 65, 58)
LINE = (221, 226, 232)

# The PDF core fonts are Latin-1 only.
_PLAIN = {
    "–": "-",
    "—": "-",
    "≥": ">=",
    "≤": "<=",
    "’": "'",
    "“": '"',
    "”": '"',
    "·": "-",
    "→": "->",
    "×": "x",
}


def _p(text: str) -> str:
    for a, b in _PLAIN.items():
        text = text.replace(a, b)
    return text.encode("latin-1", "replace").decode("latin-1")


def _checks(reach, total, today, caught):
    return [
        ("Seven times the catch", f"{caught} critical safeguards caught with evidence, against {today} today; only one of {total} slipped past both."),
        ("Right when it flags", "More than 9 in 10 of its new recommendations are correct."),
        ("Shows its evidence", "Every finding quotes the change request and the control procedure, with a second, independent opinion."),
        ("Keeps people in charge", "Doubtful cases go to the control owner; every release decision stays with people."),
        ("Inexpensive to run", "Pennies per change in model costs (estimated), on the bank's own Databricks platform."),
    ]


ASK = "The decision for leadership: approve a short practitioner test with two or three control owners and a risk lead."
VERDICT = "Ready for our control owners to test on real changes."


def build(h: dict, cons: dict, run_label: str) -> bytes:
    """One A4 page for executives: outcomes in words and a picture, no scores.
    run_label names the recorded run (date, job, version)."""
    total = h.get("key_affected", 162)
    rules_found = total - h["key_misses"]
    routed = h.get("key_routed", 30)
    silent = h["key_misses"] - h["key_recovered"] - routed
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(False)
    pdf.add_page()
    pdf.set_margins(18, 16, 18)
    w = pdf.w - 36

    def text(size, s, color=INK, style="", h_=5.2):
        pdf.set_font("Helvetica", style, size)
        pdf.set_text_color(*color)
        pdf.multi_cell(w, h_, _p(s), new_x="LMARGIN", new_y="NEXT", align="L")

    pdf.set_xy(18, 16)
    text(9, f"Control Impact Detective  |  Synthetic proof of concept  |  {run_label}", MUTED)
    pdf.ln(2)
    reach = rules_found + h["key_recovered"] + routed
    text(20, f"{reach} of {total} critical safeguards reach their owner before release, against {rules_found} today", INK, "B", 9)
    pdf.ln(1)
    text(
        10.5,
        "Tested on realistic payment changes the detective had never seen, in a synthetic bank whose dependency map "
        "is missing links near each change.",
        MUTED,
    )
    pdf.ln(6)

    # The picture: two bars on one scale, no figures
    def bar(y, label, segs):
        pdf.set_xy(18, y)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*INK)
        pdf.cell(42, 9, _p(label))
        x, bw_all = 60, w - 42
        for n, col in segs:
            if not n:
                continue
            bw = bw_all * n / total
            pdf.set_fill_color(*col)
            pdf.rect(x, y, max(bw - 0.6, 0.8), 9, "F")
            x += bw

    y = pdf.get_y()
    bar(y, "Today's check", [(rules_found, CHECK), (total - rules_found, GREY)])
    bar(y + 13, "With the detective", [(rules_found, CHECK), (h["key_recovered"], AGENT), (routed, REVIEW), (silent, RISK)])
    pdf.set_y(y + 26)
    lx = 18
    pdf.set_font("Helvetica", "", 8.5)
    for col, label in ((CHECK, "Caught by today's check"), (AGENT, "Also caught by the detective"), (REVIEW, "Flagged to a person"), (RISK, "Missed"), (GREY, "Not seen")):
        pdf.set_fill_color(*col)
        pdf.rect(lx, pdf.get_y() + 1.2, 2.6, 2.6, "F")
        pdf.set_xy(lx + 3.6, pdf.get_y())
        pdf.set_text_color(*MUTED)
        t = _p(label)
        pdf.cell(pdf.get_string_width(t) + 2, 5, t)
        lx += 3.6 + pdf.get_string_width(t) + 6
    pdf.ln(6)
    pdf.set_x(18)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*MUTED)
    pdf.cell(w - 42, 5, _p("Each bar is the same set of critical safeguards that the test changes actually affected."))
    pdf.ln(5)
    pdf.ln(5)

    for head, body in _checks(reach, total, rules_found, rules_found + h["key_recovered"]):
        yy = pdf.get_y()
        pdf.set_fill_color(229, 240, 234)
        pdf.ellipse(18, yy + 0.6, 4.6, 4.6, "F")
        pdf.set_draw_color(46, 107, 78)
        pdf.set_line_width(0.55)
        pdf.line(19.3, yy + 3.0, 20.1, yy + 3.9)
        pdf.line(20.1, yy + 3.9, 21.6, yy + 1.9)
        pdf.set_line_width(0.2)
        pdf.set_xy(25, yy)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*INK)
        pdf.cell(w - 7, 5.6, _p(head), new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(25)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(61, 71, 82)
        pdf.multi_cell(w - 7, 5, _p(body), new_x="LMARGIN", new_y="NEXT", align="L")
        pdf.ln(2.2)
    pdf.ln(2)

    # Verdict
    y = pdf.get_y()
    pdf.set_fill_color(*AGENT)
    pdf.rect(18, y, w, 22, "F")
    pdf.set_xy(23, y + 3.5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(w - 10, 6, _p("Verdict: " + VERDICT))
    pdf.set_xy(23, y + 10.5)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(w - 10, 5, _p(ASK), new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.set_y(y + 26)

    pdf.set_y(276)
    text(8, "The detailed figures, and every record behind them, are in the app's Evidence room.", MUTED)
    text(8, "Synthetic data only: no real bank, customer or control data.", MUTED)
    return bytes(pdf.output())
