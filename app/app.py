"""Control Impact Detective: a Databricks App that explains and evidences the POC.

Run locally:  RESULTS_ROOT=<folder> streamlit run app/app.py
On Databricks: deployed by scripts/deploy_app.py; reads the results volume.
"""

from __future__ import annotations

import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import content, data  # noqa: E402

st.set_page_config(
    page_title="Control Impact Detective",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
:root { --ink:#18212b; --accent:#1d5b86; --ok:#2f7d4f; --bad:#b23b32; --warn:#9a6a12; }
.block-container { padding-top: 2rem; max-width: 1200px; }
h1, h2, h3 { letter-spacing: -0.01em; }
.eyebrow { font: 600 12px/1.2 ui-monospace, Menlo, monospace; letter-spacing: .08em; text-transform: uppercase; color: #6a7480; }
.verdict { font-size: 1.25rem; line-height: 1.5; border-left: 4px solid var(--accent); padding: .4rem 0 .4rem 1rem; margin: .5rem 0 1rem; }
.pill { display:inline-block; font: 600 11px/1 ui-monospace, Menlo, monospace; text-transform: uppercase; letter-spacing:.05em; padding: 5px 8px; border-radius: 3px; }
.pill.ok { background:#e3f1e8; color:#2f7d4f } .pill.bad { background:#f7e3e1; color:#b23b32 }
.pill.warn { background:#f6ecd6; color:#9a6a12 } .pill.dim { background:#eef0f2; color:#5b6672 }
.small { font-size: .9rem; color: #5b6672; }
</style>
""",
    unsafe_allow_html=True,
)

GATE_RECOVERY, GATE_WORKLOAD, GATE_CONSISTENCY = 0.50, 0.25, 0.95

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


def pill(text, kind):
    return f'<span class="pill {kind}">{text}</span>'


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
    return "\n".join(lines)


# ------------------------------------------------------------------ navigation

SECTIONS = [
    "1 · Executive summary",
    "2 · Context: the problem",
    "3 · How it works",
    "4 · Evidence",
    "5 · Case explorer",
    "6 · Limits and next steps",
    "7 · FAQ",
    "8 · Ask a question",
    "9 · Technical appendix",
]
with st.sidebar:
    st.markdown("### 🔎 Control Impact Detective")
    st.caption("Payments control-impact proof of concept · synthetic benchmark")
    section = st.radio("Sections", SECTIONS, label_visibility="collapsed")
    st.divider()
    st.caption(
        "New here? Read sections 1 and 2 first. Numbers on the Evidence page are read live "
        "from the run results."
    )
    st.caption(
        f"Results source: `{data.RESULTS_ROOT}`"
        + ("" if frozen_live else " (recorded figures shown; live files not found)")
    )
    if st.button("Refresh results"):
        st.cache_data.clear()
        st.rerun()


# ------------------------------------------------------------------ 1. executive


def page_executive():
    st.markdown(
        '<div class="eyebrow">Section 1 · for leadership</div>', unsafe_allow_html=True
    )
    st.title(
        "Can an AI agent find the controls a payment change affects when lineage is broken?"
    )
    st.markdown(
        f'<div class="verdict"><b>Yes. On 18 held-out cases it had never seen, the agent recovered '
        f'<b>{H["key_recovered"]} of {H["key_misses"]}</b> affected key controls that the rules-based method missed '
        f'(<b>{pct(H["key_miss_recovery"], 0)}</b>, target 50%; 95% interval 71–84%).</b> '
        f'<b>{pct(H["new_control_precision"], 0)}</b> of its new recommendations were correct. The cost is review effort: '
        f'<b>{H["uncertain_controls"]}</b> controls sent to a person across 18 cases, about '
        f'{H["avoidable_review_items_per_case"]:.1f} unnecessary items per change.</div>',
        unsafe_allow_html=True,
    )
    c = st.columns(4)
    c[0].metric("Recovered (held-out)", pct(H["key_miss_recovery"], 0))
    c[1].metric("Precision of new flags", pct(H["new_control_precision"], 0))
    c[2].metric(
        "Unneeded items / change",
        f'{H["avoidable_review_items_per_case"]:.1f}',
    )
    c[3].metric("Same decision, 5 runs", pct(cons["agreement"], 0))

    st.subheader("Where things stand")
    winner, why = ab_decision()
    rows = [
        (
            "Agentic path runs end to end on Databricks",
            pill("Done", "ok"),
            "Live jobs on gpt-oss-120b; every step logged and replayable.",
        ),
        (
            "Recover ≥ 50% of key controls the rules miss",
            pill("Met", "ok"),
            f"Held-out: {pct(H['key_miss_recovery'])} ({H['key_recovered']} of {H['key_misses']}) on 18 test cases. Development check: {pct(F['key_miss_recovery'])} on 8 unseen cases.",
        ),
        (
            "Added review workload ≤ 25% vs rules",
            pill("Not met", "bad"),
            f"Held-out: {H['added_review_items']} added items vs {H['baseline_workload']} rules items; {pct(H.get('review_queue_true_share'), 0)} of added items are genuinely affected. Gate unreachable by any method that passes the first; see FAQ.",
        ),
        (
            "Same key decision across 5 runs ≥ 95%",
            (
                pill("Met", "ok")
                if cons and cons.get("agreement", 0) >= GATE_CONSISTENCY
                else (pill("Not met", "bad") if cons else pill("Running", "warn"))
            ),
            (
                f"{pct(cons['agreement'])} on {cons['key_pairs']} key pairs"
                if cons
                else "Five repeat runs on three cases in progress."
            ),
        ),
        (
            "Stricter agent (variant B) A/B test",
            (
                pill("B rejected" if winner == "A" else "B adopted", "ok")
                if winner
                else pill("Running", "warn")
            ),
            why,
        ),
    ]
    st.markdown(
        "<table style='width:100%'>"
        + "".join(
            f"<tr><td style='width:42%'>{a}</td><td style='width:12%'>{b}</td><td class='small'>{c}</td></tr>"
            for a, b, c in rows
        )
        + "</table>",
        unsafe_allow_html=True,
    )
    left, right = st.columns(2)
    with left:
        st.subheader("What it means")
        st.markdown(
            "- Where lineage is incomplete, the agent finds most of what the rules miss, with quoted evidence a reviewer can check.\n"
            "- It does not replace control owners: it produces a review list with reasons, and sends disagreements to a person.\n"
            "- The held-out result (78%) is higher than the development check (65%), so the method was not overfitted to the cases used for fixing.\n"
            "- Two open problems: review volume (about 4 unnecessary items per change), and run-to-run variation (80% same decision on key controls, target 95%)."
        )
    with right:
        st.subheader("Decision needed")
        st.markdown(
            "- **Continue:** the stop rule agreed in advance (held-out below 50%) was not triggered.\n"
            "- **Next:** a practitioner review of real findings, and work on stability (e.g. majority vote over runs) and review volume.\n"
            "- Not yet: a production pilot, because the stability and workload gates are not met."
        )
    st.caption(
        "All data is synthetic. Headline figures: held-out test split, variant A, code frozen, one run. Details in sections 4 and 6."
    )


# ------------------------------------------------------------------ 2. context


def page_context():
    st.markdown(
        '<div class="eyebrow">Section 2 · start here if you are new</div>',
        unsafe_allow_html=True,
    )
    st.title("The problem, in plain words")
    st.markdown(content.CONTEXT_INTRO)
    st.graphviz_chart(
        """
digraph { rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#f5f6f3", color="#9aa6b2", fontname="Helvetica"];
  D03 [label="Field changed\\nD03 Debtor town name", fillcolor="#e3edf5"];
  R01 [label="Rule\\nR01 Structured address validation"];
  R03 [label="Rule\\nR03 Screening field set"];
  S03 [label="System\\nS03 Screening engine"];
  C012 [label="Key control\\nC012 Required-field validation", fillcolor="#e3f1e8"];
  C02 [label="Key control\\nC02 Sanctions screening", fillcolor="#e3f1e8"];
  D03 -> R01; D03 -> R03; R03 -> S03 [label=" via I02"]; S03 -> C02;
  R01 -> C012 [style=dashed, color="#b23b32", fontcolor="#b23b32", label=" link missing\\n in the metadata"];
}""",
        use_container_width=True,
    )
    st.markdown(content.CONTEXT_EXAMPLE)
    st.subheader("Why it matters")
    st.markdown(
        "- A missed control can stop working after a release with nobody noticing until an audit or an incident.\n"
        "- Impact reviews are manual and depend on lineage that is often out of date exactly where change happens.\n"
        "- The proof of concept tests whether an agent can close that gap, and was designed so that the answer could be no."
    )
    st.subheader("Glossary")
    st.dataframe(
        pd.DataFrame(content.GLOSSARY, columns=["Term", "Meaning"]),
        hide_index=True,
        use_container_width=True,
    )


# ------------------------------------------------------------------ 3. how it works


def page_how():
    st.markdown(
        '<div class="eyebrow">Section 3 · the system</div>', unsafe_allow_html=True
    )
    st.title("How one change is investigated")
    st.graphviz_chart(
        """
digraph { rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#ffffff", color="#9aa6b2", fontname="Helvetica"];
  T [label="Change ticket\\n+ degraded lineage\\n+ control procedures"];
  B [label="Rules baseline\\nfollow visible links"];
  A [label="Agent loop (≤60 steps)\\nexplore · search · read", fillcolor="#e3edf5"];
  F [label="Findings\\nquotes + reason\\n+ counter-evidence", fillcolor="#e3edf5"];
  V [label="Verifier\\nindependent check", fillcolor="#e3edf5"];
  R [label="Recommend", fillcolor="#e3f1e8"]; H [label="Human review\\n(UNCERTAIN)", fillcolor="#f6ecd6"];
  T -> B -> A -> F -> V; V -> R [label=" agree"]; V -> H [label=" disagree"];
}""",
        use_container_width=True,
    )
    st.subheader("The agent's tools (all read-only)")
    st.dataframe(
        pd.DataFrame(
            [
                ("trace_metadata", "Runs the rules baseline on the visible links"),
                (
                    "explore_node",
                    "Shows a field, rule or system: its description and visible links",
                ),
                (
                    "search_controls",
                    "Ranks control procedures by matching words (never hides any)",
                ),
                (
                    "inspect_control",
                    "Reads up to 15 control procedures; required before a finding",
                ),
                (
                    "submit_findings",
                    "Up to 8 decisions with exact quotes, reason, counter-evidence and the chain",
                ),
                ("finish", "Stops; refused up to 3 times while controls are undecided"),
            ],
            columns=["Tool", "What it does"],
        ),
        hide_index=True,
        use_container_width=True,
    )
    st.subheader("Safeguards")
    st.markdown(
        "- **Evidence is checked mechanically:** quotes must appear word for word in the ticket and the procedure, or the finding is rejected.\n"
        "- **No side effects:** tools only read; the agent never writes lineage links.\n"
        "- **Second opinion:** a verifier call checks every non-'unaffected' finding; disagreement goes to a person.\n"
        "- **Nothing is assumed safe:** controls without a decision are reported as uninvestigated.\n"
        "- **Answer key isolated:** labels are used only for scoring; tests check they never reach a prompt.\n"
        "- **Robust runs:** handles the model's reasoning-only or cut-off replies, retries, and resumes interrupted jobs."
    )


# ------------------------------------------------------------------ 4. evidence


def per_case_chart(metrics):
    cases = [c for c in metrics.get("cases", []) if c.get("key_misses")]
    if not cases:
        return None
    rows = []
    for c in cases:
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
        .mark_bar()
        .encode(
            y=alt.Y(
                "case:N",
                sort="-x",
                title=None,
                axis=alt.Axis(labelOverlap=False, labelLimit=200),
            ),
            x=alt.X("sum(count):Q", title="Key controls the rules missed"),
            color=alt.Color(
                "part:N",
                scale=alt.Scale(
                    domain=["Recovered", "Still missed"], range=["#2f7d4f", "#c9cfd6"]
                ),
                legend=alt.Legend(title=None, orient="bottom"),
            ),
            order=alt.Order("part:N", sort="ascending"),
            tooltip=["case", "part", "count"],
        )
        .properties(height=max(200, 44 * len(cases)))
    )


def page_evidence():
    st.markdown(
        '<div class="eyebrow">Section 4 · results, read live from the run files</div>',
        unsafe_allow_html=True,
    )
    st.title("Evidence")
    st.markdown(
        "Every result below comes from a run whose plan and reading rule were committed before it ran. Development results are labelled as such; only the held-out run counts as final."
    )

    st.subheader("All runs at a glance")
    table = []
    for r in runs:
        s = summary_of(r)
        if not s:
            table.append(
                {
                    "Run": r["label"],
                    "Cases": len(r["cases"]),
                    "Recovered": "running",
                    "Recovery": "",
                    "Precision": "",
                    "Sent to review": "",
                    "Avoidable items": "",
                }
            )
            continue
        table.append(
            {
                "Run": r["label"],
                "Cases": s.get("cases"),
                "Recovered": f"{s['key_recovered']} / {s['key_misses']}",
                "Recovery": pct(s.get("key_miss_recovery")),
                "Precision": pct(s.get("new_control_precision")),
                "Sent to review": s.get("uncertain_controls"),
                "Avoidable items": s.get("avoidable_review_items", ""),
            }
        )
    if not any(summary_of(r) for r in runs):
        for label, rec in (
            ("Held-out test, variant A (18 cases)", RECORDED_HELDOUT),
            ("Frozen check, variant A (8 unseen cases)", RECORDED_FROZEN),
            ("A/B test, variant B (same 8 cases)", RECORDED_B),
        ):
            table.append(
                {
                    "Run": label + " · recorded",
                    "Cases": rec["cases"],
                    "Recovered": f"{rec['key_recovered']} / {rec['key_misses']}",
                    "Recovery": pct(rec["key_miss_recovery"]),
                    "Precision": pct(rec["new_control_precision"]),
                    "Sent to review": rec["uncertain_controls"],
                    "Avoidable items": rec["avoidable_review_items"],
                }
            )
    table.append(
        {
            "Run": "Tuned development cases (earlier workspace)",
            "Cases": 4,
            "Recovered": "22 / 27",
            "Recovery": "81.5%",
            "Precision": "91.8%",
            "Sent to review": 41,
            "Avoidable items": "not measured",
        }
    )
    st.dataframe(pd.DataFrame(table), hide_index=True, use_container_width=True)
    if not frozen_live:
        st.info(
            "Live run files were not found, so recorded figures from docs/results.md are shown where needed."
        )

    left, right = st.columns(2)
    with left:
        st.subheader("Frozen check, by case")
        fr = find_run(runs, "frozen")
        chart = per_case_chart(fr["metrics"][0]) if fr and fr["metrics"] else None
        if chart is not None:
            st.altair_chart(chart, use_container_width=True)
        else:
            st.caption(
                "Per-case results appear when the frozen-check files are readable."
            )
    with right:
        st.subheader("Recovery across approaches")
        cmp = [
            {"approach": a, "detail": d, "recovery": v}
            for a, d, v in data.EARLIER_RESULTS["phases"]
        ]
        cmp.append(
            {
                "approach": "Detective, tuned cases",
                "detail": "4 dev cases",
                "recovery": 81.5,
            }
        )
        cmp.append(
            {
                "approach": "Detective, unseen cases",
                "detail": "8 dev cases, frozen",
                "recovery": round(100 * F["key_miss_recovery"], 1),
            }
        )
        if heldout:
            cmp.append(
                {
                    "approach": "Detective, held-out",
                    "detail": "18 test cases",
                    "recovery": round(100 * heldout["key_miss_recovery"], 1),
                }
            )
        df = pd.DataFrame(cmp)
        bars = (
            alt.Chart(df)
            .mark_bar(color="#1d5b86")
            .encode(
                y=alt.Y(
                    "approach:N",
                    sort=None,
                    title=None,
                    axis=alt.Axis(labelLimit=320, labelOverlap=False),
                ),
                x=alt.X(
                    "recovery:Q",
                    title="Key-miss recovery (%)",
                    scale=alt.Scale(domain=[0, 100]),
                ),
                tooltip=["approach", "detail", "recovery"],
            )
        )
        rule = (
            alt.Chart(pd.DataFrame({"x": [50]}))
            .mark_rule(color="#b23b32", strokeDash=[4, 3])
            .encode(x="x:Q")
        )
        st.altair_chart((bars + rule).properties(height=220), use_container_width=True)
        st.caption(
            "Dashed line: the 50% gate. Earlier phases used different methods and case sets."
        )

    st.subheader("A/B test: variant A vs variant B")
    winner, why = ab_decision()
    st.markdown(
        f"**Rule (registered before the run):** adopt B only if avoidable review items fall by ≥30% and recovered key controls drop by no more than 3 of 49. **Result:** {('variant ' + winner + ' goes to the held-out run. ') if winner else ''}{why}"
    )
    if variant_b:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Variant": "A (frozen check)",
                        "Recovered": f"{F['key_recovered']} / {F['key_misses']}",
                        "Precision": pct(F["new_control_precision"]),
                        "Sent to review": F["uncertain_controls"],
                        "Avoidable items": F.get("avoidable_review_items"),
                    },
                    {
                        "Variant": "B (chain required)",
                        "Recovered": f"{variant_b['key_recovered']} / {variant_b['key_misses']}",
                        "Precision": pct(variant_b.get("new_control_precision")),
                        "Sent to review": variant_b.get("uncertain_controls"),
                        "Avoidable items": variant_b.get("avoidable_review_items"),
                    },
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )

    st.subheader("Consistency across five runs")
    cr = find_run(runs, "consistency")
    if cr and cr["metrics"]:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Run": i + 1,
                        "Recovered": f"{m['summary']['key_recovered']} / {m['summary']['key_misses']}",
                        "Precision": pct(m["summary"].get("new_control_precision")),
                        "Sent to review": m["summary"].get("uncertain_controls"),
                        "Avoidable items": m["summary"].get("avoidable_review_items"),
                    }
                    for i, m in enumerate(cr["metrics"])
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )
    st.markdown(
        f"**Agreement on key-control decisions:** {pct(cons['agreement'])} of {cons['key_pairs']} pairs (target 95%)."
        if cons
        else "Agreement is computed when all five runs finish."
    )


# ------------------------------------------------------------------ 5. explorer

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


def page_explorer():
    st.markdown(
        '<div class="eyebrow">Section 5 · see the agent work</div>',
        unsafe_allow_html=True,
    )
    st.title("Case explorer")
    st.markdown(
        "Pick a run and a case to see every action the agent chose and every decision it made, checked against the answer key it never saw."
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
        "Case", cases, format_func=lambda c: f"{c} · {key.get(c, {}).get('title', '')}"
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
    m = st.columns(4)
    m[0].metric("Missed key controls recovered", f"{rec} / {len(key_miss)}")
    m[1].metric(
        "Correct new recommendations",
        sum(r["outcome"] == "Correct recovery" for r in rows),
    )
    m[2].metric("False flags", sum(r["outcome"] == "False flag" for r in rows))
    m[3].metric("Sent to review", sum(r["final"] == "UNCERTAIN" for r in rows))

    tab1, tab2 = st.tabs(["Decisions vs answer key", "Investigation steps"])
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
                    "Mark": OUTCOME_COLORS.get(r["outcome"], ""),
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


# ------------------------------------------------------------------ 6. limits


def page_limits():
    st.markdown(
        '<div class="eyebrow">Section 6 · what is not solved yet</div>',
        unsafe_allow_html=True,
    )
    st.title("Limits and next steps")
    st.dataframe(
        pd.DataFrame(content.LIMITS, columns=["Issue", "Evidence", "Response"]),
        hide_index=True,
        use_container_width=True,
    )
    st.subheader("Next steps")
    st.markdown(
        "Done: A/B test (variant A kept), five-run consistency (80%), held-out run (78% recovery).\n\n"
        "1. Practitioner review of a sample of recommended and review items from the held-out run.\n"
        "2. Stability: run each case three times and keep the majority decision; measure agreement again.\n"
        "3. Review volume: target the verifier's over-strict rejections and the UNCERTAIN items that are not affected.\n"
        "4. Then a pilot decision on a real, small change set with control owners."
    )


# ------------------------------------------------------------------ 7. FAQ


def page_faq():
    st.markdown(
        '<div class="eyebrow">Section 7 · questions people ask</div>',
        unsafe_allow_html=True,
    )
    st.title("FAQ")
    audience = st.radio(
        "For", ["Everyone", "Leadership", "Technical", "Controls"], horizontal=True
    )
    for who, q, a in content.FAQ:
        if audience in ("Everyone", who):
            with st.expander(f"{q}  ·  {who}"):
                st.markdown(a)
    st.caption("Not answered here? Ask in section 8.")


# ------------------------------------------------------------------ 8. ask


def page_ask():
    st.markdown(
        '<div class="eyebrow">Section 8 · ask anything about the project</div>',
        unsafe_allow_html=True,
    )
    st.title("Ask a question")
    st.markdown(
        "Answers come from the project's documents and the results loaded in this app, using the workspace model endpoint. If the material does not cover your question, the answer says so."
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
                    answer = f"The model endpoint could not be reached ({type(exc).__name__}). The FAQ in section 7 covers the common questions."
            st.markdown(answer)
        st.session_state.chat += [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ]


# ------------------------------------------------------------------ 9. appendix


def page_appendix():
    st.markdown(
        '<div class="eyebrow">Section 9 · for technical reviewers</div>',
        unsafe_allow_html=True,
    )
    st.title("Technical appendix")
    st.markdown(content.REPRO)
    with st.expander("Live results summary used by the Q&A"):
        st.code(results_summary_text())
    with st.expander("Benchmark facts"):
        st.markdown(
            "- Hidden graph: 148 nodes (101 controls: 30 key, 60 standard, 11 supporting), 238 links.\n"
            "- 54 changes: 36 development, 18 held-out test. Labels from graph paths, never from a model.\n"
            "- Main condition: 30% change-correlated degradation. Rules baseline finds 51 of 276 affected key-control pairs on the development split.\n"
            "- Model: databricks-gpt-oss-120b, temperature 0; up to 60 agent steps per case plus one verifier call per finding."
        )


PAGES = dict(
    zip(
        SECTIONS,
        [
            page_executive,
            page_context,
            page_how,
            page_evidence,
            page_explorer,
            page_limits,
            page_faq,
            page_ask,
            page_appendix,
        ],
    )
)
PAGES[section]()
