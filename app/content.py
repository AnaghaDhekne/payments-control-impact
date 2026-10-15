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
        "Yes. It runs end to end on Databricks with gpt-oss-120b, and every step is logged. On eight cases it had never seen, with code frozen, it recovered 32 of the 49 key controls the rules missed (65%), against a 50% target.",
    ),
    (
        "Leadership",
        "Can I trust the 65%?",
        "It is the most defensible figure so far: the cases were never inspected while fixing the agent, the code was frozen at one commit, and the reading rule was written into the repository before the run. It is still synthetic data, one run, and eight cases; the held-out run on 18 untouched cases is the final check.",
    ),
    (
        "Leadership",
        "Why is it lower than the 81.5% shown earlier?",
        "81.5% came from four cases used while fixing the agent, so it was optimistic. A drop on unseen cases is expected; the result still clears the target.",
    ),
    (
        "Leadership",
        "What does it cost in reviewer effort?",
        "On the eight unseen cases, reviewers would see 169 items beyond the rules baseline: 79 correct new recommendations, 8 wrong ones and 82 sent for a human decision. About 7 items per case turn out to be unaffected. This is the main weakness.",
    ),
    (
        "Leadership",
        "Is it ready for production?",
        "No. It is a proof of concept on a synthetic benchmark. A pilot decision should wait for the held-out result, the consistency result and a practitioner review of real findings.",
    ),
    (
        "Leadership",
        "What decision is needed?",
        "Whether to continue to the held-out run and a practitioner review, which the current results support. If the held-out run falls below 50%, the recommendation becomes investing in lineage metadata instead.",
    ),
    (
        "Leadership",
        "Which targets were met?",
        "Recovery: met (65% vs 50%). Added review workload: not met (the target of 25% cannot be met on this benchmark by any method that recovers 50%, because correct recoveries count as workload; it is reported unchanged). Consistency over five runs: being measured.",
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
        "A stricter agent that must cite a chain from the changed item to the control before claiming AFFECTED. It is being compared with variant A on the same eight cases; it wins only if avoidable review items fall by at least 30% and recovery drops by no more than 3 of 49.",
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
        "Review burden",
        "82 items sent to human review across eight unseen cases; about 7 avoidable items per case.",
        "Variant B A/B test; verifier changes tested only on fresh cases.",
    ),
    (
        "Agent over-claims across functional areas",
        "CHG-025: message mapping flagged against reconciliation controls; the verifier withheld approval.",
        "Variant B requires a cited chain.",
    ),
    (
        "Verifier too strict on clear text links",
        "CHG-026: a threshold change vs 'payments exceeding configured thresholds' left in review.",
        "Let direct text evidence count as a chain.",
    ),
    (
        "Unaffected decisions are never re-checked",
        "CHG-029: two key family members marked unaffected, no second look.",
        "Verify unaffected decisions on key controls.",
    ),
    (
        "Run-to-run variation",
        "Same three cases: precision 78% in one run, 90% in the next.",
        "Five-run consistency measurement.",
    ),
    (
        "Synthetic benchmark",
        "Control families share dependencies by construction.",
        "Practitioner review of a sample of findings.",
    ),
]

REPRO = """
| Result | Job / folder | Code |
|---|---|---|
| Tuned cases (4) | suite-08 / suite-09 (earlier workspace) | 9a16f02, 6be2cab |
| Frozen check, 8 unseen cases | `suite-10`, job 211771677628591 | 799189a (variant A) |
| A/B, variant B | `suite-12`, job 663596150833963 | 67bd813 (variant B) |
| Consistency, 3 cases × 5 | `suite-11`, job 189647926488694 | 43457ab |
| Held-out, 18 cases | `heldout-final` | d149a52 or later, chosen variant |

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
