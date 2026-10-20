// The evidence room: methodology, results, every held-out change, the
// pre-registered tests, architecture, limits, reproducibility and Q&A.

import { esc, pct, el, ROUTE_LABEL, TYPE_LABEL } from "./util.js";
import { createGraph } from "./graph.js";
import { go, openInspector, getCase } from "./main.js";

export const ROOM_PAGES = [
  { id: "method", label: "Benchmark and method" },
  { id: "results", label: "Results" },
  { id: "changes", label: "All 18 test changes" },
  { id: "architecture", label: "Architecture" },
  { id: "limits", label: "Limits and fixes tried" },
  { id: "reproduce", label: "Reproduce" },
  { id: "ask", label: "Ask about the POC" },
];

export async function renderRoom(main, app, c, page) {
  const room = el(`<div class="room"><nav aria-label="Evidence room"><h2>Evidence room</h2>
    ${ROOM_PAGES.map((p) => `<a href="#/room/${p.id}?case=${app.caseId}" ${p.id === page ? 'aria-current="page"' : ""}>${esc(p.label)}</a>`).join("")}</nav>
    <div class="pane" id="pane"></div></div>`);
  main.append(room);
  const pane = room.querySelector("#pane");
  const alias = { tests: "limits" }; // old link to the merged page
  await (PAGES[alias[page] || page] || PAGES.method)(pane, app, c);
}

const table = (head, rows, cls = "") =>
  `<table class="t ${cls}"><thead><tr>${head.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody></table>`;

const PAGES = {
  async method(pane, app) {
    pane.innerHTML = `<h1>Benchmark and method</h1>
      <p class="lead">How the test bank is scored and damaged. Its size and make-up are shown at the start of the walkthrough. The agent only ever sees a damaged copy of the map.</p>
      <section><h2>How it is scored</h2>
        <p><b>Answer key.</b> A control is affected when the changed item reaches it by following impact-carrying links in their direction through the complete map, at most six steps, stopping at the first control. This is plain code; no model labels anything.</p>
        <p><b>Damage.</b> For each change, 30% of the 237 recordable links are removed, nearest the change first, while keeping most of the changed item's own links; tickets may lose a sentence, use a legacy name, or wrongly say "control impact: N/A".</p>
        <p><b>Comparison.</b> The current check follows the remaining links. The agent starts from its result and reads the ticket, the item descriptions and the control procedures. Both are scored against the answer key; only key controls the check missed count towards recovery.</p></section>
      <section><h2>What the damage does to the current check</h2>${table(
        ["Lineage damage", "Key controls the check finds (18 test changes)"],
        app.exp.rules_by_damage.map((r) => `<tr><td>${esc(r.damage)}</td><td class="num">${pct(r.found, 1)}</td></tr>`)
      )}</section>
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
    const bar = (parts, total) =>
      `<div class="sbar">${parts.filter(([, n]) => n).map(([cls, n]) => `<span class="${cls}" style="flex:${n}" title="${n}">${n / total >= 0.06 ? n : ""}</span>`).join("")}</div>`;
    pane.innerHTML = `<h1>Results</h1>
      <p class="lead">Held-out test: 18 synthetic changes never used while building the agent; version A frozen before the run; one run.</p>
      <section><h2>Against the three goals set at the start</h2><div class="goals">
        <div class="goal"><div class="g-t">Find at least half of the key controls the existing check misses</div>
          <div class="g-v">${pct(P.recovery, 1)}</div><span class="badge recommended">Met</span>
          <p>${P.agent_found_key} of ${P.key_misses} recommended, on changes never seen. 95% range ${pct(P.recovery_interval[0], 1)}–${pct(P.recovery_interval[1], 1)}.</p></div>
        <div class="goal"><div class="g-t">Keep the extra review small</div>
          <div class="g-v">${P.added_unaffected}<small> avoidable items</small></div><span class="badge review">Not met as set</span>
          <p>${P.added_items} items were added for review: ${P.added_affected} genuinely affected, ${P.added_unaffected} not (about ${P.per_change.unaffected} per change). The goal counted real impacts as workload too. Reviewer time was not measured.</p></div>
        <div class="goal"><div class="g-t">Give the same decision on every run</div>
          <div class="g-v">${pct(P.consistency.agreement)}</div><span class="badge review">Not met · target 95%</span>
          <p>${Math.round(P.consistency.agreement * P.consistency.pairs)} of ${P.consistency.pairs} key decisions identical over five runs, on three development changes.</p></div>
      </div></section>
      <section><h2>Where the ${P.key_affected} affected key controls went</h2>
        ${bar([["check", P.check_found_key], ["agent", P.agent_found_key], ["review", P.key_routed], ["silent", P.key_silent]], P.key_affected)}
        <div class="legend" style="margin-top:10px"><span><i class="sw" style="background:var(--check)"></i>Found by the existing check · ${P.check_found_key}</span><span><i class="sw" style="background:var(--agent)"></i>Recommended by the agent · ${P.agent_found_key}</span><span><i class="sw" style="background:var(--review)"></i>Routed to a person · ${P.key_routed}</span><span><i class="sw" style="background:var(--risk)"></i>Not surfaced · ${P.key_silent}</span></div></section>
      <section><h2>By type of change</h2><p style="color:var(--ink-2);margin-top:0">Key controls the existing check missed, three changes of each type.</p>
        <div class="bytype">${Object.entries(P.by_type).map(([k, v]) => `<div class="bt-row"><div class="bt-n"><b>${esc(k)}</b>${v.key_misses} missed by the check</div>${v.key_misses ? bar([["agent", v.found], ["review", v.routed], ["silent", v.silent]], v.key_misses) : '<div class="bt-none">The check missed none</div>'}</div>`).join("")}</div>
        <p style="font-size:13px;color:var(--ink-3)">Screening-engine changes are the weak spot: the checker withholds agreement when no visible link connects the engine to the control, so most findings go to a person rather than being recommended.</p></section>
      <section><h2>Compared with the approaches tried before</h2>
        <p style="color:var(--ink-2)">Each step added information the lineage metadata lacks. The sets, models and scoring differ, so read this as a progression, not a league table; a plain keyword baseline on the same changes has not been run.</p>
        ${table(["Approach", "Result", "Measured on", "Caveat"], app.exp.approaches.map(
          (a) => `<tr><td>${esc(a.approach)}</td><td class="num">${pct(a.recovery, 1)}<br><span style="font-size:12px;color:var(--ink-3)">${esc(a.measure)}</span></td><td>${esc(a.set)}</td><td>${esc(a.caveat)}</td></tr>`
        ))}</section>
      <section><h2>Development runs (not the headline)</h2>${table(["Run", "Changes", "Key misses found", "Precision", "Unaffected items"], [
        fr && `<tr><td>Frozen check, version A, unseen development changes</td><td class="num">${fr.cases ?? 8}</td><td class="num">${fr.key_recovered} of ${fr.key_misses}</td><td class="num">${pct(fr.new_control_precision, 1)}</td><td class="num">${fr.avoidable_review_items}</td></tr>`,
        vb && `<tr><td>Version B on the same changes</td><td class="num">${vb.cases ?? 8}</td><td class="num">${vb.key_recovered} of ${vb.key_misses}</td><td class="num">${pct(vb.new_control_precision, 1)}</td><td class="num">${vb.avoidable_review_items}</td></tr>`,
      ].filter(Boolean))}</section>`;
  },

  async changes(pane, app, c) {
    const seg = (cls, n, total) => (n ? `<span class="${cls}" style="flex:${n}">${n}</span>` : "");
    const rows = app.exp.cases.map(
      (x) => `<li class="cl-row" data-id="${x.id}" tabindex="0" role="button" aria-label="${esc(x.id)} ${esc(x.title)}">
        <div class="cl-t"><b>${esc(x.id)}</b> ${esc(x.title)}<span>${x.affected} affected controls · ${x.model_calls} model calls</span></div>
        ${x.key_affected ? `<div class="sbar sm">${seg("check", x.check_found_key)}${seg("agent", x.key_found_by_agent)}${seg("review", x.key_routed)}${seg("silent", x.key_silent)}</div>` : '<div class="bt-none">No key controls affected</div>'}
        <div class="cl-k">${x.key_affected} key</div></li>`
    );
    pane.innerHTML = `<h1>All 18 test changes</h1><p class="lead">Each bar is one change's affected key controls: who found them. Select a change to see every decision against the answer key and open any control's evidence.</p>
      <div class="legend" style="margin-bottom:10px"><span><i class="sw" style="background:var(--check)"></i>Existing check</span><span><i class="sw" style="background:var(--agent)"></i>Recommended by the agent</span><span><i class="sw" style="background:var(--review)"></i>Routed to a person</span><span><i class="sw" style="background:var(--risk)"></i>Not surfaced</span></div>
      <ul class="clist">${rows.join("")}</ul>
      <section id="detail"></section>`;
    const detail = pane.querySelector("#detail");
    const show = async (id) => {
      const k = await getCase(id);
      pane.querySelectorAll("[data-id]").forEach((r) => r.classList.toggle("on", r.dataset.id === id));
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
          <button type="button" data-f="all" aria-pressed="false">Every decision</button></div></div><div id="dt"></div>`;
      detail.querySelectorAll("[data-f]").forEach((b) =>
        b.addEventListener("click", () => {
          filter = b.dataset.f;
          detail.querySelectorAll("[data-f]").forEach((x) => x.setAttribute("aria-pressed", x === b));
          draw();
        })
      );
      draw();
    };
    pane.querySelectorAll(".cl-row").forEach((r) => {
      r.addEventListener("click", () => show(r.dataset.id));
      r.addEventListener("keydown", (e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), show(r.dataset.id)));
    });
    show(c.id);
  },

  async architecture(pane) {
    pane.innerHTML = `<h1>Architecture</h1>
      <p class="lead">One Databricks workspace. A job investigates each change with a language model, fixed code checks every finding, and this app shows the recorded result. The answer key is used only for scoring and never reaches the model.</p>
      <section><div class="ra">
        <div class="ra-col"><div class="ra-h">1 · Inputs</div><div class="ra-sub">Unity Catalog volume</div>
          <div class="ra-box"><b>Change tickets</b>what is changing, as written</div>
          <div class="ra-box"><b>Lineage map</b>with 30% of links removed</div>
          <div class="ra-box"><b>Control procedures</b>101 controls, as written</div>
          <div class="ra-box key"><b>Answer key</b>kept apart; scoring only</div></div>
        <div class="ra-arrow" aria-hidden="true">→</div>
        <div class="ra-col ra-core"><div class="ra-h">2 · Investigation</div><div class="ra-sub">Databricks Job, one run per change</div>
          <div class="ra-loop"><b>Agent loop</b>
            <ol><li>Run today's lineage check</li><li>Explore items and their recorded links</li><li>Search and read control procedures</li><li>Submit findings with quotes and reasons</li></ol>
            <span>repeats until every candidate control is decided</span></div>
          <div class="ra-box model"><b>Model Serving</b>GPT OSS 120B: chooses the next step and writes each finding</div></div>
        <div class="ra-arrow" aria-hidden="true">→</div>
        <div class="ra-col"><div class="ra-h">3 · Checks and routing</div><div class="ra-sub">fixed code + a second model call</div>
          <div class="ra-box"><b>Quote check</b>both quotes must appear verbatim, or the finding is rejected</div>
          <div class="ra-box model"><b>Independent checker</b>a separate call agrees or disagrees</div>
          <div class="ra-box"><b>Routing</b>agree → recommended · disagree → to a person · not affected → reason kept</div></div>
        <div class="ra-arrow" aria-hidden="true">→</div>
        <div class="ra-col"><div class="ra-h">4 · Results</div><div class="ra-sub">Unity Catalog volume</div>
          <div class="ra-box"><b>Run record</b>every step, finding and decision</div>
          <div class="ra-box"><b>Scorer</b>compares decisions with the answer key</div>
          <div class="ra-box"><b>Databricks App</b>this experience, read from the recorded files</div></div>
      </div></section>
      <section><h2>How one change is investigated</h2><ol class="ra-steps">
        <li><b>Start from today's answer.</b> The agent first runs the same lineage check the bank uses, so it knows what is already covered.</li>
        <li><b>Look where the map is thin.</b> It explores the changed item and its neighbours, seeing only the links the damaged map still records.</li>
        <li><b>Read like a reviewer.</b> It searches the control procedures by wording and reads the candidates; reading is required before any finding.</li>
        <li><b>Commit with evidence.</b> Each finding quotes the ticket and the procedure, gives a reason and names any counter-evidence. Fixed code rejects quotes that are not verbatim, and the agent must correct them.</li>
        <li><b>Get a second opinion.</b> A separate model call judges each finding. Disagreements go to a person.</li>
        <li><b>Record everything.</b> Every step is saved, so the app replays the run exactly; nothing on screen calls a model, except the Ask page.</li>
      </ol></section>
      <section><h2>Design choices</h2><ul class="ra-notes">
        <li><b>Read-only.</b> The agent's tools only read. It never edits lineage or controls.</li>
        <li><b>People decide.</b> The output is a routed list with evidence; nothing is approved automatically.</li>
        <li><b>Isolated scoring.</b> Tests check that answer-key labels never appear in a prompt.</li>
        <li><b>Synthetic inputs.</b> No real payment systems, change tools or control libraries are connected; a pilot would connect them.</li>
      </ul></section>`;
  },

  async limits(pane, app) {
    pane.innerHTML = `<h1>Limits and fixes tried</h1><p class="lead">What the proof of concept does not show, where it goes wrong, and what was tried to fix it.</p>
      <div class="scope-note" style="margin-bottom:22px"><b>Not measured, not claimed:</b> reviewer time, accuracy on real bank data, cost or savings, and any production outcome. Routing an item to a person is not a completed review.</div>
      <section><h2>Known weaknesses</h2>${table(["Weakness", "Evidence", "Next step"], app.exp.limits.map((l) => `<tr><td><b>${esc(l.issue)}</b></td><td>${esc(l.evidence)}</td><td>${esc(l.response)}</td></tr>`))}</section>
      <section><h2>Fixes tried, none adopted</h2><p style="color:var(--ink-2);margin-top:0">Each fix had an adoption rule written before it ran. None met all of its rules, so the original agent (version A) is final.</p>
        ${table(["Fix", "What happened", "Rule it had to meet"], app.exp.version_tests.map((v) => `<tr><td><b>${esc(v.name)}</b><br><span style="color:var(--ink-3);font-size:12px">${esc(v.test)}</span></td><td>${esc(v.result)}</td><td>${esc(v.rule)}</td></tr>`))}
        <p style="font-size:13px;color:var(--ink-3)">What was learnt: the tie-break is reliable when it promotes a finding (68 of 70 promotions were right) but not when it dismisses one; voting across runs steadies decisions, but a three-run vote reached 94.4%, just short of 95%. Source: docs/results.md.</p></section>
      <details class="terms"><summary>Terms used in the evidence room</summary>${table(["Term", "Meaning"], app.exp.glossary.map((g) => `<tr><td><b>${esc(g.term)}</b></td><td>${esc(g.meaning)}</td></tr>`))}</details>`;
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
