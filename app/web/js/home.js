// The product landing page: what the detective is, in plain words, for someone
// who has never heard of lineage or controls. Every figure comes from the same
// recorded run as the rest of the experience; nothing here is a projection.

import { esc, pct, el, highlight } from "./util.js";
import { go, getCase } from "./main.js";

const EXAMPLE = { case: "CHG-027", control: "C02" };

const arrow = `<div class="fl-arrow" aria-hidden="true"><svg viewBox="0 0 40 16"><path d="M0 8h34M28 2l7 6-7 6" fill="none" stroke="currentColor" stroke-width="1.6"/></svg></div>`;

export async function renderHome(main, app) {
  const P = app.exp.portfolio;
  const B = app.exp.benchmark;
  const ex = await getCase(EXAMPLE.case);
  const d = ex.decision(EXAMPLE.control);
  const ctrl = app.graph.nodes.find((n) => n.id === EXAMPLE.control);
  const doc = ex.document_overrides?.[EXAMPLE.control] || app.graph.documents[EXAMPLE.control]?.text || "";
  const surfaced = P.check_found_key + P.agent_found_key;
  const perCall = Math.round(P.model_calls / P.changes);
  const added = Math.round(P.per_change.total) - Math.round(P.per_change.check);

  const page = el(`<div class="home">
    <section class="h-hero">
      <div class="h-wrap h-hero-grid">
        <div>
          <p class="h-eyebrow">For banks changing payment systems</p>
          <h1>See which safety checks a system change could quietly break, before it goes live.</h1>
          <p class="h-sub">Banks protect every payment with safety checks, called <b>controls</b>: is the customer on a sanctions list, is the amount right, was the payment recorded. When a system changes, some of those checks can stop working. Control Impact Detective reads the change and the bank's own documents, finds the checks at risk, and shows its evidence for each, so the right people can act before release.</p>
          <div class="h-cta">
            <a class="btn primary lg" href="#" data-demo>See it work on an example <span aria-hidden="true">→</span></a>
            <a class="btn lg" href="#how">How it works</a>
          </div>
          <p class="h-fine">Proof of concept, tested on a realistic made-up bank. No real bank or customer data.</p>
        </div>
        <div class="h-compare card" aria-label="One change, two answers">
          <div class="h-compare-h">One real test case: ${esc(ex.title.split(" — ")[0])}</div>
          <div class="h-ans today">
            <span class="h-ans-l">Today's check</span>
            <span class="h-ans-v">${ex.counts.check_found}</span>
            <span class="h-ans-t">safety checks flagged. The change looks safe to release.</span>
          </div>
          <div class="h-ans with">
            <span class="h-ans-l">With the detective</span>
            <span class="h-ans-v">${ex.counts.agent_recommended}</span>
            <span class="h-ans-t">safety checks found at risk, ${ex.counts.agent_recommended_right} of them correctly, each with quoted evidence.</span>
          </div>
          <div class="h-compare-f">${ex.counts.affected} were actually affected, according to the test's answer key.</div>
        </div>
      </div>
    </section>

    <section class="h-band">
      <div class="h-wrap">
        <h2 class="h-h2">The problem, in plain words</h2>
        <div class="h-three">
          <div><span class="h-num">1</span><h3>Every change touches safety checks</h3><p>A new field in a payment message or a new screening interface can stop a check from seeing what it needs. Nobody notices until something slips through.</p></div>
          <div><span class="h-num">2</span><h3>Teams rely on a map of connections</h3><p>Before release, the bank follows a map of which systems feed which checks. It is like finding which rooms lose power by reading the wiring diagram.</p></div>
          <div><span class="h-num">3</span><h3>The map always has gaps</h3><p>When wires are missing from the diagram, rooms that will lose power look fine. In our test, the map-based check found <b>${pct(P.check_found_key / P.key_affected)}</b> of the affected key checks.</p></div>
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

    <section class="h-sec alt">
      <div class="h-wrap">
        <h2 class="h-h2">What you get for each change</h2>
        <p class="h-intro">A list of safety checks at risk. Each one comes with the reason, the exact words it relied on, and the second opinion. This is a real finding from the test.</p>
        <article class="card h-sample" aria-label="Example finding">
          <div class="h-sample-h">
            <div><div class="h-sample-id">${esc(EXAMPLE.control)} · key control · change ${esc(EXAMPLE.case)}</div><h3>${esc(ctrl.name)}</h3></div>
            <span class="badge recommended">At risk: recommended for re-test</span>
          </div>
          <div class="h-sample-b">
            <div><h4>Why</h4><p>${esc(d.proposer_reason)}</p></div>
            <div><h4>Evidence, quoted</h4>
              <div class="doc"><span class="src">From the change request</span>${highlight(ex.ticket.text, d.ticket_quote)}</div>
              <div class="doc" style="margin-top:8px"><span class="src">From the check's procedure</span>${highlight(doc, d.control_quote)}</div></div>
            <div><h4>Second opinion</h4><p>Agreed. ${esc(d.checker_reason || "")}</p></div>
            <div><h4>Suggested next step</h4><p>The control owner assesses the impact and decides whether to re-test before release.</p></div>
          </div>
          <div class="h-sample-f"><a class="btn" href="#" data-demo-control>Open this finding in the demo <span aria-hidden="true">→</span></a></div>
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
          <b>The trade-off:</b> reviewers receive about ${Math.round(P.per_change.total)} items per change instead of about ${Math.round(P.per_change.check)}. Of the ${added} extra, about ${Math.round(P.per_change.real)} are real impacts today's check missed and about ${Math.round(P.per_change.unaffected)} turn out not to be affected.
          <span class="h-trade-r">${P.key_silent} affected key check, out of ${P.key_affected}, was missed entirely.</span>
        </div>
      </div>
    </section>

    <section class="h-sec alt">
      <div class="h-wrap">
        <h2 class="h-h2">Where it fits in a bank</h2>
        <p class="h-intro">It sits between raising a change and approving it, inside the bank's own data platform.</p>
        <div class="arch">
          <div class="arch-col">
            <div class="fl-label">The bank's systems</div>
            <div class="arch-box">Change management<span>change requests</span></div>
            <div class="arch-box">Data lineage catalogue<span>the connection map</span></div>
            <div class="arch-box">Control library<span>check procedures and owners</span></div>
          </div>
          ${arrow}
          <div class="arch-col arch-core">
            <div class="fl-label">Runs in the bank's Databricks workspace</div>
            <div class="arch-core-b">
              <div class="arch-name">Control Impact Detective</div>
              <div class="arch-part"><b>Jobs</b><span>run one investigation per change</span></div>
              <div class="arch-part"><b>Model Serving</b><span>the language model that reads and reasons</span></div>
              <div class="arch-part"><b>Unity Catalog</b><span>inputs, results and the full audit trail</span></div>
              <div class="arch-part"><b>App</b><span>this experience, for reviewers and leaders</span></div>
            </div>
          </div>
          ${arrow}
          <div class="arch-col">
            <div class="fl-label">Where results go</div>
            <div class="arch-box">Control owners<span>findings to assess, with evidence</span></div>
            <div class="arch-box">Change board<span>a summary for the release decision</span></div>
            <div class="arch-box">Risk and audit<span>a recorded trail of every step</span></div>
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

    <section class="h-sec alt">
      <div class="h-wrap h-faq">
        <h2 class="h-h2">Common questions</h2>
        <details><summary>Does it replace the people who review changes?</summary><p>No. It prepares the list and the evidence. Control owners and the change board still decide, and anything uncertain is sent to them rather than settled by the system.</p></details>
        <details><summary>Do we need a perfect connection map first?</summary><p>No. It is designed for the map you already have. It starts from today's map-based check and then looks for what the map is missing.</p></details>
        <details><summary>How do we know a finding is right?</summary><p>Each finding quotes the change request and the check's procedure, gives its reasoning, and passes an independent second opinion. In the test, ${P.new_right} of ${P.new_total} new recommendations were right. Short or generic quotes are flagged as weak evidence.</p></details>
        <details><summary>Can it miss something?</summary><p>Yes. In the test it missed ${P.key_silent} affected key check out of ${P.key_affected} without flagging it. That is why a pilot would also have owners examine a sample of the checks it judged not affected.</p></details>
        <details><summary>What does it cost to run?</summary><p>Running cost and reviewer time were not measured in the proof of concept. In the test it made about ${perCall} model calls per change; a pilot would measure cost and time directly.</p></details>
      </div>
    </section>

    <section class="h-final">
      <div class="h-wrap">
        <h2>See it on a real test case</h2>
        <p>Five short steps: the change, the gap in the map, the investigation, the results, and the decision.</p>
        <div class="h-cta center">
          <a class="btn primary lg" href="#" data-demo>Start the walkthrough <span aria-hidden="true">→</span></a>
          <a class="btn lg light" href="summary.pdf" download>One-page summary (PDF)</a>
          <a class="btn lg light" href="#" data-room>Evidence and method</a>
        </div>
      </div>
    </section>
  </div>`);
  main.append(page);

  page.querySelectorAll("[data-demo]").forEach((a) =>
    a.addEventListener("click", (e) => {
      e.preventDefault();
      go("change", { caseId: EXAMPLE.case });
    })
  );
  page.querySelector("[data-demo-control]").addEventListener("click", (e) => {
    e.preventDefault();
    go("investigate", { caseId: EXAMPLE.case, control: EXAMPLE.control });
  });
  page.querySelector("[data-room]").addEventListener("click", (e) => {
    e.preventDefault();
    go("room", { caseId: EXAMPLE.case });
  });
  page.querySelector('a[href="#how"]').addEventListener("click", (e) => {
    e.preventDefault();
    page.querySelector("#how").scrollIntoView({ behavior: "smooth" });
  });
}
