"""Control Impact Detective: a Databricks App that explains and evidences the POC.

Run locally:  streamlit run app/app.py   (reads RESULTS_ROOT, else the bundled copies)
On Databricks: deployed from the repository root; reads the results volume.

Reading order: Start here (the problem, how it works) is common to everyone; then
the Executive view (results, options) or the Technical view (data, evidence,
case explorer, architecture). Each page leads with its message (Minto).
"""

from __future__ import annotations

import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import content, data, synthetic, ui  # noqa: E402

st.set_page_config(
    page_title="Control Impact Detective",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)
ui.style()

GATE_RECOVERY, GATE_WORKLOAD, GATE_CONSISTENCY = 0.50, 0.25, 0.95
FROZEN_ON = "2026-10-19"

# ------------------------------------------------------------------ data


@st.cache_data(ttl=300, show_spinner="Reading run results from the volume…")
def load_runs():
    return data.available_runs()


@st.cache_data(ttl=300)
def load_consistency():
    return data.consistency()


@st.cache_data(ttl=3600, show_spinner="Building the answer key…")
def load_key():
    k = data.answer_key()
    return {"cases": k["cases"]}


@st.cache_data(ttl=300)
def load_case(folder, run, change_id):
    return data.case_result(folder, run, change_id)


def find_run(runs, kind):
    return next((r for r in runs if r["kind"] == kind), None)


def summary_of(run):
    """Pooled summary of the first finished run in a folder, or None."""
    if not run or not run["metrics"]:
        return None
    return run["metrics"][0].get("summary")


def pct(x, digits=1):
    return "–" if x is None else f"{100 * x:.{digits}f}%"


runs = load_runs()
frozen = summary_of(find_run(runs, "frozen"))
variant_b = summary_of(find_run(runs, "ab"))
heldout = summary_of(find_run(runs, "heldout"))
cons = load_consistency()

# Recorded fallbacks (docs/results.md) when the volume is unreachable.
RECORDED_FROZEN = {
    "cases": 8,
    "key_misses": 49,
    "key_recovered": 32,
    "key_miss_recovery": 32 / 49,
    "new_control_precision": 79 / 87,
    "baseline_workload": 38,
    "added_review_items": 169,
    "avoidable_review_items": 56,
    "avoidable_review_items_per_case": 7.0,
    "uncertain_controls": 82,
    "uninvestigated_controls": 2,
}
RECORDED_B = {
    "cases": 8,
    "key_misses": 49,
    "key_recovered": 27,
    "key_miss_recovery": 27 / 49,
    "new_control_precision": 1.0,
    "baseline_workload": 38,
    "added_review_items": 136,
    "avoidable_review_items": 46,
    "avoidable_review_items_per_case": 5.75,
    "uncertain_controls": 86,
    "uninvestigated_controls": 42,
}
RECORDED_CONS = {"key_pairs": 10, "agreement": 0.8, "target": 0.95}
RECORDED_HELDOUT = {
    "cases": 18,
    "key_misses": 144,
    "key_recovered": 113,
    "key_miss_recovery": 113 / 144,
    "new_control_precision": 262 / 280,
    "baseline_workload": 64,
    "added_review_items": 406,
    "avoidable_review_items": 75,
    "avoidable_review_items_per_case": 75 / 18,
    "review_queue_true_share": 0.8153,
    "uncertain_controls": 126,
    "uninvestigated_controls": 8,
}
frozen_live = frozen is not None and frozen.get("cases") == 8
F = frozen if frozen_live else RECORDED_FROZEN
if not variant_b or variant_b.get("cases") != 8:
    variant_b = RECORDED_B
if not cons:
    cons = RECORDED_CONS
if not heldout or heldout.get("cases") != 18:
    heldout = RECORDED_HELDOUT
H = heldout


def ab_decision():
    """Apply the pre-registered A/B rule, or explain why it cannot be applied yet."""
    if not variant_b or variant_b.get("cases") != 8:
        return None, "Variant B is still running on the eight cases."
    a_av, b_av = F.get("avoidable_review_items"), variant_b.get(
        "avoidable_review_items"
    )
    a_rec, b_rec = F["key_recovered"], variant_b["key_recovered"]
    if a_av is None or b_av is None:
        return None, "Avoidable-item counts are missing for one variant."
    ok_burden = b_av <= 0.7 * a_av
    ok_recall = b_rec >= a_rec - 3
    winner = "B" if ok_burden and ok_recall else "A"
    why = (
        f"Avoidable items {a_av} → {b_av} ({'≥30% fewer' if ok_burden else 'not 30% fewer'}); "
        f"key controls recovered {a_rec} → {b_rec} ({'within 3' if ok_recall else 'dropped by more than 3'})."
    )
    return winner, why


def results_summary_text():
    lines = [
        f"Frozen check (variant A, 8 unseen development cases): {F['key_recovered']} of {F['key_misses']} key misses recovered ({pct(F['key_miss_recovery'])}); precision {pct(F['new_control_precision'])}; {F['uncertain_controls']} UNCERTAIN; added review items {F['added_review_items']} vs baseline {F['baseline_workload']}; avoidable items {F.get('avoidable_review_items')}.",
    ]
    if variant_b:
        lines.append(
            f"Variant B on the same cases ({variant_b.get('cases')} done): {variant_b['key_recovered']} of {variant_b['key_misses']} recovered; precision {pct(variant_b.get('new_control_precision'))}; avoidable items {variant_b.get('avoidable_review_items')}."
        )
    w, why = ab_decision()
    lines.append(f"A/B decision: {'variant ' + w if w else 'pending'}. {why}")
    lines.append(
        f"Consistency (5 runs): {pct(cons.get('agreement')) + ' agreement on ' + str(cons.get('key_pairs')) + ' key pairs' if cons else 'still running'}."
    )
    lines.append(
        f"Held-out test: {str(heldout['key_recovered']) + ' of ' + str(heldout['key_misses']) + ' (' + pct(heldout['key_miss_recovery']) + ')' if heldout else 'not run yet'}."
    )
    lines.append(
        "Version C fresh-damage test (18 test changes, 30% random damage): 3-run vote of C recovered 49 of 93 (52.7%) vs A 46.5 (50.0%); "
        "unnecessary review items 0.33 vs 0.61 per change; precision 98.1%; two independent votes agreed on 94.4% of 162 key-control pairs "
        "(target 95%, not met); C not adopted, A stays. C costs about four times A's model calls."
    )
    lines.append(
        "Final bounded round (2026-10-18/19): variant D (A + tie-break) vs unchanged A on 5 fresh-damage development cases, 2 runs each: "
        "recovery 18 vs 20 of 32 key misses, unaffected review items 16 vs 30, undecided key controls 0 vs 0, repeatability 76% vs 76%. "
        "D not adopted; version A is final."
    )
    return "\n".join(lines)


# ------------------------------------------------------------------ diagrams

# ------------------------------------------------------------------ navigation helpers

PAGES: dict = {}


def nav_buttons(prev, nxt, next_label=None):
    """Back and next links at the foot of a page, so the reading path walks itself."""
    st.markdown('<div class="navbtns"></div>', unsafe_allow_html=True)
    left, _, right = st.columns([2, 1, 2])
    if prev and prev in PAGES:
        left.page_link(PAGES[prev], label=f"Back: {PAGES[prev].title.split('  ')[-1]}")
    if nxt and nxt in PAGES:
        right.page_link(
            PAGES[nxt], label=f"Next: {next_label or PAGES[nxt].title.split('  ')[-1]}"
        )


# ------------------------------------------------------------------ start here


def page_problem():
    ui.overview_css()
    T = ui.t
    ui.page_head(
        "Understand the problem",
        "Payment changes can silently break controls when the lineage map is incomplete",
        step="1 of 5",
    )
    st.markdown(
        '<div class="scq">'
        '<div><div class="s">Situation</div><p>Banks run about 100 controls on payments. Each depends on fields, '
        "rules and systems.</p></div>"
        f'<div><div class="s">Complication</div><p>The {T("lineage map")} linking them has gaps. With 30% missing, '
        f"the {T('current check')} finds only 11% of affected {T('key control')}s.</p></div>"
        '<div><div class="s">Question</div><p>Can an AI agent find what the check misses, and show its evidence?</p></div>'
        '<div class="answer"><div class="s">Answer, on synthetic data</div><p>Mostly yes: it finds 78% of what the '
        "check misses, and 94% of its recommendations are right. Not yet repeatable enough.</p></div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("### One change, traced")
    ui.broken_link_animation()
    with st.expander("Terms used in this dashboard"):
        st.dataframe(
            pd.DataFrame(content.GLOSSARY, columns=["Term", "Meaning"]),
            hide_index=True,
            use_container_width=True,
        )
    nav_buttons("overview", "how")


def page_how():
    ui.overview_css()
    ui.page_head(
        "Understand the problem",
        "The agent reads what a reviewer reads, and every finding is checked twice",
        step="2 of 5",
    )
    ui.flow_diagram()
    with st.expander("Show details: the safeguards and the agent's tools"):
        ui.keylines(
            [
                (
                    "It starts where the current check stops",
                    "It begins from the check's result and reads the ticket, the descriptions and the control procedures.",
                ),
                (
                    "Every finding is checked twice",
                    "Quotes must appear word for word; then an independent model call agrees or disagrees.",
                ),
                (
                    "Disagreements are routed to people",
                    "Disagreements go to a person with both arguments. Nothing is assumed safe.",
                ),
            ],
            [ui.BLUE, ui.GREEN, ui.AMBER],
        )
        st.dataframe(
            pd.DataFrame(
                [
                    ("trace_metadata", "Runs the current check on the visible links"),
                    (
                        "explore_node",
                        "Shows a field, rule or system with its visible links",
                    ),
                    ("search_controls", "Ranks control procedures by matching words"),
                    (
                        "inspect_control",
                        "Reads up to 15 procedures; required before a finding",
                    ),
                    (
                        "submit_findings",
                        "Up to 8 decisions with quotes, reason, counter-evidence",
                    ),
                    ("finish", "Stops; refused while controls are undecided"),
                ],
                columns=["Tool (read-only)", "What it does"],
            ),
            hide_index=True,
            use_container_width=True,
        )
    nav_buttons("problem", "case", "One change, end to end")


# ------------------------------------------------------------------ one case, end to end

HELDOUT_RUN = {
    "job": "862812162377923",
    "date": "16 Oct 2026",
    "version": "A",
    "code": "d149a52",
}


def provenance(kind="heldout"):
    """Where the numbers on this page come from, and that they are a replay."""
    r = find_run(runs, kind)
    live = bool(r and r.get("live"))
    source = (
        f"loaded from the results volume <code>{data.RESULTS_ROOT}</code>"
        if live
        else "recorded copy of the run files, shipped with this app"
    )
    st.markdown(
        f'<div class="prov"><b>Source</b> held-out run · Databricks job {HELDOUT_RUN["job"]} · '
        f'{HELDOUT_RUN["date"]} · version {HELDOUT_RUN["version"]} (code {HELDOUT_RUN["code"]}) · {source}. '
        "A replay of a finished evaluation, not a live run of the agent.</div>",
        unsafe_allow_html=True,
    )


def safety_finding():
    """The one affected key control that nobody would have looked at."""
    ui.callout(
        '<span class="tag">Remaining control-coverage risk</span>'
        "<b>1 of the 162 affected key controls was neither recommended nor routed for review:</b> "
        "Unresolved sanctions alerts are reviewed (C03), on a screening field-set change (CHG-024). The agent "
        "marked it not affected. The 78% headline does not cover it; in a production workflow this is the kind "
        "of impact that would reach release unchecked. The other 30 misses were routed for human review, so "
        "their safety depends on those items being worked.",
        "risk",
    )


def misses_breakdown():
    """What happened to the 31 key controls neither the check nor the agent recommended."""
    ui.segbar(
        [
            (
                None,
                [
                    (
                        30,
                        "<b>30 routed for human review</b> the agent said affected; its independent checker "
                        "was not sure. No reviewer worked them in this POC.",
                        ui.AMBER,
                        False,
                    ),
                    (
                        1,
                        "<b>1 silent miss</b>",
                        ui.RED,
                        False,
                    ),
                ],
            )
        ],
        31,
    )
    st.markdown(
        '<p class="small">The one silent miss: <b>Unresolved sanctions alerts are reviewed</b> (C03) on a '
        "screening field-set change (CHG-024), marked not affected. By change type, the 31 are screening engine "
        "15, creditor town name 9, screening field set 7. For safety, review items must be worked, not "
        "skipped: they hold 30 of the 31 remaining impacts.</p>",
        unsafe_allow_html=True,
    )


def investigation_workbench():
    """User-directed, evidence-backed investigation of the recorded CHG-027 run."""
    st.markdown(
        '<div class="section-index"><span>LIVE INTERACTION / RECORDED CASE</span>'
        '<span>SELECT WHAT TO INSPECT</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown("### Investigate CHG-027 yourself")
    st.caption(
        "Switch between the intact reference map, the degraded lineage the rules check received, "
        "and the recovered agent view. The graph is regenerated on selection; this is a recorded "
        "synthetic case, not a new model inference."
    )
    mode = st.radio(
        "Investigation state",
        ["Complete reference", "Broken lineage", "Agent investigation"],
        index=1, horizontal=True, key="investigation_mode",
    )
    mode = mode or "Broken lineage"
    if mode == "Complete reference":
        overlay, explanation = "complete", (
            "Reference state: all affected relationships exist in the synthetic answer key. "
            "This is evaluation ground truth, not a view the baseline had access to."
        )
    elif mode == "Broken lineage":
        overlay, explanation = "damaged", (
            "Rules-only view: correlated lineage damage hides the engine-to-control relationships. "
            "The baseline reports zero of 20 affected controls for this change."
        )
    else:
        overlay, explanation = "overlay", (
            "The red dashed edges show what was missing in lineage, not newly written links. "
            "The recorded agent recommended all 20 affected controls by reading documents; "
            "select a control below to inspect the evidence. Human review was not performed."
        )
    st.info(explanation)
    # The existing graph generator uses the same deterministic CHG-027 synthetic fixture.
    # Keep the state transitions explicit rather than autoplaying a diagram.
    try:
        st.graphviz_chart(
            syn_dot("CHG-027", 30, "correlated", overlay, True),
            use_container_width=True,
        )
    except Exception as exc:
        st.warning(f"Graph unavailable ({type(exc).__name__}); use the case evidence below.")
    run = find_run(runs, "heldout")
    result = data.case_result(run["folder"], "run1", "CHG-027") if run else None
    findings = (result or {}).get("verified_findings", [])
    if not findings:
        st.caption("Recorded findings are not available in this deployment.")
        return
    ids = sorted({f.get("control_id") for f in findings if f.get("control_id")})
    control = st.selectbox("Inspect a control and its recorded evidence", ids, index=ids.index("C02") if "C02" in ids else 0)
    finding = next(f for f in findings if f.get("control_id") == control)
    left, right = st.columns([1, 1], gap="large")
    with left:
        st.markdown("**Source evidence**")
        st.markdown("Change ticket")
        st.info(finding.get("ticket_quote") or "No ticket quote recorded")
        st.markdown("Control procedure")
        st.info(finding.get("control_quote") or "No control quote recorded")
    with right:
        st.markdown("**Investigator assessment**")
        st.write(finding.get("proposer_causal_reason") or finding.get("causal_reason") or "No rationale recorded")
        st.markdown("**Independent check**")
        st.write(finding.get("causal_reason") or "No checker rationale recorded")
        st.caption("Recorded model output, not a completed practitioner review.")


def page_case():
    ui.overview_css()
    ex = synthetic.example("CHG-027")
    res = None
    r = find_run(runs, "heldout")
    if r:
        res = data.case_result(r["folder"], "run1", "CHG-027")
    ui.page_head(
        "Understand the problem",
        "One change, end to end: the check finds none of 20 affected controls; the agent finds all 20",
        step="3 of 5",
        synthetic=True,
    )
    st.markdown(
        '<div class="verdict-strip"><div class="verdict-primary">'
        '<span>CHG-027 / SCREENING INTERFACE CHANGE</span>'
        '<strong>0 → 20 <small>of 20</small></strong>'
        '<p>The lineage-only check sees no affected controls. '
        'The recorded agent identifies all 20; each recommendation remains subject '
        'to practitioner review.</p></div>'
        '<div class="verdict-secondary">'
        '<b>01</b><span>Change request</span>'
        '<b>02</b><span>Broken engine-to-control links</span>'
        '<b>03</b><span>Document evidence and recommendation</span>'
        '</div></div>',
        unsafe_allow_html=True,
    )
    investigation_workbench()
    ui.legend(
        [
            ("Changed item", "#F0997B"),
            ("Affected control", "#ED93B1"),
            ("Link missing from the map the check uses", ui.RED),
        ]
    )
    st.markdown("### A recommendation you can audit")
    f = next(
        (
            v
            for v in (res or {}).get("verified_findings", [])
            if v["control_id"] == "C02"
        ),
        None,
    )
    doc = next(d for d in ex["case"]["control_documents"] if d["control_id"] == "C02")
    if f:
        ui.score_table(
            [
                (
                    "Control",
                    "Payment parties are sanctions screened before release (C02, key)",
                ),
                ("Quote from the ticket", f"“{ui.esc(f['ticket_quote'])}”"),
                (
                    "Quote from the procedure",
                    f"“{ui.esc(f['control_quote'])}” <span style='color:#5B6675'>— full text: "
                    f"{ui.esc(doc['text'])}</span>",
                ),
                (
                    "Agent's reason",
                    ui.esc(f.get("proposer_causal_reason") or f["causal_reason"]),
                ),
                ("Independent checker", "Agreed: " + ui.esc(f["causal_reason"])),
                (
                    "Decision",
                    ui.badge("Recommended", "ok") + " &nbsp;Answer key: affected",
                ),
                (
                    "Proposed reviewer action",
                    "Re-test the control against the changed interface before release. Not performed in this POC: the benchmark shows the recommendation, not a completed review.",
                ),
            ]
        )
    st.markdown("### Inspect the reviewer handoff")
    good, hard = st.tabs(
        ["This change (CHG-027)", "Hardest type: screening engine change (CHG-015)"]
    )
    for tab, cid in ((good, "CHG-027"), (hard, "CHG-015")):
        with tab:
            rr = data.case_result(r["folder"], "run1", cid) if r else None
            if rr:
                reviewer_queue(
                    data.decisions_table(rr), compact=True, key=f"case_{cid}"
                )
    with st.expander("Show details: every step the agent took on CHG-027"):
        if res:
            st.dataframe(
                pd.DataFrame(data.step_rows(res)),
                hide_index=True,
                use_container_width=True,
            )
    provenance()
    nav_buttons("how", "results")


# ------------------------------------------------------------------ executive

PER_CHANGE = {
    "today": 64 / 18,
    "real": 331 / 18,
    "unaffected": 75 / 18,
    "calls": 1280 / 18,
    "minutes_median": 11,
}


# ------------------------------------------------------------------ shared visuals


def key_controls_bar(agent=True, height=70):
    """Where the 162 affected key controls ended up (or, without the agent, what the current check finds)."""
    rules_found = 162 - H["key_misses"]
    if agent:
        rows = [
            ("Found by the current check", rules_found, ui.BLUE),
            ("Found by the agent", H["key_recovered"], ui.GREEN),
            ("Still missed", H["key_misses"] - H["key_recovered"], ui.GREY),
        ]
    else:
        rows = [
            ("Found by the current check", rules_found, ui.BLUE),
            ("Missed by the current check", H["key_misses"], ui.GREY),
        ]
    parts = pd.DataFrame(
        [{"part": p, "n": n, "o": i + 1} for i, (p, n, _) in enumerate(rows)]
    )
    colors = [c for _, _, c in rows]
    last = len(rows)
    bar = (
        alt.Chart(parts)
        .mark_bar(size=height - 14, stroke="white", strokeWidth=3)
        .encode(
            x=alt.X(
                "n:Q",
                stack="zero",
                axis=None,
                scale=alt.Scale(domain=[0, 162], nice=False),
            ),
            color=alt.Color(
                "part:N",
                scale=alt.Scale(domain=list(parts["part"]), range=colors),
                legend=None,
            ),
            order=alt.Order("o:Q"),
            tooltip=[
                alt.Tooltip("part", title=""),
                alt.Tooltip("n", title="Key controls"),
            ],
        )
    )
    text = (
        alt.Chart(parts)
        .transform_window(end="sum(n)", sort=[alt.SortField("o")])
        .transform_calculate(mid="datum.end - datum.n / 2")
        .mark_text(
            fontSize=18,
            fontWeight=600,
            font="IBM Plex Sans, Helvetica, Arial, sans-serif",
        )
        .encode(
            x="mid:Q",
            text="n:Q",
            color=alt.condition(
                f"datum.o == {last}", alt.value(ui.INK), alt.value("white")
            ),
        )
    )
    st.altair_chart(
        (bar + text).properties(height=height).configure_view(strokeWidth=0),
        use_container_width=True,
    )
    ui.legend([(p, c) for p, _, c in rows])


def reviewer_chart():
    """Items a reviewer gets per change: today vs with the agent, labelled at the end."""
    domain = [
        "From the current check",
        "Real impacts the check missed",
        "Not affected (overhead)",
    ]
    colors = [ui.BLUE, ui.GREEN, ui.GREY]
    p = PER_CHANGE
    per = pd.DataFrame(
        [
            {"row": "Today", "part": domain[0], "n": p["today"], "o": 1},
            {"row": "With the agent", "part": domain[0], "n": p["today"], "o": 1},
            {"row": "With the agent", "part": domain[1], "n": p["real"], "o": 2},
            {"row": "With the agent", "part": domain[2], "n": p["unaffected"], "o": 3},
        ]
    )
    totals = pd.DataFrame(
        [
            {"row": "Today", "x": p["today"], "t": f"  about {p['today']:.0f} items"},
            {
                "row": "With the agent",
                "x": p["today"] + p["real"] + p["unaffected"],
                "t": f"  about {p['today'] + p['real'] + p['unaffected']:.0f} items",
            },
        ]
    )
    y = alt.Y(
        "row:N",
        sort=["Today", "With the agent"],
        title=None,
        axis=alt.Axis(
            labelFont="IBM Plex Sans, Helvetica, Arial",
            labelFontSize=14,
            labelColor=ui.INK,
            domain=False,
            ticks=False,
            labelPadding=10,
        ),
    )
    bars = (
        alt.Chart(per)
        .mark_bar(size=30, stroke="white", strokeWidth=2)
        .encode(
            y=y,
            x=alt.X(
                "n:Q",
                stack="zero",
                axis=None,
                scale=alt.Scale(domain=[0, 48], nice=False),
            ),
            color=alt.Color(
                "part:N", scale=alt.Scale(domain=domain, range=colors), legend=None
            ),
            order=alt.Order("o:Q"),
            tooltip=[
                alt.Tooltip("part", title=""),
                alt.Tooltip("n", format=".1f", title="Items"),
            ],
        )
    )
    labels = (
        alt.Chart(totals)
        .mark_text(
            align="left",
            fontSize=14,
            font="IBM Plex Sans, Helvetica, Arial, sans-serif",
            color=ui.INK,
        )
        .encode(y=y, x="x:Q", text="t:N")
    )
    st.altair_chart(
        (bars + labels).properties(height=110).configure_view(strokeWidth=0),
        use_container_width=True,
    )
    ui.legend(list(zip(domain, colors)))


def brief_box():
    st.markdown(
        '<div class="brief"><div class="bt">In one minute</div><dl>'
        "<dt>What works</dt><dd>On synthetic test data, the agent found <b>113 of the 144</b> important controls "
        "today's automated check missed, and <b>94%</b> of what it recommended was right.</dd>"
        "<dt>What is not ready</dt><dd>Its decisions are <b>80%</b> repeatable (target 95%), and it adds about "
        "<b>4</b> unaffected items per change for reviewers. It has not yet been tried on real data, and no "
        "reviewer has worked its output.</dd>"
        "<dt>Remaining coverage risk</dt><dd><b>1 of 162</b> affected key controls was neither recommended nor "
        "routed for review.</dd>"
        "<dt>What is open</dt><dd>A practitioner review, closing the two gaps first, both, or stopping here.</dd>"
        "</dl></div>",
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------ overview


def page_overview():
    """A single client conversation, with proof available on demand."""
    ui.overview_css()
    st.markdown(
        '<div class="case-masthead"><span>PAYMENTS / CONTROL EXPOSURE</span>'
        '<span>INTERACTIVE CLIENT BRIEF · SYNTHETIC STUDY</span></div>'
        '<div class="investigation-hero">'
        '<div class="hero-eyebrow">THE INVISIBLE CONTROL</div>'
        '<div class="hero-h">Your payment change looks safe. Is it?</div>'
        '<p class="hero-deck">One missing dependency can hide a control that needs to be '
        'assessed before release. Explore how the blind spot appears — and how evidence '
        'can bring it back into view.</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-index"><span>01 / EXPLORE THE FAILURE</span>'
        '<span>CHOOSE WHAT THE INVESTIGATOR SEES</span></div>',
        unsafe_allow_html=True,
    )
    ui.broken_link_animation(height=370)
    st.markdown(
        '<div class="section-index"><span>02 / THE RESULT</span>'
        '<span>18 HELD-OUT CHANGES · 30% CORRELATED LINEAGE LOSS</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="verdict-strip"><div class="verdict-primary">'
        '<span>AFFECTED KEY-CONTROL INSTANCES IDENTIFIED</span>'
        '<strong>18 → 131 <small>of 162</small></strong>'
        '<p>Existing lineage-only check versus the AI-assisted investigation. '
        'The agent recovered 113 impacts the original check missed.</p></div>'
        '<div class="verdict-secondary">'
        '<b>331</b><span>new genuine review findings</span>'
        '<b>75</b><span>unaffected additional review items</span>'
        '<b>1</b><span>affected key control still silently missed</span>'
        '</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-index"><span>03 / THE DECISION</span>'
        '<span>WHAT SHOULD THE CLIENT DO NEXT?</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown('### Validate with control owners before a pilot.')
    st.write(
        'The synthetic result supports a limited practitioner evaluation, not deployment. '
        'Review the remaining silent miss, measure consistency and time real investigations '
        'before making a cost-saving claim.'
    )
    a, b, c = st.columns(3)
    with a:
        st.page_link(PAGES['case'], label='Explore the evidence →')
    with b:
        st.page_link(PAGES['synthetic'], label='Test the degradation →')
    with c:
        st.page_link(PAGES['decision'], label='Evaluate the pilot decision →')
    with st.expander('Study conditions, limitations and run provenance'):
        st.caption(
            'Recorded synthetic evaluation, not live banking data. '
            'No completed practitioner review, measured savings or production approval.'
        )
        provenance()


# ------------------------------------------------------------------ present


SLIDES = 7


def _slide_head(i, title, sub):
    dots = "".join(
        f'<span class="{"on" if j <= i else ""}"></span>' for j in range(SLIDES)
    )
    st.markdown(
        f'<div class="slide-meta"><span>{i + 1} of {SLIDES} &nbsp;·&nbsp; Synthetic benchmark data</span>'
        f'<span class="dots">{dots}</span></div>'
        f'<div class="slide-h">{title}</div><p class="slide-s">{sub}</p>',
        unsafe_allow_html=True,
    )


def page_present():
    ui.overview_css()
    i = st.session_state.setdefault("slide", 0)
    if i == 0:
        _slide_head(
            0,
            "Payment changes can silently break controls",
            "Each change must be checked against every control it could affect. One missing link in the map, "
            "and today's automated check never reaches the control.",
        )
        ui.broken_link_animation()
    elif i == 1:
        _slide_head(
            1,
            "With 30% of the links missing, today's check finds 11% of what a change affects",
            "Across 18 test changes, 162 important controls were affected. The check found 18.",
        )
        key_controls_bar(agent=False, height=90)
    elif i == 2:
        _slide_head(
            2,
            "The agent reads what a reviewer would read, and every finding is checked twice",
            "It works from the change ticket and the control procedures, not only the map. Disagreements go to a person.",
        )
        ui.flow_diagram()
    elif i == 3:
        _slide_head(
            3,
            "It finds 113 of the 144 the check misses, and 94% of what it recommends is right",
            "Tested on changes it had never seen, with its design frozen beforehand.",
        )
        key_controls_bar(agent=True, height=90)
    elif i == 4:
        _slide_head(
            4,
            "A reviewer would get more to look at, and most of it is real",
            "About 26 items per change instead of 4: about 18 are real impacts that were being missed, about 4 are not affected.",
        )
        reviewer_chart()
    elif i == 5:
        _slide_head(
            5,
            "Two things are not good enough yet",
            "Both were measured against targets set before the tests.",
        )
        st.markdown(
            '<div class="gaps">'
            '<div class="gap"><div class="v">80% <small>target 95%</small></div><p><b>Repeatability.</b> Run the same '
            "change five times: four in five important decisions come out the same. A three-run vote reached 94.4%.</p></div>"
            '<div class="gap"><div class="v">4.2 <small>per change</small></div><p><b>Unaffected items for review.</b> '
            "Alongside about 18 real finds per change. A tie-break step cut these but also dismissed some real ones.</p></div>"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        _slide_head(
            6,
            "The options open from here",
            "The evidence is from synthetic data; the choice of next step rests with leadership.",
        )
        st.markdown(
            '<div class="opts">'
            '<div class="opt"><div class="h">Practitioner review</div><p>Control owners judge a sample of real '
            "output. Two or three people, a few hours.</p></div>"
            '<div class="opt"><div class="h">Close the two gaps</div><p>A five-run vote and a promote-only tie-break, '
            "registered in advance, tested on new changes.</p></div>"
            '<div class="opt"><div class="h">Both</div><p>Independent: the review uses existing output; the fixes '
            "use new runs.</p></div>"
            '<div class="opt"><div class="h">Stop here</div><p>Keep the benchmark, code and results as documented.</p></div>'
            "</div>",
            unsafe_allow_html=True,
        )
    st.markdown('<div class="navbtns"></div>', unsafe_allow_html=True)
    a, b, _, c = st.columns([1, 1, 2, 1.4])
    if a.button("Back", disabled=i == 0, use_container_width=True):
        st.session_state.slide = i - 1
        st.rerun()
    if i < SLIDES - 1:
        if b.button("Next", type="primary", use_container_width=True):
            st.session_state.slide = i + 1
            st.rerun()
    elif b.button("Start again", use_container_width=True):
        st.session_state.slide = 0
        st.rerun()
    c.page_link(PAGES["overview"], label="Leave the presentation")


# ------------------------------------------------------------------ results and options


def page_results():
    ui.overview_css()
    T = ui.t
    ui.page_head(
        "Results and options",
        "The agent finds four in five controls the current check misses",
        f"18 synthetic payment changes it had never seen ({T('held-out')}), 30% of the {T('lineage map')} "
        "removed, original agent frozen before the test.",
        step="4 of 5",
        synthetic=True,
    )
    st.markdown(
        '<div class="section-index"><span>EXECUTIVE VERDICT / WHAT CHANGED</span>'
        '<span>HELD-OUT SYNTHETIC EVALUATION</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="verdict-strip"><div class="verdict-primary">'
        '<span>KEY CONTROL COVERAGE</span><strong>18 → 131 <small>of 162</small></strong>'
        '<p>Baseline rules found 18 affected key controls. The agent recovered 113 more.</p></div>'
        '<div class="verdict-secondary"><b>331</b><span>new genuine impacts surfaced</span>'
        '<b>75</b><span>unaffected items added to review</span>'
        '<b>1</b><span>affected key control not surfaced or routed</span></div></div>',
        unsafe_allow_html=True,
    )
    with st.expander("Full diagnostic metrics"):
        ui.kpis(
            [
            (
                pct(H["key_miss_recovery"], 0),
                f"of missed {T('key control')}s found",
                "Target 50%",
            ),
            (
                pct(H["new_control_precision"], 0),
                f"of {T('recommended')} controls right",
                "262 of 280",
            ),
            ("18.5%", "unaffected share of added items", "75 of 406; true impacts excluded"),
            (pct(cons["agreement"], 0), "same decision across 5 runs", "Target 95%"),
            ]
        )
    safety_finding()
    ui.chart_title(
        f"The agent finds {H['key_recovered']} of the {H['key_misses']} important controls the check misses",
        "All 162 important controls affected by the 18 test changes. 30 of the 31 still missed were routed for human review; 1 was not surfaced.",
    )
    key_controls_bar(agent=True, height=78)
    ui.chart_title(
        "What happened to the 31 still missed",
        "Neither the check nor the agent recommended them.",
    )
    misses_breakdown()
    ui.chart_title(
        "A reviewer would get about 26 items per change instead of 4; about 18 of them are real impacts",
        "Average over the 18 test changes.",
    )
    reviewer_chart()
    st.markdown("### Evaluation standards and decision")
    ui.score_table(
        [
            (
                "Find ≥ 50% of missed key controls",
                ui.badge("Met", "ok"),
                "78.5% on unseen changes.",
            ),
            (
                "Same key decision across 5 runs ≥ 95%",
                ui.badge("Not met", "bad"),
                f"{pct(cons['agreement'], 0)}. How much it found was stable; which items were routed for review varied.",
            ),
            (
                "Avoidable-review share: 75 of 406 added items (18.5%)",
                ui.badge("Observed; pilot target pending", "warn"),
                "This is the meaningful efficiency metric. The original ≤25% total-added-volume gate "
                "was flawed and is archived for audit; the future acceptance limit needs agreement before retesting.",
            ),
        ]
    )
    with st.expander("Before quoting these numbers"):
        ui.score_table(
            [
                (
                    "Synthetic data",
                    "An invented bank's payments, built so every right answer is known.",
                ),
                (
                    "Compared with the automated check",
                    "Not with an experienced reviewer; that is not measured yet.",
                ),
                (
                    "30% of the map removed",
                    "A stress level fixed in advance. At 60% the current check finds 7%.",
                ),
                (
                    "Cost and speed",
                    f"About {PER_CHANGE['calls']:.0f} model calls and a median of {PER_CHANGE['minutes_median']} "
                    "minutes per change on a shared endpoint.",
                ),
                (
                    "Review volume target",
                    "Original target retained for audit. Proposed future measure: unaffected share of additional items "
                    "(75/406 = 18.5%), with an acceptance threshold agreed before the next evaluation. "
                    "This is not a retrospective pass. Reviewer time was not measured.",
                ),
                (
                    "Final version",
                    "The original agent (A). Three alternatives were tested against rules written in advance; none was adopted.",
                ),
            ]
        )
    provenance()
    download_summary()
    nav_buttons("case", "decision")


def download_summary():
    from app import onepager

    try:
        pdf = onepager.build(H, cons, FROZEN_ON)
    except Exception:  # fpdf2 missing in an old deployment
        return
    st.download_button(
        "Download one-page summary (PDF)",
        pdf,
        file_name="control-impact-poc-summary.pdf",
        mime="application/pdf",
    )


def executive_value_case():
    """Compare rules baseline with agent review capacity, not invented ROI."""
    st.markdown("### Executive value case | Baseline versus AI-assisted review")
    st.caption(
        "Scenario extrapolated from 18 synthetic changes; not measured staff time or ROI. "
        "Baseline = existing rules-based lineage check (64 review items / 18 changes)."
    )
    c1, c2, c3 = st.columns(3)
    changes = c1.number_input("Changes assessed per month", min_value=1, max_value=10000, value=100, step=10)
    minutes = c2.number_input("Minutes per review item (assumption)", min_value=1, max_value=240, value=5)
    rate = c3.number_input("Fully loaded reviewer cost ($/hour)", min_value=1, max_value=1000, value=75, step=5)
    baseline_items = changes * 64 / 18
    useful_items = changes * 331 / 18
    avoidable_items = changes * 75 / 18
    assisted_items = baseline_items + useful_items + avoidable_items
    baseline_hours = baseline_items * minutes / 60
    useful_hours = useful_items * minutes / 60
    avoidable_hours = avoidable_items * minutes / 60
    assisted_hours = assisted_items * minutes / 60
    st.markdown("#### Like-for-like review workload")
    left, right = st.columns(2)
    with left:
        st.metric("Baseline hours / month", f"{baseline_hours:,.1f}")
        st.metric("Baseline labor / month", f"${baseline_hours * rate:,.0f}")
    with right:
        st.metric("AI-assisted hours / month", f"{assisted_hours:,.1f}")
        st.metric("AI-assisted labor / month", f"${assisted_hours * rate:,.0f}")
    st.markdown("#### What explains the difference?")
    st.markdown(
        f"- **Existing review:** {baseline_items:,.0f} items, "
        f"{baseline_hours:,.1f} hours, ${baseline_hours * rate:,.0f} labor.\n"
        f"- **New genuine impacts:** {useful_items:,.0f} items, "
        f"{useful_hours:,.1f} hours, ${useful_hours * rate:,.0f} labor. "
        "Necessary control work, **not avoidable overhead**.\n"
        f"- **Unaffected additional items:** {avoidable_items:,.0f} items, "
        f"{avoidable_hours:,.1f} hours, ${avoidable_hours * rate:,.0f} labor. "
        "Potentially avoidable overhead."
    )
    st.caption(
        "A lower baseline review cost reflects fewer items being surfaced, including missed "
        "real impacts; it does not prove better efficiency. These totals exclude investigation "
        "time, model serving costs, integration costs and prevented incidents. "
        "Net savings or ROI cannot be inferred without a timed practitioner pilot."
    )


def delivery_readiness():
    """Stakeholder-oriented assessment: evidence, ownership and client readiness."""
    st.markdown(
        '<div class="section-index"><span>DELIVERY ASSESSMENT</span>'
        '<span>BEYOND A MODEL DEMO</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown("### What a project reviewer should be able to verify")
    st.caption(
        "These are practical review dimensions, not official WorldLink scores or "
        "comparisons with other interns. Every claim points to POC evidence or an explicit gap."
    )
    items = [
        ("01 / CLIENT PROBLEM", "A decision worth making",
         "A payments change can affect controls outside incomplete lineage. "
         "The proposed decision is whether to pilot AI-assisted control-impact discovery.",
         "Defined problem and buyer; client-specific workflow not validated."),
        ("02 / ENGINEERING OWNERSHIP", "Built beyond a prompt",
         "Deterministic baseline, synthetic benchmark, documented agent path, "
         "recorded runs and reproducible evaluation.",
         "Reproducibility documented; deployed runtime still needs a walkthrough."),
        ("03 / EVALUATION", "Measured against a baseline",
         "18 held-out changes, 162 affected key-control instances, "
         "113 of 144 baseline misses recovered; 75 of 406 added items unaffected.",
         "One silent miss; 80% repeatability versus 95% original target."),
        ("04 / GOVERNANCE", "Evidence before automation",
         "Cited source passages, independent checker and reviewer routing. "
         "No automatic clearance or claim of completed human validation.",
         "Real practitioner acceptance and model-risk approval outstanding."),
        ("05 / OPERATIONAL VALUE", "Cost and adoption",
         "A transparent baseline-versus-assisted workload scenario, "
         "with necessary true-positive work separated from avoidable review.",
         "Actual minutes, model spend, savings and ROI not measured."),
        ("06 / CLIENT READINESS", "A defensible next decision",
         "Inspectable example, architecture, limitations and next-step options "
         "for an executive, architect and control owner.",
         "Needs realistic client data and practitioner sign-off before a pilot decision."),
    ]
    for number, heading, evidence, gap in items:
        with st.expander(f"{number}  —  {heading}", expanded=False):
            st.markdown(f"**Evidence:** {evidence}")
            st.markdown(f"**Remaining gap:** {gap}")
    st.markdown(
        "**Recommended next decision:** authorize a limited practitioner validation "
        "of existing recorded findings, with timed reviews and a documented silent-miss "
        "assessment. Do not treat this synthetic benchmark as client acceptance."
    )


def page_decision():
    ui.overview_css()
    ui.page_head(
        "Results and options",
        "Two gaps remain; four options are open",
        "The choice of next step rests with leadership.",
        step="5 of 5",
        synthetic=True,
    )
    st.markdown(
        '<div class="gaps">'
        '<div class="gap"><div class="v">80% <small>target 95%</small></div><p><b>Repeatability.</b> Four in five '
        "important decisions are the same across five runs. A three-run vote reached 94.4%.</p></div>"
        '<div class="gap"><div class="v">4.2 <small>per change</small></div><p><b>Unaffected items for review</b>, '
        "alongside about 18 real finds. Not yet tried on real data or judged by control owners.</p></div>"
        "</div>",
        unsafe_allow_html=True,
    )
    executive_value_case()
    st.markdown("### Options")
    st.markdown(
        '<div class="opts">'
        '<div class="opt"><div class="h">Practitioner review</div><p>Control owners judge a sample of the agent\'s '
        "output. Two or three people, a few hours. Answers whether it is right and useful in practice.</p></div>"
        '<div class="opt"><div class="h">Close the two gaps</div><p>A five-run vote for repeatability and a tie-break '
        "that may only promote findings (68 of 70 promotions were right). Model capacity only.</p></div>"
        '<div class="opt"><div class="h">Both</div><p>Independent of each other: the review uses existing output; '
        "the fixes use new runs.</p></div>"
        '<div class="opt"><div class="h">Stop here</div><p>Keep the benchmark, code and results as documented. '
        "Nothing runs in production.</p></div>"
        "</div>",
        unsafe_allow_html=True,
    )
    delivery_readiness()
    st.markdown("### Demonstrated so far, and what production would need")
    st.markdown(
        '<div class="ready">'
        "<div><h4>Demonstrated in this proof of concept</h4><ul>"
        "<li>Runs end to end on Databricks, every step logged</li>"
        "<li>Finds 78% of the key impacts the lineage check misses, on unseen synthetic changes</li>"
        "<li>Cites exact quotes; a second model call checks each finding</li>"
        "<li>Sends disagreements to a person; never assumes a control is safe</li></ul></div>"
        "<div><h4>Not yet demonstrated</h4><ul>"
        "<li>Accuracy on real changes and real control documents</li>"
        "<li>Usefulness to control owners, and reviewer time</li>"
        "<li>Repeatability at 95%</li>"
        "<li>Behaviour at other levels of lineage completeness on real data</li></ul></div>"
        "<div><h4>Needed before production</h4><ul>"
        "<li>Access to real change tickets, lineage and procedures</li>"
        "<li>Model-risk review and approval</li>"
        "<li>Integration with the change process and an audit trail</li>"
        "<li>Monitoring of accuracy and drift over time</li></ul></div>"
        "</div>",
        unsafe_allow_html=True,
    )
    with st.expander("Known limits"):
        ui.score_table(
            [
                (
                    ui.esc(i),
                    f"{ui.esc(e)}<br><span style='color:#5B6675'>{ui.esc(r)}</span>",
                )
                for i, e, r in content.LIMITS
            ]
        )
    download_summary()
    nav_buttons("results", "synthetic", "Technical detail: the synthetic data")


# ------------------------------------------------------------------ technical: evidence


def page_evidence():
    ui.page_head(
        "Technical view",
        "Every result comes from a run with rules fixed in advance",
        "Development results are labelled as such. Only the held-out run is the headline.",
        synthetic=True,
    )
    st.markdown("### Main runs")
    table = []
    for r in runs:
        s = summary_of(r)
        if not s:
            continue
        table.append(
            {
                "Run": r["label"],
                "Changes": s.get("cases"),
                "Key misses recovered": f"{s['key_recovered']} of {s['key_misses']}",
                "Recovery": pct(s.get("key_miss_recovery")),
                "Precision": pct(s.get("new_control_precision")),
                "For review": s.get("uncertain_controls"),
                "Unaffected items": s.get("avoidable_review_items"),
            }
        )
    st.dataframe(pd.DataFrame(table), hide_index=True, use_container_width=True)

    st.markdown("### By change")
    options = [r for r in runs if r["kind"] in ("heldout", "frozen") and r["metrics"]]
    if options:
        pick = st.radio(
            "Run",
            [r["label"] for r in options],
            horizontal=True,
            label_visibility="collapsed",
        )
        fr = options[[r["label"] for r in options].index(pick)]
        chart = per_case_chart(fr["metrics"][0])
        if chart is not None:
            st.altair_chart(chart, use_container_width=True)
            ui.legend([("Recovered by the agent", ui.GREEN), ("Still missed", ui.GREY)])
        st.caption(
            "Changes where the current check already found every key control are not shown."
        )

    st.markdown("### Versions tested to close the two gaps")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Version": "Stricter evidence rule (B)",
                    "Test": "8 unseen development changes",
                    "Rule fixed in advance": "Unaffected items ≥ 30% fewer; recovery within 3",
                    "Result": "Unaffected 56 → 46 (−18%); recovered 32 → 27",
                    "Decision": "Not adopted",
                },
                {
                    "Version": "Extra checks + three-run vote (C)",
                    "Test": "18 test changes, fresh random damage",
                    "Rule fixed in advance": "Two votes agree ≥ 95%; recovery ≥ 50%; unaffected ≤ 3 per change",
                    "Result": "Agree 94.4% (needed 95%); recovery 52.7%; unaffected 0.33 per change; ≈ 4× cost",
                    "Decision": "Not adopted",
                },
                {
                    "Version": "Tie-break step (D)",
                    "Test": "5 fresh development changes, 2 runs each",
                    "Rule fixed in advance": "Recovery ≥ A; unaffected ≤ A; repeatability ≥ A",
                    "Result": "Recovered 18 vs 20 of 32; unaffected 16 vs 30",
                    "Decision": "Not adopted",
                },
                {
                    "Version": "Tie-break on saved runs (A + tie-break)",
                    "Test": "7 saved runs, paired",
                    "Rule fixed in advance": "≤ 10% of truly affected review items dismissed",
                    "Result": "Recovered 258 → 267 of 411; unaffected −38%; 21.8% dismissed",
                    "Decision": "Not adopted",
                },
            ]
        ),
        hide_index=True,
        use_container_width=True,
    )
    with st.expander("Repeatability: three changes, five runs"):
        cr = find_run(runs, "consistency")
        if cr and cr["metrics"]:
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Run": i + 1,
                            "Key misses recovered": f"{m['summary']['key_recovered']} of {m['summary']['key_misses']}",
                            "Precision": pct(m["summary"].get("new_control_precision")),
                            "For review": m["summary"].get("uncertain_controls"),
                            "Unaffected items": m["summary"].get(
                                "avoidable_review_items"
                            ),
                        }
                        for i, m in enumerate(cr["metrics"])
                    ]
                ),
                hide_index=True,
                use_container_width=True,
            )
        st.markdown(
            f"Identical recommend / not-recommend decisions on {pct(cons['agreement'], 0)} of "
            f"{cons['key_pairs']} affected key controls (target 95%)."
        )
    nav_buttons("synthetic", "explorer")


# ------------------------------------------------------------------ technical: architecture


def page_architecture():
    ui.page_head(
        "Technical view",
        "Everything runs in one Databricks workspace; the answer key never reaches the model",
        "How the parts fit, and how to reproduce any number in this dashboard.",
    )
    ui.architecture_diagram()
    ui.keylines(
        [
            (
                "Built on standard Databricks parts",
                "Code in a Git folder, runs as Jobs, the model on Model Serving, results in a Unity Catalog volume, "
                "this dashboard as a Databricks App.",
            ),
            (
                "Scoring is separate from solving",
                "The answer key is computed offline from the complete map and used only by the scorer. "
                "Tests check it never appears in a prompt.",
            ),
            (
                "Every run can be replayed",
                "Each step, finding and model reply is saved. Interrupted runs resume where they stopped.",
            ),
        ],
        [ui.BLUE, ui.INK, ui.GREEN],
    )
    st.markdown("### Who decides what")
    st.markdown(
        '<div class="ready">'
        "<div><h4>Fixed code (same answer every time)</h4><ul>"
        "<li>Benchmark, damage and answer key</li><li>The current check (follows visible links)</li>"
        "<li>Quote check: quotes must match word for word</li><li>Scoring against the answer key</li></ul></div>"
        "<div><h4>The model (gpt-oss-120b)</h4><ul>"
        "<li>Which items to explore and procedures to read</li><li>Each control: affected or not, with reason</li>"
        "<li>The independent second opinion</li></ul></div>"
        "<div><h4>People</h4><ul>"
        "<li>Every item the two model calls disagree on</li><li>Final call on any control impact</li>"
        "<li>Any change to lineage or controls (the agent changes nothing)</li></ul></div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("### Boundaries")
    ui.score_table(
        [
            (
                "Inside",
                "One Databricks workspace: Git folder, Jobs, Model Serving, a Unity Catalog volume, this App.",
            ),
            (
                "Read-only",
                "The agent's tools only read. It never writes lineage links or edits controls.",
            ),
            (
                "Not connected",
                "No real payment systems, change tools or control repositories; all data is synthetic.",
            ),
            (
                "Answer key",
                "Used only by the scorer; tests check it never reaches a prompt.",
            ),
        ]
    )
    with st.expander("Reproduce the results"):
        st.markdown(content.REPRO)
    with st.expander("Results summary used by the assistant"):
        st.code(results_summary_text())
    nav_buttons("explorer", "faq")


# ------------------------------------------------------------------ technical: synthetic data


@st.cache_data(show_spinner=False)
def syn_example(change_id, level, mode):
    ex = synthetic.example(change_id, level, mode)
    return {k: v for k, v in ex.items() if k != "edges"}


@st.cache_data(show_spinner=False)
def syn_dot(change_id, level, mode, show, focused):
    ex = synthetic.example(change_id, level, mode)
    return synthetic.map_dot(
        highlight=ex["path_edges"],
        removed=ex["removed"],
        show=show,
        focus=synthetic.focus_nodes(ex) if focused else None,
        changed=set(ex["change"]["changed_node_ids"]),
        affected=set(ex["affected"]),
    )


AGENT_WORDS = {
    "Rules already had it": "rules had it",
    "Correct recovery": "recommended ✓",
    "Sent to review (affected)": "sent to review",
    "Missed": "missed (marked unaffected)",
    "Not investigated": "not decided",
}


@st.cache_data(show_spinner=False)
def agent_outcomes(change_id):
    """Outcome per control from the scored agent run that covers this change."""
    for kind, label in (("heldout", "held-out run"), ("frozen", "frozen check")):
        r = find_run(runs, kind)
        if r and change_id in r["cases"]:
            res = data.case_result(r["folder"], "run1", change_id)
            if res:
                return {
                    row["control"]: row["outcome"] for row in data.decisions_table(res)
                }, label
    return None, None


def page_synthetic():
    ui.page_head(
        "Technical view",
        "Break the dependency map. See what each method misses.",
        "An invented but realistic model of one bank's outbound cross-border payments. The full map is known, "
        "so the right answer for every change is known; the agent only ever sees a damaged copy. "
        "No real bank, customer or control data is used.",
        synthetic=True,
    )
    with st.expander("Benchmark inventory (148 nodes, 238 links, 101 controls, 54 changes)"):
        ui.kpis(
        [
            (
                "148",
                "items in the map",
                "fields, rules, interfaces, systems, processes, reports, evidence, controls",
            ),
            (
                "238",
                "links between them",
                "each with a direction: impact flows along it",
            ),
            ("101", "controls", "30 key, 60 standard, 11 supporting"),
            ("54", "change scenarios", "36 for development, 18 held out for the test"),
        ]
        )

    st.markdown("### The experiment: remove information, then measure what is missed")
    st.markdown(
        "**Complete map → remove links → run rules-only baseline → let the agent investigate → "
        "compare both against the untouched answer key.** "
        "The answer key is never shown to the agent."
    )
    left, right = st.columns([1, 2], gap="large")
    with left:
        level = st.select_slider(
            "Lineage degradation",
            options=[0, 30, 60],
            value=30,
            format_func=lambda x: f"{x}% links removed",
            key="degradation_level",
        )
        mode = st.radio(
            "Damage pattern",
            ["Change-correlated", "Random"],
            index=0,
            key="degradation_pattern",
        )
        change_id = st.selectbox(
            "Payment change to test",
            [r["Change"] for r in synthetic.change_table()],
            index=next((i for i, row in enumerate(synthetic.change_table()) if row["Change"] == "CHG-027"), 0),
            key="degradation_change",
        )
        damage_mode = "correlated" if mode == "Change-correlated" else "random"
        ex = syn_example(change_id, level, damage_mode)
        st.markdown(
            f"**{len(ex['removed'])} of {ex['edges_exposable']} exposable links removed** "
            f"for this case. **{len(ex['key_misses'])} key-control impacts missed** "
            "by the rules-only check."
        )
        st.caption(
            "Degradation is controlled synthetic metadata loss, not model accuracy loss. "
            "Change-correlated damage concentrates missing links near the changed component; "
            "random damage removes links without that proximity preference. "
            "This interactive example is a counterfactual, not a new agent run."
        )
    with right:
        graph_view = st.radio(
            "Compare map views",
            ["Complete answer key", "What the rules see", "Missing links highlighted"],
            index=2,
            horizontal=True,
            key="degradation_view",
        )
        graph_mode = {
            "Complete answer key": "complete",
            "What the rules see": "damaged",
            "Missing links highlighted": "overlay",
        }[graph_view]
        st.graphviz_chart(
            syn_dot(change_id, level, damage_mode, graph_mode, True),
            use_container_width=True,
        )
    with st.expander("How the benchmark is constructed and scored"):
        st.markdown(
            "The complete directed graph defines affected controls deterministically. "
            "The benchmark damages the metadata visible to the rules and agent, "
            "while retaining the original graph for scoring. "
            "Narrative artifacts may also be stale or incomplete. "
            "The recorded held-out result uses **30% change-correlated degradation**; "
            "changing these controls does not rerun the model."
        )

    st.markdown("### Further technical detail")
    st.caption("Reference material for reviewers who want to audit the benchmark.")
    t2, t1, t3, t4 = st.tabs(
        [
            "Worked example",
            "What is in it",
            "Complete map: 148 items, 238 links",
            "30% degradation vs complete",
        ]
    )

    with t1:
        st.markdown("### Items, by type")
        st.dataframe(
            pd.DataFrame(synthetic.type_counts()),
            hide_index=True,
            use_container_width=True,
        )
        st.markdown("### Links, by type")
        st.markdown(
            "Links have a direction: impact flows from source to target. All link types carry impact except "
            "COMPENSATED_BY (a manual fallback)."
        )
        st.dataframe(
            pd.DataFrame(synthetic.link_counts()),
            hide_index=True,
            use_container_width=True,
        )
        st.markdown("### How the answer key is built")
        st.markdown(
            "A control is **affected** by a change when the changed item reaches it by following impact-carrying "
            "links in their direction through the complete map (at most 6 steps; a path stops at the first control). "
            "This is plain code, the same every time; no model creates labels. Each change affects 10 to 49 controls."
        )
        with st.expander("All 101 controls"):
            st.dataframe(
                pd.DataFrame(synthetic.control_table()),
                hide_index=True,
                use_container_width=True,
                height=420,
            )
        with st.expander("All 54 change scenarios"):
            st.dataframe(
                pd.DataFrame(synthetic.change_table()),
                hide_index=True,
                use_container_width=True,
                height=420,
            )

    changes = [r["Change"] for r in synthetic.change_table()]
    titles = {r["Change"]: r["Title"] for r in synthetic.change_table()}

    with t2:
        cid = st.selectbox(
            "Change",
            changes,
            index=changes.index("CHG-027"),
            format_func=lambda x: f"{x} · {titles[x]}",
            key="syn_example_change",
        )
        ex = syn_example(cid, 30, "correlated")
        ch, case = ex["change"], ex["case"]
        st.markdown(
            f"**{ch['title']}** changes "
            + ", ".join(
                f"`{i}` {synthetic.nodes_by_id()[i]['name']}"
                for i in ch["changed_node_ids"]
            )
            + f". Split: {ch['split']}."
        )
        a, b = st.columns(2)
        with a:
            st.markdown("**Step 1 · The answer key (complete map)**")
            st.markdown(
                f"Following the links from the changed item reaches **{len(ex['affected'])} controls**, "
                f"**{len(ex['key'])} of them key**. These are the right answers."
            )
        with b:
            st.markdown(
                "**Step 2 · What the agent and the current check see (30% damaged)**"
            )
            st.markdown(
                f"{len(ex['removed'])} of {ex['edges_exposable']} visible links are removed, nearest the change first. "
                f"{len(ex['removed_on_paths'])} of them lie on the paths above. The current check, walking only what is left, "
                f"finds **{len(ex['rules_found_affected'])} of {len(ex['affected'])}** affected controls and misses "
                f"**{len(ex['key_misses'])} key** controls."
            )
        st.markdown(
            "**The paths, in the complete map.** Orange: the changed item. Pink: affected controls. "
            "Red dashed: links the damaged view hides. Hover any box or line for details."
        )
        st.graphviz_chart(
            syn_dot(cid, 30, "correlated", "overlay", True), use_container_width=True
        )
        agent, agent_run = agent_outcomes(cid)
        table = pd.DataFrame(ex["rows"])
        if agent:
            table["Step 3 · AI agent"] = [
                AGENT_WORDS.get(agent.get(c), "not decided") for c in table["Control"]
            ]
        st.markdown(
            "**Every affected control, with its path, what damage did to it"
            + (
                f", and what the AI agent decided in the {agent_run}**"
                if agent
                else "**"
            )
        )
        st.dataframe(table, hide_index=True, use_container_width=True)
        if agent:
            missed = [
                c for c in ex["affected"] if c not in set(ex["rules_found_affected"])
            ]
            rec = sum(agent.get(c) == "Correct recovery" for c in missed)
            rev = sum(agent.get(c) == "Sent to review (affected)" for c in missed)
            st.markdown(
                f"**Step 3 · What the AI agent did.** Of the {len(missed)} affected controls the current check missed, "
                f"the agent recommended **{rec}** and sent **{rev}** to a person for review; "
                f"{len(missed) - rec - rev} were missed."
            )
        else:
            st.caption(
                "This change was not part of a scored agent run under this damage, so step 3 is not shown. "
                "The 18 test changes (held-out run) and 8 development changes (frozen check) have it."
            )
        a, b = st.columns(2)
        with a:
            st.markdown("**The ticket the AI receives**")
            st.code(
                case["change_ticket"]["title"] + "\n" + case["change_ticket"]["text"],
                language=None,
            )
        with b:
            st.markdown("**One control document the AI can read**")
            k = ex["affected"][0] if ex["affected"] else None
            doc = next(
                (d for d in case["control_documents"] if d["control_id"] == k), None
            )
            if doc:
                st.code(
                    f"{doc['control_id']} · {doc['title']} ({doc['criticality'].lower()})\n{doc['text']}",
                    language=None,
                )
        st.caption(
            "The detective's job is to recover the pink controls the current check misses, using the item names, descriptions "
            "and control texts, and to cite its evidence. Across the whole held-out run it recovered 113 of 144 such key misses."
        )

    with t3:
        a, b = st.columns([2, 1])
        with a:
            cid3 = st.selectbox(
                "Highlight a change",
                changes,
                index=changes.index("CHG-027"),
                format_func=lambda x: f"{x} · {titles[x]}",
                key="syn_map_change",
            )
        with b:
            view = st.radio(
                "Show",
                [
                    "Complete map",
                    "What the AI sees (30% damaged)",
                    "Both: removed links in red",
                ],
                key="syn_map_view",
            )
        show = {
            "Complete map": "complete",
            "What the AI sees (30% damaged)": "damaged",
        }.get(view, "overlay")
        st.caption(
            "Columns, left to right: data elements, rules, interfaces, systems, processes, reports, evidence, "
            "parent controls, family controls. Orange = the changed item; pink = controls it affects; blue lines = "
            "its paths. Use the expand icon on the chart to view it full screen; hover for names and descriptions."
        )
        st.graphviz_chart(
            syn_dot(cid3, 30, "correlated", show, False), use_container_width=True
        )

    with t4:
        a, b, c2 = st.columns([2, 1, 1])
        with a:
            cid4 = st.selectbox(
                "Change",
                changes,
                index=changes.index("CHG-027"),
                format_func=lambda x: f"{x} · {titles[x]}",
                key="syn_deg_change",
            )
        with b:
            level = st.selectbox(
                "Damage level",
                [30, 60, 0],
                key="syn_deg_level",
                format_func=lambda x: f"{x}%",
            )
        with c2:
            mode = st.selectbox(
                "Damage style",
                ["correlated", "random"],
                key="syn_deg_mode",
                format_func=lambda x: (
                    "near the change (main)" if x == "correlated" else "random"
                ),
            )
        ex4 = syn_example(cid4, level, mode)
        ui.kpis(
            [
                (str(ex4["edges_total"]), "links in the complete map", None),
                (
                    str(ex4["edges_visible"]),
                    "links the agent sees",
                    f"{len(ex4['removed'])} removed",
                ),
                (
                    f"{len(ex4['rules_found_affected'])} of {len(ex4['affected'])}",
                    "affected controls the current check finds",
                    None,
                ),
                (
                    f"{len(ex4['key_misses'])} of {len(ex4['key'])}",
                    "key controls the current check misses",
                    None,
                ),
            ]
        )
        st.markdown(
            "**How the damage is chosen.** One link is never exposed (internal). Of the other 237, the stated share is removed. "
            "In the main style, links nearest the changed item go first, but roughly the same share of the changed item's "
            "own links is kept (at least one), so it is never cut off. The damage lands on the next layer out, where impact "
            "chains continue. The random style removes links anywhere."
        )
        if level:
            st.markdown(
                "**Where the removed links are**, by distance from the changed item "
                "(0 steps = links touching the changed item itself):"
            )
            st.dataframe(
                pd.DataFrame(synthetic.degradation_by_distance(ex4)),
                hide_index=True,
                use_container_width=True,
            )
        st.markdown(
            "**This change's paths, complete vs damaged** (red dashed = removed):"
        )
        st.graphviz_chart(
            syn_dot(cid4, level, mode, "overlay", True), use_container_width=True
        )
        st.markdown(
            '**Text damage.** The ticket can lose its last sentence ("Change type: …"), gain a legacy system name, or, for every '
            'seventh change, gain a misleading "control impact: N/A" note. Control texts are single sentences without legacy '
            "names, so in practice they stay clean."
        )
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Damage": "None",
                        "Key controls the current check finds (test changes)": "100%",
                        "Missed": 0,
                    },
                    {
                        "Damage": "30% near the change (main)",
                        "Key controls the current check finds (test changes)": "11.1%",
                        "Missed": 144,
                    },
                    {
                        "Damage": "30% random",
                        "Key controls the current check finds (test changes)": "43%",
                        "Missed": 93,
                    },
                    {
                        "Damage": "60% near the change",
                        "Key controls the current check finds (test changes)": "7.4%",
                        "Missed": 150,
                    },
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )
    nav_buttons("decision", "evidence")


# ------------------------------------------------------------------ technical: case explorer


def per_case_chart(metrics):
    cases = [c for c in metrics.get("cases", []) if c.get("key_misses")]
    if not cases:
        return None
    rows = []
    titles = load_key()["cases"]
    for c in cases:
        c = {
            **c,
            "change_id": f"{titles.get(c['change_id'], {}).get('title', '')} ({c['change_id']})",
        }
        rows.append(
            {"case": c["change_id"], "part": "Recovered", "count": c["key_recovered"]}
        )
        rows.append(
            {
                "case": c["change_id"],
                "part": "Still missed",
                "count": c["key_misses"] - c["key_recovered"],
            }
        )
    df = pd.DataFrame(rows)
    return (
        alt.Chart(df)
        .mark_bar(size=16)
        .encode(
            y=alt.Y(
                "case:N",
                sort="-x",
                title=None,
                axis=alt.Axis(labelOverlap=False, labelLimit=360),
            ),
            x=alt.X("sum(count):Q", title="Key controls the current check missed"),
            color=alt.Color(
                "part:N",
                scale=alt.Scale(
                    domain=["Recovered", "Still missed"], range=[ui.GREEN, ui.GREY]
                ),
                legend=None,
            ),
            order=alt.Order("part:N", sort="ascending"),
            tooltip=["case", "part", "count"],
        )
        .properties(height=max(160, 30 * len(cases)))
    )


OUTCOME_COLORS = {
    "Correct recovery": "🟢",
    "Rules already had it": "🔵",
    "Correctly excluded": "⚪",
    "False flag": "🔴",
    "Missed": "🔴",
    "Sent to review (affected)": "🟠",
    "Sent to review (not affected)": "🟡",
    "Not investigated": "🔴",
    "Not investigated (fine)": "⚪",
    "Rules false flag": "🔴",
}


def reviewer_queue(rows, compact=False, key="main"):
    """The output as a control reviewer would get it, with the answer key optional."""
    show_key = st.toggle(
        "Show the answer key (a real reviewer would not have it)",
        value=False,
        key=f"showkey_{key}",
    )
    rules = [r for r in rows if r["outcome"].startswith("Rules")]
    ai = [r for r in rows if r["outcome"] in ("Correct recovery", "False flag")]
    review = [r for r in rows if r["outcome"].startswith("Sent to review")]

    def table(items, cols):
        df = pd.DataFrame(
            [
                {
                    "Control": r["title"],
                    "ID": r["control"] + (" · key" if r["key"] else ""),
                    **{k: f(r) for k, f in cols.items()},
                    **({"Answer key": r["answer_key"]} if show_key else {}),
                }
                for r in items
            ]
        )
        st.dataframe(df, hide_index=True, use_container_width=True)

    n_all = max(len(rules) + len(ai) + len(review), 1)
    segs = [
        (
            len(rules),
            "<b>Already linked</b> found by the current check",
            ui.BLUE,
            False,
        ),
        (len(ai), "<b>Added by the agent</b> both checks agree", ui.GREEN, False),
        (
            len(review),
            "<b>For a person to decide</b> the two checks disagree",
            ui.AMBER,
            False,
        ),
    ]
    ui.segbar([(None, [x for x in segs if x[0]])], n_all)
    if compact:
        st.caption("Open a group to see each control and the agent's stated reason.")
    groups = [
        ("Already linked by the current check", rules, {}),
        (
            "Added by the agent",
            ai,
            {"Why the agent says it is affected": lambda r: r["agent_reason"]},
        ),
        (
            "For a person to decide",
            review,
            {
                "Agent: why affected": lambda r: r["agent_reason"],
                "Independent checker: why not sure": lambda r: r["verifier_reason"],
            },
        ),
    ]
    for label, items, cols in groups:
        if not items:
            continue
        with st.expander(f"{label} ({len(items)})", expanded=not compact):
            table(items, cols)
    if show_key and review:
        true = sum(r["outcome"] == "Sent to review (affected)" for r in review)
        st.caption(
            f"{true} of the {len(review)} review items are truly affected in the answer key."
        )


def page_explorer():
    ui.page_head(
        "Technical view",
        "Every agent decision, checked against an answer key it never saw",
        "Pick a run and a change. The first tab is the review list as a control reviewer would get it; "
        "the others compare each decision with the answer key and list every step.",
        synthetic=True,
    )
    choices = [r for r in runs if r["cases"]]
    if not choices:
        st.warning("No case files were found in the results volume.")
        return
    c1, c2, c3 = st.columns([3, 1, 2])
    run = choices[
        [r["label"] for r in choices].index(
            c1.selectbox("Run", [r["label"] for r in choices])
        )
    ]
    run_name = (
        c2.selectbox("Repeat", run["runs"] or ["run1"])
        if len(run["runs"]) > 1
        else (run["runs"] or ["run1"])[0]
    )
    cases = data.case_ids(run["folder"], run_name)
    key = load_key()["cases"]
    change_id = c3.selectbox(
        "Change",
        cases,
        index=cases.index("CHG-015") if "CHG-015" in cases else 0,
        format_func=lambda c: f"{key.get(c, {}).get('title', '')} ({c})",
    )
    result = load_case(run["folder"], run_name, change_id)
    if not result:
        st.warning("Could not read that case file.")
        return
    info = key.get(change_id, {})
    st.markdown(f"#### {info.get('title', change_id)}")
    st.caption(
        f"{change_id} · {info.get('split', '')} split · ticket: “{info.get('text', '')}” · status {result.get('status')} · variant {result.get('variant', 'A')}"
    )
    rows = data.decisions_table(result)
    key_miss = [
        r
        for r in rows
        if r["key"]
        and r["answer_key"] == "Affected"
        and r["outcome"] != "Rules already had it"
    ]
    rec = sum(r["outcome"] == "Correct recovery" for r in key_miss)
    ui.kpis(
        [
            (f"{rec} of {len(key_miss)}", "missed key controls recovered", None),
            (
                str(sum(r["outcome"] == "Correct recovery" for r in rows)),
                "correct new recommendations",
                None,
            ),
            (
                str(sum(r["outcome"] == "False flag" for r in rows)),
                "wrong new recommendations",
                None,
            ),
            (
                str(sum(r["final"] == "UNCERTAIN" for r in rows)),
                "sent to a person",
                None,
            ),
        ]
    )
    tab0, tab1, tab2 = st.tabs(
        ["What a reviewer receives", "Decisions vs answer key", "Investigation steps"]
    )
    with tab0:
        reviewer_queue(rows)
    with tab1:
        view = st.radio(
            "Show",
            ["Missed key controls", "Problems only", "Everything"],
            horizontal=True,
        )
        shown = (
            key_miss
            if view == "Missed key controls"
            else (
                [
                    r
                    for r in rows
                    if r["outcome"]
                    in (
                        "False flag",
                        "Missed",
                        "Sent to review (affected)",
                        "Sent to review (not affected)",
                        "Not investigated",
                    )
                ]
                if view == "Problems only"
                else rows
            )
        )
        df = pd.DataFrame(
            [
                {
                    "Control": r["control"] + (" (key)" if r["key"] else ""),
                    "Procedure": r["title"],
                    "Agent": r["agent"],
                    "Verifier": r["verifier"],
                    "Final": r["final"],
                    "Answer key": r["answer_key"],
                    "Outcome": r["outcome"],
                }
                for r in shown
            ]
        )
        st.dataframe(df, hide_index=True, use_container_width=True)
        with st.expander("Why did the agent decide that? (reasoning per control)"):
            for r in shown:
                if r["agent_reason"]:
                    st.markdown(
                        f"**{r['control']}** · {r['outcome']}  \nAgent: {r['agent_reason']}"
                        + (
                            f"  \nVerifier: {r['verifier_reason']}"
                            if r["verifier_reason"]
                            else ""
                        )
                    )
    with tab2:
        steps = data.step_rows(result)
        st.caption(
            f"{len(steps)} steps, {sum(s['rejected'] for s in steps)} rejected and corrected. Each row is one action the model chose."
        )
        st.dataframe(pd.DataFrame(steps), hide_index=True, use_container_width=True)
    nav_buttons("evidence", "architecture")


# ------------------------------------------------------------------ help


def page_faq():
    ui.page_head(
        "Help", "Questions and answers", "Filter by audience, then open a question."
    )
    audience = st.radio(
        "For", ["Everyone", "Leadership", "Technical", "Controls"], horizontal=True
    )
    for who, q, a in content.FAQ:
        if audience in ("Everyone", who):
            with st.expander(f"{q}  ·  {who}"):
                st.markdown(a)
    st.caption("Not answered here? Use Ask the assistant.")


def page_ask():
    ui.page_head(
        "Help",
        "Ask the assistant about this proof of concept",
        "Answers come only from the project documents and the recorded results. If they do not cover a question, "
        "the answer says so. Like any model, it can be wrong: check important figures on the Results and Evidence pages.",
    )
    if "chat" not in st.session_state:
        st.session_state.chat = []
    examples = [
        "Is the 78% held-out result trustworthy?",
        "Why does the workload gate fail?",
        "How does the agent avoid making things up?",
        "Why is consistency below target?",
    ]
    cols = st.columns(len(examples))
    clicked = next(
        (q for q, c in zip(examples, cols) if c.button(q, use_container_width=True)),
        None,
    )
    for turn in st.session_state.chat:
        with st.chat_message(turn["role"]):
            st.markdown(turn["content"])
    question = (
        st.chat_input("Ask about the results, the method, or the controls") or clicked
    )
    if question:
        from app import qa

        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Reading the project material…"):
                try:
                    answer = qa.ask(
                        question, st.session_state.chat, results_summary_text()
                    )
                except Exception as exc:  # endpoint missing or not permitted
                    answer = f"The model endpoint could not be reached ({type(exc).__name__}). Questions and answers covers the common ones."
            st.markdown(answer)
        st.session_state.chat += [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ]


# ------------------------------------------------------------------ navigation


def _page(fn, title, default=False):
    page = st.Page(fn, title=title, url_path=fn.__name__[5:], default=default)
    PAGES[fn.__name__[5:]] = page
    return page


VIEWS = {
    "Decision": [
        _page(page_overview, "The finding", default=True),
        _page(page_decision, "Decision and value"),
    ],
    "Investigation": [
        _page(page_case, "Investigate a change"),
        _page(page_results, "Evaluation"),
    ],
    "Technical evidence": [
        _page(page_synthetic, "Degradation experiment"),
        _page(page_architecture, "Method and architecture"),
        _page(page_explorer, "Run explorer"),
        _page(page_evidence, "Source evidence"),
    ],
    "Reference": [
        _page(page_problem, "Problem definition"),
        _page(page_how, "Agent workflow"),
        _page(page_present, "Presentation"),
        _page(page_faq, "FAQ"),
        _page(page_ask, "Ask"),
    ],
}
nav = st.navigation(VIEWS, position="hidden")
with st.sidebar:
    st.markdown(
        '<div class="brand">Control Impact Detective</div>'
        '<div class="brand-sub">Payments control-impact proof of concept</div>',
        unsafe_allow_html=True,
    )
    for view, pages in VIEWS.items():
        if view:
            st.markdown(f'<div class="navhead">{view}</div>', unsafe_allow_html=True)
        for pg in pages:
            st.page_link(pg)
    source = (
        "live run files"
        if any(r.get("live") for r in runs)
        else "recorded run files shipped with the app"
    )
    st.markdown(
        f'<div class="sidefoot about"><b>About this proof of concept</b><br>'
        f"Status: proof of concept, not in production.<br>"
        f"Owner: Anagha Dhekne.<br>"
        f"Built October 2026; final version A frozen {FROZEN_ON}.<br>"
        f"Synthetic benchmark; no real bank, customer or control data.<br>"
        f"Results from {source}.</div>",
        unsafe_allow_html=True,
    )
nav.run()
