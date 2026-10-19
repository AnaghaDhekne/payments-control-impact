"""Purpose-built client investigation experience; the legacy Streamlit pages remain available as an appendix."""
from __future__ import annotations

import html
import json
import streamlit as st
import streamlit.components.v1 as components

def show(case=None):
    findings = (case or {}).get("verified_findings", [])
    control = next((f for f in findings if f.get("control_id") == "C02"), None)
    evidence = {
        "ticket": (control or {}).get("ticket_quote", "Recorded ticket quote unavailable in this deployment."),
        "procedure": (control or {}).get("control_quote", "Recorded procedure quote unavailable in this deployment."),
        "reason": (control or {}).get("proposer_causal_reason") or (control or {}).get("causal_reason", "See the technical evidence for the recorded causal reasoning."),
        "recorded": bool(control),
    }
    payload = json.dumps(evidence, ensure_ascii=True).replace("<", "\\u003c")
    page = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root{--bg:#0b1019;--panel:#111b29;--stroke:#29384b;--ink:#edf4f9;--muted:#99a9b9;--lime:#d5f17c;--orange:#ffb17c;--red:#ff7e82}
*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--ink);font-family:'DM Sans',sans-serif}button{font:inherit}button:focus-visible{outline:2px solid var(--lime);outline-offset:4px}
.shell{min-height:770px;padding:25px clamp(20px,3.5vw,58px) 34px;background:radial-gradient(ellipse at 72% 30%,#182c3b 0%,transparent 45%),#0b1019}
.top{display:flex;justify-content:space-between;align-items:center;gap:12px;border-bottom:1px solid #273344;padding-bottom:20px}.brand{display:flex;align-items:center;gap:12px;font-weight:700;letter-spacing:.12em;font-size:11px}.mark{display:grid;place-items:center;width:30px;height:30px;border:1px solid var(--lime);color:var(--lime);font-size:18px}.meta{font-size:10px;letter-spacing:.14em;color:var(--muted);text-transform:uppercase}
.eyebrow{margin:42px 0 13px;font-size:11px;letter-spacing:.22em;color:var(--lime);font-weight:700;text-transform:uppercase}
h1{font-family:Manrope,sans-serif;font-size:clamp(35px,5.1vw,70px);line-height:1.06;letter-spacing:-.065em;max-width:930px;margin:0;font-weight:700}
h1 em{font-style:normal;color:var(--lime)}.sub{max-width:680px;color:#adbdca;font-size:15px;line-height:1.7;margin:22px 0 29px}
.workspace{display:grid;grid-template-columns:minmax(0,1.75fr) minmax(285px,.8fr);border:1px solid var(--stroke);background:rgba(14,22,33,.93);min-height:390px}
.graph{padding:25px;min-width:0;border-right:1px solid var(--stroke)}.graphhead{display:flex;justify-content:space-between;gap:12px;align-items:center}.tiny{font-size:10px;letter-spacing:.16em;color:#91a6b9;text-transform:uppercase}.status{font-size:11px;color:var(--orange)}.map{width:100%;height:305px;overflow:visible}.edge{stroke:#547184;stroke-width:2;fill:none}.broken{stroke:var(--red);stroke-dasharray:5 7}.recovered{stroke:var(--lime);stroke-width:3;stroke-dasharray:7 5}.node rect{fill:#172739;stroke:#3a5164;stroke-width:1.5;rx:8}.node text{font-size:12px;fill:#e3eef7;font-weight:600}.node .k{font-size:9px;fill:#9aafc0;letter-spacing:1px}.node.change rect{stroke:#ffb17c}.node.target rect{stroke:var(--red)}.node.target.found rect{stroke:var(--lime);fill:#24372b}.node{cursor:pointer}.node:hover rect{stroke-width:3}
.panel{padding:25px;display:flex;flex-direction:column}.panel h2{font-family:Manrope,sans-serif;font-size:24px;letter-spacing:-.045em;line-height:1.2;margin:17px 0}.panel p{font-size:13px;line-height:1.65;color:#b5c5d0}.panel .result{margin-top:auto;border-top:1px solid var(--stroke);padding-top:20px}.big{font-size:46px;font-weight:700;letter-spacing:-.065em}.big small{font-size:13px;color:#a9bdc8;letter-spacing:0}.actions{display:flex;gap:9px;flex-wrap:wrap;margin-top:20px}.action{padding:13px 16px;border:1px solid #526475;background:transparent;color:#dfe9f2;cursor:pointer;border-radius:3px;font-size:12px;font-weight:700}.action.primary{background:var(--lime);color:#152019;border-color:var(--lime)}.action:hover{filter:brightness(1.12)}
.bottom{display:flex;justify-content:space-between;gap:20px;align-items:center;border-top:1px solid var(--stroke);padding-top:18px;margin-top:22px}.bottom p{font-size:11px;color:#93a6b6;max-width:780px;line-height:1.6;margin:0}.index{font-size:11px;color:var(--lime);letter-spacing:.13em}
.quote{border-left:2px solid var(--lime);padding:10px 0 10px 14px;margin:15px 0;font-size:13px;line-height:1.6;color:#e6f1f8;overflow-wrap:anywhere}.tag{display:inline-block;border:1px solid #526c58;color:var(--lime);padding:6px 9px;font-size:10px;letter-spacing:.1em;text-transform:uppercase}
@media(max-width:790px){.workspace{grid-template-columns:1fr}.graph{border-right:0;border-bottom:1px solid var(--stroke)}.map{height:260px}.panel{min-height:260px}.top .meta{display:none}.shell{padding:20px 18px}h1{font-size:38px}}
@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style></head><body><main class="shell"><header class="top"><div class="brand"><span class="mark">◇</span> CONTROL / EXPOSURE</div><div class="meta">FIELD NOTE 01 &nbsp; / &nbsp; RECORDED SYNTHETIC CASE</div></header>
<div class="eyebrow">Release assurance / Interactive case CHG-027</div><h1>Would you approve this release?<br><em>The check says yes.</em></h1><p class="sub">The impact check reports zero affected controls. You are reviewing a payment screening interface change. Challenge the result before signing off.</p>
<section class="workspace" aria-label="Interactive investigation"><div class="graph"><div class="graphhead"><span class="tiny">PAYMENT CONTROL DEPENDENCY / CHG-027</span><span class="status" id="status">● INCOMPLETE LINEAGE</span></div>
<svg class="map" viewBox="0 0 720 310" role="img" aria-label="Interactive dependency map: payment interface to screening engine to sanctions control."><defs><marker id="arr" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0 0 L7 3.5 L0 7" fill="#547184"/></marker></defs>
<path class="edge" d="M210 152 H292" marker-end="url(#arr)"/><path class="edge" id="lastEdge" d="M502 152 H558" marker-end="url(#arr)"/>
<path class="broken" id="gapEdge" d="M502 152 H520 M542 152 H558" style="display:block"/><text id="gapX" x="531" y="143" text-anchor="middle" fill="#ff7e82" font-size="19">×</text>
<path class="recovered" id="recoverEdge" d="M502 137 Q530 92 558 137" style="display:none"/>
<g class="node change" tabindex="0" role="button" aria-label="Inspect changed payment interface" data-node="change"><rect x="15" y="111" width="195" height="82"/><text class="k" x="30" y="135">CHANGE REQUEST</text><text x="30" y="158">Screening interface</text><text x="30" y="175">CHG-027</text></g>
<g class="node" tabindex="0" role="button" aria-label="Inspect screening engine" data-node="engine"><rect x="292" y="111" width="210" height="82"/><text class="k" x="307" y="135">PAYMENT SYSTEM</text><text x="307" y="158">Sanctions screening</text><text x="307" y="175">engine</text></g>
<g class="node target" id="target" tabindex="0" role="button" aria-label="Inspect sanctions control" data-node="control"><rect x="558" y="111" width="152" height="82"/><text class="k" x="572" y="135">KEY CONTROL</text><text x="572" y="158">C02 · Sanctions</text><text x="572" y="175">before release</text></g>
<text x="15" y="267" fill="#8299ab" font-size="11">Select a node to inspect it. The missing link is not automatically repaired.</text>
</svg><div class="actions"><button class="action" id="reference">Show hidden reference</button><button class="action" id="reset">Reset investigation</button><button class="action primary" id="investigate">Challenge the result ↗</button></div></div>
<aside class="panel" aria-live="polite"><div class="tiny" id="panelK">01 / BLIND SPOT</div><h2 id="panelH">No impacts reported. Would you sign off?</h2><div id="panelBody"><p>The metadata link to the sanctions control is absent. Rules-only analysis reports <strong style="color:#fff">0 of 20</strong> affected controls for this change.</p><p>What if the procedure tells a different story?</p></div><div class="result" id="result"><div class="tiny">RULES-ONLY FINDING</div><div class="big">0 <small>/ 20 affected controls</small></div></div></aside></section>
<div class="bottom"><p><strong style="color:#e7f2f7">A recorded investigation, not a live AI call.</strong> CHG-027 is a synthetic held-out case. Agent recommendations require human validation. Across the full 18-change evaluation, 113 of 144 baseline key-control misses were recovered; one affected key control was still silently missed.</p><span class="index">EXPLORE → UNDERSTAND → DECIDE</span></div></main>
<script>const E=__PAYLOAD__;
const $=id=>document.getElementById(id);let state='broken';
function panel(k,h,body,footer){$('panelK').textContent=k;$('panelH').textContent=h;$('panelBody').innerHTML=body;$('result').innerHTML=footer}
const msg=s=>'<p>'+s+'</p>';const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function render(next){state=next;$('lastEdge').style.display=next==='reference'?'block':'none';$('gapEdge').style.display=next==='broken'?'block':'none';$('gapX').style.display=next==='broken'?'block':'none';$('recoverEdge').style.display=next==='investigated'?'block':'none';$('target').classList.toggle('found',next==='investigated');$('status').textContent=next==='reference'?'● COMPLETE REFERENCE':next==='broken'?'● INCOMPLETE LINEAGE':'● EVIDENCE-BASED RECOMMENDATION';$('status').style.color=next==='investigated'?'#d5f17c':'#ffb17c';
if(next==='reference')panel('00 / EVALUATION ANSWER KEY','The dependency exists.',msg('The intact synthetic reference map links the change to the control. This complete view is <strong>not</strong> what the rules-only check received.'),'<div class="tiny">REFERENCE MAP</div><div class="big">20 <small>/ 20 affected controls in answer key</small></div>');
if(next==='broken')panel('01 / BLIND SPOT','No impacts reported. Would you sign off?',msg('The engine-to-control relationship is missing from the metadata supplied to the baseline.')+msg('The rules-only check reports <strong>0 of 20</strong> affected controls for CHG-027.'),'<div class="tiny">RULES-ONLY FINDING</div><div class="big">0 <small>/ 20 affected controls</small></div>');
if(next==='investigated')panel('02 / RECORDED INVESTIGATION','The release needs control review.',msg('The recorded agent used change and control documentation to recommend all <strong>20 of 20</strong> affected controls. This is a finding for review, not a repair to the metadata.')+'<span class="tag">Select the control node for its evidence</span>','<div class="tiny">AGENT-ASSISTED FINDING</div><div class="big">20 <small>/ 20 correctly recommended</small></div>')}
$('reference').onclick=()=>render('reference');$('reset').onclick=()=>render('broken');$('investigate').onclick=()=>render('investigated');
function inspect(which){if(which==='change')panel('CASE / CHG-027','The change request',msg('The payment screening request interface changes. The impact must be traced into downstream screening controls.'),'<div class="tiny">SOURCE</div><p>Recorded synthetic change ticket</p>');if(which==='engine')panel('DEPENDENCY / ENGINE','A critical intermediary',msg('The screening engine is reachable from the changed interface. Missing engine-to-control metadata prevents the baseline from continuing.'),'<div class="tiny">EXPOSURE</div><p>Broken downstream relationship</p>');if(which==='control'){const quotes=E.recorded?'<div class="tiny">TICKET EXCERPT</div><div class="quote">'+escape(E.ticket)+'</div><div class="tiny">CONTROL PROCEDURE EXCERPT</div><div class="quote">'+escape(E.procedure)+'</div>':msg('Recorded excerpts are unavailable in this deployment. Open the technical case evidence.');panel('EVIDENCE / CONTROL C02','Sanctions screening before release',quotes+msg('<strong>Agent reasoning:</strong> '+escape(E.reason)), '<div class="tiny">STATUS</div><p>'+(state==='investigated'?'Recommended by recorded agent · human review not performed':'Known affected in synthetic reference · not found by current baseline')+'</p>')}}
document.querySelectorAll('[data-node]').forEach(n=>{n.addEventListener('click',()=>inspect(n.dataset.node));n.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();inspect(n.dataset.node)}})});
render('broken');
</script></body></html>"""
    page = page.replace("__PAYLOAD__", payload)
    components.html(page, height=825, scrolling=True)
