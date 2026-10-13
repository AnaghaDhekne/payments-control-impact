"""Databricks Apps / Streamlit executive explorer for saved POC evaluations."""
import json
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "output/heldout_run/heldout_results.json"
REVIEW = ROOT / "output/heldout_run/review_study_results.json"

@st.cache_data
def load_data():
    with RESULTS.open(encoding="utf-8") as f:
        evaluation = json.load(f)
    review = None
    if REVIEW.exists():
        with REVIEW.open(encoding="utf-8") as f:
            review = json.load(f)
    return evaluation, review

st.set_page_config(page_title="Payments Control Impact Explorer", page_icon="🛡️", layout="wide")
st.title("Payments Control Impact Explorer")
st.caption("Databricks POC • Synthetic held-out evaluation • Saved-results replay (not live inference)")
if not RESULTS.exists():
    st.error("Evaluation artifact missing: output/heldout_run/heldout_results.json. Deploy the complete repository.")
    st.stop()
data, review = load_data()
summary = data["summary"]
cases = pd.DataFrame(data["per_case"])
page = st.sidebar.radio("Explore", ["Executive overview", "Scenario explorer", "Validation and limitations"])
st.sidebar.caption("Oracle-adjudicated evaluation, not real-world deployment.")

if page == "Executive overview":
    st.subheader("Recovering control visibility when dependency metadata is incomplete")
    a,b,c,d = st.columns(4)
    a.metric("Key misses recovered", summary["recovery"], f'{summary["total_key_recovered"]}/{summary["total_key_misses"]}')
    b.metric("Control precision", summary["control_precision"], f'{summary["total_true_new"]}/{summary["total_new_controls"]}')
    c.metric("Held-out scenarios", len(cases))
    d.metric("Edge precision", summary["edge_precision"], f'{summary["correct_edges"]}/{summary["total_edges"]}')
    st.info("Both predeclared recovery and control-precision targets passed on held-out synthetic data. Results use hidden synthetic truth for offline scoring, not human approvals.")
    chart = pd.DataFrame([
        {"Metric":"Recovery", "Achieved":100*summary["total_key_recovered"]/summary["total_key_misses"], "Target":50},
        {"Metric":"Control precision", "Achieved":100*summary["total_true_new"]/summary["total_new_controls"], "Target":80},
    ])
    fig = go.Figure()
    fig.add_bar(name="Achieved", x=chart["Metric"], y=chart["Achieved"])
    fig.add_bar(name="Target", x=chart["Metric"], y=chart["Target"])
    fig.update_layout(barmode="group", yaxis_title="Percent", yaxis_range=[0,100], height=360)
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Explore the underlying scenarios")
    st.dataframe(cases[["change_id","key_misses","key_recovered","recovery","new_controls","precision"]], use_container_width=True, hide_index=True)
    st.caption("Metrics are pooled across cases; per-case percentages should not be averaged to reproduce pooled totals.")

elif page == "Scenario explorer":
    selected = st.selectbox("Select evaluated change request", cases["change_id"].tolist())
    case = next(x for x in data["per_case"] if x["change_id"] == selected)
    a,b,c = st.columns(3)
    a.metric("Baseline key-control misses", case["key_misses"])
    b.metric("Recovered by AI", case["key_recovered"])
    c.metric("Newly surfaced controls", case["new_controls"])
    st.caption("This explorer uses saved offline evaluation artifacts. It does not generate new recommendations.")
    missing = set(case["key_miss_controls"])
    recovered = set(case["recovered_controls"])
    rows = [{"Control ID":c, "Outcome":"Recovered" if c in recovered else "Still missed"} for c in sorted(missing)]
    st.subheader("Control-level drill-down")
    if rows:
        outcome = st.multiselect("Filter outcomes", ["Recovered","Still missed"], default=["Recovered","Still missed"])
        st.dataframe(pd.DataFrame(rows).query("Outcome in @outcome"), hide_index=True, use_container_width=True)
    else:
        st.info("No baseline key-control misses for this scenario.")
    st.subheader("Impact coverage")
    if missing:
        fig = px.pie(names=["Recovered", "Still missed"], values=[len(recovered & missing),len(missing-recovered)], hole=0.55)
        st.plotly_chart(fig, use_container_width=True)
    with st.expander("Evidence and dependency graph — data requirements"):
        st.write("This summary artifact contains control IDs and counts, but not the source-ticket text, proposed edge endpoints, exact quotes, or graph topology. Do not invent those details.")
        st.write("To enable evidence-linked graph drill-down, export validated, case-keyed JSON containing observable ticket/control text, original edges, proposed edges, evidence spans, and oracle labels, with provenance. Keep hidden labels out of model prompts.")

else:
    st.subheader("Validation and limitations")
    st.write("**Evaluation:**", data["evaluation"])
    st.write("**Pipeline:**", data["pipeline"])
    st.write("**Quote handling:**", data.get("fix_quotes_version","Not recorded"))
    st.json(data["gates"], expanded=False)
    st.warning("Control-level precision is not edge precision. Only 23 of 91 proposed edges were oracle-correct, even though 83 of 91 newly surfaced controls were correct.")
    if review:
        st.subheader("Exploratory LLM-as-reviewer study (not human review)")
        a,b,c = st.columns(3)
        a.metric("Approvals", review["approve"])
        b.metric("Rejections", review["reject"])
        c.metric("Uncertain", review["uncertain"])
        st.caption("The simulated reviewer study is out of scope for the primary feasibility claim. Its reported metrics require a decision-level reconciliation before use as executive KPIs.")
    st.info("This POC is not production-ready. Synthetic oracle scoring does not establish real-world reviewer accuracy, safety, or regulatory suitability.")
    with st.expander("Source artifact details"):
        st.code(str(RESULTS.relative_to(ROOT)))
        st.json(summary)
