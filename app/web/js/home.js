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
        <p class="h-eyebrow">Why this problem matters beyond the test bank</p>
        <h2 class="h-h2">Payment changes depend on connections that are difficult to keep mapped.</h2>
        <p class="h-intro h-intro-d">Banks follow a map of which systems feed which checks. Dependency maps can have gaps: when a change lands in one, a check can quietly stop working while the map still looks fine.</p>
        <div class="h-facts">
          <div class="h-fact"><b>2 of 31</b><p>of the world's largest banks fully meet the Basel risk-data principles, which include knowing where data comes from and goes.</p><a class="h-src" href="https://www.regulationtomorrow.com/2023/11/basel-committee-report-on-implementing-principles-for-effective-risk-data-aggregation-and-reporting-shows-progress-made-but-significant-work-remains/" target="_blank" rel="noopener noreferrer">Basel Committee progress report, Nov 2023 ↗</a></div>
          <div class="h-fact"><b>£48.65m</b><p>fined to TSB by UK regulators after a 2018 IT migration disrupted services for months; the FCA found the change's planning and governance were not robust enough.</p><a class="h-src" href="https://www.fca.org.uk/news/press-releases/tsb-fined-ps4865m-operational-resilience-failings" target="_blank" rel="noopener noreferrer">FCA, Dec 2022 ↗</a></div>
          <div class="h-fact"><b>$135.6m</b><p>fined to Citigroup by the OCC and the Federal Reserve for slow progress on data quality management and the controls around it.</p><a class="h-src" href="https://www.fintechfutures.com/regulations-compliance/us-regulators-fine-citigroup-136m-for-insufficient-progress-towards-compliance-with-2020-consent-order" target="_blank" rel="noopener noreferrer">FinTech Futures, Jul 2024 ↗</a></div>
          <div class="h-fact"><b>Top challenge</b><p>The Basel Committee names mapping the interconnections and interdependencies of critical operations among the most common challenges in adopting its operational-resilience principles.</p><a class="h-src" href="https://www.thestack.technology/banks-need-to-do-better-on-operational-resilience-basel/" target="_blank" rel="noopener noreferrer">Basel Committee newsletter, via The Stack ↗</a></div>
          <div class="h-fact"><b>End to end</b><p>The ECB's 2024 risk-data guide calls for end-to-end lineage for key risk figures; lineage only at system level falls short.</p><a class="h-src" href="https://www.mckinsey.com/capabilities/risk-and-resilience/our-insights/bcbs-239-2-0-resurgence-strengthening-risk-management-and-decision-making" target="_blank" rel="noopener noreferrer">ECB guide, May 2024, via McKinsey ↗</a></div>
          <div class="h-fact"><b>Change is constant</b><p>Swift extended the ISO 20022 structured-address deadline in August 2026: readiness was still uneven across all regions. Address fields are exactly the kind of change tested here.</p><a class="h-src" href="https://www.swift.com/insights/news/swift-accepts-community-request-extend-structured-address-migration-iso-20022-payment-messages" target="_blank" rel="noopener noreferrer">Swift, Aug 2026 ↗</a></div>
        </div>
        <p class="h-q"><b>The question this POC tests:</b> when a recorded dependency is missing, can an evidence-backed AI investigation still surface the affected payment controls for their owners? These sources show the need; they do not validate the POC.</p>
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
        <h2 class="h-h2">Where it fits</h2>
        <p class="h-intro">Between a payment change request and the human release decision: the detective adds evidence-backed findings to the existing lineage check. It does not approve a release.</p>
        <p class="h-fine center">The demonstration runs on Databricks with synthetic bank inputs. Platform architecture and integration requirements are documented in the Technical Handbook.</p>
      </div>
    </section>

    <section class="h-sec">
      <div class="h-wrap h-two">
        <div>
          <h2 class="h-h2">What it has shown</h2>
          <ul class="h-proof yes">
            <li>Finds most of what an incomplete map hides, on changes it had never seen. The walkthrough shows how much.</li>
            <li>Shows its evidence for every finding, and routes doubt to people.</li>
            <li>Keeps everything the existing check finds, and only adds.</li>
            <li>Runs end to end on Databricks.</li>
          </ul>
          <p class="h-next"><b>Next to prove:</b> the same results on a real bank's changes, judged by control owners, with steadier run-to-run decisions.</p>
        </div>
        <div><h2 class="h-h2">What still needs proof</h2><p>Control owners must assess findings and excluded controls on real change records. A supervised pilot would then measure accuracy, stability, review effort, and operational cost.</p></div>
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
        <p class="ov-note">These measure different populations and must not be added together.</p>
        <div class="ov-comp">
          <p>The ${P.added_items} added items are ${P.new_total} new recommendations and ${uncertain} findings sent to a person. Without the detective, those controls would still need checking, by tracing the lineage gaps by hand or by missing them; a missed control fails silently after release. ${P.added_affected} are real impacts; the ${P.added_unaffected} others come with evidence to clear them.</p></div>
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

    <section class="h-sec alt">
      <div class="h-wrap">
        <h2 class="h-h2">Running cost: model usage per change</h2>
        <div class="ov-cost">
          <div><b>${(P.model_calls / P.changes).toFixed(0)}</b><span>model calls per change, recorded (${P.model_calls.toLocaleString("en-US")} across ${P.changes})</span></div>
          <div><b>≈ 450k</b><span>tokens per change, estimated: about 430k read, 20k–70k written</span></div>
          <div><b>≈ $0.07–$0.11</b><span>per change at Databricks' list rate for GPT-OSS-120B and an example $0.07 per DBU</span></div>
        </div>
        <p class="h-fine">Token counts were not logged in the recorded run; they are estimated by replaying its prompts (about four characters per token). List rate: 2.143 DBU per million tokens read, 8.571 written (<a href="https://www.databricks.com/product/pricing/foundation-model-serving" target="_blank" rel="noopener noreferrer">Databricks pricing ↗</a>); contract prices differ. Cost grows with the size of the control catalogue and with any multi-run vote; a pilot would log actual usage.</p>
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
