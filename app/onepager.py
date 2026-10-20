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


def build(h: dict, cons: dict, run_label: str) -> bytes:
    """One A4 page. run_label names the recorded run (date, job, version)."""
    total = h.get("key_affected", 162)
    rules_found = total - h["key_misses"]
    routed = h.get("key_routed", 30)
    silent = h["key_misses"] - h["key_recovered"] - routed
    added, added_aff = h.get("added_items", 406), h.get("added_affected", 331)
    new_right, new_total = h.get("new_right", 262), h.get("new_total", 280)
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
    text(19, "Finds nearly four in five of the key controls the existing lineage check misses", INK, "B", 8.5)
    pdf.ln(1)
    text(
        10.5,
        "Measured on 18 synthetic payment changes the detective had never seen, with 30% of the lineage map "
        "removed nearest each change. Compared with today's automated check, not with a person.",
        MUTED,
    )
    pdf.ln(4)

    # KPI row
    y = pdf.get_y()
    kpis = [
        (f"{100 * h['key_miss_recovery']:.1f}%", "key misses recommended", f"{h['key_recovered']} of {h['key_misses']}; target 50%"),
        (f"{100 * h['new_control_precision']:.1f}%", "recommendations right", f"{new_right} of {new_total}"),
        (f"{added_aff} of {added}", "added items are real", f"{added - added_aff} not affected"),
        (f"{100 * cons['agreement']:.0f}%", "same key decision, 5 runs", "target 95%"),
    ]
    cw = w / 4
    pdf.set_draw_color(*LINE)
    pdf.line(18, y, 18 + w, y)
    for i, (v, l, n) in enumerate(kpis):
        x = 18 + i * cw
        pdf.set_xy(x, y + 3)
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_text_color(*INK)
        pdf.cell(cw, 9, _p(v))
        pdf.set_xy(x, y + 13)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(cw, 4.5, _p(l))
        pdf.set_xy(x, y + 17.5)
        pdf.set_text_color(*MUTED)
        pdf.cell(cw, 4.5, _p(n))
    pdf.line(18, y + 24, 18 + w, y + 24)
    pdf.set_y(y + 30)

    # Stacked bar, in the dashboard's colours and words
    text(11, f"Where the {total} affected key controls went", INK, "B")
    pdf.ln(1.5)
    y = pdf.get_y()
    x = 18
    segs = (
        (rules_found, CHECK, "Existing lineage check"),
        (h["key_recovered"], AGENT, "Recommended by the detective"),
        (routed, REVIEW, "Sent to a person"),
        (silent, RISK, "Not surfaced"),
    )
    for n, col, _label in segs:
        if not n:
            continue
        bw = w * n / total
        pdf.set_fill_color(*col)
        pdf.rect(x, y, max(bw - 0.6, 0.8), 9, "F")
        if bw > 8:
            pdf.set_xy(x, y)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(bw, 9, str(n), align="C")
        x += bw
    pdf.set_y(y + 11.5)
    lx = 18
    pdf.set_font("Helvetica", "", 8.5)
    for n, col, label in segs:
        pdf.set_fill_color(*col)
        pdf.rect(lx, pdf.get_y() + 1.2, 2.6, 2.6, "F")
        pdf.set_xy(lx + 3.6, pdf.get_y())
        pdf.set_text_color(*MUTED)
        t = _p(f"{label} - {n}")
        pdf.cell(pdf.get_string_width(t) + 2, 5, t)
        lx += 3.6 + pdf.get_string_width(t) + 7
    pdf.ln(7)
    text(
        9,
        f"The one not surfaced is C03 (unresolved sanctions alerts) on CHG-024, marked not affected; the planned fix is "
        f"a second check on key controls marked not affected, before any pilot.",
        (61, 71, 82),
    )
    pdf.ln(3)

    lines = [
        (
            "What a bank gains",
            "A shortlist of the controls a change may break, each with quoted evidence and an independent verifier's view; "
            "nothing the existing lineage check finds is lost, and doubtful cases go to a person instead of being decided silently.",
        ),
        (
            "The extra items are mostly real impacts",
            f"These controls need checking with or without the detective: by tracing lineage gaps by hand, or by missing them. "
            f"Of the {added} items it adds, {added_aff} are real impacts the lineage check missed; the other {added - added_aff} come with evidence to clear them.",
        ),
        (
            "Running cost",
            "71 model calls per change on average (1,280 across 18). Estimated about 450k tokens per change, roughly "
            "$0.07-$0.11 at Databricks' list rate for GPT-OSS-120B (token counts estimated by replaying the recorded prompts).",
        ),
        (
            "Next: steadier decisions run to run",
            f"Across five runs, {100 * cons['agreement']:.0f}% of key decisions were identical, against a 95% target; a multi-run vote reached 94.4%.",
        ),
    ]
    for head, body in lines:
        text(10.5, head, INK, "B")
        text(9.5, body, (61, 71, 82))
        pdf.ln(1.5)
    pdf.ln(1)

    # Scorecard
    text(11, "Scorecard against the targets set at the start", INK, "B")
    pdf.ln(1)
    for target, status, detail in (
        ("Find >= 50% of missed key controls", "Met", f"{100 * h['key_miss_recovery']:.1f}% on unseen changes"),
        ("Same key decision across 5 runs >= 95%", "Not met", f"{100 * cons['agreement']:.0f}%"),
        ("Judged by control owners on real changes", "Next", "the proposed practitioner validation"),
    ):
        yy = pdf.get_y()
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(*INK)
        pdf.set_xy(18, yy)
        pdf.cell(w * 0.44, 6, _p(target))
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(*{"Met": (30, 107, 73), "Next": AGENT}.get(status, REVIEW))
        pdf.cell(w * 0.12, 6, status)
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(*MUTED)
        pdf.cell(w * 0.44, 6, _p(detail))
        pdf.set_draw_color(*LINE)
        pdf.line(18, yy + 6.5, 18 + w, yy + 6.5)
        pdf.set_y(yy + 7.5)
    pdf.ln(3)

    # Next step
    pdf.set_fill_color(244, 246, 249)
    y = pdf.get_y()
    pdf.rect(18, y, w, 22, "F")
    pdf.set_fill_color(*AGENT)
    pdf.rect(18, y, 1.2, 22, "F")
    pdf.set_xy(22, y + 2.5)
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(*INK)
    pdf.multi_cell(w - 6, 5.2, "Suggested next step", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(22)
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(61, 71, 82)
    pdf.multi_cell(
        w - 6,
        5,
        _p(
            "Two or three control owners and a risk lead judge a sample of the recorded output: all 30 key controls sent "
            "to a person, plus samples of those recommended and those marked not affected. The choice rests with leadership."
        ),
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.set_y(282)
    text(8, "Synthetic data only: no real bank, customer or control data. Proof of concept, not in production.", MUTED)
    return bytes(pdf.output())
