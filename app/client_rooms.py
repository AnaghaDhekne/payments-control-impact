"""Companion screens to the immersive client investigation: evaluation and release decision."""
import streamlit.components.v1 as components

def show(mode="evaluation"):
    page = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root{--bg:#0b1019;--panel:#111b29;--line:#304052;--white:#eaf3f9;--dim:#a1b3c3;--green:#d5f17c;--warn:#ffb17c}*{box-sizing:border-box}
body{background:var(--bg);color:var(--white);margin:0;font:14px 'DM Sans',sans-serif}
main{min-height:730px;padding:26px clamp(20px,4vw,64px);background:radial-gradient(ellipse at 75% 20%,#193044,transparent 50%),var(--bg)}
header{display:flex;justify-content:space-between;border-bottom:1px solid var(--line);padding-bottom:20px;font-size:11px;letter-spacing:.16em;font-weight:700}.mark{color:var(--green)}.eyebrow{color:var(--green);font-size:11px;letter-spacing:.2em;margin-top:49px;text-transform:uppercase}
h1{font:700 clamp(35px,5vw,66px)/1.1 Manrope,sans-serif;letter-spacing:-.065em;max-width:970px;margin:16px 0}h1 em{color:var(--green);font-style:normal}
.lead{font-size:15px;color:var(--dim);max-width:760px;line-height:1.75;margin-bottom:34px}
.layout{display:grid;grid-template-columns:1.4fr .8fr;border:1px solid var(--line);min-height:365px}
.primary{padding:28px;border-right:1px solid var(--line)}aside{padding:28px;display:flex;flex-direction:column}
.k{color:#92a9ba;font-size:10px;letter-spacing:.18em;text-transform:uppercase}h2{font:700 23px Manrope,sans-serif;letter-spacing:-.04em;line-height:1.2;margin:17px 0}p{color:#b4c5d1;line-height:1.65}
.bar{height:32px;display:flex;overflow:hidden;background:#253344;margin:25px 0 8px}.bar .rules{background:#718fa6}.bar .agent{background:var(--green)}.bar .miss{background:#394c5f}
.legend{display:flex;gap:20px;flex-wrap:wrap;font-size:11px;color:var(--dim)}.legend b{color:#fff}
.stat{font:700 64px Manrope,sans-serif;letter-spacing:-.08em;margin:20px 0}.stat small{font:400 15px 'DM Sans',sans-serif;color:var(--dim);letter-spacing:0}
.rule{border-top:1px solid var(--line);padding:17px 0}.rule strong{color:#fff}.warning{color:var(--warn)}
button{border:1px solid #5d7180;background:transparent;color:#f0f5f8;border-radius:3px;padding:12px 17px;font:700 12px 'DM Sans',sans-serif;cursor:pointer;margin:8px 8px 8px 0}button:hover,button[aria-pressed=true]{background:var(--green);border-color:var(--green);color:#16231b}button:focus-visible{outline:2px solid var(--green);outline-offset:3px}
footer{margin-top:25px;padding-top:17px;border-top:1px solid var(--line);font-size:11px;color:var(--dim);line-height:1.6}
@media(max-width:780px){.layout{grid-template-columns:1fr}.primary{border-right:0;border-bottom:1px solid var(--line)}main{padding:20px}.stat{font-size:46px}}
</style></head><body><main><header><span>◇ &nbsp; CONTROL / EXPOSURE</span><span class="mark" id="header">RECORDED SYNTHETIC STUDY</span></header><div class="eyebrow" id="eyebrow"></div><h1 id="title"></h1><p class="lead" id="lead"></p><section class="layout"><div class="primary" id="primary"></div><aside id="aside"></aside></section><footer id="foot">Evidence: 18 held-out synthetic changes, 30% change-correlated lineage degradation. These results are not from a live bank deployment. A recommendation is not a completed control review.</footer></main>
<script>
const $=x=>document.getElementById(x),mode="__MODE__";
if(mode==='evaluation'){
$('eyebrow').textContent='Evidence / What changed';
$('title').innerHTML='The baseline saw 18.<br><em>The investigation surfaced 113 more.</em>';
$('lead').textContent='Explore the gap between a clean-looking impact report and the controls actually affected. Every figure below comes from the recorded held-out evaluation.';
$('primary').innerHTML='<div class="k">KEY-CONTROL COVERAGE / 162 AFFECTED INSTANCES</div><div class="stat">131 <small>identified with AI assistance</small></div><div class="bar"><div class="rules" style="width:11.111%"></div><div class="agent" style="width:69.753%"></div><div class="miss" style="width:19.136%"></div></div><div class="legend"><span><b>18</b> baseline found</span><span><b>113</b> recovered</span><span><b>31</b> not recovered as recommendations</span></div><div class="rule" style="margin-top:24px">The agent recovered <strong>113 of 144</strong> key-control impacts missed by the baseline. Of the remaining 31, <strong>30 were routed for human review</strong> and <strong>one was silently missed</strong>.</div>';
$('aside').innerHTML='<div class="k">INTERROGATE THE TRADE-OFF</div><h2 id="sideTitle">More coverage requires more review.</h2><p id="sideText">406 additional review items: 331 genuine affected controls and 75 unaffected items. The 331 are necessary findings, not wasted work.</p><div style="margin-top:auto"><button id="work" aria-pressed="true">Review burden</button><button id="risk" aria-pressed="false">Residual risk</button><button id="repeat" aria-pressed="false">Consistency</button></div>';
const states={work:['More coverage requires more review.','406 additional review items: 331 genuine affected controls and 75 unaffected items. The 331 are necessary findings, not wasted work.'],risk:['One silent miss remains.','The recorded agent failed to surface or route one affected key-control instance. The case must be investigated before a practitioner pilot.'],repeat:['Repeatability missed its target.','Original agent agreement was approximately 80% versus a 95% target. A three-run voting approach improved it to 94.4%, at roughly four times the model cost.']};
for(const k of Object.keys(states)){$(k).onclick=()=>{$('sideTitle').textContent=states[k][0];$('sideText').textContent=states[k][1];for(const j of Object.keys(states))$(j).setAttribute('aria-pressed',String(j===k))}}
}else{
$('eyebrow').textContent='Decision room / Release assurance';
$('title').innerHTML='A better signal.<br><em>Not yet a release approval.</em>';
$('lead').textContent='The question is not whether the AI found more. It is whether the control owners can trust the evidence, absorb the review work, and catch what the system still misses.';
$('primary').innerHTML='<div class="k">RECOMMENDATION / CONTROLLED PRACTITIONER EVALUATION</div><h2>Do not move directly to production.</h2><div class="rule"><strong>01 / Validate</strong><p>Ask payments and sanctions control owners to review recommended impacts and sample excluded controls.</p></div><div class="rule"><strong>02 / Investigate</strong><p>Explain the silent miss and verify the proposed review process does not silently discard other affected controls.</p></div><div class="rule"><strong>03 / Measure</strong><p>Time actual reviewer work, capture model cost and test consistency before making any ROI claim.</p></div>';
$('aside').innerHTML='<div class="k">RELEASE ASSURANCE / GATES</div><h2>What can we say today?</h2><div class="rule"><strong style="color:var(--green)">Demonstrated</strong><p>113 key-control misses recovered in synthetic held-out evaluation.</p></div><div class="rule"><strong class="warning">Not demonstrated</strong><p>Zero silent misses, 95% repeatability, real-world review savings or production readiness.</p></div><div style="margin-top:auto;color:var(--green);font-size:12px">NEXT STEP → Practitioner validation</div>';
}
</script></body></html>"""
    components.html(page.replace("__MODE__", mode), height=790, scrolling=True)
