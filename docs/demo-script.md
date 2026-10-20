# Executive demo script (6–7 minutes)

Navigation: one header on every page (Home, Walkthrough, Product overview,
Evidence room); the step bar (the test bank, then five steps), the **Next** button and the case selector appear only
inside the walkthrough. Every figure below is checked against
the running app by `tests/test_demo_claims.py`; if a sentence here changes,
change that test too.

Before the meeting: open the app, check the footer shows job 862812162377923
(2026-10-16), and keep the evidence room in a second tab for questions.

| Time | Screen | Do | Say |
|---|---|---|---|
| 0:00–0:40 | Landing page | Point to the change record on the right | "Banks protect payments with safety checks, called controls. Here is one change from our test bank, a screening-interface change. The existing lineage check flags no controls for review. What might it have missed?" Say once that the bank and data are synthetic. |
| 0:40–1:10 | The test bank, then 1 The change | Click **Walkthrough** in the header: it opens on *The test bank*. Then press **Next** (top right) from step to step | "The test bank has 148 items and 101 controls, and every item carries a code. On this change, the impact check finds nothing to review. It follows the lineage map from the changed item, the screening request interface, to the controls that depend on it." |
| 1:10–2:10 | 2 The blind spot | Paths view (default): first *What the lineage records* ("The map ends here"), then *What is actually connected* | "0 of 20 affected controls are reachable, because 13 of the 24 links on the way are missing from the map. Take the sanctions-screening control: the map records the link from the screening request interface to the Screening Engine, but the link from the Screening Engine to the control is missing, so the check never puts it in front of its owner." Read the "Why it matters to the bank" line. |
| 2:10–3:20 | 3 The investigation | Press Play (or › a step at a time), then *Show result*; click C02 | "This is a recording of the agent's own steps. For C02 it quotes the request, 'Screening request interface', and the procedure, 'screened before payment release'. The panel opens with why it landed here, then three separate questions: is the evidence in the documents, does it support the impact, is the outcome right. The second review agreed; one link was worked out by the AI rather than on record, and the owner still decides." Optionally *Reveal the answer key*. |
| 3:20–4:40 | 4 The consequence | Read the headline; hover the squares | "On this change the existing lineage check flagged nothing; the detective recommended the affected controls it missed, each with quoted evidence. Three views of the same 101 controls show the difference." |
| 4:40–5:10 | Case selector | Switch to CHG-015 (screening engine change) | "Here the existing lineage check already flags 7 controls; the detective recommends 3 more and sends 10 to a person. It adds less where lineage is better, and it says when it is unsure." |
| 5:10–6:30 | 5 The decision, then **Next: Product overview** | Read the 18-change summary and click the silent miss, then walk the boxes and the validation card | "Across 18 changes the detective had never seen, it recommended 113 of the 144 key-control impacts the check missed: 78.5%, with a 95% range of 71.1–84.4%. 262 of its 280 new recommendations were right. 30 more went to a person and 1 was not surfaced: C03 on CHG-024, and the planned fix is a second check on key controls marked not affected. Without it, these controls would still need checking, by hand or not at all, and a miss is the costly outcome: 331 of the 406 items it adds are real impacts, and the 75 others come with evidence to clear them. Next is steadier run-to-run decisions (8 of 10 identical over five runs, against 95%; the records are on Evaluation evidence)." If asked about simpler tools: earlier approaches reached 49.5% and 57.6%, on different sets. | Demonstrated on synthetic evidence; ready for control owners to judge. If leadership chooses a practitioner validation, it uses the recorded output: all 30 key controls sent to a person plus samples of the recommended and not-affected ones, judged by named control owners and signed off by a risk lead. Correctness is compared with the 93.6% measured here; the number of affected key controls found among the not-affected sample is expected to be none." End on: "The choice rests with leadership." Offer the one-page PDF. |

## Three likely questions

**Why not keyword search or better rules?** The rules are the existing lineage check:
it found 11.1% of affected key controls at this damage level (42.6% if the same links were removed at random). Earlier language approaches reached 49.5% (retrieval,
development set) and 57.6% (edge proposals, five runs combined); the detective
reached 78.5%. Sets and scoring differ, so it is a progression, not a league
table. A plain keyword baseline has not been run.

**The data is synthetic. Why would this transfer?** It may not, and we do not
claim it does. That is what the practitioner validation is for: real owners
judging real output, with criteria agreed in advance.

**What about the routed items and the miss?** Routed means sent to an owner
with evidence; nobody reviewed them in the proof of concept. The miss came
from an unchecked not-affected decision; checking those on key controls is a
condition before any pilot.
