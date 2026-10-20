// Control Impact Detective — application shell, state, routing and the evidence inspector.

import { esc, highlight, ROUTE_LABEL, TYPE_LABEL, routingReason, quoteWeakness } from "./util.js";
import { SCREENS, MOMENTS } from "./screens.js";
import { renderRoom, ROOM_PAGES } from "./room.js";
import { renderHome, renderOverview } from "./home.js";

const app = {
  exp: null,
  graph: null,
  cases: {},
  caseId: null,
  route: "change",
  sub: null,
  selected: null,
  revealTruth: false,
  listeners: new Set(),
};
window.__app = app; // for debugging in the browser console

async function loadJSON(path) {
  const r = await fetch(path, { cache: "no-cache" });
  if (!r.ok) throw new Error(`${path}: ${r.status}`);
  return r.json();
}

export async function getCase(id) {
  if (!app.cases[id]) app.cases[id] = enrich(await loadJSON(`data/cases/${id}.json`));
  return app.cases[id];
}

/** Derived look-ups for one change, computed once. */
function enrich(c) {
  const edges = Object.fromEntries(app.graph.edges.map((e) => [e.id, e]));
  const removed = new Set(c.removed_links);
  const focusEdges = c.focus.edges.map((id) => edges[id]);
  const pair = {};
  for (const e of app.graph.edges) if (e.carries_impact) pair[`${e.source}>${e.target}`] = e.id;
  const visible = (e) => e.exposable && !removed.has(e.id);
  // What the current check can reach: follow visible impact links from the
  // changed items; a control ends a path.
  const nodes = Object.fromEntries(app.graph.nodes.map((n) => [n.id, n]));
  const reach = new Set(c.changed);
  const queue = [...c.changed];
  while (queue.length) {
    const x = queue.shift();
    if (nodes[x]?.type === "CONTROL" && !c.changed.includes(x)) continue;
    for (const e of app.graph.edges) {
      if (e.source === x && e.carries_impact && visible(e) && !reach.has(e.target)) {
        reach.add(e.target);
        queue.push(e.target);
      }
    }
  }
  const pathEdges = (cid) => {
    const out = [];
    for (const p of c.paths[cid] || []) for (let i = 0; i < p.length - 1; i++) out.push(pair[`${p[i]}>${p[i + 1]}`]);
    return out.filter(Boolean);
  };
  const decisions = Object.fromEntries(c.decisions.map((d) => [d.control, d]));
  const onPaths = new Set(c.affected.flatMap(pathEdges));
  return {
    ...c,
    edgeMap: edges,
    focusEdges,
    removedSet: removed,
    reach,
    pathEdges,
    decision: (id) => decisions[id],
    missingOnPaths: [...onPaths].filter((id) => removed.has(id)),
    linksOnPaths: onPaths.size,
    affectedSet: new Set(c.affected),
    keySet: new Set(c.key),
    baselineSet: new Set(c.baseline),
  };
}

// ---------------------------------------------------------------- routing

function parseHash() {
  const h = location.hash.replace(/^#\/?/, "");
  const [path, query] = h.split("?");
  const parts = (path || "home").split("/");
  const q = new URLSearchParams(query || "");
  return { route: parts[0] || "home", sub: parts[1] || null, caseId: q.get("case"), control: q.get("control") };
}

export function go(route, opts = {}) {
  const caseId = opts.caseId || app.caseId;
  const sub = opts.sub ? `/${opts.sub}` : "";
  const control = opts.control ? `&control=${opts.control}` : "";
  const target = `#/${route}${sub}?case=${caseId}${control}`;
  if (location.hash === target) render();
  else location.hash = target;
}

async function render() {
  const { route, sub, caseId, control } = parseHash();
  app.route = route;
  app.sub = sub;
  app.caseId = caseId && app.exp.cases.some((c) => c.id === caseId) ? caseId : app.caseId || app.exp.flagship;
  const c = await getCase(app.caseId);
  renderTop();
  const main = document.getElementById("main");
  main.innerHTML = "";
  main.className = "";
  if (route === "home") {
    await renderHome(main, app);
  } else if (route === "overview") {
    await renderOverview(main, app);
  } else if (route === "room") {
    await renderRoom(main, app, c, sub || ROOM_PAGES[0].id);
  } else {
    const screen = SCREENS[route] || SCREENS.change;
    await screen(main, app, c);
  }
  main.firstElementChild?.classList.add("fade-in");
  document.title = `${titleFor(route)} · Control Impact Detective`;
  if (control) openInspector(control);
  else closeInspector(false);
  window.scrollTo(0, 0);
}

const titleFor = (r) => (r === "home" ? "Find the controls a change could break" : r === "overview" ? "Product overview" : r === "room" ? "Evidence room" : MOMENTS.find((m) => m.id === r)?.label || "Change");

function renderTop() {
  const inWalk = MOMENTS.some((m) => m.id === app.route);
  const section = inWalk ? "walkthrough" : app.route === "room" ? "room" : app.route === "overview" ? "overview" : "home";
  document.querySelectorAll("#sitenav a").forEach((a) => {
    const n = a.dataset.nav;
    if (n === "walkthrough") a.href = `#/change?case=${app.caseId}`;
    if (n === "room") a.href = `#/room?case=${app.caseId}`;
    if (n === section) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  // The step bar and case selector belong to the walkthrough only.
  document.getElementById("subbar").hidden = !inWalk;
  document.body.classList.toggle("has-subbar", inWalk);
  const nav = document.getElementById("journey");
  const idx = MOMENTS.findIndex((m) => m.id === app.route);
  nav.innerHTML = MOMENTS.map(
    (m, i) =>
      `<li><a href="#/${m.id}?case=${app.caseId}" ${i === idx ? 'aria-current="step"' : ""} class="${idx > i ? "done" : ""}">` +
      `<span class="n">${i + 1}</span><span class="t">${esc(m.label)}</span></a></li>`
  ).join("");
  const sel = document.getElementById("case");
  if (!sel.options.length) {
    sel.innerHTML = app.exp.cases
      .map((c) => `<option value="${c.id}">${esc(c.title.replace(" change", ""))} · ${c.id}</option>`)
      .join("");
    sel.addEventListener("change", () => go(app.route, { caseId: sel.value, sub: app.sub }));
  }
  sel.value = app.caseId;
  const p = app.exp.provenance;
  document.getElementById("provenance").innerHTML =
    `<span class="chip recorded"><span class="dot" style="background:var(--missing)"></span>Recorded results, not a live run</span>` +
    `<span class="chip synthetic">Synthetic bank · no real data</span>` +
    `<span><b>Source</b> held-out run, Databricks job ${esc(p.job)} · ${esc(p.date)} · version ${esc(p.version)} (code ${esc(p.code)}) · ${esc(p.model)}</span>` +
    `<span>${esc(p.condition)}</span>`;
}

// ---------------------------------------------------------------- inspector

const node = (id) => app.graph.nodes.find((n) => n.id === id);

function chainHTML(c, cid) {
  const p = (c.paths[cid] || [])[0];
  if (!p) return "";
  const parts = [];
  p.forEach((id, i) => {
    if (i) {
      const e = c.edgeMap[app.graph.edges.find((x) => x.source === p[i - 1] && x.target === id && x.carries_impact)?.id];
      const missing = e && (c.removedSet.has(e.id) || !e.exposable);
      parts.push(`<span class="l ${missing ? "missing" : ""}" title="${missing ? "Missing from the lineage map" : "Recorded in the lineage map"}"></span>`);
    }
    parts.push(`<span class="n" title="${esc(node(id)?.name)}">${esc(id)}</span>`);
  });
  return `<div class="chain">${parts.join("")}</div>`;
}

function controlBody(c, cid) {
  const n = node(cid);
  const d = c.decision(cid);
  const doc = app.graph.documents[cid];
  const text = c.document_overrides?.[cid] || doc?.text || "";
  const truth = c.affectedSet.has(cid);
  const route = c.baselineSet.has(cid) ? "check" : d?.route || "undecided";
  const action = {
    check: "Already flagged by the lineage check: assess the impact and re-test before release.",
    recommended: "Proposed: the control owner assesses the impact and decides whether to re-test before release.",
    review: "Proposed: the control owner weighs both arguments below and decides whether the control is affected.",
    not_affected: "None proposed. The agent gives its reason below; nothing is routed to a person.",
    undecided: "None. The agent did not reach a decision on this control.",
  }[route];
  const sections = [];
  sections.push(`<section><h4>Where the decision landed</h4><span class="badge ${route}">${esc(ROUTE_LABEL[route])}</span>
    ${route === "check" ? `<span class="ev doc">Documented</span>` : ["recommended", "review"].includes(route) ? `<span class="ev val">Needs human validation</span>` : ""}
    ${routingReason(d?.routing_reason) ? `<p style="font-size:13px;color:var(--ink-2);margin:8px 0 0">${esc(routingReason(d.routing_reason))}</p>` : ""}</section>`);
  const ep = d?.evidence_path?.length ? [...d.evidence_path, cid].filter((x, i, a) => a.indexOf(x) === i) : null;
  if (ep && ep.length > 1 && route !== "check") {
    const parts = [];
    ep.forEach((id, i) => {
      if (i) {
        const e = app.graph.edges.find((x) => x.source === ep[i - 1] && x.target === id && x.carries_impact);
        const documented = e && e.exposable && !c.removedSet.has(e.id);
        parts.push(`<span class="lk ${documented ? "doc" : "inf"}">${documented ? "documented link" : "inferred link"}</span>`);
      }
      parts.push(`<span class="n" title="${esc(node(id)?.name)}">${esc(id)}</span>`);
    });
    sections.push(`<section><h4>How the agent connects it to the change</h4><div class="evpath">${parts.join("")}</div>
      <p style="font-size:12.5px;color:var(--ink-3);margin:8px 0 0"><span class="ev doc" style="margin:0">Documented</span> recorded in the lineage map the bank already has. <span class="ev inf" style="margin:0">Inferred</span> not in the map; the agent proposes it from the documents. No confidence score is given; the owner validates.</p></section>`);
  }
  if (truth && app.revealTruth) sections.push(`<section><h4>In the complete synthetic map (the answer key)</h4>${chainHTML(c, cid)}
    <p style="font-size:12.5px;color:var(--ink-3);margin:8px 0 0">Dashed: link missing from the lineage map the current check uses.</p></section>`);
  if (d?.ticket_quote || d?.control_quote) {
    const weak = (q) => {
      const w = quoteWeakness(q);
      return w ? `<span class="weak">Weak evidence: ${esc(w)}</span>` : "";
    };
    const anyWeak = quoteWeakness(d.ticket_quote) || quoteWeakness(d.control_quote);
    sections.push(`<section><h4>Evidence the agent cited <span class="ev doc">Documented: quoted from the documents</span></h4>
      <div class="doc"><span class="src">Change ticket ${esc(c.ticket.document_id || "")}${weak(d.ticket_quote)}</span>${highlight(c.ticket.text, d.ticket_quote)}</div>
      <div class="doc" style="margin-top:8px"><span class="src">Control procedure ${esc(cid)}${weak(d.control_quote)}</span>${highlight(text, d.control_quote)}</div>
      ${n.family ? `<p style="font-size:12px;color:var(--ink-3);margin:6px 0 0">This procedure is a synthetic template generated for its control family, not a written procedure.</p>` : ""}
      <p style="font-size:12px;color:var(--ink-3);margin:6px 0 0">Highlighted: the words quoted, verbatim. A verbatim quote proves the words exist in the source, not that they matter${anyWeak ? "; a quote here is thin, so judge the finding on the chain and the reasoning" : ""}.</p></section>`);
  } else {
    sections.push(`<section><h4>Control procedure</h4><div class="doc"><span class="src">${esc(cid)}</span>${esc(text)}</div>
      ${n.family ? `<p style="font-size:12px;color:var(--ink-3);margin:6px 0 0">A synthetic template generated for its control family, not a written procedure.</p>` : ""}</section>`);
  }
  if (d?.proposer) {
    sections.push(`<section><h4>Reasoning, as recorded</h4>
      <div class="verdict"><span class="who a">AI</span><div><b>Agent: ${esc(d.proposer.toLowerCase())}</b>${esc(d.proposer_reason || "")}
      ${d.proposer_counter && d.proposer_counter !== "none" ? `<br><span style="color:var(--ink-3)">Counter-evidence considered: ${esc(d.proposer_counter)}</span>` : ""}</div></div>
      ${d.checker ? `<div class="verdict"><span class="who c">2nd</span><div><b>Independent checker: ${esc(d.checker.toLowerCase())}</b>${esc(d.checker_reason || "Agreed with the agent.")}</div></div>` : ""}
      </section>`);
  }
  sections.push(`<section><h4>Proposed reviewer action</h4><p style="margin:0;font-size:13.5px">${esc(action)}</p>
    <p class="honest" style="margin-top:8px">Routing is not a completed review. No control owner acted on this in the proof of concept.</p></section>`);
  sections.push(`<section><h4>Synthetic ground truth</h4>
    ${app.revealTruth
      ? `<span class="badge ${truth ? "truth-yes" : "truth-no"}">${truth ? "Affected by this change" : "Not affected by this change"}</span>
         <p style="font-size:12.5px;color:var(--ink-3);margin:8px 0 0">From the complete synthetic map. A real reviewer would not have this.</p>`
      : `<button class="btn" id="reveal" type="button">Reveal the answer key</button>
         <p style="font-size:12.5px;color:var(--ink-3);margin:8px 0 0">Hidden by default: a real reviewer would not know it.</p>`}
    </section>`);
  return { n, html: sections.join("") };
}

function itemBody(c, id) {
  const n = node(id);
  const out = app.graph.edges.filter((e) => e.source === id || e.target === id);
  const rows = out
    .map((e) => {
      const other = e.source === id ? e.target : e.source;
      const missing = c.removedSet.has(e.id) || !e.exposable;
      return `<li style="margin:4px 0"><span class="badge ${missing ? "review" : "not_affected"}" style="padding:2px 8px">${missing ? "missing" : "recorded"}</span>
        ${e.source === id ? "→" : "←"} <b>${esc(other)}</b> ${esc(node(other)?.name || "")} <span style="color:var(--ink-3)">${esc(e.relationship.toLowerCase().replace("_", " "))}</span></li>`;
    })
    .join("");
  const missingN = out.filter((e) => c.removedSet.has(e.id) || !e.exposable).length;
  return {
    n,
    html: `<section><h4>What it is</h4><p style="margin:0">${esc(n.description)}</p>
      ${n.aliases?.length ? `<p style="font-size:12.5px;color:var(--ink-3);margin:6px 0 0">Also called: ${esc(n.aliases.join(", "))}</p>` : ""}</section>
      <section><h4>Links in the complete map (${out.length}; ${missingN} missing from lineage in this change)</h4><ul style="list-style:none;padding:0;margin:0;font-size:13px">${rows}</ul></section>
      ${c.changed.includes(id) ? `<section><p class="honest">This is the item the change modifies.</p></section>` : ""}
      ${c.reach.has(id) && !c.changed.includes(id) ? `<section><p class="honest">The current check can reach this item through recorded links.</p></section>` : ""}`,
  };
}

export async function openInspector(id, caseId) {
  if (caseId && caseId !== app.caseId) {
    go(app.route, { caseId, control: id, sub: app.sub });
    return;
  }
  const c = await getCase(app.caseId);
  app.selected = id;
  const n = node(id);
  const { html } = n.type === "CONTROL" ? controlBody(c, id) : itemBody(c, id);
  const ins = document.getElementById("inspector");
  ins.innerHTML = `<header><div><div class="cid">${esc(n.id)} · ${esc(TYPE_LABEL[n.type])}${n.criticality === "KEY" ? " · key control" : ""} · ${esc(c.id)}</div>
    <h2>${esc(n.name)}</h2></div><button class="btn ghost" id="close" aria-label="Close the inspector">✕</button></header>
    <div class="body">${html}</div>`;
  ins.classList.add("open");
  ins.setAttribute("aria-hidden", "false");
  ins.inert = false;
  ins.querySelector("#close").onclick = () => closeInspector();
  const rv = ins.querySelector("#reveal");
  if (rv) rv.onclick = () => {
    app.revealTruth = true;
    openInspector(id);
  };
  ins.querySelector("#close").focus({ preventScroll: true });
  app.listeners.forEach((f) => f(id));
}

export function closeInspector(notify = true) {
  const ins = document.getElementById("inspector");
  ins.classList.remove("open");
  ins.setAttribute("aria-hidden", "true");
  ins.inert = true; // a closed drawer must not take keyboard focus
  app.selected = null;
  if (notify) app.listeners.forEach((f) => f(null));
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeInspector();
});

// ---------------------------------------------------------------- boot

(async function boot() {
  try {
    [app.exp, app.graph] = await Promise.all([loadJSON("data/experience.json"), loadJSON("data/graph.json")]);
    app.caseId = app.exp.flagship;
    window.addEventListener("hashchange", render);
    await render();
  } catch (err) {
    document.getElementById("main").innerHTML = `<div style="padding:40px"><h2>The evidence files could not be loaded</h2><p>${esc(err.message)}</p></div>`;
    console.error(err);
  }
})();
