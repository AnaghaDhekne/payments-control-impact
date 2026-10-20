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
    <p class="ba-cap">Each bar is the same set of critical safeguards that the test changes actually affected.</p>
  </div>`;
}

export const OUTCOMES = [
  ["Hidden impacts now surface before release", "Most of the safeguards a change would quietly break, invisible to today's check, are found before go-live."],
  ["Every finding can be checked", "Each comes with the exact lines from the change request and the control procedure, and a second, independent opinion."],
  ["People stay in charge", "Doubtful cases go straight to the control owner, and every release decision stays with people."],
  ["Next: our own changes", "Control owners put it to work on real changes from our pipeline, then leadership decides on a supervised pilot."],
];

export const VERDICT = "Ready for our control owners to test on real changes.";

export function outcomeList() {
  return `<div class="oc">${OUTCOMES.map(([h, p]) => `<div class="oc-i"><b>${h}</b><p>${p}</p></div>`).join("")}</div>`;
}

export const verdictBadge = () => `<div class="verdict"><span>Verdict</span>${VERDICT}</div>`;

/** The figures behind the outcomes, folded away for analysts. */
export const numbers = (html) => `<details class="nums"><summary>See the numbers</summary><div class="nums-b">${html}</div></details>`;
