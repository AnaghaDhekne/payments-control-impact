// Interactive dependency graph drawn in SVG from precomputed Graphviz positions.
// Supports pan (drag), zoom (wheel, buttons, keys), hover tooltips, selection and
// per-node / per-edge classes supplied by the caller on every update.

import { esc, short, tip, TYPE_LABEL } from "./util.js";

const NS = "http://www.w3.org/2000/svg";
const W = 132;
const H = 26;

export function createGraph(host, { nodes, edges, layout, onSelect, label = "Dependency map" }) {
  const byId = Object.fromEntries(nodes.map((n) => [n.id, n]));
  const svg = document.createElementNS(NS, "svg");
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", label);
  svg.setAttribute("tabindex", "0");
  const pad = 40;
  const full = { x: -pad, y: -pad, w: layout.width + 2 * pad, h: layout.height + 2 * pad };
  let view = { ...full };
  const setView = () => svg.setAttribute("viewBox", `${view.x} ${view.y} ${view.w} ${view.h}`);
  setView();
  svg.setAttribute("preserveAspectRatio", "xMidYMid meet");

  const gEdges = document.createElementNS(NS, "g");
  const gNodes = document.createElementNS(NS, "g");
  svg.append(gEdges, gNodes);

  const edgeEls = {};
  for (const e of edges) {
    const a = layout.pos[e.source];
    const b = layout.pos[e.target];
    if (!a || !b) continue;
    const p = document.createElementNS(NS, "path");
    const x1 = a[0] + W / 2;
    const x2 = b[0] - W / 2;
    const forward = x2 > x1 + 10;
    const d = forward
      ? `M${x1},${a[1]} C${(x1 + x2) / 2},${a[1]} ${(x1 + x2) / 2},${b[1]} ${x2},${b[1]}`
      : `M${a[0]},${a[1] + H / 2} C${a[0]},${a[1] + 60} ${b[0]},${b[1] - 60} ${b[0]},${b[1] - H / 2}`;
    p.setAttribute("d", d);
    p.setAttribute("class", "g-edge");
    p.dataset.id = e.id;
    gEdges.append(p);
    edgeEls[e.id] = p;
  }

  const nodeEls = {};
  for (const id of Object.keys(layout.pos)) {
    const n = byId[id];
    if (!n) continue;
    const [x, y] = layout.pos[id];
    const g = document.createElementNS(NS, "g");
    g.setAttribute("class", "g-node");
    g.setAttribute("transform", `translate(${x - W / 2},${y - H / 2})`);
    g.setAttribute("tabindex", "0");
    g.setAttribute("role", "button");
    g.setAttribute("aria-label", `${n.id} ${n.name}`);
    g.dataset.id = id;
    const r = document.createElementNS(NS, "rect");
    r.setAttribute("width", W);
    r.setAttribute("height", H);
    r.setAttribute("rx", n.type === "CONTROL" ? 13 : 5);
    const t1 = document.createElementNS(NS, "text");
    t1.setAttribute("x", 9);
    t1.setAttribute("y", 17);
    t1.setAttribute("class", "id");
    t1.textContent = n.id;
    const t2 = document.createElementNS(NS, "text");
    t2.setAttribute("x", 9 + Math.max(30, n.id.length * 6.6));
    t2.setAttribute("y", 17);
    t2.textContent = short(n.name.replace(/^.* — /, ""), n.criticality === "KEY" ? 14 : 16);
    g.append(r, t1, t2);
    if (n.criticality === "KEY") {
      const k = document.createElementNS(NS, "path");
      k.setAttribute("d", `M${W - 12},${H / 2 - 4} l4,4 l-4,4 l-4,-4 z`);
      k.setAttribute("class", "key");
      g.append(k);
    }
    gNodes.append(g);
    nodeEls[id] = g;
  }

  // ---- interaction
  let hoverText = () => "";
  gNodes.addEventListener("mousemove", (evt) => {
    const g = evt.target.closest(".g-node");
    if (!g) return tip(evt, null);
    const n = byId[g.dataset.id];
    tip(evt, `<b>${esc(n.id)} · ${esc(n.name)}</b><span>${esc(TYPE_LABEL[n.type])}${n.criticality === "KEY" ? " · key control" : ""}</span>${hoverText(n.id) ? `<div class="tb">${hoverText(n.id)}</div>` : ""}`);
  });
  gNodes.addEventListener("mouseleave", (evt) => tip(evt, null));
  gNodes.addEventListener("click", (evt) => {
    const g = evt.target.closest(".g-node");
    if (g && !moved) onSelect?.(g.dataset.id);
  });
  gNodes.addEventListener("keydown", (evt) => {
    const g = evt.target.closest(".g-node");
    if (g && (evt.key === "Enter" || evt.key === " ")) {
      evt.preventDefault();
      onSelect?.(g.dataset.id);
    }
  });

  let drag = null;
  let moved = false;
  svg.addEventListener("pointerdown", (evt) => {
    drag = { x: evt.clientX, y: evt.clientY, vx: view.x, vy: view.y };
    moved = false;
  });
  window.addEventListener("pointermove", (evt) => {
    if (!drag) return;
    const dx = evt.clientX - drag.x;
    const dy = evt.clientY - drag.y;
    if (Math.abs(dx) + Math.abs(dy) > 4) {
      moved = true;
      svg.classList.add("dragging");
    }
    const s = view.w / svg.clientWidth;
    view.x = drag.vx - dx * s;
    view.y = drag.vy - dy * s;
    setView();
  });
  window.addEventListener("pointerup", () => {
    drag = null;
    svg.classList.remove("dragging");
    setTimeout(() => (moved = false), 0);
  });
  const zoom = (f, cx = view.x + view.w / 2, cy = view.y + view.h / 2) => {
    const nw = Math.min(full.w * 1.4, Math.max(220, view.w * f));
    const nh = (nw / view.w) * view.h;
    view = { x: cx - ((cx - view.x) * nw) / view.w, y: cy - ((cy - view.y) * nh) / view.h, w: nw, h: nh };
    setView();
  };
  svg.addEventListener(
    "wheel",
    (evt) => {
      evt.preventDefault();
      const pt = svg.createSVGPoint();
      pt.x = evt.clientX;
      pt.y = evt.clientY;
      const p = pt.matrixTransform(svg.getScreenCTM().inverse());
      zoom(evt.deltaY > 0 ? 1.12 : 0.89, p.x, p.y);
    },
    { passive: false }
  );
  svg.addEventListener("keydown", (evt) => {
    if (evt.target !== svg) return;
    const step = view.w * 0.08;
    const k = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] }[evt.key];
    if (k) {
      evt.preventDefault();
      view.x += k[0];
      view.y += k[1];
      setView();
    } else if (evt.key === "+" || evt.key === "=") zoom(0.85);
    else if (evt.key === "-") zoom(1.18);
    else if (evt.key === "0") fit();
  });
  const fit = () => {
    view = { ...full };
    setView();
  };

  const wrap = host;
  wrap.append(svg);
  const zbox = document.createElement("div");
  zbox.className = "zoom";
  zbox.innerHTML = `<button type="button" aria-label="Zoom in">+</button><button type="button" aria-label="Zoom out">−</button><button type="button" aria-label="Fit to view" style="font-size:12px">⤢</button>`;
  const [zi, zo, zf] = zbox.querySelectorAll("button");
  zi.onclick = () => zoom(0.8);
  zo.onclick = () => zoom(1.25);
  zf.onclick = fit;
  wrap.append(zbox);

  return {
    svg,
    /** state: {node: id => class string, edge: id => class string, hover: id => html} */
    update(state) {
      for (const [id, g] of Object.entries(nodeEls)) g.setAttribute("class", `g-node ${state.node?.(id) || ""}`);
      for (const [id, p] of Object.entries(edgeEls)) p.setAttribute("class", `g-edge ${state.edge?.(id) || ""}`);
      if (state.hover) hoverText = state.hover;
    },
    focusOn(ids) {
      const pts = ids.map((i) => layout.pos[i]).filter(Boolean);
      if (!pts.length) return;
      const xs = pts.map((p) => p[0]);
      const ys = pts.map((p) => p[1]);
      const x0 = Math.min(...xs) - 120;
      const y0 = Math.min(...ys) - 80;
      const w = Math.max(...xs) - x0 + 120;
      const h = Math.max(...ys) - y0 + 80;
      const ar = svg.clientWidth / Math.max(1, svg.clientHeight);
      const vw = Math.min(full.w, Math.max(w, h * ar, 760));
      const vh = Math.max(h, vw / ar);
      // Centre the focused items in both directions.
      view = { x: x0 - (vw - w) / 2, y: y0 - (vh - h) / 2, w: vw, h: vh };
      setView();
    },
    pulse(edgeIds) {
      for (const id of edgeIds) {
        const p = edgeEls[id];
        if (!p) continue;
        p.classList.remove("pulse");
        void p.getBBox();
        p.classList.add("pulse");
      }
    },
    fit,
  };
}
