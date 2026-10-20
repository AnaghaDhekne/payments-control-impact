"""A one-page PDF summary of the results, for executives to keep or forward."""

from __future__ import annotations

from fpdf import FPDF

INK = (27, 36, 48)
MUTED = (91, 102, 117)
BLUE = (47, 111, 174)
GREEN = (46, 148, 104)
GREY = (195, 202, 211)
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


def build(h: dict, cons: dict, frozen_on: str) -> bytes:
    rules_found = 162 - h["key_misses"]
    still = h["key_misses"] - h["key_recovered"]
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(False)
    pdf.add_page()
    pdf.set_margins(18, 16, 18)
    w = pdf.w - 36

    def text(size, s, color=INK, style="", h_=5.2):
        pdf.set_font("Helvetica", style, size)
        pdf.set_text_color(*color)
        pdf.multi_cell(w, h_, _p(s), new_x="LMARGIN", new_y="NEXT")

    pdf.set_xy(18, 16)
    text(
        9,
        f"Payments control-impact proof of concept  |  Synthetic benchmark data  |  Version A, frozen {frozen_on}",
        MUTED,
    )
    pdf.ln(2)
    text(
        19,
        "The detective finds nearly four in five of the controls the existing lineage check misses",
        INK,
        "B",
        8.5,
    )
    pdf.ln(1)
    text(
        10.5,
        "Measured on 18 synthetic payment changes the detective had never seen, with 30% of the lineage map removed. "
        "Compared with today's automated check, not with a person.",
        MUTED,
    )
    pdf.ln(4)

    # KPI row
    y = pdf.get_y()
    kpis = [
        (
            f"{100 * h['key_miss_recovery']:.0f}%",
            "missed key controls found",
            "target 50%; range 71-84%",
        ),
        (
            f"{100 * h['new_control_precision']:.0f}%",
            "recommendations right",
            "262 of 280",
        ),
        (
            "331 of 406",
            "added items truly affected",
            "75 not affected",
        ),
        (
            f"{100 * cons['agreement']:.0f}%",
            "same decision, 5 runs",
            "target 95%",
        ),
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

    # Stacked bar
    text(11, "Where the 162 affected key controls ended up", INK, "B")
    pdf.ln(1.5)
    y = pdf.get_y()
    x = 18
    for n, col, label in (
        (rules_found, BLUE, "Found by the existing lineage check"),
        (h["key_recovered"], GREEN, "Found by the detective"),
        (still, GREY, "Still missed"),
    ):
        bw = w * n / 162
        pdf.set_fill_color(*col)
        pdf.rect(x, y, bw - 0.6, 9, "F")
        pdf.set_xy(x, y)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*((255, 255, 255) if col != GREY else INK))
        pdf.cell(bw, 9, str(n), align="C")
        x += bw
    pdf.set_y(y + 11)
    text(
        8.5,
        "Blue: found by the existing lineage check   Green: found by the detective   Grey: still missed (30 of 31 routed for human review; 1 silent miss)",
        MUTED,
    )
    pdf.ln(3)

    # Safety finding
    y = pdf.get_y()
    pdf.set_fill_color(251, 239, 238)
    pdf.rect(18, y, w, 19.5, "F")
    pdf.set_fill_color(179, 38, 30)
    pdf.rect(18, y, 1.2, 19.5, "F")
    pdf.set_xy(22, y + 2)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(156, 34, 25)
    pdf.multi_cell(
        w - 6, 4.6, "Remaining control-coverage risk", new_x="LMARGIN", new_y="NEXT"
    )
    pdf.set_x(22)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*INK)
    pdf.multi_cell(
        w - 6,
        4.4,
        _p(
            "1 of 162 affected key controls was neither recommended nor routed for review (C03, unresolved "
            "sanctions alerts, change CHG-024): the detective judged it not affected, and this version does not "
            "double-check those decisions. The other 30 misses were routed for human review."
        ),
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.set_y(y + 22.5)

    # Key lines
    lines = [
        (
            "It finds what the existing lineage check misses",
            f"{h['key_recovered']} of {h['key_misses']} missed key controls found, each with quoted evidence; 18 of 280 recommendations were wrong.",
        ),
        (
            "The extra items are mostly real impacts",
            "Without the detective these controls would still need checking, by tracing lineage gaps by hand or by missing them. Of the 406 items it adds, 331 are real impacts the lineage check missed; 75 are not affected and come with evidence to clear them.",
        ),
        (
            "Next: steadier decisions run to run",
            "Across five runs, 80% of key decisions were identical, against a 95% target.",
        ),
        (
            "Cost and speed",
            "About 70 model calls and a median of 11 minutes per change on a shared Free Edition endpoint.",
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
        ("Find >= 50% of missed key controls", "Met", "78.5% on unseen changes"),
        (
            "Review items added",
            "Reported",
            "406: 331 real impacts, 75 not affected",
        ),
        (
            "Tried with control owners in practice",
            "Not yet",
            "the proposed practitioner validation",
        ),
        ("Same key decision across 5 runs >= 95%", "Not met", "80%"),
    ):
        yy = pdf.get_y()
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(*INK)
        pdf.set_xy(18, yy)
        pdf.cell(w * 0.42, 6, _p(target))
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(
            *{"Met": (30, 107, 73), "Reported": MUTED, "Not yet": MUTED}.get(
                status, (156, 34, 25)
            )
        )
        pdf.cell(w * 0.14, 6, status)
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(*MUTED)
        pdf.cell(w * 0.44, 6, _p(detail))
        pdf.set_draw_color(*LINE)
        pdf.line(18, yy + 6.5, 18 + w, yy + 6.5)
        pdf.set_y(yy + 7.5)
    pdf.ln(3)

    # Decision
    pdf.set_fill_color(244, 246, 249)
    y = pdf.get_y()
    pdf.rect(18, y, w, 26, "F")
    pdf.set_fill_color(*BLUE)
    pdf.rect(18, y, 1.2, 26, "F")
    pdf.set_xy(22, y + 2.5)
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(*INK)
    pdf.multi_cell(
        w - 6, 5.2, "Options open to leadership", new_x="LMARGIN", new_y="NEXT"
    )
    pdf.set_x(22)
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(61, 71, 82)
    pdf.multi_cell(
        w - 6,
        5,
        _p(
            "A practitioner review of a sample of the detective's output, including controls it marked not affected; "
            "closing the gaps on the benchmark first (a five-run vote, a promote-only tie-break, a second check of "
            "not-affected key controls, each registered in advance); both; or stopping at the proof of concept."
        ),
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.set_y(282)
    text(
        8,
        "Synthetic benchmark: no real bank, customer or control data. Proof of concept, not in production.",
        MUTED,
    )
    return bytes(pdf.output())
