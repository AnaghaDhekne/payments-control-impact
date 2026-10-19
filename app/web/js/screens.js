// The five moments of the client journey. Each screen = a story column (the
// question and the answer) and a canvas where the evidence can be explored.

import { esc, pct, el, ROUTE_LABEL, reducedMotion, tip } from "./util.js";
import { createGraph } from "./graph.js";
import { go, openInspector, getCase } from "./main.js";

export const MOMENTS = [
  { id: "change", label: "The change" },
  { id: "blindspot", label: "The blind spot" },
  { id: "investigate", label: "The investigation" },
  { id: "consequence", label: "The consequence" },
  { id: "decision", label: "The decision" },
];

const kicker = (i, text) => `<div class="kicker"><span class="n">${i}</span>${esc(text)}</div>`;
const nodeOf = (app, id) => app.graph.nodes.find((n) => n.id === id);
const controls = (app) => app.graph.nodes.filter((n) => n.type === "CONTROL");
const nextBtn = (route, label) => `<a class="btn primary" href="#" data-go="${route}">${esc(label)} <span aria-hidden="true">→</span></a>`;

function wireGo(root, app) {
  root.querySelectorAll("[data-go]").forEach((a) =>
    a.addEventListener("click", (e) => {
      e.preventDefault();
      go(a.dataset.go, { sub: a.dataset.sub });
    })
  );
}

// ------------------------------------------------------------------ control estate

/** 101 controls as a field of squares; `state(id)` returns a class or "". */
function estate(app, title, note, state, keyOnly = false) {
  const cs = controls(app).filter((n) => !keyOnly || n.criticality === "KEY");
  const cells = cs
    .map((n) => {
      const s = state(n.id);
      return `<button type="button" class="cell ${s} ${n.criticality === "KEY" ? "key" : ""}" data-id="${n.id}" aria-label="${esc(n.id)} ${esc(n.name)}${s ? ": " + s : ""}"></button>`;
    })
    .join("");
  return `<div class="estate card"><div class="card-b"><h3>${esc(title)}<span>${esc(note)}</span></h3>
    <div class="grid" style="grid-template-columns:repeat(${keyOnly ? 10 : 11},1fr)">${cells}</div></div></div>`;
}

function wireEstates(root, app, c) {
  root.querySelectorAll(".estate .cell").forEach((b) => {
    b.addEventListener("click", () => openInspector(b.dataset.id));
    b.addEventListener("mousemove", (e) => {
      const n = nodeOf(app, b.dataset.id);
      const d = c.decision(n.id);
      const route = c.baselineSet.has(n.id) ? "check" : d?.route;
      tip(e, `<b>${esc(n.id)} · ${esc(n.name)}</b><span>${route ? esc(ROUTE_LABEL[route]) : "Not flagged"}</span>`);
    });
    b.addEventListener("mouseleave", (e) => tip(e, null));
  });
}

// ------------------------------------------------------------------ 1. the change

async function change(main, app, c) {
  const changed = c.changed.map((id) => nodeOf(app, id));
  const isAddress = changed.some((n) => /town|address|postal/i.test(n.name + n.description));
  const damage = {
    omit_sentence: "one sentence of the ticket is missing",
    legacy_alias: "the ticket uses a legacy system name",
    misleading_na: "the ticket wrongly says “control impact: N/A”",
  };
  const dmg = (c.ticket_damage || []).map((d) => damage[d] || d).join("; ");
  const stage = el(`<div class="stage">
    <aside class="story">
      ${kicker(1, "The change")}
      <h1 class="title">A routine ${isAddress ? "address-data" : "payment-system"} change. The impact check finds nothing to review.</h1>
      <p class="lead">Before release, a bank checks which controls a change could break, by following its lineage map from the changed item to the controls that depend on it.</p>
      <div class="figure"><span class="big">${c.counts.check_found}</span><span class="of">controls flagged</span></div>
      <div class="figure-label">by the conventional lineage check, out of 101</div>
      <p class="question">Can this change proceed, or is something missing?</p>
      <div class="next">${nextBtn("blindspot", "Open the dependency map")}</div>
      <p class="note">A synthetic scenario: an invented bank, with a complete map we can check against. No real release was approved or stopped.</p>
    </aside>
    <section class="canvas change-canvas">
      <article class="card record" aria-label="Change record">
        <div class="rh"><div><div class="rid">CHANGE RECORD · ${esc(c.id)}</div><div class="rt">${esc(c.title)}</div></div>
          <span class="chip">${esc((c.change_type || "").replace("_", " ").toLowerCase())}</span></div>
        <dl>
          <dt>What changes</dt><dd>${changed.map((n) => `<b>${esc(n.name)}</b> (${esc(n.id)}) — ${esc(n.description)}`).join("<br>")}</dd>
          ${isAddress ? `<dt>Context</dt><dd>Structured postal addresses are part of ISO 20022 (CBPR+) payment messages; their fields feed validation, screening and message mapping.</dd>` : ""}
          <dt>Planned release</dt><dd>${esc(c.implementation_date || "")} · release group ${esc(c.release_group || "")}</dd>
          <dt>Ticket, as received</dt><dd><div class="ticket-text">${esc(c.ticket.text)}</div>
            ${dmg ? `<div style="font-size:12px;color:var(--ink-3);margin-top:6px">Test condition: ${esc(dmg)}.</div>` : ""}</dd>
        </dl>
        <div class="assessment"><div class="zero">${c.counts.check_found}</div>
          <div><b>Conventional impact assessment: ${c.counts.check_found ? `${c.counts.check_found} affected control${c.counts.check_found > 1 ? "s" : ""} found` : "no affected controls found"}</b>
          <span>Lineage traversal from ${esc(c.changed.join(", "))} through recorded links. The result looks reassuring.</span></div></div>
      </article>
      ${estate(app, "The bank's 101 controls, as the check sees them", `${c.counts.check_found} flagged`, (id) => (c.baselineSet.has(id) ? "check" : ""))}
      <div class="legend"><span><i class="sw" style="background:var(--check)"></i>Flagged by the lineage check</span><span><i class="sw" style="background:var(--idle)"></i>Not flagged</span><span>White inner border: key control</span></div>
    </section></div>`);
  main.append(stage);
  wireGo(stage, app);
  wireEstates(stage, app, c);
}

// ------------------------------------------------------------------ 2. the blind spot

async function blindspot(main, app, c) {
  const missing = c.missingOnPaths.length;
  const unreached = c.affected.filter((id) => !c.baselineSet.has(id)).length;
  let mode = "lineage";
  let scope = "focus";
  const stage = el(`<div class="stage">
    <aside class="story">
      ${kicker(2, "The blind spot")}
      <h1 class="title">The map the check relies on is missing links, exactly around this change.</h1>
      <p class="lead">Switch between what the lineage records and what is actually connected. Then click a control to trace why the check cannot reach it.</p>
      <div class="counters" style="grid-template-columns:1fr">
        <div class="counter blue"><div class="v">${c.counts.check_found} of ${c.counts.affected}</div><div class="l">affected controls the check can reach (${c.counts.check_found_key} of ${c.counts.key_affected} key)</div></div>
        <div class="counter amber"><div class="v">${missing} of ${c.linksOnPaths}</div><div class="l">links on the paths to them are missing from the lineage map</div></div>
        <div class="counter ink"><div class="v">${unreached}</div><div class="l">affected controls left invisible to a lineage-only assessment</div></div>
      </div>
      <p style="margin-top:20px">Missing links are not an error in the check. It does exactly what it should with the map it is given; the map is incomplete where change happens.</p>
      <div class="next">${nextBtn("investigate", "Replay the AI investigation")}</div>
      <p class="note">Damage applied for the test: 30% of the map's links removed, nearest the change first (71 of 237 recorded links). The complete map is the synthetic ground truth.</p>
    </aside>
    <section class="canvas">
      <div class="graph-wrap" id="gw">
        <div class="graph-bar">
          <div class="seg" role="group" aria-label="Map view">
            <button type="button" data-mode="lineage" aria-pressed="true">What the lineage records</button>
            <button type="button" data-mode="complete" aria-pressed="false">What is actually connected</button>
          </div>
          <div class="right"><div class="seg" role="group" aria-label="Map scope">
            <button type="button" data-scope="focus" aria-pressed="true">This change</button>
            <button type="button" data-scope="all" aria-pressed="false">Whole map · 148 items</button></div></div>
        </div>
        <div class="graph-legend legend" id="gl"></div>
      </div>
    </section></div>`);
  main.append(stage);
  wireGo(stage, app);
  const gw = stage.querySelector("#gw");
  let graph;
  let selected = null;

  const build = () => {
    gw.querySelector("svg")?.remove();
    gw.querySelector(".zoom")?.remove();
    const all = scope === "all";
    const nodes = all ? app.graph.nodes : c.focus.nodes.map((id) => nodeOf(app, id));
    const edges = all ? app.graph.edges.filter((e) => e.carries_impact) : c.focusEdges;
    graph = createGraph(gw, {
      nodes,
      edges,
      layout: all ? app.graph.layout : c.focus.layout,
      label: all ? "The whole synthetic map: 148 items and their links" : `Dependency map around ${c.id}`,
      onSelect: (id) => {
        selected = id;
        paint(true);
        openInspector(id);
      },
    });
    paint(false);
  };

  const paint = (pulse) => {
    const complete = mode === "complete";
    const sel = selected && c.affectedSet.has(selected) ? new Set(c.pathEdges(selected)) : new Set();
    graph.update({
      node: (id) => {
        const cls = [];
        if (c.changed.includes(id)) cls.push("changed");
        else if (c.reach.has(id)) cls.push("reach");
        if (complete && c.affectedSet.has(id)) cls.push("truth");
        if (!complete && !c.reach.has(id) && scope === "focus") cls.push("dim");
        if (id === selected) cls.push("selected");
        return cls.join(" ");
      },
      edge: (id) => {
        const e = c.edgeMap[id];
        const missing = c.removedSet.has(id) || !e.exposable;
        const cls = [];
        if (missing) cls.push(complete ? "hidden" : "gone");
        else cls.push(c.reach.has(e.source) && c.reach.has(e.target) ? "reach" : "vis");
        if (sel.has(id)) cls.push("path");
        return cls.join(" ");
      },
      hover: (id) =>
        c.changed.includes(id)
          ? "The changed item"
          : c.reach.has(id)
          ? "Reachable by the current check"
          : complete && c.affectedSet.has(id)
          ? "Affected by the change, but not reachable through recorded links"
          : "",
    });
    if (pulse && sel.size) graph.pulse([...sel].filter((id) => c.removedSet.has(id)));
    stage.querySelector("#gl").innerHTML = complete
      ? `<span><i class="sw" style="background:var(--navy)"></i>Changed item</span><span><i class="sw" style="background:var(--check-soft);border:1px solid var(--check)"></i>Reached by the check</span><span><i class="sw" style="border:1.6px solid var(--ink)"></i>Actually affected</span><span><i class="sw dash"></i>Missing from lineage</span>`
      : `<span><i class="sw" style="background:var(--navy)"></i>Changed item</span><span><i class="sw" style="background:var(--check-soft);border:1px solid var(--check)"></i>Reached by the check</span><span><i class="sw line" style="border-color:#aeb3c4"></i>Recorded link</span>`;
  };

  stage.querySelectorAll("[data-mode]").forEach((b) =>
    b.addEventListener("click", () => {
      mode = b.dataset.mode;
      stage.querySelectorAll("[data-mode]").forEach((x) => x.setAttribute("aria-pressed", x === b));
      paint(false);
      if (mode === "complete" && !reducedMotion()) graph.pulse(c.missingOnPaths);
    })
  );
  stage.querySelectorAll("[data-scope]").forEach((b) =>
    b.addEventListener("click", () => {
      scope = b.dataset.scope;
      stage.querySelectorAll("[data-scope]").forEach((x) => x.setAttribute("aria-pressed", x === b));
      build();
    })
  );
  app.listeners.clear();
  app.listeners.add((id) => {
    selected = id;
    paint(false);
  });
  build();
}

// ------------------------------------------------------------------ 3. the investigation

const replayState = {};

async function investigate(main, app, c) {
  const steps = c.steps;
  const n = steps.length;
  const st = (replayState[c.id] ||= { i: 0, playing: false, speed: 1 });
  const verb = {
    explore_node: "Explore",
    inspect_control: "Read procedures",
    search_controls: "Search procedures",
    submit_findings: "Submit findings",
    submit_finding: "Submit findings",
    trace_metadata: "Run the current check",
    finish: "Finish",
    "invalid reply": "Invalid reply",
  };
  const stage = el(`<div class="stage">
    <aside class="story">
      ${kicker(3, "The investigation")}
      <h1 class="title">Replay how the agent found what the map hides.</h1>
      <p class="lead">Every step below is the agent's own recorded action on this change: what it explored, which control procedures it read, and which findings it submitted.</p>
      <p><span class="chip recorded"><span class="dot" style="background:var(--missing)"></span>Recorded replay · job ${esc(app.exp.provenance.job)} · ${esc(app.exp.provenance.date)}</span></p>
      <p>Nothing on this screen calls a model. Each finding had to quote the ticket and the procedure word for word; an independent model call then agreed or disagreed. Disagreements are routed to a person.</p>
      <p>Click any control on the map to inspect the evidence behind its decision.</p>
      <div class="next">${nextBtn("consequence", "See the consequence")}</div>
      <p class="note">${c.counts.steps} investigation steps and ${c.counts.verify_calls} independent checks: ${c.counts.model_calls} model calls in total for this change.</p>
    </aside>
    <section class="canvas"><div class="investigate">
      <div class="card replay">
        <div class="controls">
          <button class="btn primary" id="play" type="button">Play</button>
          <button class="btn" id="back" type="button" aria-label="Previous step">‹</button>
          <button class="btn" id="fwd" type="button" aria-label="Next step">›</button>
          <button class="btn ghost" id="end" type="button">Show result</button>
          <div class="seg speed" role="group" aria-label="Speed">${[1, 2, 4].map((s) => `<button type="button" data-speed="${s}" aria-pressed="${s === st.speed}">${s}×</button>`).join("")}</div>
        </div>
        <div class="scrub-wrap"><label for="scrub" id="scrubl"></label><input id="scrub" class="scrub" type="range" min="0" max="${n + 1}" step="1"></div>
        <ol class="steps" id="steps"></ol>
      </div>
      <div class="right-col">
        <div class="card"><div class="ledger" id="ledger"></div></div>
        <div class="graph-wrap" id="gw"><div class="graph-legend legend" id="gl"></div></div>
      </div>
    </div></section></div>`);
  main.append(stage);
  wireGo(stage, app);

  const list = stage.querySelector("#steps");
  list.innerHTML =
    steps
      .map((s, k) => {
        const what = s.action === "explore_node" ? `${s.explored.join(", ")}` : s.action === "inspect_control" ? `${s.read.length} procedures` : s.action === "search_controls" ? `“${esc(s.query || "")}”` : "";
        const rej = s.rejected?.length ? `<div class="rej">${s.rejected.length} rejected: ${esc(s.rejected[0].why)}</div>` : "";
        return `<li data-k="${k + 1}"><span class="sn">${s.step}</span><div><span class="act">${esc(verb[s.action] || s.action)}</span> ${what}
          <div class="res">${esc(s.summary.replace(/^Rejected: /, "Rejected and corrected: "))}</div>${rej}</div></li>`;
      })
      .join("") + `<li class="phase" data-k="${n + 1}">Independent check of ${c.counts.verify_calls} findings, then routing</li>`;

  const gw = stage.querySelector("#gw");
  const graph = createGraph(gw, {
    nodes: c.focus.nodes.map((id) => nodeOf(app, id)),
    edges: c.focusEdges,
    layout: c.focus.layout,
    label: `Replay of the investigation of ${c.id}`,
    onSelect: (id) => openInspector(id),
  });

  let framed = null;
  const paint = () => {
    const i = st.i;
    const done = i > n;
    const upto = steps.slice(0, Math.min(i, n));
    const explored = new Set(upto.flatMap((s) => s.explored));
    const read = new Set(upto.flatMap((s) => s.read));
    const accepted = new Set(upto.flatMap((s) => s.accepted));
    graph.update({
      node: (id) => {
        const cls = [];
        if (c.changed.includes(id)) cls.push("changed");
        const d = c.decision(id);
        if (done && c.baselineSet.has(id)) cls.push("r-check");
        else if (done && d?.route === "recommended") cls.push("r-recommended");
        else if (done && d?.route === "review") cls.push("r-review");
        else if (accepted.has(id)) cls.push("read explored");
        else if (read.has(id)) cls.push("read");
        if (explored.has(id)) cls.push("explored");
        if (id === app.selected) cls.push("selected");
        return cls.join(" ");
      },
      edge: (id) => {
        const e = c.edgeMap[id];
        return c.removedSet.has(id) || !e.exposable ? "gone" : "vis";
      },
      hover: (id) => {
        const d = c.decision(id);
        if (done && d) return esc(ROUTE_LABEL[c.baselineSet.has(id) ? "check" : d.route]);
        if (accepted.has(id)) return "Finding submitted; awaiting the independent check";
        if (read.has(id)) return "Procedure read by the agent";
        if (explored.has(id)) return "Explored by the agent";
        return "";
      },
    });
    const rec = done ? c.decisions.filter((d) => d.route === "recommended").length : 0;
    const rev = done ? c.decisions.filter((d) => d.route === "review").length : 0;
    stage.querySelector("#ledger").innerHTML = done
      ? `<div><div class="v">${c.counts.check_found}</div><div class="l"><i class="sw" style="background:var(--check)"></i>Current check</div></div>
         <div><div class="v">${rec}</div><div class="l"><i class="sw" style="background:var(--agent)"></i>Recommended</div></div>
         <div><div class="v">${rev}</div><div class="l"><i class="sw" style="background:var(--review)"></i>Routed to a person</div></div>
         <div><div class="v">${101 - rec - rev - c.counts.check_found}</div><div class="l">Not affected, with reasons</div></div>`
      : `<div><div class="v">${explored.size}</div><div class="l">Items explored</div></div>
         <div><div class="v">${read.size}</div><div class="l">Procedures read</div></div>
         <div><div class="v">${accepted.size}</div><div class="l">Findings submitted</div></div>
         <div><div class="v">${Math.min(i, n)} / ${n}</div><div class="l">Steps</div></div>`;
    stage.querySelector("#gl").innerHTML = done
      ? `<span><i class="sw" style="background:var(--agent)"></i>Recommended</span><span><i class="sw" style="background:var(--review)"></i>Routed for review</span><span><i class="sw" style="background:var(--check)"></i>Current check</span>`
      : `<span><i class="sw" style="border:2px solid var(--agent)"></i>Explored</span><span><i class="sw" style="background:var(--agent-soft)"></i>Procedure read</span><span><i class="sw" style="background:var(--navy)"></i>Changed item</span>`;
    list.querySelectorAll("li").forEach((li) => {
      const k = +li.dataset.k;
      li.classList.toggle("future", k > i);
      li.classList.toggle("now", k === i);
    });
    // Follow the agent: frame the items touched in this step, so labels stay readable.
    if (framed === i) {
      /* keep the user's own pan and zoom */
    } else if (i >= 1 && i <= n) {
      const s = steps[i - 1];
      const touched = [...s.explored, ...s.read, ...s.accepted].filter((id) => c.focus.layout.pos[id]);
      if (touched.length) graph.focusOn([...touched, ...c.changed.filter(() => s.explored.length)]);
    } else if (i === 0) {
      graph.focusOn([...c.changed, ...c.focus.nodes.filter((id) => c.reach.has(id))]);
    } else graph.fit();
    framed = i;
    const now = list.querySelector("li.now");
    if (now && st.playing) now.scrollIntoView({ block: "nearest", behavior: reducedMotion() ? "auto" : "smooth" });
    const scrub = stage.querySelector("#scrub");
    scrub.value = i;
    stage.querySelector("#scrubl").textContent = done ? "Complete: routed after the independent check" : i === 0 ? "Ready: press Play or drag" : `Step ${steps[i - 1].step} of ${n}`;
    stage.querySelector("#play").textContent = st.playing ? "Pause" : done ? "Replay" : "Play";
  };

  let timer = null;
  const stop = () => {
    st.playing = false;
    clearInterval(timer);
    paint();
  };
  const play = () => {
    if (st.i > n) st.i = 0;
    st.playing = true;
    clearInterval(timer);
    timer = setInterval(() => {
      st.i += 1;
      if (st.i > n) return stop();
      paint();
    }, (reducedMotion() ? 1400 : 700) / st.speed);
    paint();
  };
  stage.querySelector("#play").onclick = () => (st.playing ? stop() : play());
  stage.querySelector("#back").onclick = () => { stop(); st.i = Math.max(0, st.i - 1); paint(); };
  stage.querySelector("#fwd").onclick = () => { stop(); st.i = Math.min(n + 1, st.i + 1); paint(); };
  stage.querySelector("#end").onclick = () => { stop(); st.i = n + 1; paint(); };
  stage.querySelector("#scrub").oninput = (e) => { stop(); st.i = +e.target.value; paint(); };
  list.addEventListener("click", (e) => {
    const li = e.target.closest("li[data-k]");
    if (li) { stop(); st.i = +li.dataset.k; paint(); }
  });
  stage.querySelectorAll("[data-speed]").forEach((b) =>
    b.addEventListener("click", () => {
      st.speed = +b.dataset.speed;
      stage.querySelectorAll("[data-speed]").forEach((x) => x.setAttribute("aria-pressed", x === b));
      if (st.playing) play();
    })
  );
  app.listeners.clear();
  app.listeners.add(() => paint());
  // Leaving the screen stops the replay.
  window.addEventListener("hashchange", () => clearInterval(timer), { once: true });
  paint();
}

// ------------------------------------------------------------------ 4. the consequence

async function consequence(main, app, c) {
  const all = await Promise.all(app.exp.cases.map((x) => getCase(x.id)));
  const P = app.exp.portfolio;
  let keyOnly = false;
  const rec = c.decisions.filter((d) => d.route === "recommended");
  const rev = c.decisions.filter((d) => d.route === "review");
  const recRight = rec.filter((d) => d.truth).length;
  const revRight = rev.filter((d) => d.truth).length;
  const silent = c.affected.filter((id) => !c.baselineSet.has(id) && !["recommended", "review"].includes(c.decision(id)?.route));
  const stage = el(`<div class="stage">
    <aside class="story">
      ${kicker(4, "The consequence")}
      <h1 class="title">Far more of the real impact reaches a reviewer, at the cost of more review.</h1>
      <p class="lead">For this change, and across all 18 changes the agent had never seen.</p>
      <div class="figure"><span class="big">${P.agent_found_key}</span><span class="of">of ${P.key_misses}</span></div>
      <div class="figure-label">key-control impacts the lineage check missed were recommended by the agent (${pct(P.recovery)}; 95% range ${pct(P.recovery_interval[0])}–${pct(P.recovery_interval[1])}). Target: 50%.</div>
      <p>${P.new_right} of its ${P.new_total} new recommendations were right. Of the ${P.key_misses - P.agent_found_key} it did not recommend, ${P.key_routed} were routed to a person and ${P.key_silent} was not surfaced at all.</p>
      <p>Decisions are not yet stable: across five runs, ${Math.round(P.consistency.agreement * P.consistency.pairs)} of ${P.consistency.pairs} key decisions were identical (target 95%).</p>
      <div class="next">${nextBtn("decision", "What this means")}</div>
      <p class="note">Held-out test: 18 synthetic changes never used while building the agent; version A frozen before the run; one run.</p>
    </aside>
    <section class="canvas">
      <div class="card"><div class="card-h"><h2>This change, ${esc(c.id)}: three views of the same 101 controls</h2>
        <div class="aside"><div class="seg" role="group" aria-label="Controls shown"><button type="button" data-k="0" aria-pressed="true">All controls</button><button type="button" data-k="1" aria-pressed="false">Key only</button></div></div></div>
        <div class="card-b"><div class="estates" id="estates"></div>
        <div class="legend" style="margin-top:12px"><span><i class="sw" style="background:var(--check)"></i>Current check</span><span><i class="sw" style="background:var(--agent)"></i>Recommended by the agent</span><span><i class="sw" style="background:var(--review)"></i>Routed to a person</span><span><i class="sw" style="background:var(--ink)"></i>Actually affected (synthetic ground truth)</span></div>
        <p style="font-size:13.5px;color:var(--ink-2);margin:12px 0 0">The agent recommended <b>${rec.length}</b> (${recRight} actually affected) and routed <b>${rev.length}</b> to a person (${revRight} affected). The answer key has <b>${c.counts.affected}</b> affected; <b>${silent.length}</b> were neither recommended nor routed${silent.length ? ` (${silent.filter((id) => c.keySet.has(id)).length} key)` : ""}.</p></div></div>

      <div class="card"><div class="card-h"><h2>All 162 key-control impacts across the 18 held-out changes</h2><div class="aside"><span style="font-size:12.5px;color:var(--ink-3)">Each square is one key control affected by one change. Click to inspect.</span></div></div>
        <div class="card-b"><div class="units" id="units"></div>
        <div class="legend" style="margin-top:14px"><span><i class="sw" style="background:var(--check)"></i>Found by the lineage check · ${P.check_found_key}</span><span><i class="sw" style="background:var(--agent)"></i>Recommended by the agent · ${P.agent_found_key}</span><span><i class="sw" style="background:var(--review)"></i>Routed to a person · ${P.key_routed}</span><span><i class="sw" style="background:var(--risk)"></i>Not surfaced · ${P.key_silent}</span></div></div></div>

      <div class="risk" role="note"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18v.5"/></svg>
        <div><b>Remaining coverage risk: one affected key control was neither recommended nor routed for review.</b>
        ${P.silent.map((s) => `<a href="#" data-silent="${s.change}|${s.control}">${esc(s.control)} ${esc(nodeOf(app, s.control).name)}, on ${esc(s.change)}</a>`).join(", ")}. The agent marked it not affected. The ${P.key_routed} routed items are only safe if a control owner works them.</div></div>

      <div class="card"><div class="card-h"><h2>What a reviewer would receive per change</h2><div class="aside"><span style="font-size:12.5px;color:var(--ink-3)">Average over the 18 changes</span></div></div>
        <div class="card-b"><div class="compare">
          <span>Lineage check</span><div><div class="stack" style="width:${(100 * P.per_change.check) / P.per_change.total}%"><div style="width:100%;background:var(--check)">${P.per_change.check}</div></div></div>
          <span>With the agent</span><div><div class="stack">
            <div style="width:${(100 * P.per_change.check) / P.per_change.total}%;background:var(--check)">${P.per_change.check}</div>
            <div style="width:${(100 * P.per_change.real) / P.per_change.total}%;background:var(--agent)">${P.per_change.real}</div>
            <div style="width:${(100 * P.per_change.unaffected) / P.per_change.total}%;background:var(--idle);color:var(--ink)">${P.per_change.unaffected}</div></div></div></div>
        <p style="font-size:13.5px;color:var(--ink-2);margin:14px 0 0"><b>${P.added_affected} of the ${P.added_items}</b> items the agent adds are genuinely affected controls the lineage check missed: necessary review, not waste. <b>${P.added_unaffected}</b> (about ${P.per_change.unaffected} per change) turn out to be unaffected: that is the overhead. Reviewer time was not measured.</p></div></div>

      <div class="card"><div class="card-h"><h2>Consistency: the same change, run five times</h2><div class="aside"><span class="badge review">${Math.round(P.consistency.agreement * 100)}% · target 95% · not met</span></div></div>
        <div class="card-b"><p style="margin:0;font-size:13.5px;color:var(--ink-2)">On three development changes run five times each, ${Math.round(P.consistency.agreement * P.consistency.pairs)} of the ${P.consistency.pairs} affected key controls got the same recommend-or-not decision every time. How much it found was stable; which items went to review varied. A three-run vote reached 94.4% in a later test; the target is still unmet.</p></div></div>
    </section></div>`);
  main.append(stage);
  wireGo(stage, app);

  const drawEstates = () => {
    const box = stage.querySelector("#estates");
    box.innerHTML =
      estate(app, "Lineage check", `${c.counts.check_found} flagged`, (id) => (c.baselineSet.has(id) ? "check" : ""), keyOnly) +
      estate(app, "With the investigation", `${c.counts.check_found + rec.length + rev.length} flagged`, (id) => {
        if (c.baselineSet.has(id)) return "check";
        const r = c.decision(id)?.route;
        return r === "recommended" ? "recommended" : r === "review" ? "review" : "";
      }, keyOnly) +
      estate(app, "Synthetic ground truth", `${c.counts.affected} affected`, (id) => (c.affectedSet.has(id) ? "truth" : ""), keyOnly);
    wireEstates(stage, app, c);
  };
  stage.querySelectorAll("[data-k]").forEach((b) =>
    b.addEventListener("click", () => {
      keyOnly = b.dataset.k === "1";
      stage.querySelectorAll("[data-k]").forEach((x) => x.setAttribute("aria-pressed", x === b));
      drawEstates();
    })
  );
  drawEstates();

  // Unit rows grouped by change type.
  const groups = {};
  for (const k of all) {
    const name = k.title.split(" — ")[0];
    (groups[name] ||= []).push(k);
  }
  stage.querySelector("#units").innerHTML = Object.entries(groups)
    .map(([name, cs]) => {
      const cells = cs
        .flatMap((k) =>
          k.key.map((id) => {
            const r = k.baselineSet.has(id) ? "check" : k.decision(id)?.route;
            const s = r === "check" ? "check" : r === "recommended" ? "recommended" : r === "review" ? "review" : "silent";
            return `<button type="button" class="u ${s}" data-case="${k.id}" data-id="${id}" aria-label="${k.id} ${id}: ${s}"></button>`;
          })
        )
        .join("");
      const t = cs.reduce((a, k) => a + k.key.length, 0);
      return `<div class="row"><div class="nm"><b>${esc(name)}</b>${cs.length} changes · ${t} key impacts</div><div class="cells">${cells || '<span style="font-size:12.5px;color:var(--ink-3)">No key controls affected</span>'}</div></div>`;
    })
    .join("");
  stage.querySelectorAll(".u").forEach((b) => {
    b.addEventListener("click", () => openInspector(b.dataset.id, b.dataset.case));
    b.addEventListener("mousemove", (e) => {
      const n = nodeOf(app, b.dataset.id);
      tip(e, `<b>${esc(b.dataset.case)} · ${esc(n.id)}</b><span>${esc(n.name)}</span>`);
    });
    b.addEventListener("mouseleave", (e) => tip(e, null));
  });
  stage.querySelectorAll("[data-silent]").forEach((a) =>
    a.addEventListener("click", (e) => {
      e.preventDefault();
      const [cs, id] = a.dataset.silent.split("|");
      openInspector(id, cs);
    })
  );
}

// ------------------------------------------------------------------ 5. the decision

async function decision(main, app, c) {
  const P = app.exp.portfolio;
  const stage = el(`<div class="stage">
    <aside class="story">
      ${kicker(5, "The decision")}
      <h1 class="title">Demonstrated on synthetic evidence. Not yet ready for a pilot.</h1>
      <p class="lead">Where lineage is incomplete, an agent that reads what a reviewer reads found most of the controls the lineage check missed, and showed its evidence for each.</p>
      <p>The question that matters most is still open: do control owners find its output right and useful? Only people who own controls can answer that.</p>
      <div class="next"><a class="btn" href="#" data-go="room">Open the evidence room</a><a class="btn" href="summary.pdf" download>Download one-page summary (PDF)</a></div>
      <p class="note">This proof of concept did not measure reviewer time, accuracy on real data, or any cost or saving. None is claimed.</p>
    </aside>
    <section class="canvas">
      <div class="quad">
        <div class="card"><div class="card-h"><span class="tag" style="background:var(--agent)"></span><h2>Demonstrated</h2></div><div class="card-b"><ul>
          <li><b>${P.agent_found_key} of ${P.key_misses}</b> key impacts the lineage check missed were recommended, on changes never seen (target 50%).</li>
          <li><b>${P.new_right} of ${P.new_total}</b> new recommendations were right, each with quoted evidence.</li>
          <li>Disagreements are routed to people; nothing is assumed safe; every step is recorded and replayable.</li>
          <li>Runs end to end on Databricks: Jobs, Model Serving, Unity Catalog and this App.</li></ul></div></div>
        <div class="card"><div class="card-h"><span class="tag" style="background:var(--review)"></span><h2>Still uncertain</h2></div><div class="card-b"><ul>
          <li>Accuracy on real changes, tickets and control documents.</li>
          <li>Whether control owners find the output right and useful, and how long review takes.</li>
          <li>Repeatability: <b>${Math.round(P.consistency.agreement * 100)}%</b> of key decisions identical across runs, against 95%.</li>
          <li>The <b>${P.key_silent}</b> silent miss shows coverage is not complete.</li></ul></div></div>
        <div class="card"><div class="card-h"><span class="tag" style="background:var(--missing)"></span><h2>To validate before any pilot</h2></div><div class="card-b"><ul>
          <li>A practitioner review of a sample of recommended and routed items.</li>
          <li>Repeatability at 95%, for example a five-run vote, registered in advance and tested on new changes.</li>
          <li>Review overhead, for example a tie-break that may only promote findings (68 of 70 promotions were right).</li>
          <li>Model-risk review, real-data access, audit trail and monitoring.</li></ul></div></div>
        <div class="card"><div class="card-h"><span class="tag" style="background:var(--navy)"></span><h2>What a bank could gain by investigating further</h2></div><div class="card-b"><ul>
          <li>Earlier sight of control impacts that incomplete lineage hides, before release rather than at audit.</li>
          <li>An evidence trail for each impact: the quotes and the reasoning behind it.</li>
          <li>Explicit routing of uncertain impacts to the control owners who should decide.</li>
          <li>A view of where lineage is weakest, from the links the agent had to infer.</li></ul></div></div>
      </div>
      <div class="card"><div class="card-h"><h2>Options open from here</h2><div class="aside"><span style="font-size:12.5px;color:var(--ink-3)">The choice rests with leadership</span></div></div>
        <div class="card-b"><div class="options">
          <div class="option focus"><h3>Practitioner review</h3><p>Control owners judge a sample of the agent's output.</p><small>Answers the biggest open question. Two or three people, a few hours.</small></div>
          <div class="option"><h3>Close the two gaps</h3><p>A five-run vote and a promote-only tie-break, each registered in advance.</p><small>Model capacity only.</small></div>
          <div class="option"><h3>Both</h3><p>Independent: the review uses existing output; the fixes use new runs.</p><small>Can run in parallel.</small></div>
          <div class="option"><h3>Stop here</h3><p>Keep the benchmark, code and results as documented.</p><small>Nothing runs in production.</small></div>
        </div></div></div>
    </section></div>`);
  main.append(stage);
  wireGo(stage, app);
}

export const SCREENS = { change, blindspot, investigate, consequence, decision };
