// Small helpers shared by every screen. No framework: the app is plain ES modules.

export const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

export const pct = (x, d = 0) => (x == null ? "–" : `${(100 * x).toFixed(d)}%`);

export function el(html) {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
}

/** Highlight the first case-insensitive occurrence of a quote inside a text. */
export function highlight(text, quote) {
  const t = String(text ?? "");
  const q = String(quote ?? "").trim();
  if (!q) return esc(t);
  let i = t.toLowerCase().indexOf(q.toLowerCase());
  let len = q.length;
  if (i < 0) {
    // Same words, different hyphens or spacing ("town-name" vs "town name").
    const words = q.toLowerCase().split(/[^a-z0-9]+/).filter(Boolean);
    if (!words.length) return esc(t);
    const m = new RegExp(words.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("[^a-z0-9]+"), "i").exec(t);
    if (!m) return esc(t);
    i = m.index;
    len = m[0].length;
  }
  return esc(t.slice(0, i)) + `<mark class="q">${esc(t.slice(i, i + len))}</mark>` + esc(t.slice(i + len));
}

export const reducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const tipEl = () => document.getElementById("tip");
export function tip(evt, html) {
  const t = tipEl();
  if (!html) {
    t.classList.remove("on");
    return;
  }
  t.innerHTML = html;
  t.classList.add("on");
  const x = Math.min(evt.clientX + 14, window.innerWidth - t.offsetWidth - 10);
  const y = Math.min(evt.clientY + 14, window.innerHeight - t.offsetHeight - 10);
  t.style.left = `${x}px`;
  t.style.top = `${y}px`;
}

export const ROUTE_LABEL = {
  check: "Found by the current check",
  recommended: "Recommended by the agent",
  review: "Routed to a control owner",
  not_affected: "Marked not affected",
  undecided: "Not decided",
};

export const TYPE_LABEL = {
  DATA_ELEMENT: "Data element",
  RULE: "Rule",
  INTERFACE: "Interface",
  SYSTEM: "System",
  PROCESS: "Process",
  REPORT: "Report",
  EVIDENCE: "Evidence",
  CONTROL: "Control",
};

export const short = (s, n = 24) => (s.length <= n ? s : s.slice(0, n - 1) + "…");

/** Plain-language routing reasons; internal labels never reach the screen. */
export function routingReason(reason) {
  if (!reason) return "";
  if (/disagree/i.test(reason)) return "The agent and its independent checker disagreed, so the item goes to a person.";
  if (/UNAFFECTED/.test(reason))
    return "The agent judged this control not affected. In this version, not-affected decisions are not double-checked by the independent checker.";
  return /[A-Z]{4,}/.test(reason) ? "" : reason;
}

/** A quote proves words exist, not that they matter: flag the thin ones. */
export function quoteWeakness(q) {
  const t = String(q ?? "").trim();
  if (!t) return "";
  if (/\bfamily\b/i.test(t)) return "quotes a family label from a synthetic template";
  const n = t.split(/\s+/).filter(Boolean).length;
  if (n <= 2) return n === 1 ? "a one-word quote" : "a two-word quote";
  return "";
}

// ---------------------------------------------------------------- reference codes
// Every item in the map has a short code (C02, S03...). Recorded text from the
// agent uses bare codes; on screen each code always carries its name.
let NAMES = {};
export const setNames = (map) => (NAMES = map);
const CODE = /\b(RP\d{2}|[CDRISPE]\d{2,3})\b(?!\s*\()/g;
/** Escape text and put the name in front of every known code: "Screening Engine (S03)". */
export function expandCodes(text, self = null) {
  const t = String(text ?? "");
  return esc(t).replace(CODE, (m, _g, off) => {
    if (m === self) return `${off === 0 ? "This" : "this"} control (${m})`;
    const name = NAMES[m];
    if (!name) return m;
    // Already named right after the code ("S03, the Screening Engine ...")?
    const after = esc(t).slice(off + m.length, off + m.length + name.length + 8).toLowerCase();
    if (after.includes(esc(name).toLowerCase())) return m;
    return `${esc(name)} (${m})`;
  });
}
export const CODE_KEY =
  "Every item in the bank's map has a short code. The letter gives its type: C control, S system, I interface, D data element, R rule, P process, RP report, E evidence.";
