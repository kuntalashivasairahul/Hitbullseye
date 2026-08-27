# AI Engineering & Prompt Systems Evaluation Repository

> **Comprehensive Multi-Assignment Submission Suite**  
> **Coursework**: Advanced AI Engineering, Prompt Architecture, Verification Discipline & Document Extraction  
> **Status**: Verified & Submission-Ready (All Formatted Publication PDFs Generated & Artifacts Audited)

---

## 📌 Executive Overview

This repository contains the complete production-grade codebase, empirical benchmark engines, raw datasets, high-resolution Matplotlib visualizations, and comprehensive publication PDF reports across three advanced AI engineering assignments:

1. **Assignment 3: Prompt Engineering Library (`Assignment-3-Prompt-Engineering`)**: Systematic benchmarking of 4 prompt engineering strategies (`zero_shot`, `few_shot`, `chain_of_thought`, `structured_template`) evaluated across a 50-case golden dataset (200 total runs) assessing format compliance, content quality, and edge-case handling.
2. **Assignment 4: AI Coding Workflow with Verification Discipline (`Assignment-4-AI-Coding-Workflow`)**: Empirical software engineering telemetry across 10 production tasks and 6 development disciplines measuring the "Illusion of Speed" vs. net developer productivity, tracking 21 defects, and enforcing a mandatory 6-point verification checklist.
3. **Assignment 5: Document Extraction Pipeline (`Assignment-5-Document-Extraction`)**: Production document processing pipeline processing 100 multi-tier documents (Invoices, Health Insurance Claims, KYC Identity Records) across 4 quality tiers, featuring schema-guided extraction, confidence calibration, fail-safe rejection gates, and human-in-the-loop (HITL) economics (89.2% net operational labor savings).

---

## 📂 Standardized Repository Architecture

```text
Hitbullseye/
├── requirements.txt                          # Root dependencies (reportlab, matplotlib, pydantic, etc.)
├── README.md                                 # Master repository documentation
├── .gitignore                                # Clean bytecode & environment ignore rules
│
├── Assignment-3-Prompt-Engineering/          # ASSIGNMENT 3: PROMPT ENGINEERING
│   ├── data/
│   │   └── golden_set.csv                    # 50 validated customer support test cases (CSV)
│   ├── evaluation/
│   │   └── rubric.md                         # Formal 1-5 scoring rubric & heuristics guide
│   ├── graphs/                               # 4 Matplotlib visualization PNG charts
│   │   ├── prompt_scores_comparison.png      # Bar chart: overall content scores
│   │   ├── format_compliance_rate.png        # Bar chart: format pass rates
│   │   ├── edge_vs_standard_performance.png  # Grouped bar chart: category performance
│   │   └── quality_dimension_breakdown.png   # Grouped bar chart: quality dimensions
│   ├── prompts/                              # 4 raw prompt text templates
│   │   ├── v1_zero_shot.txt                  # Strategy v1.0.0
│   │   ├── v2_few_shot.txt                   # Strategy v1.1.0
│   │   ├── v3_chain_of_thought.txt           # Strategy v1.2.0
│   │   └── v4_structured_template.txt        # Strategy v1.3.0
│   ├── results/                              # Benchmark result exports & analysis
│   │   ├── comparison_summary.csv            # Tabular comparison summary
│   │   ├── evaluation_results.csv            # Detailed 200-run tabular export
│   │   └── failure_catalogue.md              # Failure taxonomy & root-cause report
│   ├── README.md                             # Assignment documentation
│   └── Assignment_3-23EG107E30.pdf           # Formatted multi-page publication report
│
├── Assignment-4-AI-Coding-Workflow/          # ASSIGNMENT 4: AI-ASSISTED CODING WORKFLOW
│   ├── graphs/                               # 4 Matplotlib visualization PNG charts
│   │   ├── net_productivity_by_type.png      # Bar chart: productivity gains by discipline
│   │   ├── acceptance_rate_by_type.png       # Bar chart: AI code acceptance rates
│   │   ├── time_spent_breakdown.png          # Stacked bar chart: generation/review/fix
│   │   └── defect_distribution.png           # Donut chart: 21 defects by category
│   ├── results/                              # Benchmark reports & checklists
│   │   ├── benchmark_summary.csv             # Category breakdown summary
│   │   ├── task_type_analysis.md             # Discipline-by-discipline deep dive
│   │   └── verification_checklist.md         # 6-point pre-merge verification checklist
│   ├── tasks/                                # 10 production task implementations
│   │   ├── task_01_boilerplate_auth.py       # Boilerplate: JWT Authentication Handler
│   │   ├── task_02_boilerplate_crud.py       # Boilerplate: REST API CRUD Serializer
│   │   ├── task_03_algo_sliding_window.py    # Algorithm: Sliding Window Rate Limiter
│   │   ├── task_04_algo_graph_cycles.py      # Algorithm: Directed Graph Cycle Detector
│   │   ├── task_05_refactor_legacy_billing.py# Refactoring: Clean Billing Service
│   │   ├── task_06_refactor_async_fetcher.py # Refactoring: Concurrent Async Fetcher
│   │   ├── task_07_test_writing_order_fsm.py # Test Writing: Order State Machine
│   │   ├── task_08_debugging_race_condition.py# Debugging: Thread-Safe In-Memory Cache
│   │   ├── task_09_debugging_off_by_one.py   # Debugging: Subarray & Window Processor
│   │   └── task_10_integration_webhook_parser.py# Integration: Webhook HMAC Dispatcher
│   ├── tests/                                # 10 self-contained task test modules
│   │   ├── test_task01.py ... test_task10.py # Self-contained unit tests
│   ├── defect-log.csv                        # Root CSV log of all 21 cataloged defects
│   ├── time-log.csv                          # Root CSV log of unassisted vs assisted time
│   ├── README.md                             # Assignment documentation
│   └── Assignment_4-23EG107E30.pdf           # Formatted multi-page publication report
│
└── Assignment-5-Document-Extraction/         # ASSIGNMENT 5: DOCUMENT EXTRACTION PIPELINE
    ├── data/                                 # Raw document text collections
    │   ├── id_cards/                         # 35 raw text files (DOC_ID_001..035.txt)
    │   ├── insurance_claims/                 # 35 raw text files (DOC_CLM_001..035.txt)
    │   └── invoices/                         # 35 raw text files (DOC_INV_001..035.txt)
    ├── graphs/                               # 4 Matplotlib visualization PNG charts
    │   ├── field_level_accuracy.png          # Horizontal bar chart: field accuracy
    │   ├── confidence_calibration.png        # Bar chart: confidence vs empirical accuracy
    │   ├── routing_distribution.png          # Donut chart: 60% STP, 30% Review, 10% Reject
    │   └── cost_comparison.png               # Bar chart: Manual vs Pipeline unit costs
    ├── ground-truth/                         # Ground truth dataset
    │   └── ground_truth.csv                  # Tabular export of all 100 ground truth records
    ├── results/                              # Extraction evaluations & economic reports
    │   ├── confidence_calibration.csv        # Empirical confidence calibration bins
    │   ├── cost_analysis.md                  # Unit economics and volume scaling report
    │   ├── error_analysis.md                 # Field defect taxonomy & error analysis
    │   ├── extraction_results.csv            # Tabular extraction runs
    │   └── field_accuracy_report.csv         # Field accuracy report table
    ├── README.md                             # Assignment documentation
    └── Assignment_5-23EG107E30.pdf           # Formatted multi-page publication report
```

---

## 🔬 Detailed Module Summaries & Deliverables

### 1. Assignment 3: Prompt Engineering Library & Evaluation Framework
- **Dataset**: 50 customer support cases partitioned into 25 Standard, 10 Hostile, 8 Ambiguous, and 7 Out-of-Scope inquiries ([`data/golden_set.csv`](Assignment-3-Prompt-Engineering/data/golden_set.csv)).
- **Strategies Tested**:
  * `zero_shot` (v1.0.0): 2.84/5.00 avg score, 70.0% format pass rate (unstable on ambiguous queries, hostile tone drift).
  * `few_shot` (v1.1.0): 3.72/5.00 avg score, 100.0% format pass rate (good tone adaptation, highest prompt token overhead).
  * `chain_of_thought` (v1.2.0): **4.56/5.00 avg score**, 100.0% format pass rate (**highest content quality** across all categories).
  * `structured_template` (v1.3.0): 4.34/5.00 avg score, 100.0% format pass rate (**optimal cost-to-accuracy ratio** for programmatic JSON pipelines).
- **Core Deliverables**:
  - Publication Report: [`Assignment-3-Prompt-Engineering/Assignment_3-23EG107E30.pdf`](Assignment-3-Prompt-Engineering/Assignment_3-23EG107E30.pdf)
  - Scoring Rubric: [`Assignment-3-Prompt-Engineering/evaluation/rubric.md`](Assignment-3-Prompt-Engineering/evaluation/rubric.md)
  - Raw Templates: [`Assignment-3-Prompt-Engineering/prompts/`](Assignment-3-Prompt-Engineering/prompts/)
  - Failure Catalogue: [`Assignment-3-Prompt-Engineering/results/failure_catalogue.md`](Assignment-3-Prompt-Engineering/results/failure_catalogue.md)
  - Results Exports: [`Assignment-3-Prompt-Engineering/results/comparison_summary.csv`](Assignment-3-Prompt-Engineering/results/comparison_summary.csv) & [`evaluation_results.csv`](Assignment-3-Prompt-Engineering/results/evaluation_results.csv)

### 2. Assignment 4: AI-Assisted Coding Workflow with Verification Discipline
- **Empirical Baseline**: Evaluated developer time across 10 real-world software tasks.
- **The Speed Illusion**: Raw generation time saved is **96.1%**, but true net developer productivity is **+28.7% overall (+31.9% task average)** due to mandatory code review (42.4% of assisted time) and defect fixing (52.2% of assisted time).
- **Discipline Breakdown**:
  * *High Net ROI*: Boilerplate (+67.8%), Test Writing (+45.7%), Integration (+34.7%).
  * *Low / Negative Net ROI*: Debugging (+11.0%), Stateful Algorithms (+4.2%, with Sliding Window Rate Limiting at **-6.7% Negative ROI** due to subtle microsecond burst bugs).
- **Defect Taxonomy**: 21 cataloged defects across `edge_case` (9), `logic` (5), `performance` (3), `security` (2), and `style` (2), exported in [`defect-log.csv`](Assignment-4-AI-Coding-Workflow/defect-log.csv).
- **Core Deliverables**:
  - Publication Report: [`Assignment-4-AI-Coding-Workflow/Assignment_4-23EG107E30.pdf`](Assignment-4-AI-Coding-Workflow/Assignment_4-23EG107E30.pdf)
  - Defect & Time Logs: [`Assignment-4-AI-Coding-Workflow/defect-log.csv`](Assignment-4-AI-Coding-Workflow/defect-log.csv) & [`time-log.csv`](Assignment-4-AI-Coding-Workflow/time-log.csv)
  - 6-Point Checklist: [`Assignment-4-AI-Coding-Workflow/results/verification_checklist.md`](Assignment-4-AI-Coding-Workflow/results/verification_checklist.md)
  - Task Type Analysis: [`Assignment-4-AI-Coding-Workflow/results/task_type_analysis.md`](Assignment-4-AI-Coding-Workflow/results/task_type_analysis.md)
  - Working Tasks: [`Assignment-4-AI-Coding-Workflow/tasks/`](Assignment-4-AI-Coding-Workflow/tasks/) (10 implemented modules)
  - Unit Test Suites: [`Assignment-4-AI-Coding-Workflow/tests/`](Assignment-4-AI-Coding-Workflow/tests/) (10 self-contained task test suites)

### 3. Assignment 5: Document Extraction Pipeline with Accuracy Measurement
- **Dataset & Quality Tiers**: 100 documents (40 Invoices, 35 Claims, 25 KYC) across 60 Clean Digital, 20 Degraded Fax, 10 Handwritten, and 10 Corrupted/Unreadable. Individual raw text files partitioned into `data/invoices/`, `data/insurance_claims/`, and `data/id_cards/` (35 files each).
- **HITL Routing**: Optimized at threshold $\theta = 0.85$:
  * **Straight-Through Processing (STP)**: **60.0%**
  * **Human Review Queue**: **30.0%**
  * **Rejection Queue**: **10.0%**
  * **Post-Review Field Accuracy**: **93.4%**
- **Economics & Scaling**: 89.2% cost reduction ($1.80 manual $\rightarrow$ $0.195 automated). Scaling to 100,000 docs/month yields **$160,500/month ($1.926M/year) net savings**.
- **Core Deliverables**:
  - Publication Report: [`Assignment-5-Document-Extraction/Assignment_5-23EG107E30.pdf`](Assignment-5-Document-Extraction/Assignment_5-23EG107E30.pdf)
  - Raw TXT Collections: [`Assignment-5-Document-Extraction/data/`](Assignment-5-Document-Extraction/data/) (105 text files)
  - Ground Truth Export: [`Assignment-5-Document-Extraction/ground-truth/ground_truth.csv`](Assignment-5-Document-Extraction/ground-truth/ground_truth.csv)
  - Economic Cost Analysis: [`Assignment-5-Document-Extraction/results/cost_analysis.md`](Assignment-5-Document-Extraction/results/cost_analysis.md)
  - Error Root-Cause Analysis: [`Assignment-5-Document-Extraction/results/error_analysis.md`](Assignment-5-Document-Extraction/results/error_analysis.md)
  - Accuracy & Run Results: [`Assignment-5-Document-Extraction/results/field_accuracy_report.csv`](Assignment-5-Document-Extraction/results/field_accuracy_report.csv) & [`extraction_results.csv`](Assignment-5-Document-Extraction/results/extraction_results.csv)

---

## 📜 Execution & Verification

### Running Assignment 4 Self-Contained Tests
```bash
cd Assignment-4-AI-Coding-Workflow

# Run all 32 unit tests across the 10 tasks
python3 -m unittest discover -s tests

# Or run individual task suites directly
python3 tests/test_task01.py
python3 tests/test_task02.py
python3 tests/test_task03.py
```
