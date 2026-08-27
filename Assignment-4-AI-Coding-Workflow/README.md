# Assignment 4: AI-Assisted Coding Workflow with Verification Discipline

A systematic software engineering verification framework designed to evaluate, test, and benchmark AI-assisted coding across 6 core development disciplines and 10 realistic tasks.

---

## 📁 Project Structure

```text
Assignment-4-AI-Coding-Workflow/
├── graphs/
│   ├── net_productivity_by_type.png          # Bar chart: productivity gains by discipline
│   ├── acceptance_rate_by_type.png           # Bar chart: AI code acceptance rates
│   ├── time_spent_breakdown.png              # Stacked bar chart: generation/review/fix
│   └── defect_distribution.png               # Donut chart: 21 defects by category
├── results/
│   ├── benchmark_summary.csv                 # Category breakdown summary
│   ├── task_type_analysis.md                 # Discipline-by-discipline deep dive
│   └── verification_checklist.md             # 6-point pre-merge verification checklist
├── tasks/
│   ├── task_01_boilerplate_auth.py           # Boilerplate: JWT Authentication Handler
│   ├── task_02_boilerplate_crud.py           # Boilerplate: REST API CRUD Serializer
│   ├── task_03_algo_sliding_window.py        # Algorithm: Sliding Window Rate Limiter
│   ├── task_04_algo_graph_cycles.py          # Algorithm: Directed Graph Cycle Detector
│   ├── task_05_refactor_legacy_billing.py    # Refactoring: Clean Billing Service
│   ├── task_06_refactor_async_fetcher.py     # Refactoring: Concurrent Async Fetcher
│   ├── task_07_test_writing_order_fsm.py     # Test Writing: Order State Machine
│   ├── task_08_debugging_race_condition.py   # Debugging: Thread-Safe In-Memory Cache
│   ├── task_09_debugging_off_by_one.py       # Debugging: Subarray & Window Processor
│   └── task_10_integration_webhook_parser.py # Integration: Webhook HMAC Dispatcher
├── tests/
│   ├── test_task01.py ... test_task10.py     # Self-contained task test modules
├── defect-log.csv                            # Root CSV log of all 21 cataloged defects
├── time-log.csv                              # Root CSV log of unassisted vs assisted time
├── README.md                                 # Full documentation
└── report.pdf                                # Formatted multi-page publication report
```

---

## 📊 Empirical Telemetry & Net Productivity Findings

The framework measures developer productivity and AI code quality across 10 realistic tasks:

$$\text{Acceptance Rate (\%)} = \left( \frac{\text{Lines Kept}}{\text{Lines Generated}} \right) \times 100$$

$$\text{Raw Time Saved (\%)} = \left( \frac{\text{Unassisted Time} - \text{Generation Time}}{\text{Unassisted Time}} \right) \times 100$$

$$\text{Net Productivity (\%)} = \left( \frac{\text{Unassisted Time} - (\text{Generation} + \text{Review} + \text{Correction})}{\text{Unassisted Time}} \right) \times 100$$

### Category Breakdown Summary

| Category | Tasks | Avg Unassisted | Avg Assisted | Avg Acceptance Rate | Avg Net Productivity | Total Defects | Key Failure Mode |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Boilerplate** | 2 | 52.5 min | 17.0 min | **89.2%** | **+67.8%** | 4 | Minor style/typing nuances |
| **Test Writing** | 1 | 70.0 min | 38.0 min | **76.9%** | **+45.7%** | 2 | Missed negative edge cases |
| **Integration** | 1 | 75.0 min | 49.0 min | **76.0%** | **+34.7%** | 2 | Timing attacks, clock skew |
| **Refactoring** | 2 | 87.5 min | 59.5 min | **74.5%** | **+31.9%** | 4 | Missing idempotency caching |
| **Debugging** | 2 | 72.5 min | 64.5 min | **65.8%** | **+11.0%** | 4 | Race conditions & index bounds |
| **Algorithm** | 2 | 77.5 min | 74.0 min | **61.5%** | **+4.2%** | 5 | Off-by-one errors & complexity |

---

### Task-Level Comparison Matrix (`results/net_productivity_summary.csv`)

| Task ID | Category | Unassisted | Gen Time | Review Time | Fix Time | Total Assisted | Acceptance | Raw Saved | Net Productivity | Defects |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `TASK_01_AUTH` | boilerplate | 60 min | 2 min | 8 min | 10 min | 20 min | 87.5% | 96.7% | **+66.7%** | 2 |
| `TASK_02_CRUD` | boilerplate | 45 min | 2 min | 6 min | 6 min | 14 min | 90.9% | 95.6% | **+68.9%** | 2 |
| `TASK_03_RATE_LIMITER` | algorithm | 75 min | 3 min | 32 min | 45 min | 80 min | 57.9% | 96.0% | **-6.7%** | 3 |
| `TASK_04_GRAPH_CYCLES` | algorithm | 80 min | 3 min | 30 min | 35 min | 68 min | 65.0% | 96.2% | **+15.0%** | 2 |
| `TASK_05_BILLING_SERVICE` | refactoring | 90 min | 4 min | 25 min | 30 min | 59 min | 75.0% | 95.6% | **+34.4%** | 2 |
| `TASK_06_ASYNC_FETCHER` | refactoring | 85 min | 3 min | 25 min | 32 min | 60 min | 73.9% | 96.5% | **+29.4%** | 2 |
| `TASK_07_ORDER_FSM` | test_writing | 70 min | 3 min | 15 min | 20 min | 38 min | 76.9% | 95.7% | **+45.7%** | 2 |
| `TASK_08_THREAD_SAFE_CACHE` | debugging | 80 min | 3 min | 30 min | 38 min | 71 min | 64.8% | 96.2% | **+11.2%** | 2 |
| `TASK_09_OFF_BY_ONE` | debugging | 65 min | 2 min | 26 min | 30 min | 58 min | 66.7% | 96.9% | **+10.8%** | 2 |
| `TASK_10_WEBHOOK_DISPATCHER` | integration | 75 min | 3 min | 22 min | 24 min | 49 min | 76.0% | 96.0% | **+34.7%** | 2 |

---

## 🛠️ CLI Tools & Execution

### 1. Run Telemetry Benchmark Simulation
```bash
python3 src/telemetry_runner.py --run
```
Generates:
- `results/telemetry_log.json`
- `results/task_type_breakdown.csv`
- `results/net_productivity_summary.csv`

### 2. Task Manager Catalog & Inspection
```bash
# List all registered tasks
python3 src/task_manager.py --list

# Filter by category
python3 src/task_manager.py --category boilerplate

# Inspect complete specification
python3 src/task_manager.py --inspect TASK_01_AUTH

# Verify single task
python3 src/task_manager.py --verify TASK_08_THREAD_SAFE_CACHE

# Verify all tasks
python3 src/task_manager.py --verify-all
```

### 3. Run Automated Unit Tests (39 Tests)
```bash
python3 -m unittest discover -s tests
```
