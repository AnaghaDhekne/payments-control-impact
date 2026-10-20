// Control Impact Detective — application shell, state, routing and the evidence inspector.

import { enhance } from "./polish.js";
import { esc, highlight, ROUTE_LABEL, TYPE_LABEL, routingReason, quoteWeakness, setNames, expandCodes } from "./util.js";
import { SCREENS, MOMENTS } from "./screens.js";
import { renderRoom, ROOM_PAGES, BOOK_PAGES } from "./room.js";
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
  // What the existing lineage check can reach: follow visible impact links from the
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
  document.getElementById("tip").classList.remove("on"); // no hover left over from the last page
  const main = document.getElementById("main");
  main.innerHTML = "";
  main.className = "";
  if (route === "home") {
    await renderHome(main, app);
  } else if (route === "overview") {
    await renderOverview(main, app);
  } else if (route === "room") {
    await renderRoom(main, app, c, sub || ROOM_PAGES[0].id, "room");
  } else if (route === "handbook") {
    await renderRoom(main, app, c, sub || BOOK_PAGES[0].id, "handbook");
  } else {
    const screen = SCREENS[route] || SCREENS.change;
    await screen(main, app, c);
  }
  main.firstElementChild?.classList.add("fade-in");
  enhance(main);
  document.title = `${titleFor(route)} · Control Impact Detective`;
  if (control) openInspector(control);
  else closeInspector(false);
  window.scrollTo(0, 0);
}

const titleFor = (r) => (r === "home" ? "Find the controls a change could break" : r === "overview" ? "Product overview" : r === "room" ? "Evidence room" : r === "handbook" ? "Technical handbook" : MOMENTS.find((m) => m.id === r)?.label || "Change");

function renderTop() {
  const inWalk = MOMENTS.some((m) => m.id === app.route);
  const section = inWalk ? "walkthrough" : ["room", "handbook", "overview"].includes(app.route) ? app.route : "home";
  document.querySelectorAll("#sitenav a").forEach((a) => {
    const n = a.dataset.nav;
    if (n === "walkthrough") a.href = `#/bank?case=${app.caseId}`;
    if (n === "room") a.href = `#/room?case=${app.caseId}`;
    if (n === "handbook") a.href = `#/handbook?case=${app.caseId}`;
    if (n === section) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  // The step bar and case selector belong to the walkthrough only.
  document.getElementById("subbar").hidden = !inWalk;
  // The decision covers all 18 changes, so the change selector does not apply there.
  const selector = document.getElementById("case");
  selector.style.display = app.route === "decision" || app.route === "bank" ? "none" : "";
  document.body.classList.toggle("has-subbar", inWalk);
  const nav = document.getElementById("journey");
  const idx = MOMENTS.findIndex((m) => m.id === app.route);
  nav.innerHTML = MOMENTS.map(
    (m, i) =>
      `<li><a href="#/${m.id}?case=${app.caseId}" ${i === idx ? 'aria-current="step"' : ""} class="${idx > i ? "done" : ""}">` +
      `<span class="n ${m.intro ? "intro" : ""}">${m.intro ? "i" : i}</span><span class="t">${esc(m.label)}</span></a></li>`
  ).join("");
  // Point to the next step, both in the step bar and with a Next button.
  nav.querySelectorAll("a")[idx + 1]?.classList.add("up-next");
  const nx = document.getElementById("next-step");
  // After the last step the journey continues to the product overview.
  const nextM = inWalk ? MOMENTS[idx + 1] || { id: "overview", label: "Product overview" } : null;
  nx.hidden = !nextM;
  if (nextM) {
    nx.href = `#/${nextM.id}?case=${app.caseId}`;
    nx.innerHTML = `Next: ${esc(nextM.label)} <span aria-hidden="true">→</span>`;
  }
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
    parts.push(`<span class="n"><b>${esc(id)}</b> ${esc(node(id)?.name || "")}</span>`);
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
  const verifierAsked = !!d?.checker;
  const why = {
    check: "The bank's existing lineage check reaches this control through links on record, so it is already on the list. No AI judgement was needed.",
    recommended: "The investigator found evidence that the change affects this control, and the independent verifier agreed. It is recommended for its owner to assess.",
    review: d?.proposer === "UNCERTAIN" && d?.checker === "UNCERTAIN" ? "Neither the investigator nor the second review could decide, so the control goes to a person." : "The investigator and the independent second review disagreed, so the control goes to a person.",
    not_affected: "The investigator judged this control not affected and recorded why. Not-affected decisions are not sent to the independent verifier, so nobody checked this one.",
    undecided: "The investigation ended before this control received a decision.",
  }[route];
  const action = {
    check: "Assess the impact and re-test before release.",
    recommended: "The control owner assesses the impact and decides whether to re-test before release.",
    review: "The control owner weighs both arguments below and decides whether the control is affected.",
    not_affected: "None proposed; nothing is sent to a person.",
    undecided: "None.",
  }[route];
  const hasQuotes = !!(d?.ticket_quote || d?.control_quote);
  const outcome = !app.revealTruth ? "Hidden until you reveal the answer key" : ((["check", "recommended"].includes(route) && truth) || (route === "not_affected" && !truth)) ? "Matches the answer key" : route === "review" ? `Sent to a person; the answer key says ${truth ? "affected" : "not affected"}` : "Does not match the answer key";
  const sections = [];
  // 1. Summary first.
  sections.push(`<section class="why"><h4>Why it landed here</h4><span class="badge ${route}">${esc(ROUTE_LABEL[route])}</span>
    <p>${esc(why)}</p></section>`);
  // 2. Three different questions, kept apart.
  sections.push(`<section><h4>Three separate questions</h4><dl class="tq">
    <dt>Is the evidence really in the documents?</dt><dd>${route === "check" ? "Not needed: found through recorded links." : hasQuotes ? "Yes. Code checked that both quotes appear word for word." : "No quotes were recorded."}</dd>
    <dt>Does the evidence support the impact?</dt><dd>${route === "check" ? "Not needed." : verifierAsked ? (d.proposer === d.checker ? "The independent verifier agreed." : "The independent verifier did not agree.") + " A person makes the final judgement." : "Not checked: the independent verifier was not asked."}</dd>
    <dt>Is the outcome right?</dt><dd>${esc(outcome)}</dd></dl>
    <p class="tq-n">A quote found word for word shows the words exist, not that the reasoning is right.</p></section>`);
  // 3. Observed evidence.
  if (hasQuotes) {
    const weak = (q) => {
      const w = quoteWeakness(q);
      return w ? `<span class="weak">Weak evidence: ${esc(w)}</span>` : "";
    };
    sections.push(`<section><h4>Evidence cited <span class="ev doc">Quoted from the documents</span></h4>
      <div class="doc"><span class="src">Change ticket ${esc(c.ticket.document_id || "")}${weak(d.ticket_quote)}</span>${highlight(c.ticket.text, d.ticket_quote)}</div>
      <div class="doc" style="margin-top:8px"><span class="src">Control procedure ${esc(cid)}${weak(d.control_quote)}</span>${highlight(text, d.control_quote)}</div>
      ${n.family ? `<p style="font-size:12px;color:var(--ink-3);margin:6px 0 0">This procedure is a synthetic template generated for its control family, not a written procedure.</p>` : ""}</section>`);
  } else {
    sections.push(`<section><h4>Control procedure</h4><div class="doc"><span class="src">${esc(cid)}</span>${esc(text)}</div>
      ${n.family ? `<p style="font-size:12px;color:var(--ink-3);margin:6px 0 0">A synthetic template generated for its control family, not a written procedure.</p>` : ""}</section>`);
  }
  const ep = d?.evidence_path?.length ? [...d.evidence_path, cid].filter((x, i, a) => a.indexOf(x) === i) : null;
  if (ep && ep.length > 1 && route !== "check") {
    const parts = [];
    ep.forEach((id, i) => {
      if (i) {
        const e = app.graph.edges.find((x) => x.source === ep[i - 1] && x.target === id && x.carries_impact);
        const documented = e && e.exposable && !c.removedSet.has(e.id);
        parts.push(`<span class="lk ${documented ? "doc" : "inf"}">${documented ? "on record" : "worked out by the AI"}</span>`);
      }
      parts.push(`<span class="n"><b>${esc(id)}</b> ${esc(node(id)?.name || "")}</span>`);
    });
    sections.push(`<section><h4>How it connects to the change</h4><div class="evpath">${parts.join("")}</div></section>`);
  }
  // 4. Investigator, 5. verifier.
  if (d?.proposer) {
    sections.push(`<section><h4>Investigator</h4>
      <div class="verdict"><span class="who a">AI</span><div><b>${esc(d.proposer.toLowerCase())}</b>${expandCodes(d.proposer_reason || "", cid)}
      ${d.proposer_counter && d.proposer_counter !== "none" ? `<br><span style="color:var(--ink-3)">Counter-evidence considered: ${expandCodes(d.proposer_counter, cid)}</span>` : ""}</div></div></section>`);
    sections.push(`<section><h4>Independent verifier</h4>
      ${verifierAsked ? `<div class="verdict"><span class="who c">2nd</span><div><b>${esc(d.checker.toLowerCase())}</b>${expandCodes(d.checker_reason || "Agreed with the investigator.", cid)}</div></div>`
        : `<p class="not-asked">Not invoked. The investigator marked this control not affected, and not-affected decisions are not sent to the independent verifier. This is how a missed control can go unnoticed.</p>`}</section>`);
  }
  // 6. Final routing.
  sections.push(`<section><h4>Final routing and proposed action</h4><p style="margin:0;font-size:13.5px">${esc(action)}</p>
    <p class="honest" style="margin-top:8px">Routing is not a completed review. No control owner acted on this in the proof of concept.</p></section>`);
  // 7. Answer key.
  sections.push(`<section><h4>Answer key (synthetic)</h4>
    ${app.revealTruth
      ? `<span class="badge ${truth ? "truth-yes" : "truth-no"}">${truth ? "Affected by this change" : "Not affected by this change"}</span>
         ${truth ? `<div style="margin-top:10px">${chainHTML(c, cid)}</div><p style="font-size:12.5px;color:var(--ink-3);margin:8px 0 0">The route in the complete map; dashed links are missing from the map the check uses.</p>` : ""}
         <p style="font-size:12.5px;color:var(--ink-3);margin:8px 0 0">A real reviewer would not have this.</p>`
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
      ${c.reach.has(id) && !c.changed.includes(id) ? `<section><p class="honest">The existing lineage check can reach this item through recorded links.</p></section>` : ""}`,
  };
}

export async function openInspector(id, caseId, opts = {}) {
  // stay: show another change's evidence without leaving the page (evidence room lists).
  if (caseId && caseId !== app.caseId && !opts.stay) {
    go(app.route, { caseId, control: id, sub: app.sub });
    return;
  }
  const c = await getCase(caseId || app.caseId);
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
    openInspector(id, c.id, { stay: true });
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
    setNames(Object.fromEntries(app.graph.nodes.map((n) => [n.id, n.name])));
    window.addEventListener("hashchange", render);
    await render();
  } catch (err) {
    document.getElementById("main").innerHTML = `<div style="padding:40px"><h2>The evidence files could not be loaded</h2><p>${esc(err.message)}</p></div>`;
    console.error(err);
  }
})();
