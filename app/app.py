def page_decision():
    ui.overview_css()
    ui.page_head("Client decision", "Validate with practitioners before piloting",
                 "A controlled next step is justified; production readiness is not established.",
                 synthetic=True)
    st.markdown("### What the evidence says")
    st.markdown("**113** key-control misses recovered; **1** key-control impact silently missed; **80%** repeatability against the original 95% target.")
    st.markdown("### What we recommend")
    st.write("Have payment-control owners assess recorded findings and excluded controls, investigate the silent miss, and time their work. Measure model cost and consistency before claiming ROI.")
    st.warning("Synthetic benchmark only. No real bank data, completed practitioner validation, or demonstrated net savings.")
    with st.expander("Compare baseline and AI-assisted review cost"):
        executive_value_case()
    with st.expander("Inspect delivery readiness and remaining gaps"):
        delivery_readiness()
    with st.expander("Technical limitations and provenance"):
        provenance()
    download_summary()
    st.page_link(PAGES["case"], label="Investigate the evidence →")


def page_decision():
    """Interactive client-facing room; detailed technical pages remain available."""
    st.markdown("""<style>
    [data-testid="stMainBlockContainer"], .block-container {max-width:100%!important;padding:0!important;}
    [data-testid="stMain"] {background:#0b1019;}
    iframe {border:0!important;display:block;}
    </style>""", unsafe_allow_html=True)
    client_rooms.show("decision")
    st.page_link(PAGES["case"], label="Inspect the case evidence →")


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
    st.markdown('<div class="navhead">CLIENT EXPERIENCE</div>', unsafe_allow_html=True)
    for pg in VIEWS["Decision"]:
        st.page_link(pg)
    st.markdown('<div class="navhead">EXPLORE THE PROOF</div>', unsafe_allow_html=True)
    for pg in VIEWS["Investigation"]:
        st.page_link(pg)
    with st.expander("Technical diligence and reference"):
        for pg in VIEWS["Technical evidence"] + VIEWS["Reference"]:
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
nav.run()def page_results():
    """Interactive client-facing room; detailed technical pages remain available."""
    st.markdown("""<style>
    [data-testid="stMainBlockContainer"], .block-container {max-width:100%!important;padding:0!important;}
    [data-testid="stMain"] {background:#0b1019;}
    iframe {border:0!important;display:block;}
    </style>""", unsafe_allow_html=True)
    client_rooms.show("evaluation")
    st.page_link(PAGES["evidence"], label="Inspect run-level evidence →")



def page_decision():
    """Interactive client-facing room; detailed technical pages remain available."""
    st.markdown("""<style>
    [data-testid="stMainBlockContainer"], .block-container {max-width:100%!important;padding:0!important;}
    [data-testid="stMain"] {background:#0b1019;}
    iframe {border:0!important;display:block;}
    </style>""", unsafe_allow_html=True)
    client_rooms.show("decision")
    st.page_link(PAGES["case"], label="Inspect the case evidence →")


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
    st.markdown('<div class="navhead">CLIENT EXPERIENCE</div>', unsafe_allow_html=True)
    for pg in VIEWS["Decision"]:
        st.page_link(pg)
    st.markdown('<div class="navhead">EXPLORE THE PROOF</div>', unsafe_allow_html=True)
    for pg in VIEWS["Investigation"]:
        st.page_link(pg)
    with st.expander("Technical diligence and reference"):
        for pg in VIEWS["Technical evidence"] + VIEWS["Reference"]:
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
