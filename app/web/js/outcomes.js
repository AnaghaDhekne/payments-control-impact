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

/** The headline: affected key controls that nobody is asked to look at before release, today and with the detective. */
export function hero(P) {
  const caught = P.check_found_key + P.agent_found_key;
  const unflaggedToday = P.key_affected - P.check_found_key;
  return `<div class="hero-x">
    <p class="hx-q">Affected key controls left unflagged before release</p>
    <div class="hx-row">
      <div class="hx-side"><span class="hb-k">Today's check</span><b class="hx-n">${unflaggedToday}</b><p>of ${P.key_affected} never flagged for review.</p></div>
      <div class="hx-arrow" aria-hidden="true">→</div>
      <div class="hx-side on"><span class="hb-k">With the detective</span><b class="hx-n">${P.key_silent}</b><p>of ${P.key_affected}. ${caught} are caught with evidence and ${P.key_routed} flagged for a person to decide.</p></div>
    </div>
  </div>`;
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
