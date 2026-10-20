// The product landing page: what the detective is, in plain words, for someone
// who has never heard of lineage or controls. It sets up one change and stops
// before any result, so the walkthrough keeps its reveal; results live on the
// product overview. Every figure comes from the same
// recorded run as the rest of the experience; nothing here is a projection.

import { esc, pct, el, highlight, expandCodes } from "./util.js";
import { getCase } from "./main.js";

const EXAMPLE = { case: "CHG-027", control: "C02" };

const arrow = `<div class="fl-arrow" aria-hidden="true"><svg viewBox="0 0 40 16"><path d="M0 8h34M28 2l7 6-7 6" fill="none" stroke="currentColor" stroke-width="1.6"/></svg></div>`;

export async function renderHome(main, app) {
  const ex = await getCase(EXAMPLE.case);
  const changed = ex.changed
    .map((id) => app.graph.nodes.find((n) => n.id === id))
    .map((n) => `<b>${esc(n.name)}</b> (${esc(n.id)})`)
    .join(", ");
  const found = ex.counts.check_found;
  const checkLine = found
    ? `The existing check flags ${found} control${found > 1 ? "s" : ""} for review.`
    : "The existing check flags no controls for review.";
  const page = el(`<div class="home">
    <section class="h-hero">
      <div class="h-wrap h-hero-grid">
        <div>
          <p class="h-eyebrow">For banks changing payment systems</p>
          <h1>See which safety checks a system change could quietly break, before it goes live.</h1>
          <p class="h-sub">Banks protect payments with safety checks, called <b>controls</b>: is the customer on a sanctions list, is the amount right, was the payment recorded. When a system changes, some of those checks can stop working. Control Impact Detective reads the change and the bank's own documents, finds the checks at risk, and shows its evidence for each, so the right people can act before release.</p>
          <div class="h-cta">
            <a class="btn lg" href="#problem">Understand the problem <span aria-hidden="true">↓</span></a>
          </div>
          <p class="h-fine">Proof of concept, tested on a realistic made-up bank. No real bank or customer data.</p>
        </div>
        <aside class="h-case card" aria-label="The example change">
          <div class="h-case-k">Start here: one test change</div>
          <div class="h-case-id">CHANGE RECORD · ${esc(ex.id)}</div>
          <div class="h-case-t">${esc(ex.title)}</div>
          <dl>
            <dt>What changes</dt><dd>${changed}</dd>
            <dt>Planned release</dt><dd>${esc(ex.implementation_date || "")}</dd>
            <dt>The request says</dt><dd class="h-case-ticket">“${esc(ex.ticket.text)}”</dd>
          </dl>
          <div class="h-case-check"><span class="h-case-dot" aria-hidden="true"></span>${checkLine}</div>
          <p class="h-case-q">What might the existing check have missed? Read on, then find out for yourself in the Walkthrough.</p>
        </aside>
      </div>
    </section>

    <section class="h-band" id="problem">
      <div class="h-wrap">
        <h2 class="h-h2">The problem, in plain words</h2>
        <div class="h-three">
          <div><span class="h-num">1</span><h3>A change can affect critical controls</h3><p>A new field in a payment message or a new screening interface can stop a check from seeing what it needs. It can go unnoticed until something slips through.</p></div>
          <div><span class="h-num">2</span><h3>Teams rely on a map of connections</h3><p>Before release, the bank follows a map of which systems feed which checks. It is like finding which rooms lose power by reading the wiring diagram.</p></div>
          <div><span class="h-num">3</span><h3>Dependency maps can have gaps</h3><p>Systems change faster than their documentation, so some connections go unrecorded. When a wire is missing from the diagram, a room that will lose power looks fine.</p></div>
        </div>
      </div>
    </section>

    <section class="h-sec" id="how">
      <div class="h-wrap">
        <h2 class="h-h2">How it works</h2>
        <p class="h-intro">It does not need a perfect map. It does what a careful reviewer would do with unlimited time: start from today's check, then read the documents to find what the map leaves out.</p>
        <div class="flow" role="list">
          <div class="fl-col" role="listitem">
            <div class="fl-label">What goes in</div>
            <div class="fl-item"><b>The change request</b><span>What is changing, in the team's own words</span></div>
            <div class="fl-item"><b>The connection map</b><span>Which systems feed which checks, gaps and all</span></div>
            <div class="fl-item"><b>The check procedures</b><span>How each safety check works, as written</span></div>
          </div>
          ${arrow}
          <div class="fl-col fl-engine" role="listitem">
            <div class="fl-label">What the detective does</div>
            <ol class="fl-steps">
              <li><b>Runs today's check</b><span>Follows the map, exactly as the bank does now</span></li>
              <li><b>Investigates the gaps</b><span>Reads the change and the procedures, and traces likely missing connections</span></li>
              <li><b>Quotes its evidence</b><span>Every finding must quote the change and the procedure exactly</span></li>
              <li><b>Gets a second opinion</b><span>An independent check agrees or disagrees; disagreements go to a person</span></li>
            </ol>
          </div>
          ${arrow}
          <div class="fl-col" role="listitem">
            <div class="fl-label">What comes out</div>
            <div class="fl-item out rec"><b>At risk</b><span>Recommended for the owner to re-test, with evidence</span></div>
            <div class="fl-item out rev"><b>Needs a person</b><span>Evidence for and against, sent to the owner to decide</span></div>
            <div class="fl-item out na"><b>Not affected</b><span>With the reason recorded</span></div>
          </div>
          ${arrow}
          <div class="fl-col fl-people" role="listitem">
            <div class="fl-label">Who decides</div>
            <div class="fl-item"><b>Control owners</b><span>Assess and re-test</span></div>
            <div class="fl-item"><b>Change board</b><span>Approves the release</span></div>
          </div>
        </div>
        <p class="h-fine center">Nothing is approved, re-tested or released on the detective's word. It prepares the evidence; people decide.</p>
      </div>
    </section>

  </div>`);
  main.append(page);
  page.querySelector('a[href="#problem"]').addEventListener("click", (e) => {
    e.preventDefault();
    page.querySelector("#problem").scrollIntoView({ behavior: "smooth" });
  });
}

/** The full product overview, for visitors who want the detail. It shows
 * results, so the landing page links to it after the walkthrough invitation. */
export async function renderOverview(main, app) {
  const P = app.exp.portfolio;
  const B = app.exp.benchmark;
  const ex = await getCase(EXAMPLE.case);
  const d = ex.decision(EXAMPLE.control);
  const ctrl = app.graph.nodes.find((n) => n.id === EXAMPLE.control);
  const doc = ex.document_overrides?.[EXAMPLE.control] || app.graph.documents[EXAMPLE.control]?.text || "";
  const surfaced = P.check_found_key + P.agent_found_key;
  const perCall = Math.round(P.model_calls / P.changes);
  const page = el(`<div class="home">
    <section class="h-hero h-hero-s">
      <div class="h-wrap">
        <p class="h-eyebrow">Product overview</p>
        <h1>What the detective delivers, what it costs in review, and what is still unproven.</h1>
      </div>
    </section>

    <section class="h-sec alt">
      <div class="h-wrap">
        <h2 class="h-h2">What you get for each change</h2>
        <p class="h-intro">A list of safety checks at risk. Each one comes with the reason, the exact words it relied on, and the second opinion. This is a real finding from the test.</p>
        <article class="card h-sample" aria-label="Example finding">
          <div class="h-sample-h">
            <div><div class="h-sample-id">Control ${esc(EXAMPLE.control)} · key control · change ${esc(EXAMPLE.case)}</div><h3>${esc(ctrl.name)}</h3></div>
            <span class="badge recommended">At risk: recommended for re-test</span>
          </div>
          <div class="h-sample-b">
            <div><h4>Why</h4><p>${expandCodes(d.proposer_reason)}</p></div>
            <div><h4>Evidence, quoted</h4>
              <div class="doc"><span class="src">From the change request</span>${highlight(ex.ticket.text, d.ticket_quote)}</div>
              <div class="doc" style="margin-top:8px"><span class="src">From the check's procedure</span>${highlight(doc, d.control_quote)}</div></div>
            <div><h4>Second opinion</h4><p>Agreed. ${expandCodes(d.checker_reason || "")}</p></div>
            <div><h4>Suggested next step</h4><p>The control owner assesses the impact and decides whether to re-test before release.</p></div>
          </div>
        </article>
      </div>
    </section>

    <section class="h-sec">
      <div class="h-wrap">
        <h2 class="h-h2">Why it matters</h2>
        <p class="h-intro">Measured on ${P.changes} changes the detective had never seen, in a made-up bank with ${B.items} systems, data items and checks.</p>
        <div class="h-benefits">
          <div class="h-ben"><div class="h-big">${surfaced}<small> of ${P.key_affected}</small></div><h3>Hidden impacts, found early</h3><p>Affected key checks caught by today's check or recommended by the detective, against ${P.check_found_key} by today's check alone.</p></div>
          <div class="h-ben"><div class="h-big">${P.key_routed}</div><h3>People stay in charge</h3><p>Uncertain key checks sent to their owners with evidence for and against, instead of being decided by the system.</p></div>
          <div class="h-ben"><div class="h-big">${P.new_right}<small> of ${P.new_total}</small></div><h3>Findings you can verify</h3><p>New recommendations that were right. Each one shows its quotes and reasoning, and every step is recorded.</p></div>
        </div>
        <div class="h-trade">
          <b>The trade-off is review workload.</b> Across the ${P.changes} changes the detective added ${P.added_items} review items: ${P.added_affected} genuinely affected controls the existing check missed, and ${P.added_unaffected} that were not affected. That is about ${Math.round(P.per_change.total)} items per change instead of about ${Math.round(P.per_change.check)}. Actual reviewer time, operational cost and time savings were not measured.
          <span class="h-trade-r">${P.key_silent} affected key check, out of ${P.key_affected}, was missed entirely.</span>
        </div>
        <div class="h-cmp">
          <h3>Compared with simpler approaches tried on the way</h3>
          <table><thead><tr><th>Approach</th><th>Result</th><th>Measured on</th></tr></thead><tbody>
          ${app.exp.approaches.map((a) => `<tr><td>${esc(a.approach)}</td><td class="num"><b>${pct(a.recovery, 1)}</b> <span>${esc(a.measure)}</span></td><td>${esc(a.set)}</td></tr>`).join("")}
          </tbody></table>
          <p>Each step added information the connection map lacks. The sets, models and scoring differ, so read this as a progression, not a like-for-like comparison; a plain keyword search on the same changes has not been tested. Details are in the evidence room.</p>
        </div>
      </div>
    </section>

    <section class="h-sec alt">
      <div class="h-wrap">
        <h2 class="h-h2">Where it fits in a bank</h2>
        <p class="h-intro">It sits between raising a change and approving it, inside the bank's own data platform.</p>
        <div class="h-arch">
          <div class="h-arch-col">
            <div class="fl-label">The bank's systems</div>
            <div class="h-arch-box">Change management<span>change requests</span></div>
            <div class="h-arch-box">Data lineage catalogue<span>the connection map</span></div>
            <div class="h-arch-box">Control library<span>check procedures and owners</span></div>
          </div>
          ${arrow}
          <div class="h-arch-col arch-core">
            <div class="fl-label">Runs in the bank's Databricks workspace</div>
            <div class="h-arch-core-b">
              <div class="h-arch-name">Control Impact Detective</div>
              <div class="h-arch-part"><b>Jobs</b><span>run one investigation per change</span></div>
              <div class="h-arch-part"><b>Model Serving</b><span>the language model that reads and reasons</span></div>
              <div class="h-arch-part"><b>Unity Catalog</b><span>inputs, results and the full audit trail</span></div>
              <div class="h-arch-part"><b>App</b><span>this experience, for reviewers and leaders</span></div>
            </div>
          </div>
          ${arrow}
          <div class="h-arch-col">
            <div class="fl-label">Where results go</div>
            <div class="h-arch-box">Control owners<span>findings to assess, with evidence</span></div>
            <div class="h-arch-box">Change board<span>a summary for the release decision</span></div>
            <div class="h-arch-box">Risk and audit<span>a recorded trail of every step</span></div>
          </div>
        </div>
        <p class="h-fine center">In this proof of concept the Databricks parts run for real; the bank systems are replaced by synthetic files. Connecting real systems is part of a pilot.</p>
      </div>
    </section>

    <section class="h-sec">
      <div class="h-wrap h-two">
        <div>
          <h2 class="h-h2">What is proven, and what is not yet</h2>
          <ul class="h-proof yes">
            <li>Finds most of what an incomplete map hides: ${pct(P.recovery)} of the missed key checks, on unseen changes.</li>
            <li>Shows its evidence for every finding, and routes doubt to people.</li>
            <li>Runs end to end on Databricks, about ${perCall} model calls per change.</li>
          </ul>
          <ul class="h-proof no">
            <li>Not yet tested on a real bank's changes and documents.</li>
            <li>Reviewer time and cost per change not yet measured.</li>
            <li>Not yet repeatable enough: ${pct(P.consistency.agreement)} of decisions identical across runs, against a 95% target.</li>
          </ul>
        </div>
        <div>
          <h2 class="h-h2">How a bank would adopt it</h2>
          <ol class="h-path">
            <li><b>Practitioner validation</b><span>Control owners judge a sample of findings, including the checks it left out.</span></li>
            <li><b>Supervised pilot</b><span>Real changes and documents, with owners deciding every item.</span></li>
            <li><b>Part of the change process</b><span>Only if the pilot shows findings that are right, useful and worth the review time.</span></li>
          </ol>
        </div>
      </div>
    </section>


    <section class="h-final">
      <div class="h-wrap">
        <h2>Take it with you</h2>
        <p>The one-page summary carries the results, the limits and the options in one place.</p>
        <div class="h-cta center"><a class="btn lg light" href="summary.pdf" download>Download the one-page summary (PDF)</a></div>
      </div>
    </section>
  </div>`);
  main.append(page);
}
