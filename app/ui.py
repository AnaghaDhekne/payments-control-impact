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
BLUE = "#2F6FAE"  # found by the current check
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
.callout.risk {{ border-left-color: {RED}; background: #FBEFEE; }}
.callout .tag {{ display:block; font-size:.8rem; font-weight:600; color:{RED}; margin-bottom:.2rem; }}

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
abbr.t {{ text-decoration: none; border-bottom: 1px dotted {MUTED}; cursor: help; }}
.navbtns {{ margin-top: 2.4rem; padding-top: 1rem; border-top: 1px solid {LINE}; }}
.main [data-testid="stPageLink"] a, section.main [data-testid="stPageLink"] a {{ border: 1px solid {LINE}; border-radius: 6px; padding: .45rem .9rem; }}
.about {{ font-size: .8rem; color: {MUTED}; line-height: 1.55; }}
.about b {{ color: {INK}; font-weight: 600; }}
.prov {{ font-size:.8rem; color:{MUTED}; border-top:1px solid {LINE}; padding-top:.6rem; margin-top:1.4rem; line-height:1.5; }}
.prov b {{ color:{INK}; font-weight:600; margin-right:.3rem; }}
.journey {{ display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:0; margin:.4rem 0 1.6rem; }}
.journey > div {{ padding:.9rem 1rem; border:1px solid {LINE}; background:#fff; }}
.journey > div + div {{ border-left:none; }}
.journey .jn {{ width:24px; height:24px; border-radius:50%; background:{INK}; color:#fff; font-size:.8rem; font-weight:600; display:flex; align-items:center; justify-content:center; margin-bottom:.45rem; }}
.journey .jh {{ font-weight:600; color:{INK}; margin-bottom:.3rem; }}
.journey p {{ font-size:.9rem; line-height:1.45; margin:0; color:#3D4752; }}
.ready {{ display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:.8rem; margin:.4rem 0 1.4rem; }}
.ready > div {{ border:1px solid {LINE}; border-radius:8px; padding:.9rem 1rem; background:#fff; }}
.ready h4 {{ margin:0 0 .4rem; font-size:.98rem; font-weight:600; color:{INK}; }}
.ready ul {{ margin:0; padding-left:1.05rem; }} .ready li {{ font-size:.88rem; line-height:1.45; color:#3D4752; margin:.15rem 0; }}
@media (max-width: 900px) {{ .journey, .ready {{ grid-template-columns:1fr; }} .journey > div + div {{ border-left:1px solid {LINE}; border-top:none; }} }}
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

/* Editorial investigation identity: typography, generous whitespace, numbered evidence.
   Responsive rules prevent dense dashboard elements from colliding at laptop widths. */
:root {{ --paper:#FAF8F3; --ink:#202B36; --accent:#B75E40; --rule:#D7D0C5; }}
html, body, [data-testid="stAppViewContainer"] {{ background:var(--paper) !important; }}
.block-container {{ max-width:1280px; padding:3.2rem clamp(1rem,3vw,3.5rem) 5rem !important; }}
.block-container, .block-container * {{ box-sizing:border-box; }}
.block-container p, .block-container td, .block-container li,
.block-container .lead, .block-container .chart-s {{ overflow-wrap:anywhere; }}
.block-container h1, .block-container h2, .block-container h3 {{ overflow-wrap:break-word; }}
h1 {{ font-size:clamp(2rem,3.4vw,3.35rem) !important; max-width:26ch; letter-spacing:-.035em !important; }}
.crumb, .slide-meta {{ text-transform:uppercase; letter-spacing:.11em; font-size:.7rem !important; }}
.keylines, .kpis, .scq, .journey, .ready, .tiles, .opts, .gaps, .flow, .arch {{
  min-width:0; width:100%;
}}
.keylines > *, .kpis > *, .scq > *, .journey > *, .ready > *,
.tiles > *, .opts > *, .gaps > *, .flow > *, .arch > * {{ min-width:0; }}
.kpis {{ gap:0; }}
.kpi .v {{ font-family:'Source Serif 4',Georgia,serif; font-size:clamp(1.6rem,2.6vw,2.7rem); }}
.kpi .l {{ line-height:1.35; }}
.journey .jn {{ background:var(--accent); }}
.journey > div {{ border-top:3px solid var(--accent); }}
.tile {{ border-radius:0; border:none; border-top:2px solid var(--ink); background:transparent; }}
.tile .big {{ font-family:'Source Serif 4',Georgia,serif; font-size:2.5rem; }}
.hero-h {{ font-size:clamp(2.3rem,4.5vw,4.7rem); line-height:1.04; max-width:23ch; letter-spacing:-.045em; }}
.slide-h {{ font-size:clamp(2rem,4vw,4.3rem); max-width:24ch; letter-spacing:-.035em; }}
.brief {{ border-radius:0; border-left:5px solid var(--accent); }}
.chart-h {{ font-family:'Source Serif 4',Georgia,serif; font-size:1.4rem; line-height:1.25; margin-top:1.4rem; }}
.chart-s {{ line-height:1.5; }}
.opts {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
.opt {{ border-radius:0; border-top:3px solid var(--accent); }}
.ready > div {{ border-radius:0; }}
.legend {{ display:flex; flex-wrap:wrap; gap:.45rem 1rem; line-height:1.5; }}
.legend span {{ flex:none; }}
[data-testid="stDataFrame"], [data-testid="stVegaLiteChart"],
[data-testid="stGraphVizChart"] {{ max-width:100%; min-width:0; overflow-x:auto; }}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{ min-width:0; }}
[data-testid="stTabs"] [role="tablist"] {{ overflow-x:auto; max-width:100%; }}
[data-testid="stTabs"] button {{ flex-shrink:0; white-space:normal; }}
table.score {{ table-layout:fixed; }}
table.score td {{ overflow-wrap:anywhere; white-space:normal !important; }}
@media (max-width:1150px) {{
  .tiles {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
  .journey, .scq {{ grid-template-columns:repeat(2,minmax(0,1fr)); gap:.6rem; }}
  .journey > div + div, .scq > div + div {{ border-left:1px solid var(--rule); }}
  .flow, .arch {{ display:flex; flex-wrap:wrap; gap:.75rem; }}
  .flow .fbox, .arch .lane {{ flex:1 1 230px; }}
  .flow .arrow, .arch .arrow {{ display:none; }}
}}
@media (max-width:800px) {{
  .block-container {{ padding:1.4rem 1rem 3rem !important; }}
  .kpis, .keylines, .ready, .gaps, .opts {{ grid-template-columns:repeat(2,minmax(0,1fr)); gap:.8rem; }}
  .kpi + .kpi {{ border-left:0; padding-left:0; }}
  .kpi {{ border-bottom:1px solid var(--rule); }}
  .slide-meta {{ flex-wrap:wrap; gap:.5rem; }}
}}
@media (max-width:580px) {{
  .kpis, .keylines, .ready, .gaps, .opts, .tiles, .journey, .scq {{ grid-template-columns:1fr; }}
  .journey > div + div, .scq > div + div {{ border-top:1px solid var(--rule); }}
  .gap .v {{ font-size:2.1rem; }}
  .slide-h {{ font-size:2rem; }}
  .segbar .labels {{ display:block; }}
}}

</style>
"""


def style():
    st.markdown(CSS, unsafe_allow_html=True)


def esc(text) -> str:
    return html.escape(str(text))


def page_head(
    view: str,
    title: str,
    lead: str | None = None,
    step: str | None = None,
    synthetic: bool = False,
):
    """Where you are, the governing message (as the title), and one lead line."""
    crumb = f"<b>{esc(view)}</b>" + (f" &nbsp;·&nbsp; {esc(step)}" if step else "")
    if synthetic:
        crumb += ' &nbsp;<span class="badge dim">Synthetic benchmark data</span>'

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
        + "".join(
            "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
            for row in rows
        )
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
  .ctl { display:flex; flex-wrap:wrap; gap:8px; margin:0 0 12px; }
  .ctl button { font:600 13px 'IBM Plex Sans',sans-serif; border:1px solid #B8BFC7; padding:9px 13px; background:#fff; color:#202B36; cursor:pointer; }
  .ctl button[aria-pressed="true"] { background:#202B36; color:white; border-color:#202B36; }
  .ctl button:focus-visible { outline:3px solid #B75E40; outline-offset:2px; }
  .stepn { font-size:12px; fill:#5B6675; }
  /* No autoplay. Every state is explicitly selected by a person. */
  #anim *, #anim *::before, #anim *::after { animation:none !important; transition:opacity .25s ease, fill .25s ease; }
  #anim .flow { stroke-dasharray:none; }
  #anim .s1,#anim .s2,#anim .s3,#anim .missed,#anim .found,#anim .alab,#anim .gap,#anim .bad5,#anim .agent { opacity:0; }
  #anim[data-step="1"] .s1,#anim[data-step="1"] .ok5,#anim[data-step="1"] .rules5 { opacity:1; }
  #anim[data-step="2"] .s2,#anim[data-step="2"] .missed,#anim[data-step="2"] .gap,#anim[data-step="2"] .bad5 { opacity:1; }
  #anim[data-step="3"] .s3,#anim[data-step="3"] .found,#anim[data-step="3"] .alab,#anim[data-step="3"] .gap,#anim[data-step="3"] .bad5,#anim[data-step="3"] .agent { opacity:1; }
  #anim[data-step="2"] .ok5,#anim[data-step="2"] .rules5,#anim[data-step="3"] .ok5,#anim[data-step="3"] .rules5 { opacity:0; }
  #anim[data-step="2"] .c012 rect { fill:#EEF0F3; stroke:#B4BCC7; }
  #anim[data-step="3"] .c012 rect { fill:#BFE3D0; stroke:#2E9468; }
  #anim[data-step="3"] .agent { stroke-dasharray:none; stroke-dashoffset:0; }
  .ctl button { padding:12px 16px; border-radius:4px; font-weight:600; letter-spacing:.01em; cursor:pointer; }
  .ctl button[aria-pressed="true"] { background:#152B3A; color:#fff; border-color:#152B3A; }
  .ctl button:hover { border-color:#152B3A; }
  #anim .flow { animation:none !important; }
  .stage { font-size:18px; font-weight:600; }
  @media (prefers-reduced-motion:reduce) { * { animation:none !important; transition:none !important; } }
</style></head><body>
<div class="ctl" role="group" aria-label="Explore the investigation"><button data-step="1" type="button" aria-pressed="false">1 · Full dependency map</button><button data-step="2" type="button" aria-pressed="true">2 · Remove a link</button><button data-step="3" type="button" aria-pressed="false">3 · Investigate with AI</button></div><p id="step-description" aria-live="polite" style="font-size:13px;line-height:1.5;color:#5B6675;margin:0 0 8px">The current map hides a key control. Explore the complete reference or activate the investigation.</p>
<svg id="anim" data-step="2" viewBox="0 -62 1000 340" role="img" aria-label="A field change reaches two key controls. One link is missing, so the current check misses one control; the agent recovers it by reading the ticket and the control procedure.">
  <g class="s1"><text class="stepn" x="0" y="-40">Step 1 of 3</text><text class="stage" x="0" y="-18">The complete map: the change reaches both key controls</text></g>
  <g class="s2"><text class="stepn" x="0" y="-40">Step 2 of 3</text><text class="stage" x="0" y="-18">One link is missing, so the current check stops at the address rule</text></g>
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
  <path class="agent" d="M100,108 C170,12 720,6 870,28"/>
  <g class="alab"><text x="560" y="6" text-anchor="middle" class="lbl" fill="#1E6B49">the agent connects them from the text it reads</text></g>

  <g class="node changed"><rect x="20" y="108" width="155" height="54" rx="8"/><text class="k" x="34" y="128">Field changed</text><text class="t" x="34" y="148">Debtor town name</text></g>
  <g class="node"><rect x="255" y="28" width="200" height="54" rx="8"/><text class="k" x="269" y="48">Rule</text><text class="t" x="269" y="68">Address validation</text></g>
  <g class="node"><rect x="255" y="188" width="200" height="54" rx="8"/><text class="k" x="269" y="208">Rule</text><text class="t" x="269" y="228">Screening field set</text></g>
  <g class="node"><rect x="525" y="188" width="180" height="54" rx="8"/><text class="k" x="539" y="208">System</text><text class="t" x="539" y="228">Screening engine</text></g>
  <g class="node c012"><rect x="775" y="28" width="210" height="54" rx="8"/><text class="k" x="789" y="48">Key control</text><text class="t" x="789" y="68">Required-field validation</text></g>
  <g class="node c02"><rect x="775" y="188" width="210" height="54" rx="8"/><text class="k" x="789" y="208">Key control</text><text class="t" x="789" y="228">Sanctions screening</text></g>
  <g class="missed"><text x="880" y="102" text-anchor="middle" class="lbl" fill="#5B6675">missed by the current check</text></g>
  <g class="found"><text x="880" y="102" text-anchor="middle" class="lbl" fill="#1E6B49">recovered by the agent, with quotes</text></g>
  <text x="880" y="262" text-anchor="middle" class="lbl" fill="#5B6675">found by both</text>
</svg>
<script>
  const svg=document.getElementById('anim'), buttons=[...document.querySelectorAll('.ctl button')];
  const notes={
    1:'The complete map connects the changed field to both key controls. Select step 2 to break a link.',
    2:'The lineage link disappears. The rules-only check cannot reach required-field validation, so it misses a real impact.',
    3:'The agent reads change and control documents and recommends a missing impact with evidence for human review; it does not repair the lineage map.'
  };
  buttons.forEach(btn=>btn.addEventListener('click',()=>{
    const step=btn.dataset.step;
    svg.dataset.step=step;
    buttons.forEach(b=>b.setAttribute('aria-pressed',String(b===btn)));
    document.getElementById('step-description').textContent=notes[step];
  }));
</script>
</body></html>
"""


def broken_link_animation(height=350):
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
        + '<div class="flow" role="img" aria-label="Inputs go to the current check, then the AI agent, then two checks, then one of three outcomes.">'
        '<div class="fbox in"><div class="ft">What comes in</div><ul><li>Change ticket</li><li>Lineage map, incomplete</li><li>101 control procedures</li></ul></div>'
        '<div class="arrow"></div>'
        '<div class="fbox blue"><div class="ft">Current check</div><p>Follows the links that are still visible in the map</p></div>'
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


def term(word, definition):
    """A word with its plain-language definition on hover."""
    return f'<abbr class="t" title="{esc(definition)}">{esc(word)}</abbr>'


TERMS = {
    "key control": "One of the 30 most important controls, whose failure would matter most.",
    "lineage map": "The record of what feeds what: field to rule to system to control.",
    "current check": "Today's automated check: it follows the lineage map from the changed item to the controls.",
    "held-out": "Changes kept aside and never used while building or tuning the agent.",
    "for review": "The agent and its independent checker disagreed, so the item is routed to a person to decide.",
    "recommended": "The agent says the control is affected and its independent checker agrees.",
}


def t(word, key=None):
    return term(word, TERMS[key or word])


OVERVIEW_CSS = f"""
<style>
.hero-h {{ font-family:'Source Serif 4', Georgia, serif; font-weight:600; font-size:2.6rem; line-height:1.12;
          color:{INK}; letter-spacing:-0.015em; max-width:32ch; margin:.2rem 0 .7rem; }}
.brief {{ background:{INK}; color:#F4F6F9; border-radius:10px; padding:1.2rem 1.3rem; height:100%; }}
.brief .bt {{ font-size:.82rem; color:#AEB8C5; margin-bottom:.6rem; }}
.brief dl {{ margin:0; }}
.brief dt {{ font-size:.82rem; color:#AEB8C5; margin-top:.75rem; }}
.brief dt:first-child {{ margin-top:0; }}
.brief dd {{ margin:.15rem 0 0; font-size:1rem; line-height:1.45; color:#fff; }}
.brief dd b {{ color:#fff; }}
.tiles {{ display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:1rem; margin:1.6rem 0 .4rem; }}
.tile {{ border:1px solid {LINE}; border-radius:10px; padding:1rem 1rem .9rem; background:#fff; display:flex; flex-direction:column; }}
.tile .n {{ font-size:.8rem; color:{MUTED}; }}
.tile .h {{ font-weight:600; font-size:1.02rem; margin:.15rem 0 .4rem; color:{INK}; }}
.tile .big {{ font-size:1.9rem; font-weight:500; color:{INK}; line-height:1.1; font-variant-numeric:tabular-nums; }}
.tile .big small {{ font-size:.9rem; color:{MUTED}; font-weight:400; }}
.tile p {{ font-size:.9rem; color:#3D4752; line-height:1.45; margin:.35rem 0 0; }}
.chart-h {{ font-weight:600; font-size:1.05rem; color:{INK}; margin:.4rem 0 .1rem; }}
.chart-s {{ font-size:.88rem; color:{MUTED}; margin:0 0 .4rem; }}
.slide-meta {{ display:flex; justify-content:space-between; align-items:center; font-size:.85rem; color:{MUTED}; margin-bottom:.4rem; }}
.dots span {{ display:inline-block; width:26px; height:4px; border-radius:2px; background:{LINE}; margin-left:4px; }}
.dots span.on {{ background:{INK}; }}
.slide-h {{ font-family:'Source Serif 4', Georgia, serif; font-weight:600; font-size:2.35rem; line-height:1.15;
           color:{INK}; max-width:30ch; margin:.6rem 0 .6rem; letter-spacing:-0.01em; }}
.slide-s {{ font-size:1.12rem; color:#3D4752; line-height:1.55; max-width:68ch; margin:0 0 1.4rem; }}
.gaps {{ display:grid; grid-template-columns:1fr 1fr; gap:1.2rem; }}
.gap {{ border-top:4px solid {AMBER}; padding-top:.8rem; }}
.gap .v {{ font-size:3rem; font-weight:500; color:{INK}; line-height:1; }}
.gap .v small {{ font-size:1rem; color:{MUTED}; font-weight:400; }}
.gap p {{ font-size:1rem; color:#3D4752; margin:.5rem 0 0; line-height:1.5; }}
.opts {{ display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:1rem; margin-bottom:1.2rem; }}
.opt {{ border:1px solid {LINE}; border-radius:10px; padding:1rem; }}
.opt .h {{ font-weight:600; margin-bottom:.35rem; }}
.opt p {{ font-size:.92rem; color:#3D4752; line-height:1.45; margin:0; }}
@media (max-width: 900px) {{ .tiles, .opts, .gaps {{ grid-template-columns:1fr; }} .hero-h {{ font-size:2rem; }} }}

.case-masthead {{ display:flex; justify-content:space-between; gap:1rem; flex-wrap:wrap; padding:.6rem 0 1rem; border-top:2px solid #202B36; font-size:.68rem; letter-spacing:.14em; font-weight:600; color:#5B6675; }}
.investigation-hero {{ background:#202B36; color:#FAF8F3; padding:clamp(1.6rem,5vw,4.4rem); margin:0 0 2rem; border-bottom:7px solid #B75E40; }}
.hero-eyebrow {{ font-size:.72rem; font-weight:600; letter-spacing:.2em; color:#E5B7A7; margin-bottom:1.2rem; }}
.investigation-hero .hero-h {{ color:#FAF8F3; font-size:clamp(2.8rem,5.5vw,5.5rem); line-height:1.03; letter-spacing:-.05em; max-width:17ch; }}
.hero-deck {{ color:#E5E4DF; max-width:66ch; font-size:clamp(1rem,1.5vw,1.25rem); line-height:1.6; margin:1.5rem 0 2rem; }}
.hero-statline {{ display:flex; align-items:end; justify-content:space-between; flex-wrap:wrap; gap:2rem; padding-top:1.5rem; border-top:1px solid #64707A; }}
.hero-statline > div {{ min-width:0; }}
.hero-num {{ display:block; font-family:'Source Serif 4',Georgia,serif; font-size:clamp(3.5rem,7vw,6rem); line-height:1; color:#FAF8F3; letter-spacing:-.04em; }}
.hero-num span {{ font-size:.48em; color:#E5B7A7; }}
.hero-stat-label {{ display:block; color:#E5E4DF; font-size:.92rem; margin-top:.4rem; }}
.hero-stat-side {{ font-size:.87rem; line-height:1.9; color:#E5E4DF; }}
.hero-stat-side b {{ color:#FAF8F3; }}
.section-index {{ display:flex; flex-wrap:wrap; justify-content:space-between; gap:.6rem; border-top:1px solid #202B36; padding:.65rem 0 1rem; margin:2.6rem 0 1rem; font-size:.7rem; font-weight:600; letter-spacing:.12em; color:#5B6675; }}
.case-entry {{ min-height:165px; border-top:4px solid #B75E40; padding:1.1rem .2rem .6rem; }}
.case-entry-label {{ font-size:.7rem; color:#9B553F; letter-spacing:.12em; font-weight:600; }}
.case-entry-title {{ font-family:'Source Serif 4',Georgia,serif; color:#202B36; font-size:1.55rem; margin:.65rem 0; line-height:1.18; }}
.case-entry p {{ font-size:.91rem; line-height:1.55; color:#5B6675; }}
@media(max-width:640px) {{ .hero-statline {{ align-items:start; }} .case-entry {{ min-height:0; }} }}

.verdict-strip {{ display:grid; grid-template-columns:minmax(0,1.65fr) minmax(220px,1fr); gap:0; border-top:3px solid #202B36; border-bottom:1px solid #202B36; margin:1rem 0 2rem; }}
.verdict-primary {{ padding:2rem 2rem 2rem 0; }}
.verdict-primary > span {{ display:block; font-size:.72rem; letter-spacing:.14em; font-weight:600; color:#9B553F; }}
.verdict-primary strong {{ display:block; font-family:'Source Serif 4',Georgia,serif; font-size:clamp(2.5rem,5vw,5rem); letter-spacing:-.05em; font-weight:500; line-height:1.15; margin:.5rem 0; }}
.verdict-primary small {{ font-size:.35em; letter-spacing:0; font-weight:400; color:#5B6675; }}
.verdict-primary p {{ max-width:45ch; line-height:1.55; }}
.verdict-secondary {{ display:grid; grid-template-columns:auto 1fr; align-content:center; gap:.6rem 1rem; border-left:1px solid #D7D0C5; padding:1rem 0 1rem 1.5rem; }}
.verdict-secondary b {{ font-family:'Source Serif 4',Georgia,serif; font-size:2rem; line-height:1.15; font-weight:500; }}
.verdict-secondary span {{ align-self:center; font-size:.88rem; line-height:1.4; }}
@media(max-width:700px) {{ .verdict-strip {{ grid-template-columns:1fr; }} .verdict-secondary {{ border-left:0; border-top:1px solid #D7D0C5; padding:1rem 0; }} }}
</style>
"""


def overview_css():
    st.markdown(OVERVIEW_CSS, unsafe_allow_html=True)


def chart_title(title, sub=None):
    st.markdown(
        f'<div class="chart-h">{title}</div>'
        + (f'<div class="chart-s">{sub}</div>' if sub else ""),
        unsafe_allow_html=True,
    )


SEGBAR_CSS = f"""
<style>
.segbar {{ margin: .4rem 0 1.4rem; }}
.segbar .row {{ display:flex; align-items:stretch; gap:0; }}
.segbar .rowlabel {{ width: 120px; flex: none; font-size:.9rem; font-weight:500; color:{INK}; display:flex; align-items:center; }}
.segbar .track {{ flex:1; display:flex; }}
.segbar .seg {{ height: 44px; display:flex; align-items:center; justify-content:center; color:#fff; font-weight:600; font-size:1rem;
               border-right: 2px solid #fff; font-variant-numeric: tabular-nums; }}
.segbar .seg.light {{ color:{INK}; }}
.segbar .labels {{ display:flex; margin-top:.35rem; }}
.segbar .labels div {{ font-size:.84rem; color:#3D4752; line-height:1.3; padding-right:.5rem; }}
.segbar .labels b {{ display:block; color:{INK}; font-weight:600; }}
.segbar .row + .row {{ margin-top:.5rem; }}
.segbar .seglabels {{ flex:1; display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:.7rem; }}
.segbar .seglabel {{ width:auto !important; min-width:0; padding:.5rem .65rem; border-left:2px solid #D7D0C5; overflow-wrap:anywhere; }}
.segbar .seg {{ min-width:0; overflow:hidden; }}
</style>
"""


def segbar(rows, total, show_labels=True):
    """Stacked bars drawn in HTML, with each segment named underneath.

    rows: [(row_label or None, [(value, label, color, light_text), ...]), ...]
    """
    out = [SEGBAR_CSS, '<div class="segbar">']
    for row_label, segs in rows:
        out.append('<div class="row">')
        if row_label is not None:
            out.append(f'<div class="rowlabel">{esc(row_label)}</div>')
        out.append('<div class="track">')
        for v, _, color, light in segs:
            w = 100 * v / total
            shown = f"{v:.0f}" if isinstance(v, float) else str(v)
            out.append(
                f'<div class="seg{" light" if light else ""}" style="width:{w:.2f}%;background:{color}">{shown}</div>'
            )
        out.append("</div></div>")
    if show_labels:
        last = rows[-1]
        pad = '<div style="width:120px;flex:none"></div>' if last[0] is not None else ""
        out.append(f'<div class="labels">{pad}<div class="seglabels">')
        for v, label, _, _ in last[1]:
            out.append(f'<div class="seglabel">{label}</div>')
        out.append("</div></div>")
    out.append("</div>")
    st.markdown("".join(out), unsafe_allow_html=True)
