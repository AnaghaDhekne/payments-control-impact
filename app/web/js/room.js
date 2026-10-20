// Two reference areas share one layout:
//  - the evidence room: what was found (results, every test change, limits, Q&A);
//  - the technical handbook: how it works (architecture, benchmark, damage,
//    the investigator and verifier calls with their prompts, reproduction).

import { esc, pct, el, ROUTE_LABEL, TYPE_LABEL, expandCodes } from "./util.js";
import { createGraph } from "./graph.js";
import { go, openInspector, getCase } from "./main.js";

export const ROOM_PAGES = [
  { id: "results", label: "Evaluation evidence" },
  { id: "changes", label: "All 18 test changes" },
  { id: "limits", label: "Limits and fixes tried" },
  { id: "ask", label: "Ask about the POC" },
];
export const BOOK_PAGES = [
  { id: "architecture", label: "Architecture" },
  { id: "method", label: "Benchmark and scoring" },
  { id: "degradation", label: "How the map is damaged" },
  { id: "investigator", label: "The investigator call" },
  { id: "verifier", label: "The verifier call" },
  { id: "reproduce", label: "Reproduce" },
  { id: "pilot", label: "From POC to enterprise pilot" },
];
const BOOKS = {
  room: { title: "Evidence room", pages: ROOM_PAGES },
  handbook: { title: "Technical handbook", pages: BOOK_PAGES },
};
// Old links: pages that moved between the two areas.
const MOVED = { method: "handbook", architecture: "handbook", reproduce: "handbook", tests: "room" };

export async function renderRoom(main, app, c, page, book = "room") {
  const B = BOOKS[book];
  if (page === "tests") page = "limits";
  if (!B.pages.some((p) => p.id === page)) {
    if (MOVED[page] && MOVED[page] !== book) return go(MOVED[page], { sub: page });
    page = B.pages[0].id;
  }
  const room = el(`<div class="room"><nav aria-label="${B.title}"><h2>${B.title}</h2>
    ${B.pages.map((p) => `<a href="#/${book}/${p.id}?case=${app.caseId}" ${p.id === page ? 'aria-current="page"' : ""}>${esc(p.label)}</a>`).join("")}</nav>
    <div class="pane" id="pane"></div></div>`);
  main.append(room);
  const pane = room.querySelector("#pane");
  await PAGES[page](pane, app, c);
}

/** An exact prompt, collapsed by default, with a copy button and its source. */
const promptBlock = (id, text, source) => `<section><h2>The prompt, exactly as sent</h2>
  <details class="prompt-d"><summary>Show the ${esc(id)} prompt (${text.length.toLocaleString()} characters)</summary>
    <div class="prompt-tools"><button class="btn" type="button" data-copy="${id}">Copy</button><span class="copied" hidden>Copied</span></div>
    <pre class="code prompt" id="prompt-${id}">${esc(text)}</pre></details>
  <p style="font-size:13px;color:var(--ink-3)">Source: ${esc(source)}</p></section>`;
function wirePrompt(pane) {
  pane.querySelectorAll("[data-copy]").forEach((b) =>
    b.addEventListener("click", async () => {
      const t = pane.querySelector(`#prompt-${b.dataset.copy}`).textContent;
      try { await navigator.clipboard.writeText(t); } catch { /* clipboard blocked: the text stays selectable */ }
      const ok = b.parentElement.querySelector(".copied"); ok.hidden = false; setTimeout(() => (ok.hidden = true), 1500);
    })
  );
}

/** A list of (change, control) records grouped by change; each opens its evidence in place. */
function recordList(app, title, items) {
  const by = {};
  for (const [cs, id] of items) (by[cs] ||= []).push(id);
  const name = (id) => app.graph.nodes.find((n) => n.id === id)?.name || id;
  return `<div class="recs"><div class="recs-h"><b>${esc(title)}</b> · ${items.length} record${items.length === 1 ? "" : "s"}</div>
    ${Object.entries(by).map(([cs, ids]) => `<div class="recs-g"><div class="recs-c">${esc(cs)} <span>${ids.length}</span></div><div class="recs-l">${ids.map((id) => `<button type="button" class="rec" data-case="${cs}" data-id="${id}"><b>${esc(id)}</b> ${esc(name(id))}</button>`).join("")}</div></div>`).join("")}</div>`;
}
const wireRecords = (root) =>
  root.querySelectorAll("button.rec").forEach((b) => b.addEventListener("click", () => openInspector(b.dataset.id, b.dataset.case, { stay: true })));

const table = (head, rows, cls = "") =>
  `<table class="t ${cls}"><thead><tr>${head.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody></table>`;

const PAGES = {
  async method(pane, app) {
    const P = app.exp.portfolio;
    pane.innerHTML = `<h1>Benchmark and scoring</h1>
      <p class="lead">How the right answer is known, which changes the numbers come from, and exactly what each metric counts.</p>
      <section><h2>The answer key</h2>
        <p>A control is affected when the changed item reaches it by following impact-carrying links in their direction through the complete map, at most six steps, stopping at the first control. This is plain code; no model labels anything. The check and the detective only ever see a damaged copy of the map (<i>How the map is damaged</i>).</p></section>
      <section><h2>Development and held-out changes</h2>${table(["Set", "Changes", "Used for"], [
        `<tr><td><b>Development</b></td><td class="num">36</td><td>Building and tuning the detective, and the version tests (B, C, D). Results from these are labelled as development.</td></tr>`,
        `<tr><td><b>Held-out</b></td><td class="num">${P.changes}</td><td>One frozen run of version A, after the design was fixed. Every headline figure comes from these. Guarded in code: the test split needs an explicit confirmation flag.</td></tr>`,
      ])}</section>
      <section><h2>Metrics</h2>${table(["Metric", "Exact meaning", "Held-out value"], [
        `<tr><td><b>Key-control recovery</b></td><td>Affected key controls the baseline missed that the detective recommended (both calls said affected) ÷ affected key controls the baseline missed</td><td class="num">${P.agent_found_key} / ${P.key_misses}</td></tr>`,
        `<tr><td><b>Recommendation precision</b></td><td>New recommendations that are affected in the answer key ÷ all new recommendations (beyond the baseline)</td><td class="num">${P.new_right} / ${P.new_total}</td></tr>`,
        `<tr><td><b>Added review items</b></td><td>Every control added beyond the baseline: new recommendations plus findings sent to a person, split by the answer key into affected and unaffected</td><td class="num">${P.added_items} = ${P.added_affected} + ${P.added_unaffected}</td></tr>`,
        `<tr><td><b>Review overhead</b></td><td>Added review items that are unaffected in the answer key</td><td class="num">${P.added_unaffected}</td></tr>`,
        `<tr><td><b>Consistency</b></td><td>Affected key controls given the same recommend-or-not decision in every one of five runs ÷ affected key controls (three development changes)</td><td class="num">${Math.round(P.consistency.agreement * P.consistency.pairs)} / ${P.consistency.pairs}</td></tr>`,
        `<tr><td><b>Silent miss</b></td><td>Affected key controls neither reached by the baseline, nor recommended, nor sent to a person</td><td class="num">${P.key_silent}</td></tr>`,
      ])}
        <p style="font-size:13px;color:var(--ink-3)">Routed (uncertain) findings never count as recovered, even when the answer key shows the control was affected. Recovery counts only recommendations. Source: scripts/score_detective.py.</p></section>
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

  async degradation(pane, app) {
    const D = app.exp.degradation;
    const c = await getCase(app.caseId);
    const removed = c.removed_links.length;
    const dmg = { omit_sentence: "last sentence removed", legacy_alias: "legacy system name added", misleading_na: "“control impact: N/A” added", misleading_no_impact: "“control impact: N/A” added" };
    const nodeName = (id) => app.graph.nodes.find((n) => n.id === id)?.name || id;
    const named = (id) => `${esc(nodeName(id))} (${esc(id)})`;
    const edgeOf = (a, b) => app.graph.edges.find((x) => x.source === a && x.target === b && x.carries_impact);
    const gone = (e) => !e || c.removedSet.has(e.id) || !e.exposable;
    // Worked example: a key control the check misses because a link on its path was removed.
    const exId = c.key.find((id) => !c.baselineSet.has(id) && c.decision(id)?.route === "recommended" && (c.paths[id]?.[0] || []).some((x, i, p) => i && gone(edgeOf(p[i - 1], x))))
      || c.key.find((id) => !c.baselineSet.has(id));
    let example = `<p style="color:var(--ink-2)">The selected change has no key control hidden by the damage.</p>`;
    if (exId) {
      const path = c.paths[exId][0];
      const links = path.slice(1).map((x, i) => ({ a: path[i], b: x, miss: gone(edgeOf(path[i], x)) }));
      const cut = links.find((l) => l.miss);
      const d = c.decision(exId);
      const chain = (showMissing) => path.map((id, i) => (i ? `<span class="pv-l ${links[i - 1].miss ? (showMissing ? "miss" : "cut") : "ok"}"></span>` : "") + `<span class="pv-n ${i === 0 ? "changed" : ""}"><b>${esc(id)}</b> ${esc(nodeName(id))}</span>`).join("");
      example = `<div class="ba">
          <div><div class="ba-h">Complete map (answer key)</div><div class="pv-chain">${chain(true)}</div></div>
          <div><div class="ba-h">What the check and the detective see</div><div class="pv-chain">${path.slice(0, path.indexOf(cut.b)).map((id, i) => (i ? '<span class="pv-l ok"></span>' : "") + `<span class="pv-n ${i === 0 ? "changed" : ""}"><b>${esc(id)}</b> ${esc(nodeName(id))}</span>`).join("")}<span class="pv-end">The map ends here</span></div></div>
        </div>
        <ul class="ra-notes">
          <li><b>Removed:</b> the link ${named(cut.a)} → ${named(cut.b)}.</li>
          <li><b>Effect on the check:</b> it follows recorded links only, so it stops at ${named(cut.a)} and never reaches ${named(exId)}.</li>
          <li><b>Evidence still available to the detective:</b> ${d?.ticket_quote ? `the ticket says “${esc(d.ticket_quote)}”, and the procedure says “${esc(d.control_quote)}”.` : "the ticket and the control procedures, which the damage does not remove."}</li>
        </ul>
        <button class="btn" type="button" id="ex-open">Open the evidence for ${esc(exId)}</button>`;
    }
    const inc = (id) => app.graph.edges.filter((e) => e.exposable && (e.source === id || e.target === id)).length;
    const keepRule = c.changed.map((id) => { const n = inc(id); return `${named(id)}: ${n} recordable links, keeps at least ${Math.max(1, Math.ceil((n * 70) / 100))}`; }).join("; ");
    pane.innerHTML = `<h1>How the map is damaged</h1>
      <p class="lead">The check and the detective never see the complete map. For every change, fixed code generates a damaged copy, the same way every time, so results can be reproduced and compared.</p>
      <div class="scope-note" style="margin-bottom:22px">A controlled synthetic stress test: it shows what happens when lineage is incomplete near a change. It is not evidence that a real bank's lineage is missing 30% of its links.</div>
      <section><h2>Worked example: ${esc(c.id)}</h2>${example}</section>
      <section><h2>The links, in four rules</h2><div class="vflow">
        <div class="vc"><span class="vc-n">1</span><b>Budget</b><em>${removed} of 237</em><span>recordable links removed at 30%: round(237 × L / 100)</span></div>
        <div class="vc"><span class="vc-n">2</span><b>Nearest first</b><em>closest out</em><span>ordered by steps from a changed item; a seeded number breaks ties</span></div>
        <div class="vc"><span class="vc-n">3</span><b>Keep a frontier</b><em>never cut off</em><span>a changed item keeps ⌈n × (100 − L) / 100⌉ links, at least one. ${esc(c.id)}: ${keepRule}</span></div>
        <div class="vc"><span class="vc-n">4</span><b>Reproducible</b><em>seed ${esc(D.seed)}</em><span>plus the change, the level and the mode</span></div>
      </div></section>
      <section><h2>The documents</h2><p style="color:var(--ink-2);margin-top:0">At level L, each of these happens with probability L% (30% in the test), independently:</p>
        ${table(["Damage", "What the reader sees", "Applies to"], [
          `<tr><td><b>Legacy name</b></td><td>“Legacy reference: &lt;old system name&gt;.” added at the start</td><td>Tickets and control procedures that have an old name</td></tr>`,
          `<tr><td><b>Missing sentence</b></td><td>The last sentence is dropped</td><td>Tickets and control procedures with more than one sentence</td></tr>`,
          `<tr><td><b>Misleading assessment</b></td><td>“Ticket assessment: control impact: N/A.” added at the end</td><td>Tickets of every seventh change only</td></tr>`,
        ])}
        <p style="font-size:13px;color:var(--ink-3)">On ${esc(c.id)}: ${removed} links removed; ticket ${c.ticket_damage?.length ? esc(c.ticket_damage.map((d) => dmg[d] || d).join("; ")) : "unchanged"}.</p></section>
      <section><h2>Why nearest the change</h2><p style="color:var(--ink-2);margin-top:0">Removing links closest to the change is the hard case the product is for: documentation lags exactly where change happens. For comparison, the same 30% removed at random leaves the existing lineage check far more of the picture.</p>
        <div class="hbars">${app.exp.rules_by_damage.filter((r) => !/^None/.test(r.damage)).map((r) => `<div class="hb"><span>${esc(r.damage)}</span><div class="hb-t"><i style="width:${(100 * r.found).toFixed(1)}%"></i></div><b>${pct(r.found, 1)}</b></div>`).join("")}<p class="hb-c">Key controls the existing lineage check still finds, across the 18 test changes</p></div>
        <p style="font-size:13px;color:var(--ink-3)">Source: scripts/generate_observable.py (degrade_edges, degrade_text). A damage manifest records exactly what was removed; only the scorer reads it.</p></section>`;
    pane.querySelector("#ex-open")?.addEventListener("click", () => openInspector(exId));
  },

  async investigator(pane, app) {
    const pr = app.exp.prompts;
    const all = await Promise.all(app.exp.cases.map((x) => getCase(x.id)));
    const acts = {};
    let steps = 0;
    for (const k of all) for (const s of k.steps) { steps++; acts[s.action] = (acts[s.action] || 0) + 1; }
    const c = await getCase(app.caseId);
    const tools = [
      ["trace_metadata", "{}", "Runs the existing lineage check: controls reachable through the visible links"],
      ["explore_node", "{node_id}", "One item: name, description, visible links in and out"],
      ["search_controls", "{query, limit 1–30}", "Ranks control procedures by word overlap with the query"],
      ["inspect_control", "{control_ids: up to 15}", "Full procedure text and visible links; required before any finding on that control"],
      ["submit_findings", "{findings: up to 8}", "Decisions, each with quotes, reason, counter-evidence and the chain of items"],
      ["finish", "{}", "Stops; refused while controls are still undecided"],
    ];
    pane.innerHTML = `<h1>The investigator call</h1>
      <p class="lead">One model call per step: the model reads the situation and chooses one tool; the code runs it and feeds the result into the next step. That loop, not a single classification prompt, is what makes it an agent. ${steps} steps were recorded across the 18 test changes.</p>
      <section><h2>One recorded step at a time: ${esc(c.id)}</h2>
        <div class="sv-bar"><button class="btn" type="button" id="sv-prev" aria-label="Previous step">‹</button>
          <label class="sr" for="sv-n">Step</label><input id="sv-n" class="scrub" type="range" min="1" max="${c.steps.length}" value="1">
          <button class="btn" type="button" id="sv-next" aria-label="Next step">›</button><span id="sv-l" class="sv-l"></span></div>
        <div class="sv" id="sv"></div></section>
      <section><h2>What one call contains</h2><div class="pa">
        <div class="pa-b fixed"><b>1 · Fixed instructions</b><span>The prompt at the end of this page: role, tools, method, how to decide, rules. Identical on every step.</span></div>
        <div class="pa-b"><b>2 · case</b><span>The change ticket; the changed items with descriptions; an index of every non-control item (code, type, name); the catalogue of 101 controls (code, title, criticality). No links that the damaged map does not show.</span></div>
        <div class="pa-b"><b>3 · notebook</b><span>What has been learnt so far: every procedure read and item explored, with their visible links; decisions already submitted; how many controls are still undecided.</span></div>
        <div class="pa-b"><b>4 · history</b><span>A short record of each earlier step: the action, its arguments and a summary of the result.</span></div>
        <div class="pa-b"><b>5 · steps_remaining</b><span>Out of 60 per change.</span></div>
        <div class="pa-out"><b>Reply</b><span>Exactly one JSON object: <code>{"action": …, "args": {…}}</code></span></div>
      </div></section>
      <section><h2>Tools</h2>${table(["Tool", "Arguments", "What it does", "Used"], tools.map(([t, a, d]) => `<tr><td><code>${t}</code></td><td><code>${esc(a)}</code></td><td>${esc(d)}</td><td class="num">${acts[t] || 0}</td></tr>`))}</section>
      <section><h2>What fixed code checks on every reply</h2><div class="vgrid">
        <div class="vc ok"><b>Shape</b><span>one tool call with valid arguments, or rejected with the reason</span></div>
        <div class="vc ok"><b>Read before deciding</b><span>no finding on a control whose procedure was not inspected</span></div>
        <div class="vc ok"><b>Verbatim quotes</b><span>ticket_quote in the ticket, control_quote in the procedure, exactly</span></div>
        <div class="vc ok"><b>Known items only</b><span>every code in evidence_path exists; reason and counter-evidence filled</span></div>
        <div class="vc ok"><b>No early stop</b><span>finish refused while controls are undecided</span></div>
      </div></section>
      <section><h2>Settings</h2>${table(["", ""], [
        `<tr><td>Model</td><td>databricks-gpt-oss-120b (Databricks Model Serving)</td></tr>`,
        `<tr><td>Temperature</td><td>0; an empty reply is retried with a nudge, then once at a small temperature</td></tr>`,
        `<tr><td>Reply limit</td><td>3,000 tokens per call; findings cut off mid-reply are recovered where complete</td></tr>`,
        `<tr><td>Steps</td><td>Up to 60 per change; all 18 finished within the limit</td></tr>`,
        `<tr><td>Version</td><td>${esc(pr.variant)}, agent code ${esc(pr.code)}</td></tr>`,
      ])}</section>
      ${promptBlock("investigator", pr.investigator, `scripts/detective.py · INSTRUCTIONS_TEMPLATE with version ${pr.variant}'s “Deciding” paragraph. Followed on every step by the JSON object with case, notebook, history and steps_remaining.`)}`;
    wirePrompt(pane);
    // Step viewer: everything shown is taken from the recorded run.
    const named = (id) => `${esc(app.graph.nodes.find((n) => n.id === id)?.name || id)} (${esc(id)})`;
    const show = (n) => {
      const k = c.steps.length;
      n = Math.max(1, Math.min(k, n));
      pane.querySelector("#sv-n").value = n;
      const s = c.steps[n - 1];
      const before = c.steps.slice(0, n - 1);
      const read = new Set(before.flatMap((x) => x.read));
      const explored = new Set(before.flatMap((x) => x.explored));
      const decided = new Set(before.flatMap((x) => x.accepted));
      const nx = c.steps[n];
      const args = s.args ? esc(JSON.stringify(s.args)) : s.action === "submit_findings" ? "{findings: […]} (decisions with quotes and reasons)" : "{}";
      const learnt = [
        s.explored.length && `Explored ${s.explored.map(named).join(", ")}${s.visible_links != null ? `: ${s.visible_links} visible links` : ""}`,
        s.read.length && `Read ${s.read.length} procedure${s.read.length > 1 ? "s" : ""}: ${s.read.slice(0, 4).map(named).join("; ")}${s.read.length > 4 ? `; and ${s.read.length - 4} more` : ""}`,
        s.accepted.length && `${s.accepted.length} finding${s.accepted.length > 1 ? "s" : ""} accepted for verification`,
        s.rejected.length && `${s.rejected.length} rejected by fixed code: ${esc(s.rejected[0].why)}`,
        s.action === "finish" && (n < k ? "Refused: controls were still undecided" : "Accepted: investigation complete"),
      ].filter(Boolean);
      pane.querySelector("#sv-l").textContent = `Step ${n} of ${k}`;
      pane.querySelector("#sv").innerHTML = `
        <div class="sv-c"><h3>Model input</h3><ul>
          <li><b>case:</b> the ticket, ${c.changed.map(named).join(", ")}, the item index and the 101-control catalogue</li>
          <li><b>notebook:</b> ${read.size} procedures read, ${explored.size} items explored, ${decided.size} findings submitted so far</li>
          <li><b>history:</b> ${n - 1} earlier step${n === 2 ? "" : "s"}</li>
          <li><b>steps_remaining:</b> ${60 - (n - 1)}</li></ul></div>
        <div class="sv-c"><h3>Model action</h3><p><code>${esc(s.action)}</code></p><p class="sv-args">${args}</p></div>
        <div class="sv-c"><h3>Tool output</h3><p>${expandCodes(s.summary)}</p></div>
        <div class="sv-c"><h3>State update</h3>${learnt.length ? `<ul>${learnt.map((x) => `<li>${x}</li>`).join("")}</ul>` : "<p>Nothing new recorded.</p>"}</div>
        <div class="sv-c"><h3>Next action</h3><p>${nx ? `<code>${esc(nx.action)}</code> · ${expandCodes(nx.summary)}` : "None: the run ended here."}</p></div>`;
    };
    pane.querySelector("#sv-n").addEventListener("input", (e) => show(+e.target.value));
    pane.querySelector("#sv-prev").onclick = () => show(+pane.querySelector("#sv-n").value - 1);
    pane.querySelector("#sv-next").onclick = () => show(+pane.querySelector("#sv-n").value + 1);
    show(1);
  },

  async verifier(pane, app) {
    const pr = app.exp.prompts;
    const all = await Promise.all(app.exp.cases.map((x) => getCase(x.id)));
    const calls = all.reduce((a, k) => a + k.counts.verify_calls, 0);
    const P = app.exp.portfolio;
    const miss = P.silent[0];
    const mk = miss ? all.find((k) => k.id === miss.change) : null;
    const md = mk?.decision(miss.control);
    const mname = miss ? app.graph.nodes.find((n) => n.id === miss.control)?.name : "";
    pane.innerHTML = `<h1>The verifier call</h1>
      <p class="lead">After the investigation, a separate model call judges findings on their own evidence. It does not continue the investigator's conversation. ${calls} verifier calls were recorded across the 18 test changes.</p>
      <section><h2>When it is called</h2><div class="vgrid">
        <div class="vc ok"><b>Affected → verifier</b><span>checked on its own evidence</span></div>
        <div class="vc ok"><b>Uncertain → verifier</b><span>checked on its own evidence</span></div>
        <div class="vc weak"><b>Not affected → no verifier</b><span>reason recorded, no second look</span></div></div></section>
      <section class="warn-sec"><h2>What independent verification does not guarantee</h2>
        <p>Verification reduces unsupported positive findings and sends disagreements to a person. It cannot catch a false negative, because a control the investigator marks not affected never reaches it. Two model calls agreeing is not proof of completeness.</p>
        ${miss ? `<div class="sm"><div><b>Recorded example: ${esc(miss.control)} ${esc(mname)}, on ${esc(miss.change)}</b>
          <p>The investigator marked it not affected${md?.proposer_reason ? `: “${expandCodes(md.proposer_reason, miss.control)}”` : ""}. The verifier was never asked, so nothing routed it to a person. The answer key shows it was affected: the one silent miss among ${P.key_affected} affected key controls.</p></div>
          <button class="btn" type="button" id="sm-open">Open its evidence and decision</button></div>` : ""}
        <p style="font-size:13px;color:var(--ink-3)">The fix tested on development changes, a second look at not-affected key controls, is in Evidence room → Limits and fixes tried.</p></section>
      <section><h2>What one call contains</h2><div class="pa">
        <div class="pa-b fixed"><b>1 · Fixed instructions</b><span>The prompt at the end of this page.</span></div>
        <div class="pa-b"><b>2 · ticket and changed items</b><span>The change ticket and the changed items, with names and descriptions.</span></div>
        <div class="pa-b"><b>3 · change_neighborhood</b><span>Everything two links downstream of the changed items in the visible map, with names.</span></div>
        <div class="pa-b"><b>4 · control</b><span>The control's procedure and its own visible links.</span></div>
        <div class="pa-b"><b>5 · control_family</b><span>Up to 12 controls sharing its title prefix, with their visible links.</span></div>
        <div class="pa-b"><b>6 · hypothesis</b><span>The investigator's finding and evidence path, marked untrusted.</span></div>
        <div class="pa-out"><b>Reply</b><span><code>{decision, ticket_quote, control_quote, causal_reason, counter_evidence}</code>; quotes checked verbatim as for the investigator</span></div>
      </div></section>
      <section><h2>How the two answers become a route</h2>${table(["Investigator", "Verifier", "Result"], [
        `<tr><td>affected</td><td>affected</td><td><span class="badge recommended">Recommended</span></td></tr>`,
        `<tr><td>affected or uncertain</td><td>a different answer</td><td><span class="badge review">Sent to a person</span> (disagreement is never discarded)</td></tr>`,
        `<tr><td>uncertain</td><td>uncertain</td><td><span class="badge review">Sent to a person</span></td></tr>`,
        `<tr><td>not affected</td><td>not asked</td><td><span class="badge not_affected">Marked not affected</span>, reason kept</td></tr>`,
        `<tr><td colspan="2">Reached by the existing lineage check</td><td><span class="badge check">Found by the existing lineage check</span>, always kept</td></tr>`,
      ])}</section>
      ${promptBlock("verifier", pr.verifier, "scripts/detective.py · VERIFIER_INSTRUCTIONS, followed by the JSON evidence built by verification_evidence(). Same model and settings as the investigator.")}`;
    wirePrompt(pane);
    pane.querySelector("#sm-open")?.addEventListener("click", () => openInspector(miss.control, miss.change));
  },

  async results(pane, app) {
    const P = app.exp.portfolio;
    const B = app.exp.benchmark;
    const fr = app.exp.development_runs.frozen_check;
    const vb = app.exp.development_runs.variant_b;
    const all = await Promise.all(app.exp.cases.map((x) => getCase(x.id)));
    // Every record behind the headline claims, computed from the exported decisions.
    const rec = { check: [], recovered: [], routed: [], silent: [], newRight: [], newWrong: [], addAff: [], addUnaff: [] };
    for (const k of all) {
      for (const id of k.key) {
        const r = k.baselineSet.has(id) ? "check" : k.decision(id)?.route;
        (r === "check" ? rec.check : r === "recommended" ? rec.recovered : r === "review" ? rec.routed : rec.silent).push([k.id, id]);
      }
      for (const d of k.decisions) {
        if (k.baselineSet.has(d.control)) {
          // Found by the check, but the two reviews then disagreed: the scorer counts it as an added review item.
          if (/disagree/i.test(d.routing_reason || "")) (d.truth ? rec.addAff : rec.addUnaff).push([k.id, d.control]);
          continue;
        }
        if (d.route === "recommended") (d.truth ? rec.newRight : rec.newWrong).push([k.id, d.control]);
        if (d.route === "recommended" || d.route === "review") (d.truth ? rec.addAff : rec.addUnaff).push([k.id, d.control]);
      }
    }
    const bar = (parts, total) =>
      `<div class="sbar">${parts.filter(([, n]) => n).map(([cls, n]) => `<span class="${cls}" style="flex:${n}" title="${n}">${n / total >= 0.06 ? n : ""}</span>`).join("")}</div>`;
    const LBL = { addAff: "affected", addUnaff: "not affected" };
    const showBtn = (key, n) => `<button class="btn sm" type="button" data-rec="${key}">Show ${n}${LBL[key] ? " " + LBL[key] : ` record${n === 1 ? "" : "s"}`}</button>`;
    pane.innerHTML = `<h1>Evaluation evidence</h1>
      <p class="lead">What the held-out evaluation established, and the records behind each claim. Every list below opens the control's evidence in place.</p>
      <div class="conds">
        <div><b>${P.changes}</b>held-out changes, never used while building the detective</div>
        <div><b>30%</b>lineage damage, nearest the change first</div>
        <div><b>${B.controls}</b>controls in the benchmark, ${B.key_controls} key</div>
        <div><b>A</b>frozen version, one recorded run</div>
      </div>
      <section><h2>Evidence index</h2>${table(["Claim", "Records behind it", ""], [
        `<tr><td><b>Key-control recovery</b></td><td>The ${P.agent_found_key} recommended, out of the ${P.key_misses} affected key controls the existing lineage check missed; the rest are in the outcome table below</td><td>${showBtn("recovered", rec.recovered.length)}</td></tr>`,
        `<tr><td><b>Recommendation precision</b></td><td>The ${P.new_total} new recommendations compared with the answer key; the ${rec.newWrong.length} that were wrong</td><td>${showBtn("newWrong", rec.newWrong.length)}</td></tr>`,
        `<tr><td><b>Review composition</b></td><td>The ${P.added_items} added items: recommendations and findings sent to a person, by the answer key</td><td>${showBtn("addAff", rec.addAff.length)} ${showBtn("addUnaff", rec.addUnaff.length)}</td></tr>`,
        `<tr><td><b>Consistency</b></td><td>Every affected key control of three development changes, decided in each of ${app.exp.repeat_runs.runs} runs</td><td><button class="btn sm" type="button" id="rep-btn">Show ${app.exp.repeat_runs.rows.length} records</button></td></tr>`,
        `<tr><td><b>Known failure</b></td><td>The silent miss: an affected key control neither recommended nor sent to a person</td><td>${showBtn("silent", rec.silent.length)}</td></tr>`,
        `<tr><td><b>Version selection</b></td><td>Pre-registered tests of versions B, C and D, and why each was not adopted: <i>Limits and fixes tried</i>, in this room</td><td></td></tr>`,
      ])}<div id="rec-out"></div></section>
      <section><h2>The three evaluation questions</h2><div class="goals">
        <div class="goal"><div class="g-t">Can it recover the key controls the existing lineage check misses?</div>
          <div class="g-v">${pct(P.recovery, 1)}</div><span class="badge recommended">Goal met · at least 50%</span>
          <p>${P.agent_found_key} of ${P.key_misses} recommended, on changes never seen. 95% range ${pct(P.recovery_interval[0], 1)}–${pct(P.recovery_interval[1], 1)}.</p></div>
        <div class="goal"><div class="g-t">Is the extra review worth it?</div>
          <div class="g-v">${P.added_affected}<small> of ${P.added_items} are real impacts</small></div><span class="badge review">Original volume goal not met</span>
          <p>These controls need checking with or without the detective; it hands over a shortlist with evidence. ${P.added_unaffected} are not affected and come with evidence to clear them. The original goal (at most 25% more items) counted real impacts as extra work too.</p></div>
        <div class="goal"><div class="g-t">Are its decisions repeatable?</div>
          <div class="g-v">${pct(P.consistency.agreement)}</div><span class="badge review">Goal not met · target 95%</span>
          <p>${Math.round(P.consistency.agreement * P.consistency.pairs)} of ${P.consistency.pairs} key decisions identical over five runs, on three development changes.</p></div>
      </div></section>
      <section><h2>Where the ${P.key_affected} affected key controls went</h2>
        ${bar([["check", rec.check.length], ["agent", rec.recovered.length], ["review", rec.routed.length], ["silent", rec.silent.length]], P.key_affected)}
        ${table(["Outcome", "What it means", "Count", ""], [
          `<tr><td><span class="badge check">Found by the existing lineage check</span></td><td>The existing lineage already identified it</td><td class="num">${rec.check.length}</td><td>${showBtn("check", rec.check.length)}</td></tr>`,
          `<tr><td><span class="badge recommended">Recovered by the detective</span></td><td>Missed by the existing lineage check; the investigator and the independent verifier both said affected, so it is recommended</td><td class="num">${rec.recovered.length}</td><td>${showBtn("recovered", rec.recovered.length)}</td></tr>`,
          `<tr><td><span class="badge review">Sent to a person</span></td><td>Affected in the answer key, but the investigator and the independent verifier did not agree, so not counted as recovered</td><td class="num">${rec.routed.length}</td><td>${showBtn("routed", rec.routed.length)}</td></tr>`,
          `<tr><td><span class="badge silent">Silent miss</span></td><td>Neither recommended nor sent to a person</td><td class="num">${rec.silent.length}</td><td>${showBtn("silent", rec.silent.length)}</td></tr>`,
          `<tr class="total"><td colspan="2"><b>Total, across the ${P.changes} changes</b></td><td class="num"><b>${rec.check.length + rec.recovered.length + rec.routed.length + rec.silent.length}</b></td><td></td></tr>`,
        ])}</section>
      <section><h2>By type of change</h2><p style="color:var(--ink-2);margin-top:0">Key controls the existing lineage check missed, three changes of each type.</p>
        <div class="bytype">${Object.entries(P.by_type).map(([k, v]) => `<div class="bt-row"><div class="bt-n"><b>${esc(k)}</b>${v.key_misses} missed by the check</div>${v.key_misses ? bar([["agent", v.found], ["review", v.routed], ["silent", v.silent]], v.key_misses) : '<div class="bt-none">The check missed none</div>'}</div>`).join("")}</div>
        <p style="font-size:13px;color:var(--ink-3)">Screening-engine changes are the weak spot: the independent verifier withholds agreement when no visible link connects the engine to the control, so most findings go to a person rather than being recommended.</p></section>
      <section><h2>Compared with the approaches tried before</h2>
        <p style="color:var(--ink-2)">Each step added information the lineage metadata lacks. The sets, models and scoring differ, so read this as a progression, not a league table; a plain keyword baseline on the same changes has not been run.</p>
        ${table(["Approach", "Result", "Measured on", "Caveat"], app.exp.approaches.map(
          (a) => `<tr><td>${esc(a.approach)}</td><td class="num">${pct(a.recovery, 1)}<br><span style="font-size:12px;color:var(--ink-3)">${esc(a.measure)}</span></td><td>${esc(a.set)}</td><td>${esc(a.caveat)}</td></tr>`
        ))}</section>
      <section><h2>Development runs (not the headline)</h2>${table(["Run", "Changes", "Key misses found", "Precision", "Unaffected items"], [
        fr && `<tr><td>Frozen check, version A, unseen development changes</td><td class="num">${fr.cases ?? 8}</td><td class="num">${fr.key_recovered} of ${fr.key_misses}</td><td class="num">${pct(fr.new_control_precision, 1)}</td><td class="num">${fr.avoidable_review_items}</td></tr>`,
        vb && `<tr><td>Version B on the same changes</td><td class="num">${vb.cases ?? 8}</td><td class="num">${vb.key_recovered} of ${vb.key_misses}</td><td class="num">${pct(vb.new_control_precision, 1)}</td><td class="num">${vb.avoidable_review_items}</td></tr>`,
      ].filter(Boolean))}</section>`;
    const titles = {
      check: "Affected key controls found by the existing lineage check",
      recovered: "Affected key controls recovered by the detective",
      routed: "Affected key controls sent to a person",
      silent: "Silent misses",
      newWrong: "New recommendations the answer key says were not affected",
      addAff: "Added review items that are affected in the answer key",
      addUnaff: "Added review items the answer key says were not affected",
    };
    const out = pane.querySelector("#rec-out");
    const RR = app.exp.repeat_runs;
    const cell = { recommended: ["agent", "Rec."], review: ["review", "Person"], not_recommended: ["idle", "Not rec."] };
    pane.querySelector("#rep-btn").addEventListener("click", () => {
      out.innerHTML = `<div class="recs"><div class="recs-h"><b>Repeat runs: the same change, decided five times</b> · ${RR.rows.filter((r) => r.same).length} of ${RR.rows.length} affected key controls got the same recommend-or-not decision in every run</div>
        ${table(["Change", "Key control", ...Array.from({ length: RR.runs }, (_, i) => `Run ${i + 1}`), "Same every run"], RR.rows.map((r) =>
          `<tr><td>${esc(r.change)}</td><td><b>${esc(r.control)}</b> ${esc(r.name)}</td>${r.runs.map((x) => `<td><span class="rr ${cell[x][0]}">${cell[x][1]}</span></td>`).join("")}<td>${r.same ? "yes" : "<b>no</b>"}</td></tr>`))}
        <p style="font-size:12.5px;color:var(--ink-3);margin:8px 0 0">Development changes, version A, 30% damage. "Person" means sent to a person, which counts as not recommended. Source: results/detective_runs.tar.gz, suite-11; recomputed from these records, the agreement equals the archived summary (tested).</p></div>`;
      out.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
    pane.querySelectorAll("[data-rec]").forEach((b) =>
      b.addEventListener("click", () => {
        const key = b.dataset.rec;
        out.innerHTML = recordList(app, titles[key], rec[key]);
        wireRecords(out);
        out.scrollIntoView({ behavior: "smooth", block: "nearest" });
      })
    );
    // The outcome table's buttons show their list next to the table.
    pane.querySelectorAll("section:not(:has(#rec-out)) [data-rec]").forEach((b) =>
      b.addEventListener("click", () => {
        const sec = b.closest("section");
        let box = sec.querySelector(".rec-box");
        if (!box) { box = document.createElement("div"); box.className = "rec-box"; sec.append(box); }
        box.innerHTML = recordList(app, titles[b.dataset.rec], rec[b.dataset.rec]);
        wireRecords(box);
        out.innerHTML = "";
      })
    );
  },

  async changes(pane, app, c) {
    const all = await Promise.all(app.exp.cases.map((x) => getCase(x.id)));
    const typeOf = (k) => k.title.split(" — ")[0];
    const types = [...new Set(all.map(typeOf))];
    const CATS = {
      attention: "Needs attention (all four below)",
      missed: "Affected but not surfaced",
      affRouted: "Affected, sent to a person",
      unaffRec: "Not affected, but recommended",
      unaffRouted: "Not affected, sent to a person",
      affected: "Every affected control",
      all: "Every decision",
    };
    const rows = [];
    for (const k of all)
      for (const d of k.decisions) {
        const r = k.baselineSet.has(d.control) ? "check" : d.route;
        const cat = d.truth && !["check", "recommended", "review"].includes(r) ? "missed" : d.truth && r === "review" ? "affRouted" : !d.truth && r === "recommended" ? "unaffRec" : !d.truth && r === "review" ? "unaffRouted" : null;
        rows.push({ k, d, r, cat, type: typeOf(k) });
      }
    const f = { change: "all", type: "all", cat: "attention", key: "all" };
    const seg = (cls, n) => (n ? `<span class="${cls}" style="flex:${n}">${n}</span>` : "");
    const list = app.exp.cases.map(
      (x) => `<li class="cl-item" data-id="${x.id}"><div class="cl-row" tabindex="0" role="button" aria-expanded="false" aria-label="Show the decisions of ${esc(x.id)} below">
        <div class="cl-t"><b>${esc(x.id)}</b> ${esc(x.title)}<span>${x.affected} affected controls · ${x.model_calls} model calls</span></div>
        ${x.key_affected ? `<div class="sbar sbar-sm">${seg("check", x.check_found_key)}${seg("agent", x.key_found_by_agent)}${seg("review", x.key_routed)}${seg("silent", x.key_silent)}</div>` : '<div class="bt-none">No key controls affected</div>'}
        <div class="cl-k">${x.key_affected} key</div><span class="cl-open">Show decisions <i class="chev">▾</i></span></div>
        <div class="cl-body" hidden></div></li>`
    );
    const opt = (v, l, cur) => `<option value="${esc(v)}" ${v === cur ? "selected" : ""}>${esc(l)}</option>`;
    const decTable = (hit, inRow = false) => table([...(inRow ? [] : ["Change"]), "Control", "Key", "Decision", "Answer key", ""], hit.slice(0, LIMIT).map(({ k, d, r }) => {
      const n = app.graph.nodes.find((x) => x.id === d.control);
      return `<tr class="click" data-case="${k.id}" data-c="${d.control}" tabindex="0" title="Open the evidence for this decision">${inRow ? "" : `<td>${esc(k.id)}</td>`}<td><b>${esc(d.control)}</b> ${esc(n.name)}</td><td>${d.key ? "key" : ""}</td><td><span class="badge ${r}">${esc(ROUTE_LABEL[r])}</span></td><td>${d.truth ? "affected" : "not affected"}</td><td class="open-cue">Evidence ›</td></tr>`;
    }));
    const wireRows = (root) => root.querySelectorAll("tr[data-c]").forEach((tr) => {
      const open = () => openInspector(tr.dataset.c, tr.dataset.case, { stay: true });
      tr.addEventListener("click", open);
      tr.addEventListener("keydown", (e) => e.key === "Enter" && open());
    });
    const LIMIT = 150;
    pane.innerHTML = `<h1>All 18 test changes</h1><p class="lead">Click a change to see its decisions right below it. Click any decision to open its evidence.</p>
      <section>
        <div class="legend" style="margin-bottom:10px"><span><i class="sw" style="background:var(--check)"></i>Existing check</span><span><i class="sw" style="background:var(--agent)"></i>Recommended</span><span><i class="sw" style="background:var(--review)"></i>Sent to a person</span><span><i class="sw" style="background:var(--risk)"></i>Not surfaced</span><span>Bars: affected key controls</span></div>
        <ul class="clist">${list.join("")}</ul></section>
      <section><details class="xf-d"><summary>Filter decisions across all 18 changes</summary>
        <div class="xf">
          <label>Change<select id="f-change">${opt("all", "All 18 changes", f.change)}${all.map((k) => opt(k.id, `${k.id} · ${typeOf(k)}`, f.change)).join("")}</select></label>
          <label>Type of change<select id="f-type">${opt("all", "Every type", f.type)}${types.map((t) => opt(t, t, f.type)).join("")}</select></label>
          <label>Show<select id="f-cat">${Object.entries(CATS).map(([v, l]) => opt(v, l, f.cat)).join("")}</select></label>
          <label>Controls<select id="f-key">${opt("all", "Key and other", f.key)}${opt("key", "Key controls only", f.key)}</select></label>
        </div>
        <p class="xf-sum" id="xf-sum"></p><div id="xf-t"></div></details></section>`;
    const draw = () => {
      const hit = rows.filter(({ k, d, cat, type }) =>
        (f.change === "all" || k.id === f.change) && (f.type === "all" || type === f.type) && (f.key === "all" || d.key) &&
        (f.cat === "all" || (f.cat === "affected" ? d.truth : f.cat === "attention" ? !!cat : cat === f.cat)));
      const counts = {};
      for (const r of rows.filter(({ k, d, type }) => (f.change === "all" || k.id === f.change) && (f.type === "all" || type === f.type) && (f.key === "all" || d.key))) if (r.cat) counts[r.cat] = (counts[r.cat] || 0) + 1;
      pane.querySelector("#xf-sum").innerHTML = `${hit.length} decision${hit.length === 1 ? "" : "s"}${hit.length > LIMIT ? `, first ${LIMIT} shown` : ""}. In this selection: ${["missed", "affRouted", "unaffRec", "unaffRouted"].map((x) => `${CATS[x].toLowerCase()} <b>${counts[x] || 0}</b>`).join(" · ")}.`;
      pane.querySelector("#xf-t").innerHTML = hit.length ? decTable(hit) : `<p class="bt-none">No decisions match this selection.</p>`;
      wireRows(pane.querySelector("#xf-t"));
    };
    for (const [id, key] of [["f-change", "change"], ["f-type", "type"], ["f-cat", "cat"], ["f-key", "key"]])
      pane.querySelector("#" + id).addEventListener("change", (e) => { f[key] = e.target.value; draw(); });
    const body = (id) => {
      const x = app.exp.cases.find((y) => y.id === id);
      const mine = rows.filter(({ k, d, r }) => k.id === id && (d.truth || r === "recommended" || r === "review"));
      const att = mine.filter((m) => m.cat);
      const tile = (n, l, cls) => `<div class="cl-tile ${cls}"><b>${n}</b><span>${l}</span></div>`;
      return `<div class="cl-tiles">${tile(x.check_found_key, "key found by the existing check", "check")}${tile(x.key_found_by_agent, "key recommended by the detective", "agent")}${tile(x.key_routed, "key sent to a person", "review")}${tile(x.key_silent, "key not surfaced", "silent")}</div>
        <div class="cl-tabs" role="tablist"><button type="button" class="${att.length ? "on" : ""}" data-v="att">Needs attention (${att.length})</button><button type="button" class="${att.length ? "" : "on"}" data-v="all">Every flagged or affected control (${mine.length})</button></div>
        <div class="cl-tab" data-v="att" ${att.length ? "" : "hidden"}>${att.length ? decTable(att, true) : '<p class="bt-none">Nothing needs attention in this change: every affected control was found and nothing unaffected was flagged.</p>'}</div>
        <div class="cl-tab" data-v="all" ${att.length ? "hidden" : ""}>${att.length ? "" : '<p class="bt-none" style="margin:0 0 8px">Nothing needs attention here: every affected control was found and nothing unaffected was flagged.</p>'}${decTable(mine, true)}</div>`;
    };
    pane.querySelectorAll(".cl-item").forEach((li) => {
      const row = li.querySelector(".cl-row"), b = li.querySelector(".cl-body");
      const toggle = () => {
        const open = b.hidden;
        if (open && !b.innerHTML) {
          b.innerHTML = body(li.dataset.id); wireRows(b);
          b.querySelectorAll(".cl-tabs button").forEach((t) => t.addEventListener("click", () => {
            b.querySelectorAll(".cl-tabs button").forEach((u) => u.classList.toggle("on", u === t));
            b.querySelectorAll(".cl-tab").forEach((u) => (u.hidden = u.dataset.v !== t.dataset.v));
          }));
        }
        b.hidden = !open; li.classList.toggle("on", open); row.setAttribute("aria-expanded", String(open));
        row.querySelector(".cl-open").innerHTML = open ? 'Hide decisions <i class="chev">▴</i>' : 'Show decisions <i class="chev">▾</i>';
      };
      row.addEventListener("click", toggle);
      row.addEventListener("keydown", (e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), toggle()));
    });
    draw();
  },

  async architecture(pane) {
    pane.innerHTML = `<h1>Architecture</h1>
      <p class="lead">What was built: a Databricks job that investigates each change with a tool-using language model, fixed code that checks every proposed finding, and this app, which replays the recorded result. The answer key is used only for offline scoring and never reaches the model.</p>
      <section><div class="ra">
        <div class="ra-col"><div class="ra-h">1 · Inputs</div><div class="ra-sub">Unity Catalog volume</div>
          <div class="ra-box"><b>Change tickets</b>what is changing, as written</div>
          <div class="ra-box"><b>Lineage map</b>with 30% of links removed</div>
          <div class="ra-box"><b>Control procedures</b>101 controls, as written</div>
          <div class="ra-box key"><b>Answer key</b>kept apart; scoring only</div></div>
        <div class="ra-arrow" aria-hidden="true">→</div>
        <div class="ra-col ra-core"><div class="ra-h">2 · Investigation</div><div class="ra-sub">Databricks Job, one run per change</div>
          <div class="ra-loop"><b>Agent loop</b>
            <ol><li>Run today's existing lineage check</li><li>Explore items and their recorded links</li><li>Search and read control procedures</li><li>Submit findings with quotes and reasons</li></ol>
            <span>repeats until every candidate control is decided, within 60 steps</span></div>
          <div class="ra-box model"><b>Model Serving</b>GPT OSS 120B: chooses the next step and writes each finding</div></div>
        <div class="ra-arrow" aria-hidden="true">→</div>
        <div class="ra-col"><div class="ra-h">3 · Checks and routing</div><div class="ra-sub">fixed code + a second model call</div>
          <div class="ra-box"><b>Quote check</b>both quotes must appear verbatim, or the finding is rejected</div>
          <div class="ra-box model"><b>Independent verifier</b>a separate call on findings marked affected or uncertain; findings marked not affected skip it</div>
          <div class="ra-box"><b>Routing</b>agree → recommended · disagree → to a person · not affected → reason kept</div></div>
        <div class="ra-arrow" aria-hidden="true">→</div>
        <div class="ra-col"><div class="ra-h">4 · Results</div><div class="ra-sub">Unity Catalog volume</div>
          <div class="ra-box"><b>Run record</b>every step, prompt, reply and decision</div>
          <div class="ra-box"><b>Scorer</b>compares decisions with the answer key, offline</div>
          <div class="ra-box"><b>Databricks App</b>this experience, read from the recorded files</div></div>
      </div></section>
      <section><h2>What happens when a change is submitted</h2><ol class="seq">
        <li><b>Observable inputs only.</b> The ticket, the damaged lineage map and the control procedures. No answer-key labels.</li>
        <li><b>Deterministic baseline.</b> The existing lineage check follows the visible links. Whatever it reaches is always kept.</li>
        <li><b>Agent loop.</b> The model selects a tool → the tool runs → the observation is added to the notebook → the model sees it on the next step. Repeated within the step budget.</li>
        <li><b>Deterministic validation.</b> Each submitted finding must cite an inspected control, verbatim quotes and known item codes, or it is rejected back to the detective.</li>
        <li><b>Independent verification.</b> Findings marked affected or uncertain go to a separate model call with their evidence.</li>
        <li><b>Route.</b> Recommended, to a person, or not affected with its reason.</li>
        <li class="off"><b>Offline, after the run.</b> The scorer compares the routes with the hidden answer key. This is how the results are measured; it plays no part in a decision.</li>
      </ol></section>
      <section><h2>What runs where</h2>${table(["Part", "Runs in", "Kind"], [
        `<tr><td>Benchmark and damage generator</td><td>Python, before any run</td><td>Deterministic, seeded</td></tr>`,
        `<tr><td>Lineage baseline, tools, quote check, routing</td><td>Python inside the Databricks Job</td><td>Deterministic</td></tr>`,
        `<tr><td>Investigator and verifier</td><td>Databricks Model Serving, called from the Job</td><td>Model</td></tr>`,
        `<tr><td>Scorer</td><td>Python, after the run</td><td>Deterministic; the only reader of the answer key</td></tr>`,
        `<tr><td>Walkthrough, overview, evidence room, handbook</td><td>Databricks App</td><td>Replay of recorded files; no model calls</td></tr>`,
        `<tr><td>Ask about the POC</td><td>Databricks App → Model Serving</td><td>Model, live</td></tr>`,
      ])}</section>
      <section><h2>Engineering choices</h2><div class="vgrid">
        <div class="vc"><b>Read-only</b><span>tools only read; nothing in lineage or controls is edited</span></div>
        <div class="vc"><b>Isolated scoring</b><span>tests check answer-key labels never reach a prompt</span></div>
        <div class="vc"><b>Resumable</b><span>every step saved as it happens; a stopped job continues</span></div>
      </div></section>`;
  },

  async limits(pane, app) {
    pane.innerHTML = `<h1>Limits and fixes tried</h1><p class="lead">Where the proof of concept falls short, what was tried to fix it, and what that taught. Each fix had its adoption rule written before it ran.</p>
      <div class="scope-note" style="margin-bottom:22px"><b>Not yet shown:</b> accuracy on real bank data, how control owners work the list in practice, and any production outcome.</div>
      <section><h2>Known weaknesses</h2><div class="vgrid wide">${app.exp.limits.map((l) => `<div class="vc weak"><b>${esc(l.issue)}</b><span>${esc(l.evidence)}</span><span class="vc-next">Next: ${esc(l.response)}</span></div>`).join("")}</div></section>
      <section><h2>Experiment decision records</h2><div class="drs">
        ${app.exp.version_tests.map((v) => {
          return `<article class="dr"><div class="dr-h"><span class="dr-v">Version ${esc(v.version)}</span><h3>${esc(v.name)}</h3><span class="badge not_affected">${esc(v.decision)}</span></div>
            <dl><dt>Hypothesis</dt><dd>${esc(v.hypothesis)}</dd>
            <dt>Tested on</dt><dd>${esc(v.test)}</dd>
            <dt>Rule written in advance</dt><dd>${esc(v.rule)}</dd>
            <dt>Result</dt><dd>${esc(v.result)}</dd>
            <dt>Trade-off</dt><dd>${esc(v.trade_off)}</dd></dl></article>`;
        }).join("")}</div>
        <p style="font-size:13px;color:var(--ink-3)">None met all of its rules, so the original version A is the version evaluated. Exported with the results by scripts/build_experience_data.py from docs/results.md (pre-registered sections); a test checks each result against that document.</p></section>
      <section><h2>What we learned</h2><div class="vgrid">${app.exp.lessons.map((l, n) => `<div class="vc"><span class="vc-n">${n + 1}</span><b>${esc(l.title.replace(/\.$/, ""))}</b><span>${esc(l.detail)}</span></div>`).join("")}</div></section>
      <details class="terms"><summary>Terms used in the evidence room</summary>${table(["Term", "Meaning"], app.exp.glossary.map((g) => `<tr><td><b>${esc(g.term)}</b></td><td>${esc(g.meaning)}</td></tr>`))}</details>`;
  },

  async reproduce(pane, app) {
    const p = app.exp.provenance;
    const path = (n, title, needs, gives, cmd, note) => `<div class="rp-card"><div class="rp-h"><span class="vc-n">${n}</span><b>${title}</b></div>
      <dl><dt>Needs</dt><dd>${needs}</dd><dt>Gives</dt><dd>${gives}</dd></dl>
      <details><summary>Show the commands</summary><pre class="code">${cmd}</pre><p class="rp-f">${note}</p></details></div>`;
    pane.innerHTML = `<h1>Reproduce</h1><p class="lead">Three paths. The first two give the same numbers every time; a fresh run calls the model again, so decisions can differ.</p>
      <div class="rp-grid">
      ${path(1, "Inspect the recorded POC", "Python 3.12. No model, no credentials.", `This experience, from the recorded files (job ${esc(p.job)}, ${esc(p.date)}).`,
        "python app/server.py      # open http://localhost:8000",
        "<b>If it fails:</b> another process holds the port (set PORT=8001), or app/web/data is missing (run path 2's export).")}
      ${path(2, "Validate the results", "requirements-dev.txt. No model.", `Every test passing, including each figure here against ${esc(p.archive)}.`,
        `python -m pip install -r requirements-dev.txt
python -m pytest -q                          # figures, partitions, prompts, pages
python -m scripts.validate_graph             # benchmark integrity
python -m scripts.evaluate_baseline          # the existing lineage check on every change
python -m scripts.build_experience_data      # rebuild app/web/data from the archive`,
        "<b>If it fails:</b> a figure test failing means app/web/data no longer matches the archive. Run from the repository root.")}
      ${path(3, "Run a fresh investigation", "Databricks workspace with the repo as a Git folder, a serving endpoint (databricks-gpt-oss-120b), a Unity Catalog volume, requirements-llm.txt.", "A new run folder with every step, prompt and reply, scored against the answer key.",
        `python -m scripts.probe_model --n 6          # expect 5–6 usable replies
python -m scripts.detective_job submit --repo /Workspace/Users/&lt;you&gt;/payments-control-impact \\
    --variant A --output-dir /Volumes/workspace/default/detective_runs/&lt;run-name&gt;
python -m scripts.detective_job status &lt;run_id&gt;
python -m scripts.compare_runs --a &lt;recorded-run-folder&gt; --b &lt;your-run-folder&gt; --runs 1`,
        "<b>Expect differences:</b> temperature 0 is not deterministic on this endpoint (80% of key decisions repeated over five runs); compare pooled metrics. The held-out split needs a confirmation flag. An interrupted job resumes with the same output folder. Full steps: docs/runbook.md.")}
      </div>`;
  },

  async pilot(pane) {
    pane.innerHTML = `<h1>From POC to enterprise pilot</h1>
      <p class="lead">What would have to be built or proven before a supervised pilot on real changes. Nothing here is in place today; the POC is not production-ready.</p>
      <div class="vgrid wide"><div class="vc pilot"><b>Data integration</b><span class="pl-now"><i>Today</i>Synthetic files for tickets, lineage and procedures</span><span class="pl-need"><i>Needed</i>Read-only connectors to the change tool, the lineage catalogue and the control library</span></div><div class="vc pilot"><b>Access control</b><span class="pl-now"><i>Today</i>One workspace, one user</span><span class="pl-need"><i>Needed</i>Workspace permissions, service principals, least-privilege access to source systems</span></div><div class="vc pilot"><b>Audit retention</b><span class="pl-now"><i>Today</i>Run files in a Unity Catalog volume</span><span class="pl-need"><i>Needed</i>Retention rules, immutable run records, lineage of every finding to its inputs</span></div><div class="vc pilot"><b>Model reliability</b><span class="pl-now"><i>Today</i>80% repeatability on three development changes</span><span class="pl-need"><i>Needed</i>An agreed threshold, tested on new changes; endpoint version pinning; regression runs on change</span></div><div class="vc pilot"><b>Negative decisions</b><span class="pl-now"><i>Today</i>Not-affected decisions are not checked</span><span class="pl-need"><i>Needed</i>A second check, or sampled human review, of not-affected key controls</span></div><div class="vc pilot"><b>Human review workflow</b><span class="pl-now"><i>Today</i>Routing is recorded; nobody works the queue</span><span class="pl-need"><i>Needed</i>Owner assignment, sign-off, and feedback captured in the change tool</span></div><div class="vc pilot"><b>Operational monitoring</b><span class="pl-now"><i>Today</i>Per-run metrics after the fact</span><span class="pl-need"><i>Needed</i>Latency, cost, error and drift monitoring per change</span></div><div class="vc pilot"><b>Model risk</b><span class="pl-now"><i>Today</i>Not reviewed</span><span class="pl-need"><i>Needed</i>Model-risk validation and documentation under the bank's policy</span></div><div class="vc pilot"><b>Practitioner evaluation</b><span class="pl-now"><i>Today</i>Scored against a synthetic answer key</span><span class="pl-need"><i>Needed</i>Control owners judge real output, including what it left out</span></div></div>
      <p style="font-size:13px;color:var(--ink-3)">The practitioner validation proposed for leadership is on the walkthrough's decision screen.</p>`;
  },

  async ask(pane) {
    const SUGGEST = [
      "Why did version A remain the selected implementation?",
      "Which change types produced the most difficult findings?",
      "What caused the silent miss?",
      "How were the 406 additional review items classified?",
      "What prevents the system from approving a control automatically?",
    ];
    pane.innerHTML = `<h1>Ask about the proof of concept</h1>
      <p><span class="badge review">Live model answers · not validated evidence</span></p>
      <p class="lead">Questions are answered live by the workspace model, from the project's own documents and the recorded results. This is separate from the recorded evidence: if the model is unavailable, every other page still works.</p>
      <div class="ask-s">${SUGGEST.map((q) => `<button class="rec" type="button" data-q="${esc(q)}">${esc(q)}</button>`).join("")}</div>
      <form class="ask" id="f"><input id="q" placeholder="Ask your own question" aria-label="Your question"><button class="btn primary" type="submit">Ask</button></form>
      <div id="a"></div>
      <p class="ask-src"><b>What the model reads:</b> README.md, docs/results.md, docs/evaluation.md, docs/architecture.md, docs/runbook.md, data/README.md, the recorded held-out figures, and the full list of controls, items and test changes. Answers do not carry citations; like any model it can be wrong, so check figures on <i>Evaluation evidence</i> and in the evidence panel.</p>`;
    const ask = async (q) => {
      const out = pane.querySelector("#a");
      out.innerHTML = `<div class="answer">Reading the project material…</div>`;
      try {
        const r = await fetch("api/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: q }) });
        const j = await r.json();
        const down = j.available === false;
        out.innerHTML = `<div class="answer ${down ? "down" : ""}">${down ? "<b>The live assistant is unavailable here.</b> " : ""}${esc(j.answer || j.error || "No answer.")}</div>`;
      } catch (err) {
        out.innerHTML = `<div class="answer down"><b>The live assistant is unavailable here</b> (${esc(err.message)}). The recorded evidence on these pages is unaffected.</div>`;
      }
    };
    pane.querySelector("#f").addEventListener("submit", (e) => {
      e.preventDefault();
      const q = pane.querySelector("#q").value.trim();
      if (q) ask(q);
    });
    pane.querySelectorAll("[data-q]").forEach((b) => b.addEventListener("click", () => { pane.querySelector("#q").value = b.dataset.q; ask(b.dataset.q); }));
  },
};
