// Two reference areas share one layout:
//  - the evidence room: what was found (results, every test change, limits, Q&A);
//  - the technical handbook: how it works (architecture, benchmark, damage,
//    the investigator and verifier calls with their prompts, reproduction).

import { esc, pct, el, ROUTE_LABEL, TYPE_LABEL, expandCodes } from "./util.js";
import { createGraph } from "./graph.js";
import { go, openInspector, getCase } from "./main.js";

export const ROOM_PAGES = [
  { id: "results", label: "Results" },
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

const table = (head, rows, cls = "") =>
  `<table class="t ${cls}"><thead><tr>${head.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody></table>`;

const PAGES = {
  async method(pane, app) {
    const P = app.exp.portfolio;
    pane.innerHTML = `<h1>Benchmark and scoring</h1>
      <p class="lead">How the right answer is known, which changes the numbers come from, and exactly what each metric counts.</p>
      <section><h2>The answer key</h2>
        <p>A control is affected when the changed item reaches it by following impact-carrying links in their direction through the complete map, at most six steps, stopping at the first control. This is plain code; no model labels anything. The check and the agent only ever see a damaged copy of the map (<i>How the map is damaged</i>).</p></section>
      <section><h2>Development and held-out changes</h2>${table(["Set", "Changes", "Used for"], [
        `<tr><td><b>Development</b></td><td class="num">36</td><td>Building and tuning the agent, and the version tests (B, C, D). Results from these are labelled as development.</td></tr>`,
        `<tr><td><b>Held-out</b></td><td class="num">${P.changes}</td><td>One frozen run of version A, after the design was fixed. Every headline figure comes from these. Guarded in code: the test split needs an explicit confirmation flag.</td></tr>`,
      ])}</section>
      <section><h2>Metrics</h2>${table(["Metric", "Exact meaning", "Held-out value"], [
        `<tr><td><b>Key-control recovery</b></td><td>Affected key controls the baseline missed that the agent recommended (both calls said affected) ÷ affected key controls the baseline missed</td><td class="num">${P.agent_found_key} / ${P.key_misses}</td></tr>`,
        `<tr><td><b>Recommendation precision</b></td><td>New recommendations that are affected in the answer key ÷ all new recommendations (beyond the baseline)</td><td class="num">${P.new_right} / ${P.new_total}</td></tr>`,
        `<tr><td><b>Added review items</b></td><td>Every control added beyond the baseline: new recommendations plus findings routed to a person, split by the answer key into affected and unaffected</td><td class="num">${P.added_items} = ${P.added_affected} + ${P.added_unaffected}</td></tr>`,
        `<tr><td><b>Review overhead</b></td><td>Added review items that are unaffected in the answer key</td><td class="num">${P.added_unaffected}</td></tr>`,
        `<tr><td><b>Consistency</b></td><td>Affected key controls given the same recommend-or-not decision in every one of five runs ÷ affected key controls (three development changes)</td><td class="num">${Math.round(P.consistency.agreement * P.consistency.pairs)} / ${P.consistency.pairs}</td></tr>`,
        `<tr><td><b>Silent miss</b></td><td>Affected key controls neither reached by the baseline, nor recommended, nor routed to a person</td><td class="num">${P.key_silent}</td></tr>`,
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
          <div><div class="ba-h">What the check and the agent see</div><div class="pv-chain">${path.slice(0, path.indexOf(cut.b)).map((id, i) => (i ? '<span class="pv-l ok"></span>' : "") + `<span class="pv-n ${i === 0 ? "changed" : ""}"><b>${esc(id)}</b> ${esc(nodeName(id))}</span>`).join("")}<span class="pv-end">The map ends here</span></div></div>
        </div>
        <ul class="ra-notes">
          <li><b>Removed:</b> the link ${named(cut.a)} → ${named(cut.b)}.</li>
          <li><b>Effect on the check:</b> it follows recorded links only, so it stops at ${named(cut.a)} and never reaches ${named(exId)}.</li>
          <li><b>Evidence still available to the agent:</b> ${d?.ticket_quote ? `the ticket says “${esc(d.ticket_quote)}”, and the procedure says “${esc(d.control_quote)}”.` : "the ticket and the control procedures, which the damage does not remove."}</li>
        </ul>
        <button class="btn" type="button" id="ex-open">Open the evidence for ${esc(exId)}</button>`;
    }
    const inc = (id) => app.graph.edges.filter((e) => e.exposable && (e.source === id || e.target === id)).length;
    const keepRule = c.changed.map((id) => { const n = inc(id); return `${named(id)}: ${n} recordable links, keeps at least ${Math.max(1, Math.ceil((n * 70) / 100))}`; }).join("; ");
    pane.innerHTML = `<h1>How the map is damaged</h1>
      <p class="lead">The check and the agent never see the complete map. For every change, fixed code generates a damaged copy, the same way every time, so results can be reproduced and compared.</p>
      <div class="scope-note" style="margin-bottom:22px">A controlled synthetic stress test: it shows what happens when lineage is incomplete near a change. It is not evidence that a real bank's lineage is missing 30% of its links.</div>
      <section><h2>Worked example: ${esc(c.id)}</h2>${example}</section>
      <section><h2>The links</h2><ol class="ra-steps">
        <li><b>Budget.</b> At level L, round(237 × L / 100) recordable links are removed: ${removed} of 237 at the test level of 30% (one of the 238 links is never recordable).</li>
        <li><b>Nearest the change first.</b> Links are ordered by how close they sit to a changed item, counting steps in either direction, and removed from the closest outwards. A seeded random number breaks ties.</li>
        <li><b>Keep a local frontier.</b> Each changed item with n recordable links keeps at least ⌈n × (100 − L) / 100⌉ of them, and never fewer than one, so lineage looks stale rather than cut off. If that guard skips links, the rest of the budget comes from links further away. On ${esc(c.id)}: ${keepRule}.</li>
        <li><b>Reproducible.</b> Every choice is seeded from the run seed (${esc(D.seed)}), the change, the level and the mode.</li>
      </ol></section>
      <section><h2>The documents</h2><p style="color:var(--ink-2);margin-top:0">At level L, each of these happens with probability L% (30% in the test), independently:</p>
        ${table(["Damage", "What the reader sees", "Applies to"], [
          `<tr><td><b>Legacy name</b></td><td>“Legacy reference: &lt;old system name&gt;.” added at the start</td><td>Tickets and control procedures that have an old name</td></tr>`,
          `<tr><td><b>Missing sentence</b></td><td>The last sentence is dropped</td><td>Tickets and control procedures with more than one sentence</td></tr>`,
          `<tr><td><b>Misleading assessment</b></td><td>“Ticket assessment: control impact: N/A.” added at the end</td><td>Tickets of every seventh change only</td></tr>`,
        ])}
        <p style="font-size:13px;color:var(--ink-3)">On ${esc(c.id)}: ${removed} links removed; ticket ${c.ticket_damage?.length ? esc(c.ticket_damage.map((d) => dmg[d] || d).join("; ")) : "unchanged"}.</p></section>
      <section><h2>Why levels and modes</h2><p style="color:var(--ink-2);margin-top:0">The generator builds every combination of level (${D.levels.join("%, ")}%) and mode (${D.modes.map(esc).join(", ")}). Correlated damage, nearest the change, is the hard case the product is for: documentation lags exactly where change happens. Random damage and 60% show how fragile the current check is either way.</p>
        ${table(["Lineage damage", "Key controls the current check finds (18 test changes)"], app.exp.rules_by_damage.map((r) => `<tr><td>${esc(r.damage)}</td><td class="num">${pct(r.found, 1)}</td></tr>`))}
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
      ["trace_metadata", "{}", "Runs the current check: controls reachable through the visible links"],
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
      <section><h2>What fixed code checks on every reply</h2><ul class="ra-notes">
        <li><b>Shape.</b> The reply must be one tool call with valid arguments; anything else is rejected and the agent is told why.</li>
        <li><b>Read before deciding.</b> A finding is refused unless that control's procedure was inspected.</li>
        <li><b>Verbatim quotes.</b> ticket_quote must appear in the ticket and control_quote in that procedure, exactly; otherwise the finding is rejected and must be corrected.</li>
        <li><b>Known items only.</b> Every code in evidence_path must exist in the map; reason and counter-evidence must not be empty.</li>
        <li><b>No early stop.</b> finish is refused while controls are undecided, until the steps run out.</li>
      </ul></section>
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
      <section><h2>When it is called</h2><p style="margin-top:0;color:var(--ink-2)">For every finding the investigator marked <b>affected</b> or <b>uncertain</b>. Findings marked <b>not affected</b> are recorded with their reason but not sent to the verifier.</p></section>
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
        `<tr><td>affected or uncertain</td><td>a different answer</td><td><span class="badge review">Routed to a person</span> (disagreement is never discarded)</td></tr>`,
        `<tr><td>uncertain</td><td>uncertain</td><td><span class="badge review">Routed to a person</span></td></tr>`,
        `<tr><td>not affected</td><td>not asked</td><td><span class="badge not_affected">Marked not affected</span>, reason kept</td></tr>`,
        `<tr><td colspan="2">Reached by the current check</td><td><span class="badge check">Found by the current check</span>, always kept</td></tr>`,
      ])}</section>
      ${promptBlock("verifier", pr.verifier, "scripts/detective.py · VERIFIER_INSTRUCTIONS, followed by the JSON evidence built by verification_evidence(). Same model and settings as the investigator.")}`;
    wirePrompt(pane);
    pane.querySelector("#sm-open")?.addEventListener("click", () => openInspector(miss.control, miss.change));
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
          <p>${P.added_items} items were added for review: ${P.added_affected} genuinely affected, ${P.added_unaffected} not (about ${P.per_change.unaffected} per change). The goal counted real impacts as workload too.</p></div>
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
            <ol><li>Run today's lineage check</li><li>Explore items and their recorded links</li><li>Search and read control procedures</li><li>Submit findings with quotes and reasons</li></ol>
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
        <li><b>Deterministic baseline.</b> The lineage check follows the visible links. Whatever it reaches is always kept.</li>
        <li><b>Agent loop.</b> The model selects a tool → the tool runs → the observation is added to the notebook → the model sees it on the next step. Repeated within the step budget.</li>
        <li><b>Deterministic validation.</b> Each submitted finding must cite an inspected control, verbatim quotes and known item codes, or it is rejected back to the agent.</li>
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
      <section><h2>Engineering choices</h2><ul class="ra-notes">
        <li><b>Read-only.</b> The agent's tools only read. It never edits lineage or controls.</li>
        <li><b>Isolated scoring.</b> Tests check that answer-key labels never appear in a prompt.</li>
        <li><b>Resumable.</b> Every step is saved as it happens, so an interrupted job continues where it stopped.</li>
      </ul></section>`;
  },

  async limits(pane, app) {
    pane.innerHTML = `<h1>Limits and fixes tried</h1><p class="lead">What the proof of concept does not show, where it goes wrong, and what was tried to fix it.</p>
      <div class="scope-note" style="margin-bottom:22px"><b>Not measured, not claimed:</b> reviewer time, accuracy on real bank data, cost or savings, and any production outcome.</div>
      <section><h2>Known weaknesses</h2>${table(["Weakness", "Evidence", "Next step"], app.exp.limits.map((l) => `<tr><td><b>${esc(l.issue)}</b></td><td>${esc(l.evidence)}</td><td>${esc(l.response)}</td></tr>`))}</section>
      <section><h2>Fixes tried, none adopted</h2><p style="color:var(--ink-2);margin-top:0">Each fix had an adoption rule written before it ran. None met all of its rules, so the original agent (version A) is final.</p>
        ${table(["Fix", "What happened", "Rule it had to meet"], app.exp.version_tests.map((v) => `<tr><td><b>${esc(v.name)}</b><br><span style="color:var(--ink-3);font-size:12px">${esc(v.test)}</span></td><td>${esc(v.result)}</td><td>${esc(v.rule)}</td></tr>`))}
        <p style="font-size:13px;color:var(--ink-3)">What was learnt: the tie-break is reliable when it promotes a finding (68 of 70 promotions were right) but not when it dismisses one; voting across runs steadies decisions, but a three-run vote reached 94.4%, just short of 95%. Source: docs/results.md.</p></section>
      <details class="terms"><summary>Terms used in the evidence room</summary>${table(["Term", "Meaning"], app.exp.glossary.map((g) => `<tr><td><b>${esc(g.term)}</b></td><td>${esc(g.meaning)}</td></tr>`))}</details>`;
  },

  async reproduce(pane, app) {
    const p = app.exp.provenance;
    pane.innerHTML = `<h1>Reproduce</h1><p class="lead">Three different things, with different guarantees. Inspecting and validating the recorded run gives the same numbers every time. A fresh investigation calls a model again, so its decisions can differ from the recorded ones.</p>
      <section><h2>1 · Inspect the recorded POC</h2>
        <p class="rp-m"><b>Needs:</b> Python 3.12. No model, no credentials. <b>Gives:</b> this experience, served from the recorded files (Databricks job ${esc(p.job)}, ${esc(p.date)}).</p>
        <pre class="code">python app/server.py      # open http://localhost:8000</pre>
        <p class="rp-f"><b>If it fails:</b> another process holds the port (set PORT=8001), or app/web/data is missing (run step 2's export).</p></section>
      <section><h2>2 · Validate the results</h2>
        <p class="rp-m"><b>Needs:</b> requirements-dev.txt. No model. <b>Gives:</b> every test passing, including the checks that each figure shown here equals the archive ${esc(p.archive)}, and a re-export of the app data from it.</p>
        <pre class="code">python -m pip install -r requirements-dev.txt
python -m pytest -q                          # figures, partitions, prompts, pages
python -m scripts.validate_graph             # benchmark integrity
python -m scripts.evaluate_baseline          # the current check on every change
python -m scripts.build_experience_data      # rebuild app/web/data from the archive</pre>
        <p class="rp-f"><b>If it fails:</b> a figure test failing means app/web/data no longer matches the archive; re-run the export and look at what changed. Run commands from the repository root.</p></section>
      <section><h2>3 · Run a fresh investigation</h2>
        <p class="rp-m"><b>Needs:</b> a Databricks workspace with the repository as a Git folder, a serving endpoint (default databricks-gpt-oss-120b), a Unity Catalog volume for results, and requirements-llm.txt. <b>Gives:</b> a new run folder with every step, prompt and reply, scored against the answer key.</p>
        <pre class="code">python -m scripts.probe_model --n 6          # expect 5–6 usable replies
python -m scripts.detective_job submit --repo /Workspace/Users/&lt;you&gt;/payments-control-impact \\
    --variant A --output-dir /Volumes/workspace/default/detective_runs/&lt;run-name&gt;
python -m scripts.detective_job status &lt;run_id&gt;
python -m scripts.compare_runs --a &lt;recorded-run-folder&gt; --b &lt;your-run-folder&gt; --runs 1</pre>
        <p class="rp-f"><b>Expect differences:</b> temperature 0 does not make the endpoint deterministic; decisions differ from run to run (80% of key decisions repeated in the five-run test). Compare pooled metrics, not individual decisions. The held-out split needs an explicit confirmation flag. <b>If it fails:</b> check the endpoint with probe_model first; an interrupted job resumes when resubmitted with the same output folder. Full steps: docs/runbook.md.</p></section>`;
  },

  async pilot(pane) {
    pane.innerHTML = `<h1>From POC to enterprise pilot</h1>
      <p class="lead">What would have to be built or proven before a supervised pilot on real changes. Nothing here is in place today; the POC is not production-ready.</p>
      ${table(["Area", "Today, in the POC", "Needed for a pilot"], [
        `<tr><td><b>Data integration</b></td><td>Synthetic files for tickets, lineage and procedures</td><td>Read-only connectors to the change tool, the lineage catalogue and the control library</td></tr>`,
        `<tr><td><b>Access control</b></td><td>One workspace, one user</td><td>Workspace permissions, service principals, least-privilege access to source systems</td></tr>`,
        `<tr><td><b>Audit retention</b></td><td>Run files in a Unity Catalog volume</td><td>Retention rules, immutable run records, lineage of every finding to its inputs</td></tr>`,
        `<tr><td><b>Model reliability</b></td><td>80% repeatability on three development changes</td><td>An agreed threshold, tested on new changes; endpoint version pinning; regression runs on change</td></tr>`,
        `<tr><td><b>Negative decisions</b></td><td>Not-affected decisions are not checked</td><td>A second check, or sampled human review, of not-affected key controls</td></tr>`,
        `<tr><td><b>Human review workflow</b></td><td>Routing is recorded; nobody works the queue</td><td>Owner assignment, sign-off, and feedback captured in the change tool</td></tr>`,
        `<tr><td><b>Operational monitoring</b></td><td>Per-run metrics after the fact</td><td>Latency, cost, error and drift monitoring per change</td></tr>`,
        `<tr><td><b>Model risk</b></td><td>Not reviewed</td><td>Model-risk validation and documentation under the bank's policy</td></tr>`,
        `<tr><td><b>Practitioner evaluation</b></td><td>Scored against a synthetic answer key</td><td>Control owners judge real output, including what it left out</td></tr>`,
      ])}
      <p style="font-size:13px;color:var(--ink-3)">The practitioner validation proposed for leadership is on the walkthrough's decision screen.</p>`;
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
