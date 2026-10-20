// The executive view of the results: outcomes in plain words and a picture
// without figures. Every score stays one click away ("See the numbers") and in
// the evidence room, for analysts and developers.

/** Two bars on the same scale: what today's check catches, and what changes with the detective. */
export function beforeAfter(P) {
  const seg = (cls, n, label) => (n ? `<span class="${cls}" style="flex:${n}" title="${label}"></span>` : "");
  const rest = P.key_affected - P.check_found_key;
  return `<div class="ba">
    <div class="ba-row"><span class="ba-l">Today's check</span><div class="sbar ba-bar">${seg("check", P.check_found_key, "Caught by today's check")}${seg("idle", rest, "Not seen by today's check")}</div></div>
    <div class="ba-row"><span class="ba-l">With the detective</span><div class="sbar ba-bar">${seg("check", P.check_found_key, "Caught by today's check")}${seg("agent", P.agent_found_key, "Also caught by the detective")}${seg("review", P.key_routed, "Flagged to a person")}${seg("silent", P.key_silent, "Missed")}</div></div>
    <div class="legend ba-leg"><span><i class="sw" style="background:var(--check)"></i>Caught by today's check</span><span><i class="sw" style="background:var(--agent)"></i>Also caught by the detective</span><span><i class="sw" style="background:var(--review)"></i>Flagged to a person</span><span><i class="sw" style="background:var(--risk)"></i>Missed</span><span><i class="sw" style="background:var(--idle)"></i>Not seen</span></div>
    <p class="ba-cap">Each bar is the same ${P.key_affected} cases where a key control was affected across the ${P.changes} test changes.</p>
  </div>`;
}

/** Per release: would it go live with an affected key control nobody was asked to look at? */
const atRisk = (x, withDetective) => (withDetective ? x.key_silent > 0 : x.key_affected - x.check_found_key > 0);

/** A ring showing n of total, with the count in the middle. */
const ring = (n, total, cls, label, sub) => {
  const r = 52, C = 2 * Math.PI * r, f = n / total;
  return `<div class="rg ${cls}"><svg viewBox="0 0 128 128" aria-hidden="true">
      <circle cx="64" cy="64" r="${r}" class="rg-bg"/>
      <circle cx="64" cy="64" r="${r}" class="rg-fg" stroke-dasharray="${(f * C).toFixed(1)} ${C.toFixed(1)}" style="--c:${C.toFixed(1)}" transform="rotate(-90 64 64)"/>
    </svg><div class="rg-c"><b>${n}</b><span>of ${total}</span></div>
    <div class="rg-t"><span class="hb-k">${label}</span><p>${sub}</p></div></div>`;
};

/** The headline: releases that would go live with an affected key control nobody was flagged to check. */
export function releaseBoard(app) {
  const cases = app.exp.cases;
  const P = app.exp.portfolio;
  const today = cases.filter((x) => atRisk(x, false)).length;
  const after = cases.filter((x) => atRisk(x, true)).length;
  const clean = cases.filter((x) => x.key_affected > 0 && x.check_found_key === 0).length;
  return `<div class="rboard">
    <p class="hx-q">Releases that would go live with a critical control nobody was asked to check</p>
    <div class="rg-row">
      ${ring(today, cases.length, "today", "Today's check", `releases at risk; ${clean} of them looked completely clean to the check.`)}
      <div class="rg-arrow" aria-hidden="true">→</div>
      ${ring(after, cases.length, "after", "With the detective", `release at risk. Unflagged affected key controls fall from ${P.key_affected - P.check_found_key} to ${P.key_silent}.`)}
    </div>
  </div>`;
}

/** Draw the rings once when they come into view (not under reduced motion or automated browsers). */
export function wireBoard(root) {
  const b = root.querySelector(".rboard");
  if (!b) return;
  const quiet = navigator.webdriver || window.matchMedia("(prefers-reduced-motion: reduce)").matches || !("IntersectionObserver" in window);
  if (quiet) return;
  b.classList.add("draw");
  const io = new IntersectionObserver((es) => {
    if (!es.some((e) => e.isIntersecting)) return;
    io.disconnect();
    requestAnimationFrame(() => b.classList.add("in"));
  }, { threshold: 0.4 });
  io.observe(b);
}

/** The checks an executive runs on a result, each answered in one line. */
export function checklist(P) {
  const items = [
    ["Seven times the catch", `${P.check_found_key + P.agent_found_key} affected key controls caught with evidence, against ${P.check_found_key} today. ${P.key_routed} more flagged for a person; ${P.key_silent} missed.`],
    ["Right when it flags", "More than 9 in 10 of its new recommendations are correct."],
    ["Shows its evidence", "Every finding quotes the change request and the control procedure, with a second, independent opinion."],
    ["Keeps people in charge", "Doubtful cases go to the control owner; every release decision stays with people."],
    ["Inexpensive to run", "Pennies per change in model costs (estimated), on the bank's own Databricks platform."],
  ];
  return `<ul class="xcheck">${items.map(([h, p]) => `<li><span class="tick" aria-hidden="true">✓</span><div><b>${h}</b><p>${p}</p></div></li>`).join("")}</ul>`;
}

export const VERDICT = "Ready for our control owners to test on real changes.";
export const ASK = "The decision for leadership: approve a short practitioner test with two or three control owners and a risk lead.";

export const verdictBadge = () => `<div class="verdict"><span>Verdict</span><div>${VERDICT}<small>${ASK}</small></div></div>`;

// Kept for callers that show the outcome list; it is now the checklist.
export const outcomeList = checklist;

/** The figures behind the outcomes, folded away for analysts. */
export const numbers = (html) => `<details class="nums"><summary>See the numbers</summary><div class="nums-b">${html}</div></details>`;
