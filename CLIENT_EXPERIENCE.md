# Client experience — release assurance

This application is presented as a **single interactive product**, not as a traditional analytics dashboard. It is a recorded, synthetic proof-of-concept demonstration. It does not connect to a bank's live systems or run a new model inference when a viewer clicks.

## Audience and narrative

For payments transformation sponsors, control owners, risk leaders, and consulting stakeholders.

The decision: *Does a rules-only report showing no affected controls justify signing off on a screening-interface change?*

The intended demonstration takes roughly 3–5 minutes:

1. **Investigate** — start with CHG-027, where rules-only metadata traversal reports 0 of 20 affected controls. Click **Challenge the result**. Click the sanctions control object to read the recorded ticket/procedure evidence. Optionally compare with the intact reference map; it was not available to the baseline.
2. **Evidence** — switch to the Evidence room. Examine the held-out key-control coverage: 18 baseline identified, 113 additionally recovered, 31 not recovered as recommendations (30 routed for human review; one silent miss). Switch between review workload, residual risk, and consistency.
3. **Decision** — switch to the Decision room. Explore the three prerequisites: practitioner validation, root-cause the silent miss, and measure reviewer time/model cost/consistency. **Do not** recommend production deployment.
4. **Method** — disclose synthetic setup, correlated metadata damage, frozen agent, and the difference between recommendations and completed control reviews.

The client-facing rooms are implemented together in `app/client_experience.py`, embedded by `app/app.py`. The technical evidence, run explorer, source documents, synthetic degradation experiment, and detailed case dossier remain in the **Technical diligence and source evidence** navigation drawer. The older `app/client_rooms.py` is superseded by the unified product and is not used for client navigation.

## Source-of-truth and claims

- The highlighted CHG-027 case is recorded synthetic evidence, not a live inference. The control C02 quotes and agent reasoning are populated from `data.case_result(..., 'run1', 'CHG-027')`; if unavailable, the UI explicitly says so rather than inventing quotes.
- Held-out evaluation: 18 changes; 162 affected key-control instances; baseline found 18; AI-assisted path identified 131; 113 recovered from 144 baseline misses.
- The remaining 31 were not recovered as recommendations. 30 were routed for human review, **not** verified by humans; one was silently missed.
- Of 406 additional review items, 331 were genuine affected controls and 75 unaffected. Do not label all 406 as wasted work. Avoidable share of additional items is 75/406 (18.5%).
- Repeatability was approximately 80%, below the 95% target. Three-run voting reached approximately 94.4% at about 4× model cost.
- No real-world reviewer time, production assurance, or ROI has been established.

## Run and quality assurance

```bash
pip install -r requirements.txt
python -m pytest tests/test_client_experience.py -q
streamlit run app/app.py
```

Browser acceptance checklist:

- [ ] Desktop at 1440×900: open client experience and confirm there is no traditional metric-card dashboard at entry.
- [ ] Investigate: the default graph shows a missing dependency; **Challenge the result** changes the path and contextual panel; **Show hidden reference** displays the complete reference; **Reset investigation** returns to missing lineage.
- [ ] Click or keyboard-activate each graph node; inspect the C02 recorded quote. If recorded results are unavailable, verify the unavailable message is shown.
- [ ] Evidence: click all four questions; check numbers and distinctions between necessary findings and unaffected review items.
- [ ] Decision: click all three gates; verify production approval and ROI are not claimed.
- [ ] Method: confirm frozen-agent/synthetic limitations and intact answer-key disclosure.
- [ ] Narrow/mobile viewport: all four rooms remain usable; no clipped buttons, text, or SVG.
- [ ] Keyboard-only navigation and reduced-motion preference; inspect focus visibility.
- [ ] Open technical diligence, run explorer, synthetic experiment, and detailed case dossier; confirm they still work.
- [ ] Test with and without accessible recorded result files.
- [ ] Confirm deployment dependencies and Databricks app configuration; inspect browser console and Streamlit logs.

**Status:** Code committed. Live deployed rendering, cross-device behavior, and end-to-end browser acceptance have not yet been independently verified. Do not describe this as production-ready or visually QA-approved until the checklist passes.
