> Historical Phase 1 document. Assumptions and plans may be superseded. Start with [the current README](../../README.md).

# Payments Control Impact — Complete Project Reference

A one-stop guide for everyone — technical and non-technical readers alike.

---

## 1. What Problem Does This Project Solve?

Payment systems rely on dozens of **controls** — think of them as security checkpoints on an assembly line. One validates sender details. Another screens for sanctioned entities. Another verifies payment authorization. Another reconciles settled money against the ledger.

When an engineer makes a change to the payment platform (updates a field mapping, changes a validation rule, modifies a threshold), a critical question arises: **which of these controls might be impacted?** Missing one could mean a compliance failure, financial loss, or regulatory finding.

Today, reviewers rely on a **dependency map** (metadata) showing which system components connect to which controls. But this metadata is often incomplete or outdated — connections go missing, and controls that should have been flagged slip through unnoticed.

This project benchmarks two approaches:

| Approach | How It Works | Strength | Weakness |
| --- | --- | --- | --- |
| **Baseline** (metadata-only) | Walks the dependency graph from the changed component outward, flagging reachable controls | Fast, deterministic, no AI needed | Goes blind when metadata is degraded |
| **Hybrid** (metadata + AI) | After the baseline runs, sends candidate control documents to an LLM to recover missed controls using narrative evidence | Recovers controls the baseline misses | Costs more reviewer workload, depends on LLM availability |

---

## 2. The Payment Control Graph

### 2.1 The 10 Control Families

The payment system is modeled as a graph with nodes (components) and edges (relationships). Controls are grouped into 10 families, each representing a distinct area of payment operations:

| # | Family | Seed Control | Full Name | Criticality |
| --- | --- | --- | --- | --- |
| 1 | Validation | C01 | Required-field validation | KEY |
| 2 | Screening | C02 | Sanctions screening execution | KEY |
| 3 | Screening Review | C03 | Sanctions alert review | KEY |
| 4 | Authorization | C04 | Required payment authorization | KEY |
| 5 | Auth Monitor | C05 | Authorization exception monitoring | STANDARD |
| 6 | Mapping | C06 | Outbound transformation completeness | KEY |
| 7 | Repair | C07 | Reject and repair review | STANDARD |
| 8 | Reconciliation | C08 | Settlement and ledger reconciliation | KEY |
| 9 | Break Review | C09 | Aged reconciliation-break review | STANDARD |
| 10 | Reporting | C10 | Operational report completeness review | STANDARD |

**Criticality levels:**
- **KEY** — most critical; missing an impact here is a serious compliance risk
- **STANDARD** — important but not top-priority
- **SUPPORTING** — auxiliary; lowest impact risk

### 2.2 The 101 Controls

The graph contains **101 controls** total:

- **11 seed controls** (C01–C11): manually defined in the seed graph with real-sounding names and relationships
- **90 generated controls** (C012–C101): deterministically generated, 9 per family

#### How the 90 Generated Controls Are Created

Each family gets 9 additional controls. Each generated control connects to **two anchor nodes** — a primary anchor (like a system or evidence document) and an alternate anchor (like a rule or report). This dual-anchor design ensures each control has two distinct dependency paths, making the graph realistic for impact analysis.

| Family | Primary Anchor | Relationship | Alternate Anchor | Relationship |
| --- | --- | --- | --- | --- |
| Validation | S02 (system) | GOVERNED\_BY | R01 (rule) | DEPENDS\_ON |
| Screening | S03 (system) | GOVERNED\_BY | R03 (rule) | DEPENDS\_ON |
| Screening Review | E01 (evidence) | EVIDENCES | RP01 (report) | DEPENDS\_ON |
| Authorization | S05 (system) | GOVERNED\_BY | R02 (rule) | DEPENDS\_ON |
| Auth Monitor | E04 (evidence) | EVIDENCES | RP04 (report) | DEPENDS\_ON |
| Mapping | S06 (system) | GOVERNED\_BY | R04 (rule) | DEPENDS\_ON |
| Repair | E02 (evidence) | EVIDENCES | RP02 (report) | DEPENDS\_ON |
| Reconciliation | E03 (evidence) | EVIDENCES | RP03 (report) | DEPENDS\_ON |
| Break Review | E03 (evidence) | EVIDENCES | RP03 (report) | DEPENDS\_ON |
| Reporting | S08 (system) | GOVERNED\_BY | I04 (interface) | DEPENDS\_ON |

#### Criticality Pattern for Generated Controls

Within each family's 9 generated controls:

- First 4: same criticality as the seed (e.g., KEY for screening)
- Next 4: STANDARD
- Last 1: SUPPORTING

#### Qualifiers for Realism

Each generated control gets a descriptive qualifier to simulate real-world variation:

"daily completeness", "high-risk corridor", "priority payment", "manual override", "after-hours processing", "currency-specific", "high-value transaction", "repair queue", "weekend processing", "release monitoring"

**Example generated control:**
> C012 | KEY | Sanctions screening execution — daily completeness | Synthetic daily completeness control in the screening family.

### 2.3 Node Types in the Graph

The graph contains several types of nodes beyond controls:

| Node Type | Prefix | Examples | Purpose |
| --- | --- | --- | --- |
| CONTROL | C | C01, C012 | The controls being assessed for impact |
| DOMAIN | D | D03, D04 | Business domains (debtor data, creditor data) |
| RULE | R | R01, R03 | Business rules (validation, screening, thresholds) |
| SYSTEM | S | S03, S06 | Technical systems (screening engine, transformation service) |
| INTERFACE | I | I02, I03 | External interfaces (screening, network, settlement) |
| EVIDENCE | E | E01, E04 | Evidence artifacts (test results, audit evidence) |
| REPORT | RP | RP01, RP03 | Operational reports (exception, reconciliation) |

### 2.4 Edge Relationships

Edges represent how nodes depend on each other. Only certain relationships propagate changes:

| Relationship | Propagates? | Meaning |
| --- | --- | --- |
| USES | Yes | Node A uses node B |
| PRODUCES | Yes | Node A produces output for B |
| FEEDS | Yes | Node A feeds data to B |
| TRANSFORMS | Yes | Node A transforms data for B |
| VALIDATES | Yes | Node A validates something about B |
| SCREENS | Yes | Node A screens against B |
| GOVERNED\_BY | Yes | Node A is governed by control B |
| DEPENDS\_ON | Yes | Node A depends on B |
| EVIDENCES | Yes | Node A provides evidence for B |
| COMPENSATED\_BY | **No** | Compensating control link — contextual, not propagating |

---

## 3. The 54 Change Scenarios

### 3.1 The 18 Change Templates

Each template represents a realistic payment platform change:

| # | Changed Node | Change Type | Description |
| --- | --- | --- | --- |
| 1 | D03 | FIELD\_MAPPING | Debtor town-name mapping change |
| 2 | D04 | FIELD\_MAPPING | Debtor country-code mapping change |
| 3 | D07 | FIELD\_MAPPING | Creditor town-name mapping change |
| 4 | D08 | FIELD\_MAPPING | Creditor country-code mapping change |
| 5 | R01 | VALIDATION\_RULE | Structured-address validation rule change |
| 6 | R03 | SCREENING\_FIELD\_SET | Screening field-set change |
| 7 | R04 | MESSAGE\_MAPPING | Outbound message mapping change |
| 8 | R02 | PARAMETER\_CHANGE | High-value approval threshold change |
| 9 | I02 | INTERFACE\_CHANGE | Screening interface change |
| 10 | I03 | INTERFACE\_CHANGE | Outbound network interface change |
| 11 | RP01 | REPORT\_CHANGE | Screening exception report change |
| 12 | RP02 | REPORT\_CHANGE | Payment reject report change |
| 13 | RP03 | REPORT\_CHANGE | Reconciliation report change |
| 14 | RP04 | REPORT\_CHANGE | Authorization exception report change |
| 15 | S03 | SYSTEM\_CHANGE | Screening engine change |
| 16 | S06 | SYSTEM\_CHANGE | Transformation service change |
| 17 | I04 | INTERFACE\_CHANGE | Settlement-status feed change |
| 18 | I05 | INTERFACE\_CHANGE | Ledger-posting feed change |

### 3.2 The 3 Release Cycles

Each template is instantiated 3 times (once per release) to simulate recurring changes over time:

| Release | Implementation Date | Example Change ID |
| --- | --- | --- |
| R1 | 2026-11-14 | CHG-001: "Debtor town-name mapping change — release 1" |
| R2 | 2026-12-01 | CHG-019: "Debtor town-name mapping change — release 2" |
| R3 | 2027-01-15 | CHG-037: "Debtor town-name mapping change — release 3" |

**Total: 18 templates × 3 releases = 54 changes**

### 3.3 Train/Test Split

Changes are divided so the system can be developed on one set and evaluated on a held-out set:

- **Development split:** 36 changes (2 out of every 3) — used for building and tuning
- **Test split:** 18 changes (1 out of every 3) — held out for final, unbiased evaluation

The split is deterministic: every 3rd change (CHG-003, CHG-006, CHG-009, ...) goes to test.

---

## 4. Ground Truth — How We Know Which Controls Are Affected

Ground truth is the **answer key**. It's computed using the complete, hidden graph (with all edges intact) and is never shared with the baseline or LLM.

### 4.1 How It Works (Step by Step)

1. Start from the changed node (e.g., D08 — creditor country-code mapping)
2. Traverse outward through propagating relationships (USES, FEEDS, GOVERNED\_BY, etc.) up to 6 hops
3. Every CONTROL node reached is marked **affected**
4. For each affected control, determine required actions

### 4.2 The Three Action Rules

| Rule ID | Action | When It Applies |
| --- | --- | --- |
| GT-A1-DESIGN | REASSESS\_DESIGN | The path from change to control does NOT pass through an evidence node — this is a direct design/input dependency |
| GT-A2-EVIDENCE | REFRESH\_EVIDENCE | The path passes through an evidence or report node — the evidence itself needs updating |
| GT-A3-PERIOD | OUT\_OF\_CYCLE\_TEST | The control is KEY, the change is material, and implementation falls within the test period (2026-10-01 to 2027-03-31) |

### 4.3 Compensating Controls

A `COMPENSATED_BY` edge does **not** propagate impact. Just because control A compensates for control B doesn't mean every change to B affects A. This prevents false positives from compensating links.

---

## 5. Degradation — Simulating Real-World Metadata Problems

In the real world, the dependency graph is rarely complete. Edges go missing, descriptions become stale, and sometimes tickets contain misleading information. This project simulates these problems with a **degradation engine**.

### 5.1 Edge Removal (Structural Degradation)

| Level | Meaning | What Happens |
| --- | --- | --- |
| 0% | Perfect metadata | All edges visible — no degradation |
| 30% | Moderate loss | ~30% of exposable edges removed |
| 60% | Severe loss | ~60% of exposable edges removed |

Two **patterns** of edge removal:

| Mode | How It Works | Real-World Analogy |
| --- | --- | --- |
| **Random** | Removes edges uniformly across the entire graph | General data quality decay — equally bad everywhere |
| **Correlated** | Removes edges preferentially near the changed node, but always preserves at least one connection to the changed node | Locally stale lineage — the neighborhood around a change is often worst-documented |

The correlated mode includes a **local frontier guard**: it never removes all edges touching the changed node, ensuring the changed node isn't completely isolated. This models realistic incomplete lineage rather than total disconnection.

### 5.2 Text Degradation (Narrative Degradation)

Beyond edge removal, text descriptions are also degraded:

| Degradation | What It Does | Example |
| --- | --- | --- |
| **Legacy alias** | Prepends an outdated term to simulate stale terminology | "Legacy reference: PaymentValidationv2. Required-field validation..." |
| **Sentence omission** | Drops the last sentence from descriptions | Loses context that might help the LLM |
| **Misleading N/A** | Appends "Ticket assessment: control impact: N/A" to some tickets (1 in 7) | Simulates a human reviewer incorrectly marking a change as no-impact |

### 5.3 The Six Conditions

Combining 3 levels × 2 modes gives 6 test conditions:

| Condition | Level | Mode | What It Simulates |
| --- | --- | --- | --- |
| 1 | 0% | Random | Perfect metadata, uniform (baseline/best case) |
| 2 | 0% | Correlated | Perfect metadata, biased (same as above at 0%) |
| 3 | 30% | Random | Moderate uniform data loss |
| 4 | 30% | Correlated | Moderate loss concentrated near the change |
| 5 | 60% | Random | Severe uniform data loss |
| 6 | 60% | Correlated | Severe loss concentrated near the change |

---

## 6. The Baseline Approach (Metadata-Only)

### How It Works

1. Takes the **degraded** observable graph (with edges removed)
2. Starts from the changed node mentioned in the change ticket
3. Performs a breadth-first search through visible edges (propagating relationships only)
4. Every CONTROL node reached is "recommended" for review
5. Results are sorted by: distance (closer = higher priority), then criticality (KEY first), then control ID

### What It Sees

- The degraded graph nodes and edges (structural metadata)
- The change ticket (title, text, changed entity IDs)
- Control criticality labels

### What It Does NOT See

- The hidden complete graph (ground truth)
- Ground truth labels (which controls are actually affected)
- Narrative control documents (text descriptions) — these are reserved for the hybrid approach

### Limitations

At 0% degradation, the baseline finds 100% of affected key controls. But as degradation increases:
- At 30% random: key control recall drops to ~43%, missing 93 key-control pairs
- At 60%: even worse (results pending from the matrix evaluation)

---

## 7. The Hybrid Approach (Metadata + LLM)

### How It Works (Step by Step)

1. **Run the baseline** on the degraded graph to get initial control recommendations
2. **Retrieve candidate documents** — rank all control documents by text similarity to the change ticket (using token overlap), take the top 20 (or `top_k`)
3. **Build a prompt** containing:
   - System instructions (return JSON, specific fields, don't invent IDs, prefer UNCERTAIN when ambiguous)
   - The change ticket (title and text)
   - The baseline's recommended control IDs
   - The top 20 candidate control documents (ID, criticality, title, description)
4. **Send the prompt** to the LLM (`databricks-llama-4-maverick` at temperature 0 for determinism)
5. **Parse the response** — extract valid JSON recommendations, filter to only allowed control IDs, validate decisions and actions
6. **Merge** — combine the baseline's recommendations with the LLM's. Any control the LLM flags that the baseline missed is **added** to the final set
7. **Handle failures** — if the LLM response can't be parsed, the baseline result stands alone (no crash, graceful fallback)

### What the LLM Receives

The LLM is sent a single text prompt containing:

```
System instructions (return JSON, fields, rules)

CHANGE TICKET
[change title]
[change description text]

BASELINE IDS
[sorted list of control IDs the baseline already flagged]

CANDIDATES
- C01 | KEY | Required-field validation | [control description text]
- C02 | KEY | Sanctions screening execution | [control description text]
... (up to 20 candidates)
```

### What the LLM Returns

The LLM must return JSON with a `recommendations` array. Each item:

| Field | Required Values | Purpose |
| --- | --- | --- |
| control\_id | Must be one of the allowed candidate IDs | Which control is being assessed |
| decision | AFFECTED, UNAFFECTED, or UNCERTAIN | The LLM's impact assessment |
| actions | Any of: REASSESS\_DESIGN, REFRESH\_EVIDENCE, OUT\_OF\_CYCLE\_TEST, CONTROL\_GAP\_REVIEW | What should be done about it |
| confidence | Number 0-1 or LOW/MEDIUM/HIGH | How confident the LLM is |
| reason | Free text (max 1000 chars) | Why the LLM made this assessment |

### Response Validation

The parser enforces strict rules:
- Only control IDs from the allowed candidate set are accepted (no hallucinated IDs)
- Only valid decisions and actions are kept (invalid ones silently dropped)
- Confidence is normalized (LOW=0.33, MEDIUM=0.67, HIGH=1.0)
- Fenced JSON (```json ... ```) is automatically unwrapped
- If the response isn't valid JSON, it tries to find the first JSON object/array substring
- If that fails too, a ValueError is raised and the baseline result stands alone

---

## 8. Evaluation Metrics

### 8.1 Baseline Metrics

| Metric | Plain English |
| --- | --- |
| affected\_pairs | Total control-change pairs that should have been flagged |
| reachable\_affected\_pairs | How many the baseline actually caught |
| affected\_recall | Percentage of truly affected controls caught |
| key\_control\_pairs | Total **critical** control-change pairs that should have been flagged |
| reachable\_key\_control\_pairs | How many critical ones the baseline caught |
| key\_control\_recall | Percentage of critical controls caught |
| reviewer\_workload | Total controls the baseline asked reviewers to check |
| unreachable\_key\_control\_pairs | Critical controls completely missed |

### 8.2 Hybrid Metrics

| Metric | Plain English |
| --- | --- |
| baseline\_key\_hits | Key controls the baseline found (before LLM) |
| final\_key\_hits | Key controls found after merging baseline + LLM |
| baseline\_key\_misses | Key controls the baseline missed |
| recovered\_key\_misses | Of those misses, how many the LLM recovered |
| key\_miss\_recovery\_rate | Percentage of missed key controls the LLM recovered |
| final\_key\_recall | Final percentage of key controls found |
| final\_affected\_recall | Final percentage of all affected controls found |
| baseline\_workload | Controls the baseline alone would recommend |
| final\_workload | Controls recommended after adding LLM results |
| workload\_increase\_rate | How much extra work the LLM adds (as a percentage) |
| parse\_failure\_count | How many LLM responses couldn't be parsed |
| repeated\_run\_agreement | Run-to-run consistency (1.0 = perfectly deterministic) |

### 8.3 Go/No-Go Criteria

From the runbook, the hybrid approach passes if:

- Key miss recovery rate ≥ 40% (the LLM recovers at least 40% of what the baseline missed)
- Workload increase rate < 100% (the LLM doesn't double the reviewer's workload)
- Repeated run agreement = 1.0 (perfectly deterministic at temperature 0)
- Zero parse failures (all LLM responses are valid JSON)

---

## 9. Project Structure

```
payments-control-impact/
├── scripts/                    Core logic
│   ├── generate_benchmark.py  Builds the 101-control graph and 54 changes
│   ├── ground_truth.py        Computes the answer key (which controls are affected)
│   ├── generate_observable.py  Creates degraded views + text degradation
│   ├── baseline.py            Metadata-only ranking using graph traversal
│   ├── evaluate_baseline.py   Scores the baseline against ground truth
│   ├── hybrid.py              LLM prompt building, response parsing, merging
│   ├── evaluate_hybrid.py     Scores the hybrid approach against ground truth
│   ├── databricks_llm.py      Adapter for Databricks model serving endpoint
│   └── validate_graph.py      Validates graph structural integrity
├── tests/                     29 pytest tests covering all components
│   ├── test_benchmark_generation.py
│   ├── test_observable_generation.py
│   ├── test_ground_truth.py
│   ├── test_graph_integrity.py
│   ├── test_baseline.py
│   ├── test_hybrid.py
│   ├── test_hybrid_evaluator.py
│   └── test_model_response_contract.py
├── data/
│   └── ground_truth/          Seed graph, benchmark graph, benchmark changes
├── output/                    Results and evidence artifacts
│   ├── baseline_results.json
│   ├── hybrid_matrix.json
│   └── endpoints.txt           Available Databricks model endpoints
├── docs/                      Documentation
│   ├── runbook.md              Kill criteria and go/no-go thresholds
│   ├── domain_model.md         Payment domain description
│   ├── benchmark_generation.md How the graph is built
│   ├── observable_benchmark.md How degradation works
│   ├── ground_truth_rules.md  How impact labels are computed
│   ├── rules_baseline.md       How the baseline works
│   ├── hybrid_evaluation.md   How the hybrid is evaluated
│   └── evaluation_contract.md Metric definitions and contracts
└── .github/                   CI workflow
```

---

## 10. Databricks Integration

### Model Endpoint

The LLM calls use the Databricks SDK's `serving_endpoints.query()` API:

- **Model:** `databricks-llama-4-maverick`
- **Temperature:** 0.0 (for perfect reproducibility)
- **Max tokens:** 3000
- **Available models** (from `output/endpoints.txt`):
  - databricks-gpt-oss-120b
  - databricks-gpt-oss-20b
  - databricks-qwen3-next-80b-a3b-instruct
  - databricks-qwen35-122b-a10b
  - databricks-llama-4-maverick
  - databricks-gemma-3-12b
  - databricks-meta-llama-3-1-8b-instruct
  - databricks-meta-llama-3-3-70b-instruct
  - databricks-deepseek-v4-flash-0731

### Reproducibility

Everything is deterministic:
- Graph generation uses a fixed seed (20261007)
- Change generation uses the same seed
- Edge degradation uses per-change deterministic seeds
- Text degradation uses per-change, per-control deterministic seeds
- The LLM runs at temperature 0.0
- Three repeated runs produce identical decisions (agreement = 1.0)

---

## 11. Key Results So Far

### Baseline Performance

| Level | Mode | Key Control Recall | Affected Recall | Missed Key Pairs |
| --- | --- | --- | --- | --- |
| 0% | random | 100% | 100% | 0 |
| 0% | correlated | 100% | 100% | 0 |
| 30% | random | 43% | 47% | 93 |
| 30% | correlated | (pending) | | |
| 60% | random | (pending) | | |
| 60% | correlated | (pending) | | | |

### Hybrid Performance (Partial)

| Level | Mode | Baseline Key Recall | Hybrid Key Recall | Recovery Rate | Workload Increase | Run Agreement |
| --- | --- | --- | --- | --- | --- | --- |
| 0% | random | 100% | 100% | 0% (nothing to fix) | 0% | 1.0 |
| 0% | correlated | 100% | 100% | 0% | 0% | 1.0 |
| 30% | random | 35% | 63% | 43% | +89% | 1.0 |
| 30% | correlated | (pending) | | | | |
| 60% | random | (pending) | | | | |
| 60% | correlated | (pending) | | | | |

### Key Takeaways

1. **When metadata is perfect, the LLM adds nothing** — the baseline already finds everything, and the LLM correctly doesn't override or add noise.
2. **When metadata is degraded, the LLM recovers meaningful signal** — at 30% random loss, the LLM recovers 43% of missed key controls, boosting recall from 35% to 63%.
3. **The cost is more reviewer work** — the hybrid recommends ~89% more controls than the baseline alone (a tradeoff between coverage and false positives).
4. **It's perfectly deterministic** — three runs produce identical decisions, which is essential for audit and compliance.
5. **Zero parse failures** — every LLM response was valid JSON across all calls so far.

---

## 12. Glossary

| Term | Definition |
| --- | --- |
| **Control** | A checkpoint in the payment system that verifies, screens, or reconciles something |
| **Key control** | A control with the highest criticality — missing its impact is a serious compliance risk |
| **Change scenario** | A simulated modification to the payment platform (e.g., field mapping, validation rule) |
| **Degradation** | Simulated loss of metadata (removed graph edges, degraded text) to test robustness |
| **Baseline** | The metadata-only approach — uses graph distance to find impacted controls |
| **Hybrid** | The metadata + LLM approach — combines baseline with AI narrative analysis |
| **Ground truth** | The hidden answer key — which controls are actually affected (computed from the complete graph) |
| **Recall** | The percentage of truly affected controls that were correctly flagged |
| **Recovery rate** | Of the controls the baseline missed, the percentage the LLM successfully recovered |
| **Workload increase** | How many extra controls the hybrid recommends vs. the baseline alone |
| **Repeated run agreement** | Whether running the system 3 times produces identical results (1.0 = perfect) |
| **Parse failure** | When the LLM's response couldn't be understood as valid JSON |
| **Propagating relationship** | A graph edge type that transmits impact (e.g., DEPENDS\_ON, GOVERNED\_BY) |
| **Compensating control** | A control that backs up another — but its link doesn't propagate impact |
| **Local frontier guard** | A safeguard ensuring the changed node isn't completely isolated during correlated degradation |
| **Development split** | The 36 changes used for building and tuning the system |
| **Test split** | The 18 held-out changes used for final, unbiased evaluation |
