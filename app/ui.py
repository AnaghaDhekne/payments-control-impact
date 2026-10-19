"""Visual system for the dashboard: one stylesheet and a few page building blocks.

Every page follows the same pyramid (Minto): a governing message as the title,
a short lead, three supporting key lines, then the detail. Colours have one
meaning each across the app.
"""

from __future__ import annotations

import html

import streamlit as st

# Colour tokens (also used by the charts).
INK = "#1B2430"
MUTED = "#5B6675"
LINE = "#DDE2E8"
SURFACE = "#F4F6F9"
BLUE = "#2F6FAE"  # found by the rules method
GREEN = "#2E9468"  # recovered or recommended by the agent
AMBER = "#C98A1F"  # sent to a person for review
GREY = "#C3CAD3"  # still missed / absent
RED = "#B3261E"  # target not met

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,500;8..60,600&display=swap');
html, body, [class*="st-"], .stMarkdown, .stDataFrame, button, input, select, textarea {{
  font-family: 'IBM Plex Sans', system-ui, sans-serif;
}}
[data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu, footer, [data-testid="stDecoration"] {{ display:none !important; }}
.block-container {{ padding-top: 2.4rem; padding-bottom: 4rem; max-width: 1120px; }}
h1 {{ font-family: 'Source Serif 4', Georgia, serif !important; font-weight: 600 !important;
     font-size: 2.15rem !important; line-height: 1.18 !important; letter-spacing: -0.01em;
     color: {INK}; max-width: 40ch; padding: .1rem 0 .6rem !important; }}
h2, h3 {{ color: {INK}; letter-spacing: -0.005em; font-weight: 600 !important; }}
h3 {{ font-size: 1.15rem !important; margin-top: 1.6rem !important; }}
p, li {{ color: {INK}; }}
.crumb {{ font-size: .85rem; color: {MUTED}; margin-bottom: .1rem; }}
.crumb b {{ color: {INK}; font-weight: 600; }}
.lead {{ font-size: 1.08rem; line-height: 1.6; color: #333D49; max-width: 72ch; margin: 0 0 1.4rem; }}

.keylines {{ display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 1.6rem; margin: .4rem 0 1.8rem; }}
.keyline {{ border-top: 3px solid var(--kc, {INK}); padding-top: .7rem; }}
.keyline h4 {{ font-size: 1rem; font-weight: 600; margin: 0 0 .35rem; color: {INK}; line-height: 1.35; }}
.keyline p {{ font-size: .93rem; line-height: 1.55; color: #3D4752; margin: 0; }}

.kpis {{ display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); margin: .2rem 0 1.6rem;
        border-top: 1px solid {LINE}; border-bottom: 1px solid {LINE}; }}
.kpi {{ padding: 1rem 1.1rem 1rem 0; }}
.kpi + .kpi {{ padding-left: 1.1rem; border-left: 1px solid {LINE}; }}
.kpi .v {{ font-size: 2.1rem; font-weight: 500; line-height: 1.1; color: {INK}; font-variant-numeric: tabular-nums; }}
.kpi .l {{ font-size: .9rem; color: {INK}; margin-top: .3rem; font-weight: 500; }}
.kpi .n {{ font-size: .82rem; color: {MUTED}; margin-top: .15rem; line-height: 1.4; }}

.scq {{ display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 0; margin: .6rem 0 2rem; }}
.scq > div {{ padding: 1rem 1.1rem; border: 1px solid {LINE}; }}
.scq > div + div {{ border-left: none; }}
.scq .s {{ font-size: .8rem; color: {MUTED}; margin-bottom: .35rem; }}
.scq p {{ font-size: .93rem; line-height: 1.5; margin: 0; }}
.scq .answer {{ background: {INK}; border-color: {INK}; }}
.scq .answer p, .scq .answer .s {{ color: #F4F6F9; }}

.callout {{ border-left: 4px solid {BLUE}; background: {SURFACE}; padding: .9rem 1.1rem; margin: .6rem 0 1.4rem; border-radius: 0 4px 4px 0; }}
.callout p {{ margin: 0; line-height: 1.55; }}
.callout.warn {{ border-left-color: {AMBER}; }}

table.score {{ width:100%; border-collapse: collapse; margin: .3rem 0 1rem; font-size: .93rem; border: none !important; }}
table.score tr {{ border: none !important; background: transparent !important; }}
table.score td {{ padding: .7rem .6rem; border: none !important; border-bottom: 1px solid {LINE} !important; vertical-align: top; }}
table.score td:first-child {{ padding-left: 0; font-weight: 500; width: 36%; }}
table.score td:nth-child(2):not(:last-child) {{ width: 11%; white-space: nowrap; }}
table.score td:first-child:nth-last-child(2) {{ width: 26%; }}
table.score td:last-child {{ color: #3D4752; }}
.badge {{ display:inline-block; font-size: .78rem; font-weight: 600; padding: 3px 9px; border-radius: 999px; }}
.badge.ok {{ background:#E2F2EA; color:#1E6B49; }} .badge.bad {{ background:#F8E3E1; color:#9C2219; }}
.badge.warn {{ background:#F7EBD5; color:#7F560F; }} .badge.dim {{ background:#ECEFF3; color:#4B5562; }}

.legend {{ font-size: .85rem; color: {MUTED}; margin: -.2rem 0 1rem; }}
.legend span {{ display:inline-block; width:10px; height:10px; border-radius:2px; margin: 0 .35rem 0 .9rem; vertical-align: -1px; }}
.legend span:first-child {{ margin-left: 0; }}
.next {{ margin-top: 2.2rem; padding-top: 1rem; border-top: 1px solid {LINE}; color: {MUTED}; font-size: .92rem; }}

section[data-testid="stSidebar"] {{ background: {SURFACE}; border-right: 1px solid {LINE}; }}
section[data-testid="stSidebar"] .block-container {{ padding-top: 1.4rem; }}
.brand {{ font-family: 'Source Serif 4', Georgia, serif; font-size: 1.2rem; font-weight: 600; color: {INK}; line-height: 1.25; }}
.brand-sub {{ font-size: .82rem; color: {MUTED}; margin: .2rem 0 1rem; }}
.navhead {{ font-size: .8rem; font-weight: 600; color: {MUTED}; margin: 1.1rem 0 .15rem .2rem; }}
[data-testid="stSidebar"] [data-testid="stPageLink"] a {{ padding: .2rem .5rem; }}
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{ gap: .1rem; }}
section[data-testid="stSidebar"] [data-testid="stElementContainer"] {{ margin: 0; }}
[data-testid="stSidebar"] [data-testid="stPageLink"] p {{ font-size: .93rem; }}
.sidefoot {{ font-size: .8rem; color: {MUTED}; line-height: 1.5; margin-top: 1.4rem; padding-top: .9rem; border-top: 1px solid {LINE}; }}
[data-testid="stTabs"] button p {{ font-size: .95rem; }}
[data-testid="stExpander"] summary p {{ font-weight: 500; }}

@media (max-width: 760px) {{
  .keylines, .kpis, .scq {{ grid-template-columns: 1fr; }}
  .kpi + .kpi {{ border-left: none; padding-left: 0; border-top: 1px solid {LINE}; }}
  .scq > div + div {{ border-left: 1px solid {LINE}; border-top: none; }}
}}
</style>
"""


def style():
    st.markdown(CSS, unsafe_allow_html=True)


def esc(text) -> str:
    return html.escape(str(text))


def page_head(view: str, title: str, lead: str | None = None, step: str | None = None):
    """Where you are, the governing message (as the title), and one lead line."""
    crumb = f"<b>{esc(view)}</b>" + (f" &nbsp;·&nbsp; {esc(step)}" if step else "")
    st.markdown(f'<div class="crumb">{crumb}</div>', unsafe_allow_html=True)
    st.title(title)
    if lead:
        st.markdown(f'<p class="lead">{lead}</p>', unsafe_allow_html=True)


def keylines(items, colors=None):
    """Three supporting points: [(heading, text), ...]."""
    colors = colors or [INK] * len(items)
    st.markdown(
        '<div class="keylines">'
        + "".join(
            f'<div class="keyline" style="--kc:{c}"><h4>{h}</h4><p>{t}</p></div>'
            for (h, t), c in zip(items, colors)
        )
        + "</div>",
        unsafe_allow_html=True,
    )


def kpis(items):
    """[(value, label, note), ...] in one ruled row."""
    st.markdown(
        '<div class="kpis">'
        + "".join(
            f'<div class="kpi"><div class="v">{v}</div><div class="l">{l}</div>'
            + (f'<div class="n">{n}</div>' if n else "")
            + "</div>"
            for v, l, n in items
        )
        + "</div>",
        unsafe_allow_html=True,
    )


def badge(text, kind):
    return f'<span class="badge {kind}">{esc(text)}</span>'


def score_table(rows):
    st.markdown(
        '<table class="score">'
        + "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in rows)
        + "</table>",
        unsafe_allow_html=True,
    )


def callout(text, kind=""):
    st.markdown(
        f'<div class="callout {kind}"><p>{text}</p></div>', unsafe_allow_html=True
    )


def legend(items):
    st.markdown(
        '<div class="legend">'
        + "".join(f'<span style="background:{c}"></span>{esc(t)}' for t, c in items)
        + "</div>",
        unsafe_allow_html=True,
    )


def next_hint(text):
    st.markdown(f'<div class="next">{text}</div>', unsafe_allow_html=True)


BROKEN_LINK_HTML = """
<!doctype html><html><head>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  body { margin:0; font-family:'IBM Plex Sans',system-ui,sans-serif; color:#1B2430; background:transparent; }
  svg { width:100%; height:auto; display:block; }
  .node rect { stroke:#DDE2E8; stroke-width:1; fill:#fff; }
  .node .k { font-size:11px; fill:#5B6675; }
  .node .t { font-size:13px; font-weight:500; fill:#1B2430; }
  .edge { fill:none; stroke:#B4BCC7; stroke-width:1.6; }
  .flow { fill:none; stroke:#2F6FAE; stroke-width:2.4; stroke-dasharray:6 12; animation: flow 1s linear infinite; }
  @keyframes flow { to { stroke-dashoffset:-18; } }
  .changed rect { fill:#F0997B; stroke:#D9774F; }
  .c02 rect { fill:#ED93B1; stroke:#D9779A; }
  .c012 rect { animation: c012 12s infinite; }
  @keyframes c012 { 0%,30% { fill:#ED93B1; stroke:#D9779A; } 36%,62% { fill:#EEF0F3; stroke:#B4BCC7; } 70%,100% { fill:#BFE3D0; stroke:#2E9468; } }
  .ok5 { animation: ok5 12s infinite; }
  @keyframes ok5 { 0%,30% { opacity:1; } 32%,100% { opacity:0; } }
  .bad5 { stroke:#B3261E; stroke-width:2; stroke-dasharray:5 6; fill:none; animation: bad5 12s infinite; }
  @keyframes bad5 { 0%,30% { opacity:0; } 32%,34%,38% { opacity:1; } 36% { opacity:.2; } 40%,100% { opacity:1; } }
  .gap { animation: bad5 12s infinite; }
  .rules5 { animation: ok5 12s infinite; }
  .agent { fill:none; stroke:#2E9468; stroke-width:2.2; stroke-dasharray:640; stroke-dashoffset:640; animation: agent 12s infinite; }
  @keyframes agent { 0%,62% { stroke-dashoffset:640; opacity:0; } 63% { opacity:1; } 72%,100% { stroke-dashoffset:0; opacity:1; } }
  .lbl { font-size:12px; }
  .s1,.s2,.s3,.missed,.found,.alab { opacity:0; }
  .s1 { animation: s1 12s infinite; } .s2 { animation: s2 12s infinite; } .s3 { animation: s3 12s infinite; }
  .missed { animation: s2 12s infinite; } .found,.alab { animation: s3 12s infinite; }
  @keyframes s1 { 0%,29% { opacity:1; } 31%,100% { opacity:0; } }
  @keyframes s2 { 0%,31% { opacity:0; } 33%,61% { opacity:1; } 63%,100% { opacity:0; } }
  @keyframes s3 { 0%,63% { opacity:0; } 66%,100% { opacity:1; } }
  .stage { font-size:15px; font-weight:600; fill:#1B2430; }
  .stepn { font-size:12px; fill:#5B6675; }
  @media (prefers-reduced-motion: reduce) {
    * { animation:none !important; }
    .ok5,.rules5,.s1,.s2 { opacity:0 !important; }
    .bad5,.gap,.s3,.found,.alab { opacity:1 !important; }
    .agent { stroke-dashoffset:0 !important; opacity:1 !important; }
    .c012 rect { fill:#BFE3D0 !important; stroke:#2E9468 !important; }
  }
</style></head><body>
<svg viewBox="0 -62 1000 340" role="img" aria-label="A field change reaches two key controls. One link is missing, so the rules method misses one control; the agent recovers it by reading the ticket and the control procedure.">
  <g class="s1"><text class="stepn" x="0" y="-40">Step 1 of 3</text><text class="stage" x="0" y="-18">The complete map: the change reaches both key controls</text></g>
  <g class="s2"><text class="stepn" x="0" y="-40">Step 2 of 3</text><text class="stage" x="0" y="-18">One link is missing, so the rules method stops at the address rule</text></g>
  <g class="s3"><text class="stepn" x="0" y="-40">Step 3 of 3</text><text class="stage" x="0" y="-18">The agent reads the ticket and the control procedure, and recovers the control</text></g>

  <path class="edge" d="M175,125 C215,125 215,55 255,55"/><path class="flow" d="M175,125 C215,125 215,55 255,55"/>
  <path class="edge" d="M175,145 C215,145 215,215 255,215"/><path class="flow" d="M175,145 C215,145 215,215 255,215"/>
  <path class="edge" d="M455,215 L525,215"/><path class="flow" d="M455,215 L525,215"/>
  <path class="edge" d="M705,215 L775,215"/><path class="flow" d="M705,215 L775,215"/>
  <g class="ok5"><path class="edge" d="M455,55 L775,55"/></g>
  <g class="rules5"><path class="flow" d="M455,55 L775,55"/></g>
  <path class="bad5" d="M455,55 L590,55 M640,55 L775,55"/>
  <g class="gap"><text x="615" y="60" text-anchor="middle" font-size="18" font-weight="600" fill="#B3261E">×</text>
    <text x="615" y="40" text-anchor="middle" class="lbl" fill="#B3261E">link missing from the map</text></g>
  <path class="agent" d="M100,108 C140,-20 760,-30 870,28"/>
  <g class="alab"><text x="470" y="12" text-anchor="middle" class="lbl" fill="#1E6B49">the agent connects them from the text it reads</text></g>

  <g class="node changed"><rect x="20" y="108" width="155" height="54" rx="8"/><text class="k" x="34" y="128">Field changed</text><text class="t" x="34" y="148">Debtor town name</text></g>
  <g class="node"><rect x="255" y="28" width="200" height="54" rx="8"/><text class="k" x="269" y="48">Rule</text><text class="t" x="269" y="68">Address validation</text></g>
  <g class="node"><rect x="255" y="188" width="200" height="54" rx="8"/><text class="k" x="269" y="208">Rule</text><text class="t" x="269" y="228">Screening field set</text></g>
  <g class="node"><rect x="525" y="188" width="180" height="54" rx="8"/><text class="k" x="539" y="208">System</text><text class="t" x="539" y="228">Screening engine</text></g>
  <g class="node c012"><rect x="775" y="28" width="210" height="54" rx="8"/><text class="k" x="789" y="48">Key control</text><text class="t" x="789" y="68">Required-field validation</text></g>
  <g class="node c02"><rect x="775" y="188" width="210" height="54" rx="8"/><text class="k" x="789" y="208">Key control</text><text class="t" x="789" y="228">Sanctions screening</text></g>
  <g class="missed"><text x="880" y="102" text-anchor="middle" class="lbl" fill="#5B6675">missed by the rules method</text></g>
  <g class="found"><text x="880" y="102" text-anchor="middle" class="lbl" fill="#1E6B49">recovered by the agent, with quotes</text></g>
  <text x="880" y="262" text-anchor="middle" class="lbl" fill="#5B6675">found by both</text>
</svg></body></html>
"""


def broken_link_animation(height=330):
    import streamlit.components.v1 as components

    components.html(BROKEN_LINK_HTML, height=height)


DIAGRAM_CSS = f"""
<style>
.flow {{ display:grid; grid-template-columns: 1.25fr 28px 1fr 28px 1.1fr 28px 1.1fr 28px 1.15fr; align-items:center; margin:.4rem 0 1.8rem; }}
.fbox {{ border:1px solid {LINE}; border-radius:8px; padding:.75rem .85rem; background:#fff; }}
.fbox .ft {{ font-weight:600; font-size:.95rem; color:{INK}; margin-bottom:.25rem; }}
.fbox p, .fbox li {{ font-size:.86rem; color:#3D4752; line-height:1.45; margin:0; }}
.fbox ul {{ margin:0; padding-left:1rem; }}
.fbox.in {{ background:{SURFACE}; }}
.fbox.blue {{ border-color:{BLUE}; background:#EEF4FA; }}
.arrow {{ position:relative; height:2px; background:#8A94A3; margin:0 4px; }}
.arrow::after {{ content:""; position:absolute; right:-1px; top:-4px; border-left:7px solid #8A94A3; border-top:5px solid transparent; border-bottom:5px solid transparent; }}
.outs {{ display:flex; flex-direction:column; gap:.45rem; }}
.out {{ border:1px solid {LINE}; border-radius:8px; padding:.5rem .75rem; font-size:.9rem; font-weight:600; color:{INK}; background:#fff; }}
.out span {{ display:block; font-weight:400; font-size:.8rem; color:{MUTED}; }}
.out.g {{ border-color:{GREEN}; background:#E8F5EE; }} .out.a {{ border-color:{AMBER}; background:#FBF1DF; }}

.arch {{ display:grid; grid-template-columns: 1fr 34px 1.15fr 34px 1fr; gap:0; align-items:stretch; margin:.4rem 0 1.6rem; }}
.lane {{ border:1px solid {LINE}; border-radius:10px; padding:.8rem; background:{SURFACE}; display:flex; flex-direction:column; gap:.5rem; }}
.lane .lt {{ font-size:.82rem; color:{MUTED}; font-weight:500; }}
.lane .fbox {{ padding:.55rem .7rem; }}
.lane .fbox.key {{ border-style:dashed; background:#fff; }}
.pair {{ display:grid; grid-template-columns: 1fr 22px 1fr; align-items:center; }}
.dbl {{ height:2px; background:#8A94A3; position:relative; margin:0 3px; }}
.dbl::before, .dbl::after {{ content:""; position:absolute; top:-4px; border-top:5px solid transparent; border-bottom:5px solid transparent; }}
.dbl::before {{ left:-1px; border-right:7px solid #8A94A3; }} .dbl::after {{ right:-1px; border-left:7px solid #8A94A3; }}
.lanegap {{ display:flex; flex-direction:column; justify-content:center; gap:3.5rem; }}
.lanegap .arrow {{ margin:0 6px; }}
.archnote {{ font-size:.85rem; color:{MUTED}; margin:-.8rem 0 1.4rem; }}
@media (max-width: 860px) {{
  .flow, .arch {{ grid-template-columns: 1fr; gap:.5rem; }}
  .arrow, .lanegap {{ display:none; }}
}}
</style>
"""


def flow_diagram():
    st.markdown(
        DIAGRAM_CSS
        + '<div class="flow" role="img" aria-label="Inputs go to the rules method, then the AI agent, then two checks, then one of three outcomes.">'
        '<div class="fbox in"><div class="ft">What comes in</div><ul><li>Change ticket</li><li>Lineage map, incomplete</li><li>101 control procedures</li></ul></div>'
        '<div class="arrow"></div>'
        '<div class="fbox blue"><div class="ft">Rules method</div><p>Follows the links that are still visible</p></div>'
        '<div class="arrow"></div>'
        '<div class="fbox blue"><div class="ft">AI agent investigates</div><p>Reads, searches and explores, with read-only tools</p></div>'
        '<div class="arrow"></div>'
        '<div class="fbox"><div class="ft">Two checks</div><p>Quotes verified word for word, then an independent verifier</p></div>'
        '<div class="arrow"></div>'
        '<div class="outs"><div class="out g">Recommend<span>both agree it is affected</span></div>'
        '<div class="out a">Review by a person<span>they disagree</span></div>'
        '<div class="out">Not affected<span>with a stated reason</span></div></div>'
        "</div>",
        unsafe_allow_html=True,
    )


def architecture_diagram():
    st.markdown(
        DIAGRAM_CSS
        + '<div class="arch" role="img" aria-label="Build in a Git folder, run as Databricks Jobs with Model Serving, store in a Unity Catalog volume and show in a Databricks App.">'
        '<div class="lane"><div class="lt">Build · Git folder</div>'
        '<div class="fbox"><div class="ft">Benchmark generator</div><p>148 items, 238 links, 54 changes</p></div>'
        '<div class="fbox"><div class="ft">Damage step</div><p>Hides 30% of the links</p></div>'
        '<div class="fbox key"><div class="ft">Answer key</div><p>Computed offline; used only for scoring</p></div></div>'
        '<div class="lanegap"><div class="arrow"></div><div class="arrow"></div></div>'
        '<div class="lane"><div class="lt">Run · Databricks Jobs</div>'
        '<div class="pair"><div class="fbox blue"><div class="ft">Detective job</div><p>One agent run per change; resumable</p></div>'
        '<div class="dbl"></div><div class="fbox blue"><div class="ft">Model Serving</div><p>gpt-oss-120b</p></div></div>'
        '<div class="fbox"><div class="ft">Scorer job</div><p>Compares decisions with the answer key</p></div></div>'
        '<div class="lanegap"><div class="arrow"></div><div class="arrow"></div></div>'
        '<div class="lane"><div class="lt">Store and show</div>'
        '<div class="fbox"><div class="ft">Unity Catalog volume</div><p>Every step, finding and metric</p></div>'
        '<div class="fbox" style="border-color:#2E9468;background:#E8F5EE"><div class="ft">Databricks App</div><p>This dashboard</p></div></div>'
        "</div>",
        unsafe_allow_html=True,
    )
