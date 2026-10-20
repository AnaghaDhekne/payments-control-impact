// The five moments of the client journey. Each screen = a story column (the
// question and the answer) and a canvas where the evidence can be explored.

import { esc, pct, el, ROUTE_LABEL, reducedMotion, tip, expandCodes, CODE_KEY, quoteWeakness } from "./util.js";
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
/** "Screening Engine (S03)": never show a bare ID. */
const named = (app, id) => `${esc(nodeOf(app, id)?.name || id)} (${esc(id)})`;
const controls = (app) => app.graph.nodes.filter((n) => n.type === "CONTROL");

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

const TYPE_CODE = { CONTROL: "C", SYSTEM: "S", INTERFACE: "I", DATA_ELEMENT: "D", RULE: "R", PROCESS: "P", REPORT: "RP", EVIDENCE: "E" };
const TYPE_ORDER = ["CONTROL", "DATA_ELEMENT", "PROCESS", "SYSTEM", "INTERFACE", "RULE", "REPORT", "EVIDENCE"];
const TYPE_NAME = { CONTROL: "Controls", DATA_ELEMENT: "Data elements", PROCESS: "Processes", SYSTEM: "Systems", INTERFACE: "Interfaces", RULE: "Rules", REPORT: "Reports", EVIDENCE: "Evidence records" };

/** The test bank in numbers, shown before any change or code appears. */
function bankCard(app) {
  const B = app.exp.benchmark;
  const tc = app.graph.type_counts;
  const lc = Object.entries(app.graph.link_counts).sort((a, b) => b[1] - a[1]);
  return `<section class="card bank" aria-label="The test bank">
    <div class="card-h"><h2>The test bank</h2><div class="aside"><span style="font-size:12.5px;color:var(--ink-3)">An invented bank's outbound cross-border payments, built so the right answer for every change is known</span></div></div>
    <div class="card-b">
      <div class="bank-nums">
        <div><b>${B.items}</b>items in its map</div>
        <div><b>${B.links}</b>links between them</div>
        <div><b>${B.controls}</b>controls, ${B.key_controls} of them key</div>
        <div><b>${B.changes}</b>change scenarios, ${B.held_out} held out for the test</div>
      </div>
      <div class="bank-split">
        <div><h3>Items, and the code each one carries</h3><ul class="bank-types">
          ${TYPE_ORDER.filter((t) => tc[t]).map((t) => `<li><span class="code">${TYPE_CODE[t]}</span><span class="nm">${TYPE_NAME[t]}</span><span class="ct">${tc[t]}</span></li>`).join("")}
        </ul><p class="bank-note">So C02 is a control, S03 a system, I02 an interface. Names are shown beside codes throughout.</p></div>
        <div><h3>Links, by what they mean</h3><ul class="bank-links">
          ${lc.map(([k, v]) => `<li><span class="nm">${esc(k.toLowerCase().replace("_", " "))}</span><span class="bar"><i style="width:${(100 * v) / lc[0][1]}%"></i></span><span class="ct">${v}</span></li>`).join("")}
        </ul></div>
      </div>
    </div></section>`;
}

async function change(main, app, c) {
  const changed = c.changed.map((id) => nodeOf(app, id));
  const isAddress = changed.some((n) => /town|address|postal/i.test(n.name + n.description));
  const damage = {
    omit_sentence: "one sentence of the ticket is missing",
    legacy_alias: "the ticket uses a legacy system name",
    misleading_na: "the ticket wrongly says “control impact: N/A”",
  };
  const dmg = (c.ticket_damage || []).map((d) => damage[d] || d).join("; ");
  const found = c.counts.check_found;
  const verdict = found
    ? `The impact check flags ${found} control${found > 1 ? "s" : ""} for review.`
    : "The impact check finds nothing to review.";
  const stage = el(`<div class="stage">
    <aside class="story">
      ${kicker(1, "The change")}
      <h1 class="title">A routine ${isAddress ? "address-data" : "payment-system"} change. ${verdict}</h1>
      <p class="lead">Before release, a bank checks which controls a change could break, by following its lineage map from the changed item to the controls that depend on it. A control the check misses is not re-tested before release, and can fail unnoticed afterwards.</p>
      <div class="figure"><span class="big">${c.counts.check_found}</span><span class="of">controls flagged</span></div>
      <div class="figure-label">by the conventional lineage check, out of 101</div>
      <p class="question">Can this change proceed, or is something missing?</p>
      <p class="note">A synthetic scenario: an invented bank, with a complete map we can check against. No real release was approved or stopped.</p>
    </aside>
    <section class="canvas change-canvas">
      ${bankCard(app)}
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
          <span>Lineage traversal from ${c.changed.map((id) => named(app, id)).join(", ")} through recorded links. ${found ? "The list looks complete." : "The result looks reassuring."}</span></div></div>
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
  let scope = "paths";
  const stage = el(`<div class="stage">
    <aside class="story">
      ${kicker(2, "The blind spot")}
      <h1 class="title">The map the check relies on is missing links, exactly around this change.</h1>
      <p class="lead">Switch between what the lineage records and what is actually connected. Each row is one route from the changed item to the controls it reaches. Click a control to see the evidence.</p>
      <div class="guide" id="guide" hidden></div>
      <div class="counters" style="grid-template-columns:1fr">
        <div class="counter blue"><div class="v">${c.counts.check_found} of ${c.counts.affected}</div><div class="l">affected controls the check can reach (${c.counts.check_found_key} of ${c.counts.key_affected} key)</div></div>
        <div class="counter amber"><div class="v">${missing} of ${c.linksOnPaths}</div><div class="l">links on the paths to them are missing from the lineage map</div></div>
        <div class="counter ink"><div class="v">${unreached}</div><div class="l">affected controls left invisible to a lineage-only assessment</div></div>
      </div>
      <p style="margin-top:20px">Missing links are not an error in the check. It does exactly what it should with the map it is given; the map is incomplete where change happens.</p>
      <p class="note">Damage applied for the test: 30% of the map's links removed, nearest the change first (71 of 237 recorded links). The complete map is the synthetic ground truth.</p>
    </aside>
    <section class="canvas">
      <div class="graph-wrap" id="gw">
        <div class="graph-bar">
          <div class="seg" role="group" aria-label="Map view">
            <button type="button" data-mode="lineage" aria-pressed="true">What the lineage records</button>
            <button type="button" data-mode="complete" aria-pressed="false">What is actually connected</button>
          </div>
          <div class="right"><div class="seg" role="group" aria-label="How to show it">
            <button type="button" data-scope="paths" aria-pressed="true">Paths</button>
            <button type="button" data-scope="focus" aria-pressed="false">Network</button>
            <button type="button" data-scope="all" aria-pressed="false">Whole map · 148 items</button></div></div>
        </div>
        <div class="pv" id="pv"></div>
        <div class="graph-legend legend" id="gl"></div>
      </div>
    </section></div>`);
  main.append(stage);
  wireGo(stage, app);
  const gw = stage.querySelector("#gw");
  let graph;
  let selected = null;

  // One traced example for the reveal: a key control the check cannot reach,
  // preferably one the agent recommended, whose path crosses a missing link.
  const missingOn = (cid) => c.pathEdges(cid).filter((id) => c.removedSet.has(id) || !c.edgeMap[id].exposable);
  const candidates = c.key.filter((id) => !c.baselineSet.has(id) && missingOn(id).length);
  const guideId =
    candidates.find((id) => c.decision(id)?.route === "recommended") || candidates[0] || null;
  const guideText = () => {
    if (!guideId) return "";
    const n = nodeOf(app, guideId);
    const path = (c.paths[guideId] || [])[0] || [];
    const gone = new Set(missingOn(guideId));
    const links = [];
    for (let i = 0; i < path.length - 1; i++) {
      const e = app.graph.edges.find((x) => x.source === path[i] && x.target === path[i + 1] && x.carries_impact);
      if (e) links.push({ e, missing: gone.has(e.id) });
    }
    const fmt = (l) => `${named(app, l.e.source)} → ${named(app, l.e.target)}`;
    const known = links.filter((l) => !l.missing);
    const lost = links.filter((l) => l.missing);
    return `<div class="guide-h">Example: tracing one key control</div>
      <dl class="guide-dl">
        <dt><i class="sw line"></i>The map records</dt><dd>${known.length ? known.map(fmt).join(", ") : "No link on this route"}</dd>
        <dt><i class="sw dash"></i>Missing from the map</dt><dd>${lost.map(fmt).join(", ")}</dd>
        <dt><i class="sw ctl"></i>Control that may be affected</dt><dd><b>${esc(guideId)}</b> ${esc(n.name)} · key control</dd>
      </dl>
      <p class="guide-risk"><b>Why it matters to the bank:</b> the existing check stops at the missing link, so this control is never put in front of its owner. If the change breaks it, “${esc(n.name.charAt(0).toLowerCase() + n.name.slice(1))}” could stop holding true without anyone being told.</p>
      <p class="guide-more">Click any other control to trace it.</p>`;
  };

  const linkOf = (a, b) => app.graph.edges.find((x) => x.source === a && x.target === b && x.carries_impact);
  const isMissing = (e) => !e || c.removedSet.has(e.id) || !e.exposable;
  const chip = (id) => {
    const n = nodeOf(app, id);
    return `<span class="pv-n ${c.changed.includes(id) ? "changed" : c.reach.has(id) ? "reach" : ""}" title="${esc(n.name)}"><b>${esc(id)}</b> ${esc(n.name)}</span>`;
  };
  const renderPaths = () => {
    const complete = mode === "complete";
    const groups = new Map();
    for (const cid of c.affected) {
      const p = (c.paths[cid] || [])[0];
      if (!p) continue;
      const prefix = p.slice(0, -1);
      const k = prefix.join(">");
      if (!groups.has(k)) groups.set(k, { prefix, controls: [] });
      groups.get(k).controls.push(cid);
    }
    const rows = [...groups.values()].sort((a, b) => b.controls.length - a.controls.length);
    if (!complete) {
      // What the lineage shows: each route only as far as its first missing link.
      const vis = new Map();
      for (const cid of c.affected) {
        const p = (c.paths[cid] || [])[0];
        if (!p) continue;
        let k = 1;
        while (k < p.length && !isMissing(linkOf(p[k - 1], p[k]))) k++;
        const reached = k === p.length;
        const chainIds = reached ? p.slice(0, -1) : p.slice(0, k);
        const key = chainIds.join(">");
        if (!vis.has(key)) vis.set(key, { chainIds, seen: [], hidden: 0 });
        if (reached) vis.get(key).seen.push(cid);
        else vis.get(key).hidden++;
      }
      const html = [...vis.values()]
        .sort((a, b) => b.seen.length + b.hidden - (a.seen.length + a.hidden))
        .map(({ chainIds, seen, hidden }) => {
          const chain = chainIds.map((id, i) => (i ? `<span class="pv-l ok"></span>` : "") + chip(id)).join("");
          return `<div class="pv-g"><div class="pv-chain">${chain}${hidden ? `<span class="pv-end">${seen.length ? "Some routes end here" : "The map ends here"}</span>` : ""}</div>
            ${seen.length ? `<ul class="pv-cs">${seen.map((cid) => ctrlRow(cid, false)).join("")}</ul>` : ""}
            ${hidden ? `<p class="pv-hid">${hidden} affected control${hidden > 1 ? "s" : ""} beyond this point ${hidden > 1 ? "are" : "is"} invisible to the check.</p>` : ""}</div>`;
        })
        .join("");
      const pv = stage.querySelector("#pv");
      pv.innerHTML = html || `<p class="pv-hid">No affected controls for this change.</p>`;
      wireRows(pv);
      return;
    }
    const html = rows
      .map(({ prefix, controls }) => {
        const links = prefix.slice(1).map((id, i) => isMissing(linkOf(prefix[i], id)));
        const shown = prefix;
        let chain = "";
        shown.forEach((id, i) => {
          if (i) chain += `<span class="pv-l ${links[i - 1] ? "miss" : "ok"}" aria-label="${links[i - 1] ? "link missing from the lineage map" : "recorded link"}"></span>`;
          chain += chip(id);
        });
        const ordered = [...controls].sort((a, b) => c.keySet.has(b) - c.keySet.has(a) || a.localeCompare(b, undefined, { numeric: true }));
        const lastMissing = (cid) => isMissing(linkOf(prefix[prefix.length - 1], cid));
        const last = nodeOf(app, prefix[prefix.length - 1]);
        return `<div class="pv-g"><div class="pv-chain">${chain}</div>
          <div class="pv-sub">${controls.length} affected control${controls.length > 1 ? "s" : ""} via ${esc(last.name)}</div>
          <ul class="pv-cs">${ordered.map((cid) => ctrlRow(cid, lastMissing(cid))).join("")}</ul></div>`;
      })
      .join("");
    const pv = stage.querySelector("#pv");
    pv.innerHTML = html || `<p class="pv-hid">No affected controls for this change.</p>`;
    wireRows(pv);
  };
  const wireRows = (pv) => {
    pv.querySelectorAll("[data-id]").forEach((li) => {
      const open = () => {
        selected = li.dataset.id;
        paint(false);
        openInspector(li.dataset.id);
      };
      li.addEventListener("click", open);
      li.addEventListener("keydown", (e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), open()));
    });
  };
  const ctrlRow = (cid, missLast) => {
    const n = nodeOf(app, cid);
    const reached = c.baselineSet.has(cid);
    return `<li class="pv-c ${reached ? "reached" : "hidden"} ${cid === selected ? "sel" : ""}" data-id="${cid}" tabindex="0">
      <span class="pv-l ${missLast ? "miss" : "ok"} short" aria-hidden="true"></span>
      <span class="pv-cn"><b>${esc(cid)}</b> ${esc(n.name)}</span>
      ${c.keySet.has(cid) ? `<span class="pv-key">Key</span>` : ""}
      <span class="pv-st">${reached ? "Reached by the check" : "Hidden from the check"}</span></li>`;
  };

  const build = () => {
    gw.querySelector("svg")?.remove();
    gw.querySelector(".zoom")?.remove();
    gw.classList.toggle("paths", scope === "paths");
    if (scope === "paths") {
      graph = null;
      paint(false);
      return;
    }
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
    if (!graph) {
      renderPaths();
      const g = stage.querySelector("#guide");
      const showGuide = complete && guideId && selected === guideId;
      g.hidden = !showGuide;
      if (showGuide) g.innerHTML = guideText();
      stage.querySelector("#gl").innerHTML = complete
        ? `<span><i class="sw" style="background:var(--navy)"></i>Changed item</span><span><i class="sw line" style="border-color:#8a90a6"></i>Recorded link</span><span><i class="sw dash"></i>Missing from lineage</span><span><i class="sw" style="background:var(--check)"></i>Reached by the check</span><span><i class="sw" style="border:1.6px solid var(--ink)"></i>Hidden from the check</span>`
        : `<span><i class="sw" style="background:var(--navy)"></i>Changed item</span><span><i class="sw line" style="border-color:#8a90a6"></i>Recorded link</span><span><i class="sw" style="background:var(--check)"></i>Reached by the check</span>`;
      stage.querySelector("#gl").innerHTML += `<span class="idkey">IDs: D data · R rule · I interface · S system · P process · RP report · E evidence · C control</span>`;
      return;
    }
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
    const g = stage.querySelector("#guide");
    const showGuide = complete && guideId && selected === guideId;
    g.hidden = !showGuide;
    if (showGuide) g.innerHTML = guideText();
    stage.querySelector("#gl").innerHTML = complete
      ? `<span><i class="sw" style="background:var(--navy)"></i>Changed item</span><span><i class="sw" style="background:var(--check-soft);border:1px solid var(--check)"></i>Reached by the check</span><span><i class="sw" style="border:1.6px solid var(--ink)"></i>Actually affected</span><span><i class="sw dash"></i>Missing from lineage</span>`
      : `<span><i class="sw" style="background:var(--navy)"></i>Changed item</span><span><i class="sw" style="background:var(--check-soft);border:1px solid var(--check)"></i>Reached by the check</span><span><i class="sw line" style="border-color:#aeb3c4"></i>Recorded link</span>`;
  };

  stage.querySelectorAll("[data-mode]").forEach((b) =>
    b.addEventListener("click", () => {
      mode = b.dataset.mode;
      stage.querySelectorAll("[data-mode]").forEach((x) => x.setAttribute("aria-pressed", x === b));
      if (mode === "complete" && guideId && (!selected || !c.affectedSet.has(selected))) selected = guideId;
      paint(mode === "complete" && !reducedMotion());
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

const wrapRows = (rows) => rows.map((r) => (r.startsWith("<em") || r.startsWith('<span class="tb-why') || r.startsWith('<span class="tb-n') ? r : `<div class="tb-row">${r}</div>`)).join("");

/** Hover summary of why a control landed where it did, from the recorded run only.
 * There is no confidence score: the model was not asked for one, so none is shown. */
function decisionBasis(app, c, id, d) {
  const route = c.baselineSet.has(id) ? "check" : d.route;
  const rows = [`<em class="tb-r ${route}">${esc(ROUTE_LABEL[route])}</em>`];
  if (route === "check") {
    rows.push("Reached through links the lineage map records. No model judgement needed.");
    return wrapRows(rows);
  }
  const verdict = (v) => (v ? v.toLowerCase() : "not asked");
  rows.push(`<span class="tb-l">Agent</span> ${esc(verdict(d.proposer))}`);
  if (d.proposer === "AFFECTED") {
    const agreed = d.checker === "AFFECTED";
    rows.push(`<span class="tb-l">Second opinion</span> ${esc(verdict(d.checker))}${agreed ? " (agreed)" : d.checker ? " (disagreed)" : ""}`);
  } else {
    rows.push(`<span class="tb-l">Second opinion</span> not asked; not-affected decisions are not double-checked`);
  }
  const ep = d.evidence_path?.length ? [...d.evidence_path, id].filter((x, i, a) => a.indexOf(x) === i) : [];
  if (ep.length > 1) {
    let doc = 0, inf = 0;
    for (let i = 1; i < ep.length; i++) {
      const e = app.graph.edges.find((x) => x.source === ep[i - 1] && x.target === ep[i] && x.carries_impact);
      e && e.exposable && !c.removedSet.has(e.id) ? doc++ : inf++;
    }
    rows.push(`<span class="tb-l">Chain</span> ${doc} documented, ${inf} inferred link${inf === 1 ? "" : "s"}`);
  }
  if (d.ticket_quote || d.control_quote) {
    const weak = quoteWeakness(d.ticket_quote) || quoteWeakness(d.control_quote);
    rows.push(`<span class="tb-l">Quotes</span> ${weak ? `weak (${esc(weak)})` : "full phrases from both documents"}`);
  }
  if (d.proposer_reason) rows.push(`<span class="tb-why">${expandCodes(d.proposer_reason.length > 140 ? d.proposer_reason.slice(0, 139) + "…" : d.proposer_reason, id)}</span>`);
  rows.push(`<span class="tb-n">No confidence score: the model was not asked for one. Click for the full evidence.</span>`);
  return wrapRows(rows);
}

const replayState = {};

async function investigate(main, app, c) {
  const steps = c.steps;
  const n = steps.length;
  const st = (replayState[c.id] ||= { i: 0, playing: false });
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
      <p>Nothing on this screen calls a model. Each finding had to quote the ticket and the procedure verbatim; an independent model call then judged whether the evidence holds. Disagreements are routed to a person.</p>
      <p>Click any control on the map to inspect the evidence behind its decision.</p>
      <p class="note">${c.counts.steps} investigation steps and ${c.counts.verify_calls} independent checks: ${c.counts.model_calls} model calls in total for this change.</p>
    </aside>
    <section class="canvas"><div class="investigate">
      <div class="card replay">
        <div class="controls">
          <button class="btn primary" id="play" type="button">Play</button>
          <button class="btn" id="back" type="button" aria-label="Previous step">‹</button>
          <button class="btn" id="fwd" type="button" aria-label="Next step">›</button>
          <button class="btn ghost" id="end" type="button">Show result</button>
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

  const stepSummary = (s) => {
    if (s.action === "inspect_control" && s.read?.length) {
      const shown = s.read.slice(0, 3).map((id) => named(app, id)).join("; ");
      return `Read ${s.read.length} control procedure${s.read.length > 1 ? "s" : ""}: ${shown}${s.read.length > 3 ? `; and ${s.read.length - 3} more` : ""}`;
    }
    return expandCodes(s.summary.replace(/^Rejected: /, "Rejected and corrected: "));
  };
  const list = stage.querySelector("#steps");
  list.innerHTML =
    steps
      .map((s, k) => {
        const what = s.action === "explore_node" ? s.explored.map((id) => named(app, id)).join(", ") : s.action === "inspect_control" ? `${s.read.length} procedures` : s.action === "search_controls" ? `“${esc(s.query || "")}”` : "";
        const rej = s.rejected?.length ? `<div class="rej">${s.rejected.length} rejected: ${expandCodes(s.rejected[0].why)}</div>` : "";
        return `<li data-k="${k + 1}"><span class="sn">${s.step}</span><div><span class="act">${esc(verb[s.action] || s.action)}</span> ${what}
          <div class="res">${stepSummary(s)}</div>${rej}</div></li>`;
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
        if (done && d) return decisionBasis(app, c, id, d);
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
    }, reducedMotion() ? 2600 : 1800); // slow enough to read each step aloud
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
      <div class="figure-label">key-control impacts the lineage check missed were recommended by the agent (${pct(P.recovery, 1)}; 95% range ${pct(P.recovery_interval[0], 1)}–${pct(P.recovery_interval[1], 1)}). Target: 50%.</div>
      <p>${P.new_right} of its ${P.new_total} new recommendations were right. Of the ${P.key_misses - P.agent_found_key} it did not recommend, ${P.key_routed} were routed to a person and ${P.key_silent} was not surfaced at all.</p>
      <p>Earlier approaches on the way here recovered ${pct(app.exp.approaches[1].recovery, 1)} (retrieval, development changes) and ${pct(app.exp.approaches[2].recovery, 1)} (edge proposals, five runs combined). The comparison and its caveats are in the evidence room.</p>
      <p>Decisions are not yet stable: across five runs, ${Math.round(P.consistency.agreement * P.consistency.pairs)} of ${P.consistency.pairs} key decisions were identical (target 95%).</p>
      <p class="note">Held-out test: 18 synthetic changes never used while building the agent; version A frozen before the run; one run.</p>
    </aside>
    <section class="canvas">
      <div class="card"><div class="card-h"><h2>This change, ${esc(c.id)}: three views of the same 101 controls</h2>
        <div class="aside"><div class="seg" role="group" aria-label="Controls shown"><button type="button" data-k="0" aria-pressed="true">All controls</button><button type="button" data-k="1" aria-pressed="false">Key only</button></div></div></div>
        <div class="card-b"><div class="estates" id="estates"></div>
        <div class="legend" style="margin-top:12px"><span><i class="sw" style="background:var(--check)"></i>Current check</span><span><i class="sw" style="background:var(--agent)"></i>Recommended by the agent</span><span><i class="sw" style="background:var(--review)"></i>Routed to a person</span><span><i class="sw" style="background:var(--ink)"></i>Actually affected (synthetic ground truth)</span></div>
        <p style="font-size:13.5px;color:var(--ink-2);margin:12px 0 0">The agent recommended <b>${rec.length}</b> (${recRight} actually affected) and routed <b>${rev.length}</b> to a person (${revRight} affected). The answer key has <b>${c.counts.affected}</b> affected; <b>${silent.length}</b> were neither recommended nor routed${silent.length ? ` (${silent.filter((id) => c.keySet.has(id)).length} key)` : ""}.</p></div></div>

      <div class="sec-h"><h2>Across all 18 held-out changes</h2><p>Everything below is the whole test, the same whichever change is selected above.</p></div>
      <div class="card"><div class="card-h"><h2>All 162 key-control impacts across the 18 held-out changes</h2><div class="aside"><span style="font-size:12.5px;color:var(--ink-3)">Each square is one key control affected by one change. Click to inspect.</span></div></div>
        <div class="card-b"><div class="units" id="units"></div>
        <div class="legend" style="margin-top:14px"><span><i class="sw" style="background:var(--check)"></i>Found by the lineage check · ${P.check_found_key}</span><span><i class="sw" style="background:var(--agent)"></i>Recommended by the agent · ${P.agent_found_key}</span><span><i class="sw" style="background:var(--review)"></i>Routed to a person · ${P.key_routed}</span><span><i class="sw" style="background:var(--risk)"></i>Not surfaced · ${P.key_silent}</span></div></div></div>

      <div class="risk" role="note"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18v.5"/></svg>
        <div><b>Remaining coverage risk: one affected key control was neither recommended nor routed for review.</b>
        ${P.silent.map((s) => `<a href="#" data-silent="${s.change}|${s.control}">${esc(s.control)} ${esc(nodeOf(app, s.control).name)}, on ${esc(s.change)}</a>`).join(", ")}. The agent judged it not affected, and this version does not double-check not-affected decisions. Closing that gap, with an independent check of not-affected decisions on key controls, is a condition for any pilot. The ${P.key_routed} routed items are only safe if a control owner works them.</div></div>

      <div class="card"><div class="card-h"><h2>What a reviewer would receive per change</h2><div class="aside"><span style="font-size:12.5px;color:var(--ink-3)">Average over the 18 changes</span></div></div>
        <div class="card-b"><div class="compare">
          <span>Lineage check</span><div><div class="stack" style="width:${(100 * P.per_change.check) / P.per_change.total}%"><div style="width:100%;background:var(--check)">${P.per_change.check}</div></div></div>
          <span>With the agent</span><div><div class="stack">
            <div style="width:${(100 * P.per_change.check) / P.per_change.total}%;background:var(--check)">${P.per_change.check}</div>
            <div style="width:${(100 * P.per_change.real) / P.per_change.total}%;background:var(--agent)">${P.per_change.real}</div>
            <div style="width:${(100 * P.per_change.unaffected) / P.per_change.total}%;background:var(--idle);color:var(--ink)">${P.per_change.unaffected}</div></div></div></div>
        <p style="font-size:13.5px;color:var(--ink-2);margin:14px 0 0"><b>${P.added_affected} of the ${P.added_items}</b> items the agent adds are genuinely affected controls the lineage check missed: necessary review, not waste. <b>${P.added_unaffected}</b> (about ${P.per_change.unaffected} per change) turn out to be unaffected: that is the overhead. Actual reviewer time, operational cost and time savings were not measured.</p></div></div>

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
      <div class="next"><a class="btn" href="summary.pdf" download>Download one-page summary (PDF)</a></div>
      <p class="scope-note">This decision is about the approach as a whole, based on all 18 test changes. It is the same whichever change you looked at.</p>
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
          <li>A practitioner review of a sample of recommended, routed <i>and excluded</i> controls: what the agent left out matters as much as what it surfaced.</li>
          <li>An independent check of not-affected decisions on key controls: the one silent miss came from such a decision.</li>
          <li>Repeatability at 95%, for example a five-run vote, registered in advance and tested on new changes.</li>
          <li>Review overhead, for example a tie-break that may only promote findings (68 of 70 promotions were right).</li>
          <li>Model-risk review, real-data access, audit trail and monitoring.</li></ul></div></div>
        <div class="card"><div class="card-h"><span class="tag" style="background:var(--navy)"></span><h2>What a bank could gain by investigating further</h2></div><div class="card-b"><ul>
          <li>Earlier sight of control impacts that incomplete lineage hides, before release rather than at audit.</li>
          <li>An evidence trail for each impact: the quotes and the reasoning behind it.</li>
          <li>Explicit routing of uncertain impacts to the control owners who should decide.</li></ul></div></div>
      </div>
      <div class="card"><div class="card-h"><h2>A practitioner validation, if leadership chooses one</h2><div class="aside"><span style="font-size:12.5px;color:var(--ink-3)">Uses the recorded output; no new model runs</span></div></div>
        <div class="card-b"><div class="fit3">
          <div><h3 class="vh">Who and what</h3><ul class="vl">
            <li><b>Two or three control owners</b> for screening and payment validation, each deciding and signing their own items.</li>
            <li><b>One risk lead</b>, accountable for the sample design, the thresholds and the sign-off.</li>
            <li><b>The sample</b>, from the ${P.changes} held-out changes: all ${P.key_routed} key controls routed to a person, plus random samples of those recommended and those marked not affected.</li></ul></div>
          <div><h3 class="vh">Measured against</h3><ul class="vl">
            <li><b>Correctness:</b> the share of recommendations owners judge right, beside the ${pct(P.precision, 1)} measured against the synthetic answer key.</li>
            <li><b>Coverage:</b> affected key controls owners find among those marked not affected. Expected: none.</li>
            <li><b>Usefulness and effort:</b> the share owners would act on, and minutes per item, both recorded.</li>
            <li>Thresholds are agreed with the risk lead before the review starts.</li></ul></div>
          <div><h3 class="vh">Results that would argue against a pilot</h3><ul class="vl">
            <li>A key control missed silently among the not-affected sample.</li>
            <li>Owners judging most recommendations not useful.</li>
            <li>Repeatability not moving towards 95% with a five-run vote.</li></ul>
            <p class="vnote">Where it would sit: between raising a change and approving it. Owners decide; nothing is re-tested or released on the agent's word.</p></div>
        </div></div></div>
      <div class="card"><div class="card-h"><h2>Options open from here</h2><div class="aside"><span style="font-size:12.5px;color:var(--ink-3)">The choice rests with leadership</span></div></div>
        <div class="card-b"><div class="options">
          <div class="option focus"><h3>Practitioner review</h3><p>Control owners judge a sample of the agent's output.</p><small>Answers the biggest open question. Two or three people, a few hours.</small></div>
          <div class="option"><h3>Close the gaps first</h3><p>A five-run vote, a promote-only tie-break and a second check of not-affected key controls, each registered in advance.</p><small>Model capacity only.</small></div>
          <div class="option"><h3>Both</h3><p>Independent: the review uses existing output; the fixes use new runs.</p><small>Can run in parallel.</small></div>
          <div class="option"><h3>Stop here</h3><p>Keep the benchmark, code and results as documented.</p><small>Nothing runs in production.</small></div>
        </div></div></div>
    </section></div>`);
  main.append(stage);
  wireGo(stage, app);
}

export const SCREENS = { change, blindspot, investigate, consequence, decision };
