// The product landing page: what the detective is, in plain words, for someone
// who has never heard of lineage or controls. It sets up one change and stops
// before any result, so the walkthrough keeps its reveal; results live on the
// product overview. Every figure comes from the same
// recorded run as the rest of the experience; nothing here is a projection.

import { esc, pct, el, highlight, expandCodes } from "./util.js";
import { getCase, openInspector } from "./main.js";

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
    ? `The existing lineage check flags ${found} control${found > 1 ? "s" : ""} for review.`
    : "The existing lineage check flags no controls for review.";
  const page = el(`<div class="home">
    <section class="h-hero">
      <div class="h-wrap h-hero-grid">
        <div>
          <p class="h-eyebrow">For banks changing payment systems</p>
          <h1>See which safety checks a system change could quietly break, before it goes live.</h1>
          <p class="h-sub">Control Impact Detective reads a change and the bank's own documents, finds the safety checks at risk, and shows its evidence for each, so the right people can act before release.</p>
          <div class="h-cta">
            <a class="btn primary lg" href="#problem">Understand the problem <span aria-hidden="true">↓</span></a>
          </div>
          <p class="h-more">Banks protect payments with safety checks, called <b>controls</b>: is the customer on a sanctions list, is the amount right, was the payment recorded. When a system changes, some of those checks can stop working.</p>
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
          <p class="h-case-q">What might the existing lineage check have missed? Read on, then find out for yourself in the Walkthrough.</p>
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
        <p class="h-intro">It does not need a perfect map. It does what a careful reviewer would do with unlimited time: start from the existing lineage check, then read the documents to find what the map leaves out.</p>
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
              <li><b>Runs the existing lineage check</b><span>Follows the map, exactly as the bank does now</span></li>
              <li><b>Investigates the gaps</b><span>Reads the change and the procedures, and traces likely missing connections</span></li>
              <li><b>Quotes its evidence</b><span>Every finding must quote the change and the procedure exactly</span></li>
              <li><b>Gets an independent verifier's view</b><span>An independent check agrees or disagrees; disagreements go to a person</span></li>
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
            <li>Finds most of what an incomplete map hides, on changes it had never seen. The walkthrough shows how much.</li>
            <li>Shows its evidence for every finding, and routes doubt to people.</li>
            <li>Runs end to end on Databricks.</li>
          </ul>
          <ul class="h-proof no">
            <li>Not yet tested on a real bank's changes and documents.</li>
            <li>Reviewer time and cost per change not yet measured.</li>
            <li>Not yet repeatable enough: the same change can get different decisions on different runs.</li>
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
  const ex = await getCase(EXAMPLE.case);
  const d = ex.decision(EXAMPLE.control);
  const ctrl = app.graph.nodes.find((n) => n.id === EXAMPLE.control);
  const doc = ex.document_overrides?.[EXAMPLE.control] || app.graph.documents[EXAMPLE.control]?.text || "";
  const uncertain = P.added_items - P.new_total;
  const share = (n) => pct(n / P.added_items, 1);
  const stages = [
    ["Change submitted", "Ticket and affected systems recorded", "Reads the change context"],
    ["Impact assessment", "Follow documented lineage", "Keeps the lineage result and investigates possible gaps"],
    ["Control assessment", "Owners examine the controls identified", "Adds evidence-backed recommendations, and says when it is unsure"],
    ["Release review", "Change board reviews the assessments", "Makes the investigation record available to the decision"],
    ["Audit", "Review documentation and decisions", "Keeps the full investigation trace and its provenance"],
  ];
  const page = el(`<div class="home">
    <section class="h-hero h-hero-s">
      <div class="h-wrap">
        <p class="h-eyebrow">Control Impact Detective · Product overview</p>
        <h1>Find payment controls that incomplete lineage leaves behind.</h1>
        <p class="h-sub">A Databricks-based AI investigation that combines the existing dependency check with document evidence to surface controls a payment-system change may affect, before it is released.</p>
        <div class="ov-facts">
          <div><span>Core capability</span><b>Evidence-backed impact discovery</b></div>
          <div><span>Maturity</span><b>POC demonstrated; not production-validated</b></div>
          <div><span>Basis</span><b>Synthetic held-out evaluation: a recorded Databricks run on ${P.changes} changes</b></div>
        </div>
        <p class="ov-diff"><b>What makes this different.</b> An existing lineage check can only follow dependencies someone recorded. This keeps that check and adds a tool-using AI investigation that reads the change request and the control procedures to find relationships the recorded map cannot show. Evidence checks and an independent second review guard each recommendation; they do not remove the risk of a missed control.</p>
      </div>
    </section>

    <section class="h-sec alt">
      <div class="h-wrap">
        <h2 class="h-h2">What it delivers for each change</h2>
        <p class="h-intro">A list of controls at risk, each with its evidence and an independent verifier's view. A recorded example:</p>
        <article class="card ov-ex" aria-label="Example output">
          <div class="ov-ex-h"><div><div class="h-sample-id">Example output · change ${esc(EXAMPLE.case)} · control ${esc(EXAMPLE.control)}</div><h3>${esc(ctrl.name)}</h3></div></div>
          <div class="ov-status">
            <div><span>Existing lineage check</span><b class="no">Not surfaced</b></div>
            <div><span>AI investigation</span><b class="yes">Potential impact identified · recommended</b></div>
            <div><span>Proposed action</span><b>Control owner assesses before release</b></div>
          </div>
          <div class="ov-ex-b">
            <div><h4>Supporting evidence</h4>
              <div class="doc"><span class="src">Change request</span>${highlight(ex.ticket.text, d.ticket_quote)}</div>
              <div class="doc" style="margin-top:8px"><span class="src">Control procedure</span>${highlight(doc, d.control_quote)}</div>
              <p class="ov-why">${expandCodes(d.proposer_reason, EXAMPLE.control)}</p></div>
            <div><h4>Independent verification</h4><p><b>${esc((d.checker || "").toLowerCase())}</b>: ${expandCodes(d.checker_reason || "", EXAMPLE.control)}</p></div>
          </div>
          <div class="h-sample-f"><button class="btn" type="button" id="ov-open">Open the full evidence and trace</button></div>
        </article>
      </div>
    </section>

    <section class="h-sec">
      <div class="h-wrap">
        <h2 class="h-h2">What the held-out evaluation shows</h2>
        <p class="h-intro">Recorded run of version A on ${P.changes} synthetic changes the detective had never seen.</p>
        <div class="ov-m">
          <div><div class="ov-v">${pct(P.recovery, 1)}</div><h3>Key-control recovery</h3><p>${P.agent_found_key} of ${P.key_misses} key-control impacts the existing lineage check missed were recommended.</p></div>
          <div><div class="ov-v">${pct(P.precision, 1)}</div><h3>Recommendation precision</h3><p>${P.new_right} of ${P.new_total} new recommendations were affected in the synthetic answer key.</p></div>
          <div><div class="ov-v">${P.added_affected}</div><h3>Additional affected controls surfaced</h3><p>Recommended or sent to a person; not all were confirmed recommendations.</p></div>
          <div><div class="ov-v">${P.added_unaffected}</div><h3>Additional unaffected items</h3><p>Among the ${P.added_items} added items, by the synthetic answer key.</p></div>
        </div>
        <p class="ov-note">These measure different populations and must not be added together. No reviewer time or cost was measured.</p>
        <div class="ov-comp"><h3>What the additional review contains</h3>
          <div class="sbar"><span class="agent" style="flex:${P.added_affected}">${P.added_affected} affected · ${share(P.added_affected)}</span><span class="idle" style="flex:${P.added_unaffected}">${P.added_unaffected} · ${share(P.added_unaffected)}</span></div>
          <p>The ${P.added_items} added items are ${P.new_total} new recommendations and ${uncertain} findings sent to a person. This classifies review items; it does not measure reviewer time or avoidable cost.</p></div>
      </div>
    </section>

    <section class="h-sec alt">
      <div class="h-wrap">
        <h2 class="h-h2">Where it fits in the change process</h2>
        <p class="h-intro">A proposed operating model; it is not deployed in a bank.</p>
        <table class="t ov-t"><thead><tr><th>Stage</th><th>Today</th><th>What the detective adds</th></tr></thead><tbody>
          ${stages.map(([a, b, c2]) => `<tr><td><b>${esc(a)}</b></td><td>${esc(b)}</td><td>${esc(c2)}</td></tr>`).join("")}
        </tbody></table>
      </div>
    </section>

    <section class="h-final">
      <div class="h-wrap">
        <h2>What happens next?</h2>
        <p>The proof of concept shows that an evidence-backed AI investigation can recover controls that incomplete lineage hides, in a synthetic bank. The next step is for control owners to validate its findings, what it left out and how useful it is, before any supervised pilot.</p>
        <div class="h-cta center"><a class="btn lg light" href="summary.pdf" download>Download the one-page summary (PDF)</a></div>
      </div>
    </section>
  </div>`);
  main.append(page);
  page.querySelector("#ov-open").addEventListener("click", () => openInspector(EXAMPLE.control, EXAMPLE.case));
}
