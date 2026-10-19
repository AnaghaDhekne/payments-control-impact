"""Control Impact Detective: a Databricks App that explains and evidences the POC.

Run locally:  streamlit run app/app.py   (reads RESULTS_ROOT, else the bundled copies)
On Databricks: deployed from the repository root; reads the results volume.

Reading order: Start here (the problem, how it works) is common to everyone; then
the Executive view (results, decision) or the Technical view (data, evidence,
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

# ------------------------------------------------------------------ start here


def page_problem():
    ui.page_head(
        "Start here",
        "Payment changes can silently break controls, because the map that links them is incomplete",
        "A one-minute read for everyone, before any results. It sets out the situation, the problem, "
        "the question this proof of concept answers, and the short answer.",
        step="1 of 2",
    )
    st.markdown(
        '<div class="scq">'
        '<div><div class="s">Situation</div><p>A bank relies on about a hundred controls on its payment flow, '
        "such as blocking sanctioned parties before release. Each depends on fields, rules and systems.</p></div>"
        '<div><div class="s">Complication</div><p>Every change must be checked against the controls it touches. '
        "The lineage map used for this is incomplete exactly where change happens; with 30% of links missing, "
        "a rules engine finds only 11% of the affected key controls.</p></div>"
        '<div><div class="s">Question</div><p>Can an AI agent find the affected controls the rules miss, by reading '
        "the ticket and the control procedures as a reviewer would, and show its evidence?</p></div>"
        '<div class="answer"><div class="s">Answer</div><p>Mostly yes. On 18 changes it had never seen it recovered '
        "78% of the key controls the rules missed, 94% of its additions correct. Its review list is still too long "
        "and not yet repeatable enough for production.</p></div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("### One change, traced")
    ui.broken_link_animation()
    st.markdown(
        "A release changes the debtor town-name field. In the complete map it feeds an address rule, "
        "which feeds the required-field controls. That one link is missing, so a rules engine walking the map "
        "stops and reports nothing for those controls. A person reading the ticket and the control procedures "
        "would still see the connection. That reading is what the agent automates."
    )
    with st.expander("Terms used in this dashboard"):
        st.dataframe(
            pd.DataFrame(content.GLOSSARY, columns=["Term", "Meaning"]),
            hide_index=True,
            use_container_width=True,
        )
    ui.next_hint(
        "Next: <b>How it works</b>, the steps from change ticket to review list."
    )


def page_how():
    ui.page_head(
        "Start here",
        "The agent reads what a reviewer would read, and every finding is checked twice before anyone sees it",
        "From a change ticket to a review list in four steps. Nothing is assumed safe, and every claim carries "
        "evidence a person can check.",
        step="2 of 2",
    )
    ui.flow_diagram()
    ui.keylines(
        [
            (
                "It starts where the rules stop",
                "The rules method walks the visible links. The agent starts from that result and reads the ticket, "
                "the items' descriptions and the control procedures to find what the broken links hide.",
            ),
            (
                "Every finding is checked twice",
                "Quotes must appear word for word in the ticket and the procedure, or the finding is rejected. "
                "A second, independent model call then agrees or disagrees.",
            ),
            (
                "People decide the uncertain cases",
                "Agreed findings are recommended. Disagreements go to a person with both arguments. "
                "Controls without a decision are reported, never assumed safe.",
            ),
        ],
        [ui.BLUE, ui.GREEN, ui.AMBER],
    )
    st.markdown("### What a reviewer receives")
    st.markdown(
        "One real output: a screening-engine change from the held-out test (CHG-015), the hardest change type."
    )
    r = find_run(runs, "heldout")
    res = data.case_result(r["folder"], "run1", "CHG-015") if r else None
    if res:
        reviewer_queue(data.decisions_table(res), compact=True)
    with st.expander("The agent's tools (all read-only)"):
        st.dataframe(
            pd.DataFrame(
                [
                    ("trace_metadata", "Runs the rules method on the visible links"),
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
                columns=["Tool", "What it does"],
            ),
            hide_index=True,
            use_container_width=True,
        )
    ui.next_hint(
        "Next: <b>Executive view · Results</b> for the outcome, or <b>Technical view</b> for the test data and evidence."
    )


# ------------------------------------------------------------------ executive


def page_results():
    rules_found = 162 - H["key_misses"]
    still = H["key_misses"] - H["key_recovered"]
    ui.page_head(
        "Executive view",
        "The agent recovers four in five of the key controls the rules miss; the review list is not yet lean or repeatable",
        f"Measured on 18 payment changes the agent had never seen, with 30% of the lineage removed. "
        f"Version A, frozen before the test, one run.",
    )
    ui.kpis(
        [
            (
                pct(H["key_miss_recovery"], 0),
                "of missed key controls recovered",
                "Target 50%. 95% range 71–84%.",
            ),
            (
                pct(H["new_control_precision"], 0),
                "of its recommendations correct",
                f"{262} of {280} new recommendations",
            ),
            (
                f"{H['avoidable_review_items_per_case']:.1f}",
                "unaffected review items per change",
                "75 across 18 changes",
            ),
            (pct(cons["agreement"], 0), "same decision across 5 runs", "Target 95%"),
        ]
    )
    st.markdown("### Where the 162 affected key controls ended up")
    parts = pd.DataFrame(
        [
            {"part": "Found by the rules method", "n": rules_found, "o": 1},
            {"part": "Recovered by the agent", "n": H["key_recovered"], "o": 2},
            {"part": "Still missed", "n": still, "o": 3},
        ]
    )
    colors = [ui.BLUE, ui.GREEN, ui.GREY]
    bar = (
        alt.Chart(parts)
        .mark_bar(height=46, stroke="white", strokeWidth=2)
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
            fontSize=14,
            fontWeight=600,
            font="IBM Plex Sans, Helvetica, Arial, sans-serif",
        )
        .encode(
            x="mid:Q",
            text="n:Q",
            color=alt.condition("datum.o == 3", alt.value(ui.INK), alt.value("white")),
        )
    )
    st.altair_chart(
        (bar + text).properties(height=60).configure_view(strokeWidth=0),
        use_container_width=True,
    )
    ui.legend(list(zip(parts["part"], colors)))
    ui.keylines(
        [
            (
                "It finds what the rules miss",
                f"{H['key_recovered']} of {H['key_misses']} missed key controls recovered, each with quoted evidence; "
                "18 of 280 new recommendations were wrong. 30 of the 31 still missed reached a person as review items.",
            ),
            (
                "The review list is long, but mostly real",
                "406 items beyond the rules method's 64. 331 of them are truly affected controls; "
                "75 (4.2 per change) are not. The original volume target counts the useful finds as burden.",
            ),
            (
                "It is not yet repeatable enough",
                "Across five runs, 80% of key decisions were identical, against a 95% target. "
                "Recovery itself was stable; which items go to review varied.",
            ),
        ],
        [ui.GREEN, ui.AMBER, ui.RED],
    )
    st.markdown("### Scorecard against the targets set at the start")
    ui.score_table(
        [
            (
                "Runs end to end on Databricks",
                ui.badge("Done", "ok"),
                "Live jobs on gpt-oss-120b; every step logged and replayable.",
            ),
            (
                "Recover ≥ 50% of missed key controls",
                ui.badge("Met", "ok"),
                f"{pct(H['key_miss_recovery'])} on unseen changes.",
            ),
            (
                "Added review volume ≤ 25%",
                ui.badge("Not met", "bad"),
                "406 added items vs 64; 81% of them truly affected.",
            ),
            (
                "Same key decision across 5 runs ≥ 95%",
                ui.badge("Not met", "bad"),
                f"{pct(cons['agreement'], 0)}.",
            ),
        ]
    )
    ui.callout(
        "<b>Final version: A.</b> Three alternatives aimed at the two unmet targets were each tested against a rule "
        "written before the run. None met all of its rule, so none was adopted. Details under Technical view · Evidence."
    )
    ui.next_hint("Next: <b>Decision and next steps</b>.")


def page_decision():
    ui.page_head(
        "Executive view",
        "Continue to a practitioner review; a production pilot should wait",
        "The stop rule agreed in advance was not triggered. The two gaps that remain have candidate fixes, tested but not yet good enough.",
    )
    ui.keylines(
        [
            (
                "Continue",
                "Held-out recovery was 78% against a stop line of 50%, on changes never used for tuning. "
                "The development check (65%) was lower, so the method was not overfitted.",
            ),
            (
                "Next: control owners review real output",
                "A sample of recommended and review items from the held-out run, judged by practitioners. "
                "This is the evidence the benchmark cannot give.",
            ),
            (
                "Not yet: a production pilot",
                "Decisions are 80% repeatable against 95%, and no practitioner has reviewed findings. "
                "Both must close first.",
            ),
        ],
        [ui.GREEN, ui.BLUE, ui.AMBER],
    )
    st.markdown("### Next steps, in order")
    st.markdown(
        "1. **Practitioner review** of a held-out sample: are the recommendations and review items right and useful?\n"
        "2. **Repeatability:** a five-run vote, registered in advance and tested on changes not used before "
        "(a three-run vote reached 94.4%).\n"
        "3. **Review volume:** a tie-break that may only promote findings. It was right in 68 of 70 promotions; "
        "it was its dismissals that dropped real impacts.\n"
        "4. **Pilot decision** on a small real change set with control owners."
    )
    st.markdown("### Known limits")
    ui.score_table(
        [
            (
                ui.esc(i),
                "",
                f"{ui.esc(e)}<br><span style='color:#5B6675'>{ui.esc(r)}</span>",
            )
            for i, e, r in content.LIMITS
        ]
    )


# ------------------------------------------------------------------ technical: evidence


def page_evidence():
    ui.page_head(
        "Technical view",
        "Every result comes from a run whose plan and adoption rule were fixed before it ran",
        "Development results are labelled as such. Only the held-out run is the headline.",
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
            "Changes where the rules already found every key control are not shown."
        )

    st.markdown("### Versions tested to close the two gaps")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Version": "B · stricter agent",
                    "Test": "8 unseen development changes",
                    "Rule fixed in advance": "Unaffected items ≥ 30% fewer; recovery within 3",
                    "Result": "Unaffected 56 → 46 (−18%); recovered 32 → 27",
                    "Decision": "Not adopted",
                },
                {
                    "Version": "C · sweep, re-check, tie-break, 3-run vote",
                    "Test": "18 test changes, fresh random damage",
                    "Rule fixed in advance": "Two votes agree ≥ 95%; recovery ≥ 50%; unaffected ≤ 3 per change",
                    "Result": "Agree 94.4% (needed 95%); recovery 52.7%; unaffected 0.33 per change; ≈ 4× cost",
                    "Decision": "Not adopted",
                },
                {
                    "Version": "D · A + tie-break",
                    "Test": "5 fresh development changes, 2 runs each",
                    "Rule fixed in advance": "Recovery ≥ A; unaffected ≤ A; repeatability ≥ A",
                    "Result": "Recovered 18 vs 20 of 32; unaffected 16 vs 30",
                    "Decision": "Not adopted",
                },
                {
                    "Version": "A + tie-break on A's saved runs",
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


# ------------------------------------------------------------------ technical: architecture


def page_architecture():
    ui.page_head(
        "Technical view",
        "Everything runs inside one Databricks workspace, and the answer key never reaches the model",
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
    with st.expander("Reproduce the results"):
        st.markdown(content.REPRO)
    with st.expander("Results summary used by the assistant"):
        st.code(results_summary_text())


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
        "A complete, known map of 148 items lets every answer be scored exactly",
        "An invented but realistic model of one bank's outbound cross-border payments. The full map is known, "
        "so the right answer for every change is known; the agent only ever sees a damaged copy. "
        "No real bank, customer or control data is used.",
    )
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

    t1, t2, t3, t4 = st.tabs(
        [
            "What is in it",
            "Worked example",
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
            st.markdown("**Step 2 · What the AI and the rules see (30% damaged)**")
            st.markdown(
                f"{len(ex['removed'])} of {ex['edges_exposable']} visible links are removed, nearest the change first. "
                f"{len(ex['removed_on_paths'])} of them lie on the paths above. The rules method, walking only what is left, "
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
                f"**Step 3 · What the AI agent did.** Of the {len(missed)} affected controls the rules missed, "
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
            "The detective's job is to recover the pink controls the rules miss, using the item names, descriptions "
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
                    "affected controls the rules find",
                    None,
                ),
                (
                    f"{len(ex4['key_misses'])} of {len(ex4['key'])}",
                    "key controls the rules miss",
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
                        "Key controls the rules find (test changes)": "100%",
                        "Missed": 0,
                    },
                    {
                        "Damage": "30% near the change (main)",
                        "Key controls the rules find (test changes)": "11.1%",
                        "Missed": 144,
                    },
                    {
                        "Damage": "30% random",
                        "Key controls the rules find (test changes)": "43%",
                        "Missed": 93,
                    },
                    {
                        "Damage": "60% near the change",
                        "Key controls the rules find (test changes)": "7.4%",
                        "Missed": 150,
                    },
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )


# ------------------------------------------------------------------ technical: case explorer


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
        .mark_bar(size=16)
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


def reviewer_queue(rows, compact=False):
    """The output as a control reviewer would get it, with the answer key optional."""
    show_key = st.toggle(
        "Show the answer key (a real reviewer would not have it)",
        value=False,
        key=f"showkey_{compact}",
    )
    rules = [r for r in rows if r["outcome"].startswith("Rules")]
    ai = [r for r in rows if r["outcome"] in ("Correct recovery", "False flag")]
    review = [r for r in rows if r["outcome"].startswith("Sent to review")]

    def table(items, cols):
        df = pd.DataFrame(
            [
                {
                    "Control": r["control"] + (" (key)" if r["key"] else ""),
                    "Procedure": r["title"],
                    **{k: f(r) for k, f in cols.items()},
                    **({"Answer key": r["answer_key"]} if show_key else {}),
                }
                for r in items
            ]
        )
        st.dataframe(df, hide_index=True, use_container_width=True)

    ui.legend(
        [
            (f"Recommended, found by the rules method: {len(rules)}", ui.BLUE),
            (f"Recommended, added by the agent: {len(ai)}", ui.GREEN),
            (f"For a person to decide: {len(review)}", ui.AMBER),
        ]
    )
    st.markdown(
        f"**1 · Recommended: already linked in the lineage ({len(rules)}).** Found by following the visible links."
    )
    if rules and not compact:
        table(rules, {})
    elif rules:
        st.caption(", ".join(r["control"] for r in rules))
    st.markdown(
        f"**2 · Recommended: added by the AI, agreed by the verifier ({len(ai)}).** Each cites the ticket and the procedure."
    )
    if ai:
        table(ai, {"Why the AI says it is affected": lambda r: r["agent_reason"]})
    st.markdown(
        f"**3 · For review: the AI and the verifier disagreed ({len(review)}).** "
        "Usually because no visible link connects the change to the control. A person decides."
    )
    if review:
        table(
            review,
            {
                "AI: why affected": lambda r: r["agent_reason"],
                "Verifier: why not sure": lambda r: r["verifier_reason"],
            },
        )
    if show_key and review:
        true = sum(r["outcome"] == "Sent to review (affected)" for r in review)
        st.caption(
            f"{true} of the {len(review)} review items are truly affected in the answer key."
        )


def page_explorer():
    ui.page_head(
        "Technical view",
        "Every decision the agent made, checked against the answer key it never saw",
        "Pick a run and a change. The first tab is the review list as a control reviewer would get it; "
        "the others compare each decision with the answer key and list every step.",
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
        format_func=lambda c: f"{c} · {key.get(c, {}).get('title', '')}",
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
        "Answers come only from the project documents and the recorded results. If they do not cover a question, the answer says so.",
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
    return st.Page(fn, title=title, url_path=fn.__name__[5:], default=default)


VIEWS = {
    "Start here": [
        _page(page_problem, "1  The problem", default=True),
        _page(page_how, "2  How it works"),
    ],
    "Executive view": [
        _page(page_results, "Results"),
        _page(page_decision, "Decision and next steps"),
    ],
    "Technical view": [
        _page(page_synthetic, "The synthetic data"),
        _page(page_evidence, "Evidence"),
        _page(page_explorer, "Case explorer"),
        _page(page_architecture, "Architecture and method"),
    ],
    "Help": [
        _page(page_faq, "Questions and answers"),
        _page(page_ask, "Ask the assistant"),
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
        st.markdown(f'<div class="navhead">{view}</div>', unsafe_allow_html=True)
        for pg in pages:
            st.page_link(pg)
    source = (
        "live run files"
        if any(r.get("live") for r in runs)
        else "recorded run files shipped with the app"
    )
    st.markdown(
        f'<div class="sidefoot">Final version A, frozen {FROZEN_ON}.<br>'
        f"Synthetic benchmark; no real bank data.<br>Results from {source}.</div>",
        unsafe_allow_html=True,
    )
nav.run()
