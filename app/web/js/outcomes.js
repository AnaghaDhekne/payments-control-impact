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

/**
 * The headline as a release board: one tile per test change. Red means the release
 * would go live with at least one affected key control left unflagged.
 */
export function releaseBoard(app) {
  const cases = app.exp.cases;
  const P = app.exp.portfolio;
  const today = cases.filter((x) => atRisk(x, false)).length;
  const after = cases.filter((x) => atRisk(x, true)).length;
  const clean = cases.filter((x) => x.key_affected > 0 && x.check_found_key === 0).length;
  const tile = (x) => {
    const t = atRisk(x, false), a = atRisk(x, true);
    const why = (r, w) => (r ? (w ? `${x.key_silent} affected key control left unflagged` : `${x.key_affected - x.check_found_key} affected key controls left unflagged`) : x.key_affected ? "every affected key control caught or flagged" : "no key control affected");
    return `<span class="rt ${t ? "r0" : "g0"} ${a ? "r1" : "g1"}" data-tip-today="${x.id} · ${why(t, false)}" data-tip-after="${x.id} · ${why(a, true)}"></span>`;
  };
  return `<div class="rboard" data-state="after">
    <div class="rb-head">
      <p class="hx-q">Releases that would go live with a critical control nobody was asked to check</p>
      <div class="seg rb-seg" role="group" aria-label="Show"><button type="button" data-rb="today" aria-pressed="false">Today's check</button><button type="button" data-rb="after" aria-pressed="true">With the detective</button></div>
    </div>
    <div class="rb-main">
      <div class="rb-count"><b class="rb-n" data-today="${today}" data-after="${after}">${after}</b><span>of ${cases.length} releases</span></div>
      <div class="rb-tiles" aria-hidden="true">${cases.map(tile).join("")}</div>
    </div>
    <div class="rb-foot">
      <span><i class="rt-k r"></i>Goes live with an unflagged critical control</span><span><i class="rt-k g"></i>Every affected critical control caught or flagged</span>
      <span class="rb-note">Today: <b>${today} of ${cases.length}</b>, and ${clean} of them looked completely clean to the check. With the detective: <b>${after}</b>. Unflagged affected key controls fall from ${P.key_affected - P.check_found_key} to ${P.key_silent}.</span>
    </div>
  </div>`;
}

/** Toggle and, where motion is welcome, play the board from today to with-the-detective once. */
export function wireBoard(root) {
  const b = root.querySelector(".rboard");
  if (!b) return;
  const n = b.querySelector(".rb-n");
  const set = (state) => {
    b.dataset.state = state;
    n.textContent = n.dataset[state];
    b.querySelectorAll("[data-rb]").forEach((x) => x.setAttribute("aria-pressed", String(x.dataset.rb === state)));
    b.querySelectorAll(".rt").forEach((t) => (t.title = state === "today" ? t.dataset.tipToday : t.dataset.tipAfter));
  };
  set(b.dataset.state);
  b.querySelectorAll("[data-rb]").forEach((x) => x.addEventListener("click", () => set(x.dataset.rb)));
  const quiet = navigator.webdriver || window.matchMedia("(prefers-reduced-motion: reduce)").matches || !("IntersectionObserver" in window);
  if (quiet) return;
  set("today");
  const io = new IntersectionObserver((es) => {
    if (!es.some((e) => e.isIntersecting)) return;
    io.disconnect();
    setTimeout(() => set("after"), 1100);
  }, { threshold: 0.5 });
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
