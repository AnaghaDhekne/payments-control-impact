"""Written content for the app: context for newcomers, glossary and FAQ.

Figures quoted here are the recorded results in docs/results.md. Live figures
on the Evidence page are read from the run files instead.
"""

CONTEXT_INTRO = """
**Banks run controls**: checks that stop bad payments or catch mistakes, such as
*"payments to sanctioned parties are blocked before release"* or *"required
payment fields are validated"*. Each control depends on data, rules and systems.

**Payments change constantly.** A field mapping, a validation rule, a report
or an interface is updated. When that happens, every control that depends on
the changed part may need to be re-tested or redesigned. Missing one means a
control can silently stop working.

**Finding those controls needs lineage**: a map of what feeds what (field →
rule → system → control). In practice that map is incomplete, especially
around the parts that change most. A rules engine that walks the map stops
wherever a link is missing.

**This proof of concept asks one question:** when lineage is broken, can an AI
agent find the affected controls that the rules miss, by reading change
tickets and control procedures, and cite evidence a reviewer can check?
"""

CONTEXT_EXAMPLE = """
**A concrete example (CHG-001).** A release changes the *Debtor town name*
field (D03). In the full map, D03 is used by rule R01 *Structured postal
address validation*, which feeds the *Required-field validation* controls
(C01, C012–C015 …). In the degraded map the link from R01 to those controls is
missing, so the rules walk finds **none of the 19 affected key controls**. The
agent explores D03, sees R01, reads the control procedures and recovers 14 of
them, each with quoted evidence.
"""

GLOSSARY = [
    (
        "Control",
        "A check that prevents or detects a problem in the payment flow, owned by a person or team.",
    ),
    (
        "Key control",
        "A control the bank relies on most (30 of the 101 here). Missing one is the costliest error, so the main metric is about key controls.",
    ),
    (
        "Change",
        "A release that alters a field mapping, rule, report, interface or system. The benchmark has 54.",
    ),
    (
        "Lineage",
        "The map of dependencies: which fields feed which rules, systems, reports and controls.",
    ),
    (
        "Degradation",
        "Deliberately removing lineage links near the change (30% in the main test) to mimic real, incomplete metadata.",
    ),
    (
        "Rules baseline",
        "The non-AI method: follow visible lineage links from the changed item to every control they reach.",
    ),
    (
        "Key miss",
        "An affected key control the rules baseline does not find. Recovering these is the agent's job.",
    ),
    (
        "Agent / detective",
        "An LLM that chooses read-only tools step by step (explore the map, search and read procedures) and submits findings.",
    ),
    (
        "Finding",
        "A decision on one control (AFFECTED, UNAFFECTED, UNCERTAIN) with exact quotes from the ticket and procedure and a stated reason.",
    ),
    (
        "Verifier",
        "A second, independent model call that checks each finding. If it disagrees, the control goes to a human.",
    ),
    (
        "UNCERTAIN / review item",
        "A control sent to a person to decide. Counted as workload, never as a recovery.",
    ),
    (
        "Precision",
        "Of the controls the agent newly recommends, the share that are truly affected.",
    ),
    (
        "Answer key",
        "The true affected controls, computed from the complete hidden map. The agent never sees it.",
    ),
    (
        "Development vs held-out",
        "Development cases may be looked at while building; the 18 held-out cases are run once, at the end, with everything frozen.",
    ),
    (
        "Frozen check",
        "A run on development cases never inspected during fixing, with code fixed in advance: the fairest result before the held-out run.",
    ),
    (
        "Variant A / B",
        "Two versions of the agent. B must cite a chain from the change to the control before claiming AFFECTED.",
    ),
]

# (audience, question, answer)
FAQ = [
    (
        "Leadership",
        "Does the agentic path work?",
        "Yes. It runs end to end on Databricks with gpt-oss-120b, and every step is logged. On the 18 held-out test cases, run once with code frozen, it recovered 113 of the 144 key controls the rules missed (78%; 95% interval 71–84%), against a 50% target, and 94% of its new recommendations were correct.",
    ),
    (
        "Leadership",
        "Can I trust the 78%?",
        "It is the final, pre-registered result: 18 test cases never used while building the agent, code frozen, variant chosen by a rule written before the A/B test, one run, every case reported. Limits: synthetic data, one run (repeat runs vary; see consistency), and the test cases were looked at during an earlier phase's diagnosis, though never by this agent.",
    ),
    (
        "Leadership",
        "Why do the figures differ (81.5%, 65%, 78%)?",
        "81.5% came from four cases used while fixing the agent, so it was optimistic. 65% came from eight unseen development cases, two of which (CHG-026, CHG-029) were hard misses. 78% is the held-out result over 18 cases and 144 key misses, the largest sample; its interval (71–84%) overlaps the development check's (51–77%). The figure to quote is 78%.",
    ),
    (
        "Leadership",
        "Does it add review work?",
        "Version A adds 406 review items beyond the rules baseline’s 64 (470 total). These are not 406 wrong findings: 262 are correct new recommendations, 18 are incorrect, and 126 are UNCERTAIN. Offline synthetic labels show 69 uncertain items are affected and 57 are unaffected. Without the detective these controls would still need checking, by tracing lineage gaps by hand or by missing them. In total, 331 additional items (81.5%) concern affected controls; 75 (18.5%) concern unaffected controls and come with evidence to clear them. Uncertain items do not count as recovered.",
    ),
    (
        "Leadership",
        "Is it ready for production?",
        "No. It is a proof of concept on a synthetic benchmark. Recovery passed on held-out cases, but run-to-run consistency (80% vs 95%) is not at target, and no practitioner has yet reviewed real findings.",
    ),
    (
        "Leadership",
        "What decisions are open?",
        "Whether to take the work further, and how: a practitioner review of held-out findings, work on stability, both, or stopping at the proof of concept. The stop line agreed in advance (held-out below 50%) was not reached.",
    ),
    (
        "Leadership",
        "Which targets were met?",
        "Recovery: met on held-out (78% vs 50%). Added review items: 331 of 406 are real impacts; 75 are not affected. Consistency: not met, 80% of 10 key-control pairs got the same decision in all five runs, against 95%.",
    ),
    (
        "Technical",
        "What model and infrastructure does it use?",
        "databricks-gpt-oss-120b through Databricks Model Serving, temperature 0. Runs are submitted as Databricks jobs on serverless compute and write results to a Unity Catalog volume; each run can resume after an interruption.",
    ),
    (
        "Technical",
        "How do you know the model never saw the answers?",
        "Labels are computed offline from the complete hidden graph and only used for scoring. The agent receives only the observable case (ticket, degraded lineage, control procedures). Tests check that hidden fields never appear in any prompt.",
    ),
    (
        "Technical",
        "What was broken in the first live run?",
        "The model returns reasoning and answer as separate blocks and the adapter discarded the answer, so 56 of 60 steps failed and nothing was recovered. Other fixes: accept the model's tool-call spellings, batch inspections and findings, recover findings from cut-off replies, give the verifier the change's neighbourhood, and run as jobs with resume.",
    ),
    (
        "Technical",
        "Why use a verifier?",
        "To protect precision. A second call checks each finding with the evidence; disagreement sends the control to a human instead of silently accepting or dropping it. On CHG-025 it correctly blocked several wrong cross-area claims.",
    ),
    (
        "Technical",
        "Can the agent invent controls, quotes or links?",
        "It cannot change anything: tools are read-only and no graph edges are written. Quotes must be exact substrings of the ticket and procedure or the finding is rejected. Invented control IDs are rejected by the tool.",
    ),
    (
        "Technical",
        "How consistent are the results?",
        "Recovery has been stable (the same 7 of 8 key controls in repeat runs), but precision and review volume vary (78% vs 90% precision on the same three cases). A five-run agreement figure is being measured against a 95% target.",
    ),
    (
        "Technical",
        "What is variant B?",
        "A stricter agent that must cite a chain from the changed item to the control before claiming AFFECTED. On the same eight cases it made no wrong flags (A: 8), but recovered 27 of 49 key misses (A: 32) and sent 86 controls to review (A: 82); avoidable items fell from 56 to 46, not the 30% the rule required. By the rule registered in advance, variant A went to the held-out run.",
    ),
    (
        "Technical",
        "Why is consistency below target?",
        "Three cases were run five times. Recovery of key misses was stable (7 or 8 of 8 every run), but 2 of the 10 affected key-control pairs flipped between recommended and not recommended, giving 80% against 95%. The volume of UNCERTAIN items varied most (CHG-025: 6 to 36). The model runs at temperature 0 but retries at 0.3, and the investigation path differs between runs. A majority vote over three runs is the planned fix.",
    ),
    (
        "Leadership",
        "Which expectations are met and which are not?",
        "Met: the agentic path runs end to end; it finds 78.5% of the key controls the rules miss on held-out cases (target 50%) with 94% precision; review noise can be cut to 0.3 unnecessary items per change with version C. Not met: consistency (80% for one run, 94.4% for a 3-run vote, target 95%). Not yet: practitioner review and production readiness.",
    ),
    (
        "Technical",
        "What did version C change, and why was it not adopted?",
        "Version C adds a coverage sweep, a second look at key controls marked unaffected, and a tie-break call when agent and checker disagree; three runs are combined by majority vote. On fresh-damage cases it met the recovery rule (52.7% vs 50.0%) and the review-volume rule (0.33 vs 0.61 unnecessary items per change), but two independent votes agreed on 94.4% of key controls, one short of the 95% target. The rule required all three, so version A stays.",
    ),
    (
        "Leadership",
        "Which version is final, and why?",
        "Version A, the one that passed the held-out test (78.5%). Three improvement attempts were tested against rules written in advance and none met all of them: B (stricter evidence) lost recall; C (tie-break, coverage sweep and a 3-run vote) cut review noise but repeat votes agreed on 94.4% against 95%; D (A plus the tie-break only) halved unaffected review items but recovered 18 instead of 20 of 32 key controls. Run-to-run noise is larger than these differences, so A stays.",
    ),
    (
        "Technical",
        "How realistic is the benchmark?",
        "It models one fictional bank's outbound cross-border payment flow with 148 nodes, 101 controls and 54 changes. Generated controls come in families that share dependencies, which may make some links easier than in a real inventory. A practitioner review is planned.",
    ),
    (
        "Technical",
        "How do I reproduce a result?",
        "See the Technical appendix: each result names its job, commit and command, and the runner can replay a saved transcript exactly.",
    ),
    (
        "Controls",
        "What does 'affected' mean here?",
        "A control is affected when the changed item reaches it through a dependency path in the complete map (for example a field used by a rule that a control relies on). It means the control should be reassessed, re-evidenced or re-tested.",
    ),
    (
        "Controls",
        "Why would a field mapping affect a sanctions control?",
        "Because screening uses party data. In CHG-001, the debtor town name feeds the screening field-set rule, which feeds the screening request interface and the screening engine that the sanctions control governs.",
    ),
    (
        "Controls",
        "Does this replace the control owner's judgement?",
        "No. It proposes controls with quoted evidence and sends disagreements to a person. The output is a review list with reasons, not an approval.",
    ),
    (
        "Controls",
        "What happens to controls the agent says are unaffected?",
        "They are recorded with a reason but not double-checked yet. That gap explains some misses (CHG-029); verifying 'unaffected' decisions on key controls is a planned fix.",
    ),
    (
        "Controls",
        "What is a key control?",
        "One the bank relies on most for a risk; 30 of the 101 controls here. The main metric counts only key controls the rules missed.",
    ),
]

LIMITS = [
    (
        "Steadier decisions run to run",
        "Five runs of three changes: 80% of key-control decisions identical every time, against a 95% target.",
        "A three-run vote reached 94.4%; next, a five-run vote on new changes.",
    ),
    (
        "A second look at 'not affected'",
        "Controls marked not affected are not re-checked; the one silent miss (CHG-024) came from there.",
        "An independent check of not-affected decisions on key controls.",
    ),
    (
        "Proof on real changes",
        "Scored on a synthetic bank built so the right answer is known.",
        "Control owners judge a sample of real output, including what it left out.",
    ),
]

REPRO = """
| Result | Job / folder | Code |
|---|---|---|
| Tuned cases (4) | suite-08 / suite-09 (earlier workspace) | 9a16f02, 6be2cab |
| Frozen check, 8 unseen cases | `suite-10`, job 211771677628591 | 799189a (variant A) |
| A/B, variant B | `suite-12`, job 663596150833963 | 67bd813 (variant B) |
| Consistency, 3 cases × 5 | `suite-11`, job 189647926488694 | 43457ab |
| Held-out, 18 cases | `heldout-final`, job 862812162377923 | agent code d149a52, variant A |

```bash
# from the repository folder in Databricks
python -m scripts.detective_job submit --repo /Workspace/Users/<you>/payments-control-impact \\
    --change-ids CHG-001 --variant A \\
    --output-dir /Volumes/workspace/default/detective_runs/<run-name>
python -m scripts.detective_job status <run_id>
python -m scripts.inspect_detective_run /Volumes/workspace/default/detective_runs/<run-name>/run1/CHG-001.json
python -m pytest -q   # offline tests, no credentials
```

Repository: https://github.com/AnaghaDhekne/payments-control-impact (docs/results.md holds every pre-registered plan and result).
"""
