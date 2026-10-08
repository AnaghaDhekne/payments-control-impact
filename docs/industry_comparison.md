# Industry Comparison — Existing Systems for Control Impact Analysis

Date: 2026-10-08
Project: Payments Control Impact
Purpose: Position the project against existing industry systems and identify what is genuinely novel.

## 1. GRC Platforms with Change Impact Analysis

These are the closest commercial analogs to the baseline (graph-only) approach used in this project.

### ServiceNow GRC / Change Management [^1]

- **What it does**: Tracks configuration items (CIs) in a CMDB dependency graph. When a change is requested, runs dependency analysis to surface affected controls, downstream systems, and compliance obligations.
- **Closest analog to**: The baseline approach in this project — graph traversal only.
- **Limitations**: Assumes the CMDB is accurate and complete. When metadata is stale or missing, it silently misses affected controls. No LLM or narrative-reasoning component. No degradation testing.

### Archer Integrated Risk Management (RSA/Archer) [^2]

- **What it does**: Maps risks to controls and runs control impact assessments when business processes change.
- **Limitations**: Graph-based risk-control mapping is manual or rules-driven. No AI-assisted recovery from missing metadata. No handling of degraded lineage.

### SAP GRC (Access Control + Process Control) [^3]

- **What it does**: Maps SOX and financial controls to business processes. Assesses impact of process changes on control coverage.
- **Limitations**: Control-to-process mapping is manually configured, not graph-traversed. No LLM augmentation. No degradation simulation.

### IBM OpenPages [^4]

- **What it does**: Risk and compliance management with control assessments and regulatory change tracking.
- **Limitations**: Structured mapping, not graph-traversed + LLM-augmented. No narrative reasoning, no degradation testing.

## 2. Enterprise Architecture / Dependency Mapping Tools

### LeanIX [^5]

- **What it does**: Enterprise architecture graph — maps applications, business capabilities, and dependencies. Provides impact analysis when an application or capability changes.
- **Limitations**: Strong graph-based dependency analysis, but no LLM augmentation. No payment-specific control taxonomy. No degradation testing.

### Ardoq [^6]

- **What it does**: Similar to LeanIX — dependency graphs with change impact analysis.
- **Limitations**: Graph + structured metadata only. No narrative reasoning, no handling of degraded/stale metadata.

### SAP LeanIX / Signavio [^7]

- **What it does**: Process mining + dependency analysis. Can show which controls are affected when a process changes.
- **Limitations**: Process-graph-based. No LLM, no handling of degraded metadata.

## 3. Payment-Specific Control Systems

### SWIFT CSP (Cyber Security Programme) [^8]

- **What it does**: Defines a control framework for payment infrastructures. It is a standard, not an automated impact tool.
- **Limitations**: Defines controls but does not automate "which controls are affected by this change?" No graph traversal, no LLM.

### Payment Hub Platforms (Volante, Bottomline, ACI) [^9] [^10] [^11]

- **What they do**: Payment processing with built-in control checkpoints (validation, fraud screening, reconciliation).
- **Limitations**: Operational control execution, not change-level impact assessment. Do not analyze "if I change X, which controls break?"

### RegTech Platforms (Quantexa, ComplyAdvantage) [^12] [^13]

- **What they do**: AI/ML for AML, transaction monitoring, entity resolution.
- **Limitations**: Different domain — transaction-level screening, not change-level control impact. Do not use graph + LLM hybrid.

## 4. Software Engineering Change Impact Analysis

### CodeSee / Codealike [^14]

- **What they do**: Code dependency maps, impact analysis for code changes.
- **Limitations**: Source-code focused, not compliance controls. No payment domain, no LLM.

### Sonargraph / Structure101 [^15]

- **What they do**: Architecture dependency analysis, detect broken dependencies.
- **Limitations**: Software architecture only. No control taxonomy, no narrative reasoning.

### GitHub Copilot / PR Impact Bots [^16]

- **What they do**: LLM-assisted code review and impact prediction.
- **Limitations**: Uses LLMs for code changes, not control changes. No graph-based baseline + LLM hybrid.

## 5. Emerging AI-Enhanced Compliance Tools

### LogicGate Risk Cloud [^17]

- **What it does**: Workflow + risk mapping with some ML scoring.
- **Limitations**: Risk workflow automation, not control impact recovery from degraded metadata.

### Drata / Vanta [^18] [^19]

- **What they do**: Continuous compliance monitoring — automated evidence collection.
- **Limitations**: Controls monitoring, not change impact analysis. Do not ask "which controls are affected by this change?"

### OneTrust [^20]

- **What it does**: Privacy/GRC platform with some AI features.
- **Limitations**: Regulatory change management, not payment control impact.

### Workiva [^21]

- **What it does**: Compliance reporting with some ML.
- **Limitations**: Reporting and audit, not impact prediction.

## 6. Capability Comparison Matrix

| Capability | Industry Systems | This Project |
| --- | --- | --- |
| Graph-based control impact (metadata-only) | Common (ServiceNow, LeanIX, Archer) | Baseline approach |
| LLM-assisted recovery from degraded metadata | Not found in commercial GRC | Hybrid approach |
| Degradation simulation (random + correlated) | Not standard practice | 6-condition matrix |
| Text degradation (aliases, omissions, misleading N/A) | Not done | Part of benchmark |
| Pre-registered evaluation thresholds | Rare in commercial tools | 50% recovery, 25% workload, 95% agreement |
| Three-class output (AFFECTED / UNCERTAIN / UNAFFECTED) | Most systems are binary | Separate uncertain review queue |
| Run-to-run agreement as a gate | Not measured | Five-run agreement |
| Lineage repair vs. AI comparator | Not done | Experiment F in improvement plan |
| Per-control audit rows with confidence + evidence | Rare — most tools show "affected" without scoring | audit_rows in hybrid output |
| Development/test split with frozen procedure | Not done in commercial tools | Development first, then held-out test |

## 7. What This Project Does That No Industry System Does

### 7.1 LLM-assisted recovery from degraded metadata

No commercial GRC tool uses an LLM to read control documentation and recover controls that the dependency graph missed due to stale or incomplete metadata. ServiceNow, Archer, and LeanIX all assume the graph is accurate. This project explicitly models and tests the scenario where it is not, and adds LLM narrative reasoning to recover missed controls.

### 7.2 Dual-mode degradation framework

No commercial system simulates metadata degradation (both random and correlated with local frontier guard) to test robustness. This project models real-world "locally stale lineage" — metadata is worst exactly where the change happened, but the node is never completely isolated. Text degradation (legacy aliases, sentence omission, misleading N/A) simultaneously degrades both graph structure and narrative text.

### 7.3 Pre-registered evaluation with go/no-go gates

No commercial tool publishes pre-registered thresholds (50% recovery, 25% workload, 95% five-run agreement) and evaluates against them with a held-out test split. This project's evaluation methodology is more rigorous than most published LLM benchmarks.

### 7.4 Lineage repair comparator

No commercial system asks "would simply fixing the metadata work better than AI?" This project's improvement plan includes Experiment F, which compares AI-assisted recovery against metadata repair at equivalent effort. If lineage repair supplies most of the gain, the recommendation is to fix lineage rather than deploy AI.

### 7.5 Three-class output with separate review queues

Most compliance tools use binary output (flagged or not). This project uses AFFECTED (positive recommendation), UNCERTAIN (separate review queue, counted toward workload), and UNAFFECTED (not surfaced, tracked for audit only). This mirrors how compliance reviewers actually work — they need a "maybe" bucket, not just yes/no.

## 8. Closest Commercial Analog

The closest industry analog is **ServiceNow GRC Change Management**, which uses a CMDB dependency graph to identify affected controls when a change is submitted. However, it has two fundamental limitations this project addresses:

1. **No degradation handling**: ServiceNow assumes the CMDB is accurate. When it is stale, it silently misses affected controls. This project explicitly models and tests that scenario.

2. **No narrative recovery**: ServiceNow cannot read a control's documentation and reason about whether it is affected — it only uses graph edges. This project's hybrid approach adds LLM narrative reasoning to recover controls the graph missed.

## 9. Novelty Assessment

The project's novelty lies not in any single technique, but in the **specific combination** of:

- Graph traversal (like ServiceNow/LeanIX) + LLM narrative reasoning for control recovery
- Degradation simulation with random and correlated patterns + text degradation
- Pre-registered evaluation thresholds with five-run agreement and development/test split
- Lineage repair comparator questioning whether AI is the right solution vs. data quality improvement
- Three-class output with separate uncertain review queue
- Per-control audit trail with confidence scoring

**No commercial or open-source system combines all of these.** The individual pieces exist in isolation, but the integrated approach — especially evaluating whether the LLM adds net value under realistic data quality conditions — is not present in any known industry system.

The most novel contribution is the **evaluation framework itself**: a disciplined methodology for assessing whether LLM-assisted compliance tools provide net value (recovery vs. workload) under realistic data quality conditions. This framework could be applied to other domains (healthcare, regulatory compliance, software change management) beyond payments.

## 10. Sources and Method

This comparison was compiled from publicly available product documentation and general industry knowledge of GRC, EA, and RegTech platforms as of October 2026. No vendor claims were independently verified through testing. The comparison focuses on **capability presence**, not relative quality or market position.

Source: assistant's analysis based on public product documentation and project requirements, October 2026.

## 11. Vendor References

[^1]: ServiceNow GRC — https://www.servicenow.com/products/governance-risk-compliance.html
[^2]: Archer Integrated Risk Management — https://www.archerirm.com/
[^3]: SAP GRC — https://www.sap.com/products/grc.html
[^4]: IBM OpenPages — https://www.ibm.com/products/openpages
[^5]: LeanIX — https://www.leanix.net/
[^6]: Ardoq — https://ardoq.com/
[^7]: SAP Signavio — https://www.signavio.com/
[^8]: SWIFT Customer Security Programme — https://www.swift.com/myswift/customer-security-programme-csp
[^9]: Volante Technologies — https://www.volantetech.com/
[^10]: Bottomline Technologies — https://www.bottomline.com/
[^11]: ACI Worldwide — https://www.aciworldwide.com/
[^12]: Quantexa — https://quantexa.com/
[^13]: ComplyAdvantage — https://complyadvantage.com/
[^14]: CodeSee — https://codesee.io/
[^15]: Sonargraph (hello2morrow) — https://www.hello2morrow.com/products/sonargraph
[^16]: GitHub Copilot — https://github.com/features/copilot
[^17]: LogicGate Risk Cloud — https://logicgate.com/
[^18]: Drata — https://drata.com/
[^19]: Vanta — https://vanta.com/
[^20]: OneTrust — https://www.onetrust.com/
[^21]: Workiva — https://www.workiva.com/