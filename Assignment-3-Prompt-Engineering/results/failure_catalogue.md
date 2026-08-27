# Failure Catalogue Analysis: Customer Support Prompt Library

> **Empirical Failure Mode Audit**  
> **Benchmark Dataset**: 50 Golden Set Test Cases | **Evaluations**: 200 Total Runs (4 Strategies × 50 Cases)  
> **Identified Failures**: 57 Sub-Optimal Runs (28.5% Failure Rate) across `content_score < 4` or `format_pass == False`

---

## 1. Executive Summary of Benchmark Deficiencies

Across 200 prompt executions on real-world customer inquiries, **57 evaluations failed to achieve production-grade quality**. Failure behavior varied starkly by prompt engineering strategy:

- **Zero-Shot (`v1.0.0`)**: Accounted for **33 of 57 failures (57.9%)** and 100% of format compliance failures. Unconstrained zero-shot prompts repeatedly failed bullet point instructions, exhibited defensive reactions to hostile input, and made baseless assumptions on ambiguous inquiries.
- **Few-Shot (`v1.1.0`)**: Accounted for **18 of 57 failures (31.6%)**. While in-context examples eliminated format breaking and mitigated hostile defensiveness, the model still struggled with nuanced ambiguous edge cases that deviated from the 3 demonstrations.
- **Structured Template (`v1.3.0`)**: Recorded **5 minor failures (8.8%)**, all scored at 3/5. Zero format violations occurred; failures were solely subtle criteria omissions in complex edge cases.
- **Chain of Thought (`v1.2.0`)**: Achieved the highest resilience with only **1 marginal failure (1.8%)** (`CASE_040`), maintaining a 100% format pass rate and an average score of 4.56/5.00.

---

## 2. Failure Distribution Matrix

### By Prompt Strategy
| Strategy | Version | Total Runs | Sub-Optimal Runs | Failure Rate | Primary Failure Root Cause |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`zero_shot`** | `v1.0.0` | 50 | 33 | **66.0%** | Format violations, tone defensiveness, premature assumptions |
| **`few_shot`** | `v1.1.0` | 50 | 18 | **36.0%** | Omission of secondary criteria, ambiguous query drift |
| **`structured_template`** | `v1.3.0` | 50 | 5 | **10.0%** | Incomplete edge-case detail in JSON output |
| **`chain_of_thought`** | `v1.2.0` | 50 | 1 | **2.0%** | Single multi-condition conflict edge-case (`CASE_040`) |

### By Inquiry Category
| Inquiry Category | Total Evaluations | Failures Logged | Category Failure Rate | Key Defect Mode |
| :--- | :---: | :---: | :---: | :--- |
| **Hostile / Frustrated** | 40 | 19 | 47.5% | Lack of de-escalation, dismissive phrasing, missing supervisor escalation |
| **Ambiguous Queries** | 32 | 17 | 53.1% | Guessing order status without requesting Order Number or email |
| **Standard Inquiries** | 100 | 15 | 15.0% | Format breaking (omitting required sequential bullet steps) |
| **Out-of-Scope Requests** | 28 | 6 | 21.4% | Inadequate redirection to emergency or external resources |

---

## 3. Four Core Failure Taxonomies

### 1. Structural Format Collapse
- **Occurrences**: 15 runs (all in `zero_shot`).
- **Description**: The query requested sequential numbered steps (`bulleted_steps`), but the model emitted an unbroken text block without bullet markers.
- **Remediation**: Structured schemas (`v1.3.0`) or explicit markdown format blocks enforce 100% format determinism.

### 2. Tone Defensiveness & Empathy Omission
- **Occurrences**: 19 runs (primarily in `zero_shot` and uncalibrated few-shot).
- **Description**: On hostile inquiries where customers expressed extreme anger, models responded with rigid bureaucratic denials or failed to offer sincere apologies.
- **Remediation**: Chain-of-thought Step 1 explicitly detects customer emotion and mandates sincere empathetic validation prior to drafting resolutions.

### 3. Premature Assumption Under Ambiguity
- **Occurrences**: 17 runs.
- **Description**: When inquiries lacked order IDs or tracking numbers (e.g., "Where is my package?"), models hallucinated generic shipment schedules rather than asking targeted clarification questions.
- **Remediation**: Guardrail instructions strictly forbidding speculative answers when identifiers are absent.

### 4. Incomplete Secondary Criteria Coverage
- **Occurrences**: 6 runs.
- **Description**: Model addressed the primary question (e.g. return window) but failed secondary criteria (e.g. mentioning original packaging or 2FA backup codes).

---

## 4. Notable Edge Case: `CASE_040` in Chain of Thought
In `CASE_040`, a customer requested immediate cancellation of a custom-engraved item past the 60-minute window while threatening chargebacks. `chain_of_thought` achieved 3/5 because while it correctly refused cancellation and de-escalated, it omitted the specific advice regarding warranty claims. This highlights that even reasoning chains require comprehensive boundary condition rules.
