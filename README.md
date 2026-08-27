# AI Engineering & Prompt Systems Evaluation Suite

An enterprise-grade, rigorous software engineering evaluation repository encompassing three production-grade AI assignments. Demonstrates systematic prompt engineering benchmarks, empirical AI-assisted developer telemetry with verification discipline, and a resilient document extraction pipeline with confidence calibration and operational economics.

---

## 🎯 Executive Overview

This repository provides an end-to-end framework for evaluating, verifying, and deploying AI systems in production:

1. **Assignment 3: Prompt Engineering Library & Evaluation Framework**
   - Evaluates **4 distinct prompt engineering strategies** across an empirical **50-case golden set** for an E-Commerce platform.
   - Measures **200 batch evaluations** on format compliance, content quality (1–5 rubric), inference latency, and failure modes.
   - Provides concrete architectural guidance on strategy selection, cost-latency trade-offs, and failure catalog analysis.

2. **Assignment 4: AI-Assisted Coding Workflow with Verification Discipline**
   - Evaluates human developer vs. AI-assisted productivity across **10 realistic tasks in 6 software disciplines** (Boilerplate, Algorithms, Refactoring, Test Writing, Debugging, and Integration).
   - Deconstructs the **"Illusion of Speed"**: contrasts raw code generation savings (**96.1%**) against true net productivity (**+28.7% overall / +31.9% task average**), demonstrating that **94.6% of engineering time** is spent on verification (review and bug-fixing).
   - Catalogs a **21-defect empirical taxonomy** across logic, edge-case, security, performance, and style flaws with a pre-merge **6-point verification checklist**.

3. **Assignment 5: Document Extraction Pipeline with Accuracy Measurement**
   - End-to-end information extraction pipeline tested on **100 multi-tier ground truth documents** (Invoices, Healthcare Claims, KYC Identity) against **3 strict JSON schemas**.
   - Implements **confidence calibration** across 4 probability bins and a **Human-in-the-Loop (HITL) 3-way routing queue** ($\theta = 0.85$):
     * **Straight-Through Processing (STP)**: **60.0%**
     * **Human Review Queue**: **30.0%**
     * **Rejection Queue**: **10.0%**
   - Demonstrates **93.4% post-review field accuracy** and **89.2% operational labor savings** ($1.80/doc manual down to $0.195/doc automated).

---

## 📁 Repository Architecture

```text
Hitbullseye/
├── verify_all.py                             # Master verification test & artifact harness
├── requirements.txt                          # Minimal root dependencies
├── README.md                                 # Master repository documentation
├── .gitignore                                # Clean bytecode & environment ignore rules
│
├── assignment_03_prompt_library/             # ASSIGNMENT 3: PROMPT ENGINEERING
│   ├── data/
│   │   └── golden_set.json                   # 50 validated customer support test cases
│   ├── prompts/
│   │   ├── __init__.py                       # Strategy exports
│   │   ├── zero_shot.py                      # Strategy v1.0.0 (Minimal baseline)
│   │   ├── few_shot.py                       # Strategy v1.1.0 (3 customer demonstrations)
│   │   ├── chain_of_thought.py               # Strategy v1.2.0 (3-step explicit reasoning)
│   │   └── structured_template.py            # Strategy v1.3.0 (Rigid 4-key JSON schema)
│   ├── src/
│   │   ├── __init__.py                       # Package exports
│   │   ├── dataset_generator.py              # Golden set generator & schema validator
│   │   ├── prompt_registry.py                # Central registry with CLI preview
│   │   ├── evaluator.py                      # 1-5 scoring rubric & format checker
│   │   ├── llm_client.py                     # MockLLMBackend & LiveLLMClient
│   │   ├── benchmark_runner.py               # 200-evaluation batch orchestrator
│   │   └── generate_report.py                # Report compiler
│   ├── tests/                                # 25 automated unit tests
│   ├── results/
│   │   ├── benchmark_results.json            # Telemetry for all 200 runs
│   │   ├── summary_table.csv                 # Strategy performance summary
│   │   └── failure_catalogue.json            # 57 categorized sub-optimal runs
│   ├── PROMPT_LIBRARY_GUIDE.md               # Publication report & strategy guide
│   └── README.md
│
├── assignment_04_ai_coding/                  # ASSIGNMENT 4: AI-ASSISTED CODING WORKFLOW
│   ├── data/
│   │   └── tasks_spec.json                   # 10 task specifications across 6 disciplines
│   ├── tasks/
│   │   ├── __init__.py                       # Tasks exports
│   │   ├── task_01_boilerplate_auth.py       # Boilerplate: JWT Authentication Token Handler
│   │   ├── task_02_boilerplate_crud.py       # Boilerplate: REST API CRUD Serializer
│   │   ├── task_03_algo_sliding_window.py    # Algorithm: Sliding Window Rate Limiter
│   │   ├── task_04_algo_graph_cycles.py      # Algorithm: Directed Graph Cycle Detector
│   │   ├── task_05_refactor_legacy_billing.py# Refactoring: Clean Billing Service
│   │   ├── task_06_refactor_async_fetcher.py # Refactoring: Concurrent Async Fetcher
│   │   ├── task_07_test_writing_order_fsm.py # Test Writing: Order State Machine
│   │   ├── task_08_debugging_race_condition.py# Debugging: Thread-Safe Cache with RLock
│   │   ├── task_09_debugging_off_by_one.py   # Debugging: Subarray & Window Processor
│   │   └── task_10_integration_webhook_parser.py# Integration: Webhook HMAC Dispatcher
│   ├── src/
│   │   ├── __init__.py                       # Source exports
│   │   ├── task_manager.py                   # Task inspector & test runner CLI
│   │   ├── telemetry_runner.py               # Productivity telemetry engine
│   │   └── generate_report.py                # Report compiler
│   ├── tests/                                # 39 automated unit tests
│   ├── results/
│   │   ├── telemetry_log.json                # Complete telemetry with 21 defects
│   │   ├── task_type_breakdown.csv           # Category-level metrics
│   │   └── net_productivity_summary.csv      # Unassisted vs. Assisted comparison matrix
│   ├── VERIFICATION_DISCIPLINE_GUIDE.md      # Publication report & verification checklist
│   └── README.md
│
└── assignment_05_doc_extraction/             # ASSIGNMENT 5: DOCUMENT EXTRACTION PIPELINE
    ├── data/
    │   ├── schemas/
    │   │   ├── invoice_schema.json           # Commercial invoice schema
    │   │   ├── insurance_claim_schema.json   # Healthcare claim schema
    │   │   └── kyc_identity_schema.json      # KYC verification schema
    │   └── ground_truth.json                 # 100 multi-tier verified documents
    ├── src/
    │   ├── __init__.py                       # Source exports
    │   ├── schema_validator.py               # Type, constraint, and regex validation engine
    │   ├── dataset_generator.py              # 100-sample dataset generator & exporter
    │   ├── extractor.py                      # Schema-guided extraction & rejection engine
    │   ├── cost_model.py                     # Processing economics & ROI model
    │   ├── pipeline_evaluator.py             # HITL routing & calibration evaluation harness
    │   └── generate_report.py                # Report compiler
    ├── tests/                                # 21 automated unit tests
    ├── results/
    │   ├── extraction_results.json           # 100 extraction records with field confidences
    │   ├── field_level_accuracy.csv          # Exact vs normalized accuracy per field
    │   ├── confidence_calibration.csv        # Confidence calibration bin performance
    │   └── routing_and_cost_summary.json     # Routing queue metrics and net savings
    ├── DOCUMENT_EXTRACTION_GUIDE.md          # Publication report & BFSI blueprint
    └── README.md
```

---

## 🔬 Detailed Module Summaries

### 1. Assignment 3: Prompt Engineering Library & Evaluation Framework
- **Dataset**: 50 customer support cases partitioned into 25 Standard, 10 Hostile, 8 Ambiguous, and 7 Out-of-Scope inquiries.
- **Strategies Tested**:
  * `zero_shot` (v1.0.0): 2.84/5.00 avg score, 70.0% format pass rate (unstable on ambiguous queries, hostile tone drift).
  * `few_shot` (v1.1.0): 3.72/5.00 avg score, 100.0% format pass rate (good tone adaptation, highest prompt token overhead).
  * `chain_of_thought` (v1.2.0): **4.56/5.00 avg score**, 100.0% format pass rate (**highest content quality** across all categories).
  * `structured_template` (v1.3.0): 4.34/5.00 avg score, 100.0% format pass rate (**optimal cost-to-accuracy ratio** for programmatic JSON pipelines).
- **Deliverables**: In-depth strategy guide [`assignment_03_prompt_library/PROMPT_LIBRARY_GUIDE.md`](assignment_03_prompt_library/PROMPT_LIBRARY_GUIDE.md).

### 2. Assignment 4: AI-Assisted Coding Workflow with Verification Discipline
- **Empirical Baseline**: Evaluated developer time across 10 real-world software tasks.
- **The Speed Illusion**: Raw generation time saved is **96.1%**, but true net developer productivity is **+28.7% overall (+31.9% task average)** due to mandatory code review (42.4% of assisted time) and defect fixing (52.2% of assisted time).
- **Discipline Breakdown**:
  * *High Net ROI*: Boilerplate (+67.8%), Test Writing (+45.7%), Integration (+34.7%).
  * *Low / Negative Net ROI*: Debugging (+11.0%), Stateful Algorithms (+4.2%, with Sliding Window Rate Limiting at **-6.7% Negative ROI** due to subtle microsecond burst bugs).
- **Defect Taxonomy**: 21 cataloged defects across `edge_case` (9), `logic` (5), `performance` (3), `security` (2), and `style` (2).
- **Deliverables**: Comprehensive verification guide [`assignment_04_ai_coding/VERIFICATION_DISCIPLINE_GUIDE.md`](assignment_04_ai_coding/VERIFICATION_DISCIPLINE_GUIDE.md).

### 3. Assignment 5: Document Extraction Pipeline with Accuracy Measurement
- **Dataset & Quality Tiers**: 100 documents (40 Invoices, 35 Claims, 25 KYC) across 60 Clean Digital, 20 Degraded Fax, 10 Handwritten, and 10 Corrupted/Unreadable.
- **Strict Validation**: Validated against 3 strict JSON schemas with regex, ISO 8601 date, and ICD-10 rules.
- **HITL Routing**: Optimized at threshold $\theta = 0.85$:
  * **Straight-Through Processing (STP)**: **60.0%**
  * **Human Review Queue**: **30.0%**
  * **Rejection Queue**: **10.0%**
  * **Post-Review Field Accuracy**: **93.4%**
- **Economics & Scaling**: 89.2% cost reduction ($1.80 manual $\rightarrow$ $0.195 automated). Scaling to 100,000 docs/month yields **$160,500/month ($1.926M/year) net savings**.
- **Deliverables**: Comprehensive operational guide [`assignment_05_doc_extraction/DOCUMENT_EXTRACTION_GUIDE.md`](assignment_05_doc_extraction/DOCUMENT_EXTRACTION_GUIDE.md).

---

## 🚀 One-Command Verification & Reproduction

All 85 unit tests and 19 production artifacts can be verified with a single command from the repository root:

### 1. Installation
Ensure Python 3.8+ is installed. Dependencies are strictly minimal:
```bash
pip install -r requirements.txt
```

### 2. Execute Master Verification Harness
```bash
python3 verify_all.py
```

### Expected Terminal Output:
```text
================================================================================
AI Engineering & Prompt Systems Evaluation Suite: Master Verification
================================================================================

🧪 Executing Unit Test Suites Across All 3 Assignments...

  • Assignment 3: Prompt Engineering Library         : 25 tests in 0.098s [PASSED ✓]
  • Assignment 4: AI-Assisted Coding Workflow        : 39 tests in 0.256s [PASSED ✓]
  • Assignment 5: Document Extraction Pipeline       : 21 tests in 0.083s [PASSED ✓]

Total Unit Tests Executed: 85 (Failures: 0, Errors: 0)

📁 Verifying Required Deliverables & Benchmark Artifacts...

  • A3 Golden Set (50 cases)                   : [EXISTS ✓] Valid (37,789 bytes)
  • A3 Benchmark Results (200 evaluations)     : [EXISTS ✓] Valid (489,494 bytes)
  • A3 Strategy Summary Table CSV              : [EXISTS ✓] Valid (334 bytes)
  • A3 Failure Catalogue JSON                  : [EXISTS ✓] Valid (126,197 bytes)
  • A3 Prompt Library Guide MD                 : [EXISTS ✓] Valid (12,063 bytes)
  • A4 Tasks Specification (10 tasks)          : [EXISTS ✓] Valid (15,067 bytes)
  • A4 Telemetry Log (21 defects)              : [EXISTS ✓] Valid (8,851 bytes)
  • A4 Category Breakdown CSV                  : [EXISTS ✓] Valid (478 bytes)
  • A4 Productivity Summary CSV                : [EXISTS ✓] Valid (1,365 bytes)
  • A4 Verification Discipline Guide MD        : [EXISTS ✓] Valid (13,778 bytes)
  • A5 Commercial Invoice Schema JSON          : [EXISTS ✓] Valid (1,573 bytes)
  • A5 Insurance Claim Schema JSON             : [EXISTS ✓] Valid (1,681 bytes)
  • A5 KYC Identity Schema JSON                : [EXISTS ✓] Valid (1,508 bytes)
  • A5 Ground Truth Dataset (100 docs)         : [EXISTS ✓] Valid (76,488 bytes)
  • A5 Extraction Results JSON                 : [EXISTS ✓] Valid (173,972 bytes)
  • A5 Field Level Accuracy CSV                : [EXISTS ✓] Valid (1,069 bytes)
  • A5 Confidence Calibration CSV              : [EXISTS ✓] Valid (236 bytes)
  • A5 Routing & Cost Summary JSON             : [EXISTS ✓] Valid (748 bytes)
  • A5 Document Extraction Guide MD            : [EXISTS ✓] Valid (13,238 bytes)

================================================================================
Total Unit Tests : 85/85 Passed (Failures: 0, Errors: 0)
Core Artifacts   : 19/19 Verified

>>> ALL CHECKS PASSED: REPOSITORY IS COMPLETE AND SUBMISSION READY! <<<
================================================================================
```

---

## 📜 Individual Assignment Execution Guides

To run CLI runners or test suites inside individual assignment packages:

```bash
# Assignment 3 (Prompt Library)
cd assignment_03_prompt_library
python3 src/prompt_registry.py --preview
python3 src/benchmark_runner.py
python3 src/generate_report.py
python3 -m unittest discover -s tests

# Assignment 4 (AI Coding Workflow)
cd assignment_04_ai_coding
python3 src/task_manager.py --list
python3 src/task_manager.py --verify-all
python3 src/telemetry_runner.py --run
python3 src/generate_report.py
python3 -m unittest discover -s tests

# Assignment 5 (Document Extraction)
cd assignment_05_doc_extraction
python3 src/schema_validator.py --validate-all
python3 src/dataset_generator.py --generate --verify
python3 src/pipeline_evaluator.py --run
python3 src/generate_report.py
python3 -m unittest discover -s tests
```
