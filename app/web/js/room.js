// The evidence room: methodology, results, every held-out change, the
// pre-registered tests, architecture, limits, reproducibility and Q&A.

import { esc, pct, el, ROUTE_LABEL, TYPE_LABEL } from "./util.js";
import { createGraph } from "./graph.js";
import { go, openInspector, getCase } from "./main.js";

export const ROOM_PAGES = [
  { id: "method", label: "Benchmark and method" },
  { id: "results", label: "Results" },
  { id: "changes", label: "All 18 test changes" },
  { id: "tests", label: "Versions tested" },
  { id: "architecture", label: "Architecture" },
  { id: "limits", label: "Limits" },
  { id: "reproduce", label: "Reproduce" },
  { id: "ask", label: "Ask about the POC" },
];

export async function renderRoom(main, app, c, page) {
  const room = el(`<div class="room"><nav aria-label="Evidence room"><h2>Evidence room</h2>
    ${ROOM_PAGES.map((p) => `<a href="#/room/${p.id}?case=${app.caseId}" ${p.id === page ? 'aria-current="page"' : ""}>${esc(p.label)}</a>`).join("")}</nav>
    <div class="pane" id="pane"></div></div>`);
  main.append(room);
  const pane = room.querySelector("#pane");
  await (PAGES[page] || PAGES.method)(pane, app, c);
}

const table = (head, rows, cls = "") =>
  `<table class="t ${cls}"><thead><tr>${head.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody></table>`;

const PAGES = {
  async method(pane, app) {
    const B = app.exp.benchmark;
    const tc = app.graph.type_counts;
    const lc = app.graph.link_counts;
    pane.innerHTML = `<h1>Benchmark and method</h1>
      <p class="lead">An invented bank's outbound cross-border payments, built so that the right answer for every change is known. The agent only ever sees a damaged copy of the map.</p>
      <section><div class="counters" style="grid-template-columns:repeat(4,minmax(0,1fr))">
        <div class="counter ink"><div class="v">${B.items}</div><div class="l">items in the complete map</div></div>
        <div class="counter ink"><div class="v">${B.links}</div><div class="l">directed links between them</div></div>
        <div class="counter ink"><div class="v">${B.controls}</div><div class="l">controls, ${B.key_controls} of them key</div></div>
        <div class="counter ink"><div class="v">${B.changes}</div><div class="l">change scenarios, ${B.held_out} held out for the test</div></div></div></section>
      <section><h2>How it is scored</h2>
        <p><b>Answer key.</b> A control is affected when the changed item reaches it by following impact-carrying links in their direction through the complete map, at most six steps, stopping at the first control. This is plain code; no model labels anything.</p>
        <p><b>Damage.</b> For each change, 30% of the 237 recordable links are removed, nearest the change first, while keeping most of the changed item's own links; tickets may lose a sentence, use a legacy name, or wrongly say "control impact: N/A".</p>
        <p><b>Comparison.</b> The current check follows the remaining links. The agent starts from its result and reads the ticket, the item descriptions and the control procedures. Both are scored against the answer key; only key controls the check missed count towards recovery.</p></section>
      <section><h2>What the damage does to the current check</h2>${table(
        ["Lineage damage", "Key controls the check finds (18 test changes)"],
        app.exp.rules_by_damage.map((r) => `<tr><td>${esc(r.damage)}</td><td class="num">${pct(r.found, 1)}</td></tr>`)
      )}</section>
      <section><h2>Items and links</h2><div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">${table(
        ["Item type", "Count"],
        Object.entries(tc).map(([k, v]) => `<tr><td>${esc(TYPE_LABEL[k])}</td><td class="num">${v}</td></tr>`)
      )}${table(
        ["Link type", "Count"],
        Object.entries(lc).sort((a, b) => b[1] - a[1]).map(([k, v]) => `<tr><td>${esc(k.toLowerCase().replace("_", " "))}</td><td class="num">${v}</td></tr>`)
      )}</div></section>
      <section><h2>The complete map</h2><p style="color:var(--ink-2)">All 148 items. Drag to pan, scroll or use the buttons to zoom; click an item for its links.</p>
        <div class="graph-wrap" id="full" style="height:620px"></div></section>`;
    const c = await getCase(app.caseId);
    const g = createGraph(pane.querySelector("#full"), {
      nodes: app.graph.nodes,
      edges: app.graph.edges.filter((e) => e.carries_impact),
      layout: app.graph.layout,
      label: "The complete synthetic map",
      onSelect: (id) => openInspector(id),
    });
    g.update({ node: (id) => (c.changed.includes(id) ? "changed" : ""), edge: () => "vis" });
  },

  async results(pane, app) {
    const P = app.exp.portfolio;
    const fr = app.exp.development_runs.frozen_check;
    const vb = app.exp.development_runs.variant_b;
    pane.innerHTML = `<h1>Results</h1>
      <p class="lead">Held-out test: 18 synthetic changes never used while building the agent, version A frozen before the run, one run. Development results are labelled as such.</p>
      <section><h2>Against the targets set at the start</h2>${table(["Target", "Result", "Status"], [
        `<tr><td>Find ≥ 50% of the key controls the check misses</td><td>${P.agent_found_key} of ${P.key_misses} (${pct(P.recovery, 1)}; 95% range ${pct(P.recovery_interval[0], 1)}–${pct(P.recovery_interval[1], 1)})</td><td><span class="badge recommended">Met</span></td></tr>`,
        `<tr><td>Added review volume ≤ 25% of the check's</td><td>${P.added_items} added vs ${P.check_items}. The target counts every added item, including the ${P.added_affected} genuinely affected ones; this tension was noted before any results and the target was kept as written.</td><td><span class="badge review">Not met as defined</span></td></tr>`,
        `<tr><td>Same key decision across 5 runs ≥ 95%</td><td>${Math.round(P.consistency.agreement * P.consistency.pairs)} of ${P.consistency.pairs} (${pct(P.consistency.agreement)}), three development changes</td><td><span class="badge review">Not met</span></td></tr>`,
      ])}</section>
      <section><h2>Where the 162 key-control impacts went</h2>${table(["", "Count"], [
        `<tr><td>Found by the current check</td><td class="num">${P.check_found_key}</td></tr>`,
        `<tr><td>Recommended by the agent (and actually affected)</td><td class="num">${P.agent_found_key}</td></tr>`,
        `<tr><td>Routed to a person after the agent and its checker disagreed</td><td class="num">${P.key_routed}</td></tr>`,
        `<tr><td>Not surfaced</td><td class="num">${P.key_silent}</td></tr>`,
      ])}</section>
      <section><h2>By change type</h2>${table(["Change type", "Changes", "Key misses", "Recommended", "Routed", "Not surfaced"], Object.entries(P.by_type).map(
        ([k, v]) => `<tr><td>${esc(k)}</td><td class="num">${v.changes}</td><td class="num">${v.key_misses}</td><td class="num">${v.found}</td><td class="num">${v.routed}</td><td class="num">${v.silent}</td></tr>`
      ))}<p style="font-size:13px;color:var(--ink-3)">Screening-engine changes are the weak spot: the checker withholds agreement when no visible link connects the engine to the control, so most findings are routed rather than recommended.</p></section>
      <section><h2>Review items added</h2>${table(["", "Items", "Per change"], [
        `<tr><td>From the current check</td><td class="num">${P.check_items}</td><td class="num">${P.per_change.check}</td></tr>`,
        `<tr><td>Added by the agent, genuinely affected</td><td class="num">${P.added_affected}</td><td class="num">${P.per_change.real}</td></tr>`,
        `<tr><td>Added by the agent, not affected</td><td class="num">${P.added_unaffected}</td><td class="num">${P.per_change.unaffected}</td></tr>`,
      ])}</section>
      <section><h2>Development runs (not the headline)</h2>${table(["Run", "Changes", "Key misses found", "Precision", "Unaffected items"], [
        fr && `<tr><td>Frozen check, version A, unseen development changes</td><td class="num">${fr.cases ?? 8}</td><td class="num">${fr.key_recovered} of ${fr.key_misses}</td><td class="num">${pct(fr.new_control_precision, 1)}</td><td class="num">${fr.avoidable_review_items}</td></tr>`,
        vb && `<tr><td>Version B on the same changes</td><td class="num">${vb.cases ?? 8}</td><td class="num">${vb.key_recovered} of ${vb.key_misses}</td><td class="num">${pct(vb.new_control_precision, 1)}</td><td class="num">${vb.avoidable_review_items}</td></tr>`,
      ].filter(Boolean))}</section>`;
  },

  async changes(pane, app, c) {
    const rows = app.exp.cases.map(
      (x) => `<tr class="click" data-id="${x.id}" tabindex="0"><td>${esc(x.id)}</td><td>${esc(x.title)}</td><td class="num">${x.affected}</td><td class="num">${x.key_affected}</td><td class="num">${x.check_found_key}</td><td class="num">${x.key_found_by_agent}</td><td class="num">${x.key_routed}</td><td class="num">${x.key_silent}</td><td class="num">${x.model_calls}</td></tr>`
    );
    pane.innerHTML = `<h1>All 18 test changes</h1><p class="lead">Select a change to see every control decision against the answer key, and open any control's evidence.</p>
      <section>${table(["Change", "Title", "Affected", "Key", "Key: check", "Key: agent", "Key: routed", "Key: not surfaced", "Model calls"], rows)}</section>
      <section id="detail"></section>`;
    const detail = pane.querySelector("#detail");
    const show = async (id) => {
      const k = await getCase(id);
      pane.querySelectorAll("tr[data-id]").forEach((r) => (r.style.background = r.dataset.id === id ? "var(--agent-soft)" : ""));
      let filter = "issues";
      const draw = () => {
        const ds = k.decisions.filter((d) => {
          if (filter === "issues") return (d.truth && !["check", "recommended"].includes(k.baselineSet.has(d.control) ? "check" : d.route)) || (!d.truth && ["recommended", "review"].includes(d.route));
          if (filter === "affected") return d.truth;
          return true;
        });
        detail.querySelector("#dt").innerHTML = table(
          ["Control", "Name", "Key", "Decision", "Answer key"],
          ds.map((d) => {
            const r = k.baselineSet.has(d.control) ? "check" : d.route;
            const n = app.graph.nodes.find((x) => x.id === d.control);
            return `<tr class="click" data-c="${d.control}" tabindex="0"><td>${esc(d.control)}</td><td>${esc(n.name)}</td><td>${d.key ? "key" : ""}</td><td><span class="badge ${r}">${esc(ROUTE_LABEL[r])}</span></td><td>${d.truth ? "affected" : "not affected"}</td></tr>`;
          })
        );
        detail.querySelectorAll("tr[data-c]").forEach((r) => {
          const open = () => openInspector(r.dataset.c, id);
          r.addEventListener("click", open);
          r.addEventListener("keydown", (e) => e.key === "Enter" && open());
        });
      };
      detail.innerHTML = `<h2>${esc(k.id)} · ${esc(k.title)}</h2>
        <div class="filters"><div class="seg" role="group" aria-label="Filter">
          <button type="button" data-f="issues" aria-pressed="true">Misses and wrong flags</button>
          <button type="button" data-f="affected" aria-pressed="false">All affected</button>
          <button type="button" data-f="all" aria-pressed="false">Every decision</button></div>
          <a class="btn" href="#/investigate?case=${k.id}">Replay this investigation</a></div><div id="dt"></div>`;
      detail.querySelectorAll("[data-f]").forEach((b) =>
        b.addEventListener("click", () => {
          filter = b.dataset.f;
          detail.querySelectorAll("[data-f]").forEach((x) => x.setAttribute("aria-pressed", x === b));
          draw();
        })
      );
      draw();
    };
    pane.querySelectorAll("tr[data-id]").forEach((r) => {
      r.addEventListener("click", () => show(r.dataset.id));
      r.addEventListener("keydown", (e) => e.key === "Enter" && show(r.dataset.id));
    });
    show(c.id);
  },

  async tests(pane, app) {
    pane.innerHTML = `<h1>Versions tested to close the gaps</h1>
      <p class="lead">Each alternative was registered with an adoption rule before it ran. None met all of its rules, so the original agent (version A) is final.</p>
      ${table(["Version", "Test", "Rule fixed in advance", "Result", "Decision"], app.exp.version_tests.map(
        (v) => `<tr><td><b>${esc(v.name)}</b><br><span style="color:var(--ink-3);font-size:12px">${esc(v.version)}</span></td><td>${esc(v.test)}</td><td>${esc(v.rule)}</td><td>${esc(v.result)}</td><td><span class="badge not_affected">${esc(v.decision)}</span></td></tr>`
      ))}
      <p style="font-size:13px;color:var(--ink-3);margin-top:12px">Source: ${esc(app.exp.version_tests.map((v) => v.source.split(" · ")[1]).join("; "))}, in docs/results.md.</p>
      <section style="margin-top:24px"><h2>What was learnt</h2><p>The tie-break is reliable when it promotes a finding (68 of 70 promotions were right) but not when it dismisses one. Voting across runs steadies decisions, but a three-run vote reached 94.4%, just short of 95%.</p></section>`;
  },

  async architecture(pane) {
    pane.innerHTML = `<h1>Architecture</h1><p class="lead">Everything runs inside one Databricks workspace. The answer key is used only for scoring and never reaches the model.</p>
      <section><div class="arch">
        <div class="lane"><h3>Build · Git folder</h3><div class="box"><b>Benchmark generator</b>148 items, 238 links, 54 changes</div><div class="box"><b>Damage step</b>removes 30% of links, damages tickets</div><div class="box key"><b>Answer key</b>computed offline; scoring only</div></div>
        <div class="lane"><h3>Run · Databricks Jobs</h3><div class="box"><b>Detective job</b>one agent run per change; resumable; every step saved</div><div class="box"><b>Model Serving</b>databricks-gpt-oss-120b, temperature 0</div><div class="box"><b>Scorer</b>compares decisions with the answer key</div></div>
        <div class="lane"><h3>Store and show</h3><div class="box"><b>Unity Catalog volume</b>run files: steps, findings, metrics</div><div class="box"><b>Databricks App</b>this experience, served from recorded files</div></div>
      </div></section>
      <section><h2>Who decides what</h2>${table(["", "Decides"], [
        `<tr><td><b>Fixed code</b> (same answer every time)</td><td>The benchmark and damage; the current check; the quote check (quotes must match word for word); scoring.</td></tr>`,
        `<tr><td><b>The model</b></td><td>Which items to explore and procedures to read; each control's decision and reason; the independent second opinion.</td></tr>`,
        `<tr><td><b>People</b></td><td>Every item the two model calls disagree on; the final call on any impact; any change to lineage or controls (the agent changes nothing).</td></tr>`,
      ])}</section>
      <section><h2>Boundaries</h2>${table(["", ""], [
        `<tr><td>Read-only</td><td>The agent's tools only read. It never writes lineage links or edits controls.</td></tr>`,
        `<tr><td>Not connected</td><td>No real payment systems, change tools or control repositories. All data is synthetic.</td></tr>`,
        `<tr><td>Isolation</td><td>Tests check that answer-key labels never appear in a prompt.</td></tr>`,
      ])}</section>
      <section><h2>The agent's tools</h2>${table(["Tool", "What it does"], [
        ["trace_metadata", "Runs the current check on the visible links"],
        ["explore_node", "Shows a field, rule or system with its visible links"],
        ["search_controls", "Ranks control procedures by matching words"],
        ["inspect_control", "Reads up to 15 procedures; required before a finding"],
        ["submit_findings", "Up to 8 decisions with quotes, reason and counter-evidence"],
        ["finish", "Stops; refused while controls are undecided"],
      ].map(([a, b]) => `<tr><td>${a}</td><td>${b}</td></tr>`))}</section>`;
  },

  async limits(pane, app) {
    pane.innerHTML = `<h1>Limits</h1><p class="lead">What the proof of concept does not show, and what is known to go wrong.</p>
      ${table(["Issue", "Evidence", "Response"], app.exp.limits.map((l) => `<tr><td><b>${esc(l.issue)}</b></td><td>${esc(l.evidence)}</td><td>${esc(l.response)}</td></tr>`))}
      <section style="margin-top:24px"><h2>Not measured, not claimed</h2><p>Reviewer time, accuracy on real bank data, cost or savings, and any production outcome. Routing an item to a person is not a completed review.</p></section>
      <section><h2>Terms</h2>${table(["Term", "Meaning"], app.exp.glossary.map((g) => `<tr><td><b>${esc(g.term)}</b></td><td>${esc(g.meaning)}</td></tr>`))}</section>`;
  },

  async reproduce(pane, app) {
    const p = app.exp.provenance;
    pane.innerHTML = `<h1>Reproduce</h1><p class="lead">Every figure in this experience is exported from the repository by one script, and checked by tests against the recorded run archive.</p>
      <section>${table(["", ""], [
        `<tr><td>Held-out run</td><td>Databricks job ${esc(p.job)}, ${esc(p.date)}, version ${esc(p.version)}, agent code ${esc(p.code)}, ${esc(p.model)}</td></tr>`,
        `<tr><td>Condition</td><td>${esc(p.condition)}</td></tr>`,
        `<tr><td>Recorded files</td><td>${esc(p.archive)} (heldout-final/run1)</td></tr>`,
      ])}</section>
      <section><h2>Commands</h2><pre class="code">python -m pip install -r requirements-dev.txt
python -m pytest -q                         # includes the checks on every figure shown here
python -m scripts.validate_graph            # benchmark integrity
python -m scripts.evaluate_baseline         # the current check on every change
python -m scripts.build_experience_data     # re-export app/web/data from the recorded runs

# re-run the agent on Databricks (model endpoint required)
python -m pip install -r requirements-llm.txt
python -m scripts.detective_job submit --repo /Workspace/Users/&lt;you&gt;/payments-control-impact ...
python -m scripts.detective_job status &lt;run_id&gt;</pre>
      <p style="font-size:13px;color:var(--ink-3)">Full instructions: docs/runbook.md. Pre-registrations and results: docs/results.md.</p></section>`;
  },

  async ask(pane) {
    pane.innerHTML = `<h1>Ask about the proof of concept</h1>
      <p class="lead">Answers come only from the project's documents and recorded results, using the workspace model endpoint. If they do not cover a question, the answer says so. Like any model, it can be wrong: check figures against the Results page.</p>
      <form class="ask" id="f"><input id="q" placeholder="For example: why is consistency below target?" aria-label="Your question"><button class="btn primary" type="submit">Ask</button></form>
      <div id="a"></div>`;
    pane.querySelector("#f").addEventListener("submit", async (e) => {
      e.preventDefault();
      const q = pane.querySelector("#q").value.trim();
      if (!q) return;
      const out = pane.querySelector("#a");
      out.innerHTML = `<div class="answer">Reading the project material…</div>`;
      try {
        const r = await fetch("api/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: q }) });
        const j = await r.json();
        out.innerHTML = `<div class="answer">${esc(j.answer || j.error || "No answer.")}</div>`;
      } catch (err) {
        out.innerHTML = `<div class="answer">The assistant is not available here (${esc(err.message)}). The Results and Limits pages answer the common questions.</div>`;
      }
    });
  },
};
