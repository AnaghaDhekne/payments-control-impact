# Simulated Human Review Study — Results

**Date:** 2026-10-13
**Method:** LLM-as-reviewer (GPT OSS 120B, blinded — sees only observable evidence)
**Scope:** 91 filtered proposals from 18 held-out test cases

## Key Findings

The simulated review reveals a **major gap** between oracle-adjudicated and
review-based evaluation:

| Metric | Oracle Adjudication | Simulated Review |
| --- | --- | --- |
| Recovery | 57.6% | **5.6%** |
| Precision | 91.2% | **27.3%** |
| False positives | 8 | 8 |
| False negatives | 0 | **15** |
| UNCERTAIN burden | 0% | 13.2% |

**Both gates FAIL after simulated review** (recovery 5.6% < 50%, precision 27.3% < 80%).

## What Happened

1. **Reviewer too conservative:** Rejected 74.7% of proposals, approved only 12.1%.
2. **15 false negatives:** Correct edges rejected — these are key controls the AI
   correctly identified but the reviewer rejected. In production, these would be
   missed controls (a safety issue).
3. **8 false positives:** Incorrect edges approved — the reviewer couldn't distinguish
   correct from incorrect edges based on observable evidence alone.
4. **12 UNCERTAIN:** 13.2% of proposals were ambiguous, adding review burden.

## Interpretation

The oracle-adjudicated results (91.2% precision, 57.6% recovery) represent an
**upper bound**. The simulated review shows that when the same evidence is
evaluated independently:

- Precision drops from 91.2% to 27.3% — the reviewer approves many wrong edges
- Recovery drops from 57.6% to 5.6% — the reviewer rejects most correct edges
- The system's evidence is often **indirect or circumstantial** — the ticket text
  doesn't explicitly mention the control, making it hard for a reviewer to confirm

## Limitations of This Study

1. **Same LLM as reviewer and proposer:** The GPT OSS 120B model both generated and
   reviewed the proposals. A human expert with payment compliance domain knowledge
   may perform very differently.
2. **Simulated, not real:** This is a simulated review, not a human review. Real
   reviewers may have higher domain expertise, better evidence interpretation, and
   different decision thresholds.
3. **Review prompt may be too strict:** The prompt asks "Does the ticket evidence
   support this edge?" which sets a high bar. A more nuanced prompt might ask about
   likelihood rather than certainty.
4. **No calibration:** The reviewer had no training examples or calibration — real
   review processes include calibration sessions.

## Recommendation

1. **Do NOT deploy without real human review.** The oracle results are optimistic;
   the simulated review shows the system is not ready for unsupervised use.
2. **Improve evidence quality:** The AI needs to provide stronger, more explicit
   evidence for each proposed edge — not just quotes but clear causal reasoning.
3. **Calibrate review thresholds:** A multi-tier review process (AI proposes →
   junior reviewer screens → senior reviewer approves KEY controls) may be more
   effective than single-pass review.
4. **Address false negatives:** The 15 rejected-correct edges represent missed key
   controls. The system needs to surface stronger evidence for indirect relationships.
5. **Conduct real human review:** This simulated study is a lower bound on review
   performance. Real human reviewers with domain expertise are essential.

## Review Metrics

- Total reviews: 91
- APPROVE: 11 (12.1%)
- REJECT: 68 (74.7%)
- UNCERTAIN: 12 (13.2%)
- Average review time: 2.6s per edge (simulated)
- Overall accuracy: 61.5% (correct APPROVE + correct REJECT)
- High-confidence reviews: 31 (8 approved, 2 correct)
- Medium-confidence reviews: 60 (3 approved, 1 correct)
