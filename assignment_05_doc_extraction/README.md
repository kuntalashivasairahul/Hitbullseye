# Assignment 5: Document Extraction Pipeline with Accuracy Measurement

A robust, enterprise-grade information extraction evaluation framework for benchmarking document AI models against strict JSON schemas, multi-tier ground truth datasets, confidence calibration bins, and Human-in-the-Loop (HITL) operational routing.

---

## 📁 Project Structure

```text
assignment_05_doc_extraction/
├── data/
│   ├── schemas/
│   │   ├── invoice_schema.json               # Schema for commercial invoices
│   │   ├── insurance_claim_schema.json       # Schema for health insurance claims
│   │   └── kyc_identity_schema.json          # Schema for KYC identity verification
│   └── ground_truth.json                     # Exactly 100 multi-tier verified documents
├── src/
│   ├── __init__.py                           # Source exports
│   ├── schema_validator.py                   # Type, constraint, and regex validation engine
│   ├── dataset_generator.py                  # 100-sample dataset generator & exporter
│   ├── extractor.py                          # Schema-guided extraction & rejection engine
│   ├── cost_model.py                         # Processing economics & ROI model
│   └── pipeline_evaluator.py                 # HITL routing & calibration evaluation harness
├── tests/
│   ├── __init__.py                           # Test package marker
│   ├── test_dataset_and_schemas.py           # Schemas & dataset unit tests (14 tests)
│   └── test_extraction_pipeline.py           # Extractor, routing & cost tests (7 tests)
├── results/
│   ├── extraction_results.json               # Full extraction records & field confidences
│   ├── field_level_accuracy.csv              # Exact vs normalized accuracy per field
│   ├── confidence_calibration.csv            # Empirical confidence calibration bins
│   └── routing_and_cost_summary.json         # STP rates, queue routing, and net savings
├── requirements.txt                          # Minimal dependencies
└── README.md                                 # Full documentation
```

---

## 📋 Strict JSON Extraction Schemas (`data/schemas/`)

| Schema File | Target Domain | Required Fields | Key Regex / Format Constraints |
| :--- | :--- | :--- | :--- |
| `invoice_schema.json` | Commercial Invoices | `invoice_number`, `vendor_name`, `invoice_date`, `total_amount`, `tax_amount`, `currency`, `line_items_count` | `invoice_number`: `^[A-Z0-9\-#]{3,30}$`<br>`invoice_date`: ISO `YYYY-MM-DD`<br>`currency`: `^[A-Z]{3}$` |
| `insurance_claim_schema.json` | Healthcare Claims | `claim_id`, `policy_number`, `patient_name`, `hospital_name`, `admission_date`, `claim_amount`, `diagnosis_code` | `claim_id`: `^CLM-[A-Z0-9]{4,12}$`<br>`policy_number`: `^POL-[A-Z0-9]{5,15}$`<br>`diagnosis_code`: WHO ICD-10 |
| `kyc_identity_schema.json` | KYC Verification | `id_number`, `full_name`, `dob`, `expiry_date`, `document_type`, `nationality` | `id_number`: `^[A-Z0-9\-]{5,25}$`<br>`dob`: ISO `YYYY-MM-DD`<br>`document_type`: `[passport, national_id, drivers_license, tax_id]` |

---

## 📊 Ground Truth Dataset Distribution (`data/ground_truth.json`)

The ground truth dataset contains exactly **100 synthetic, verified documents**:
- **40 Invoices**: 24 Clean Digital, 8 Degraded Scans, 4 Handwritten, 4 Corrupted (`should_reject: true`)
- **35 Insurance Claims**: 21 Clean Digital, 7 Degraded Scans, 4 Handwritten, 3 Corrupted (`should_reject: true`)
- **25 KYC Identity Documents**: 15 Clean Digital, 5 Degraded Scans, 2 Handwritten, 3 Corrupted (`should_reject: true`)
- **Totals**: 60 Clean (60%), 20 Degraded (20%), 10 Handwritten (10%), 10 Unreadable/Rejected (10%).

---

## 🎯 Human-in-the-Loop (HITL) Routing & Cost Model

The operational pipeline routes documents across three destination queues using a confidence threshold ($\theta = 0.85$):
1. **Straight-Through Processing (STP)**: $\text{Confidence} \ge 0.85$ and strict schema validation passes.
2. **Human Review Queue**: $\text{Confidence} < 0.85$ or schema validation fails.
3. **Rejection Queue**: Unreadable, corrupt, or out-of-scope files automatically rejected.

### Operational Benchmark Results (`results/routing_and_cost_summary.json`)

| Routing Queue / Metric | Document Count | Share (%) | Unit Cost | Total Cost |
| :--- | :---: | :---: | :---: | :---: |
| **Straight-Through Processing (STP)** | 60 | 60.0% | $0.015 | $0.90 |
| **Human Review Queue** | 30 | 30.0% | $0.615 ($0.015 AI + $0.60 human) | $18.45 |
| **Rejection Queue** | 10 | 10.0% | $0.015 | $0.15 |
| **Total Pipeline** | **100** | **100.0%** | **$0.195 / doc** | **$19.50** |
| **Baseline 100% Manual Processing** | 100 | — | $1.80 / doc | $180.00 |
| **Net Operational Labor Savings** | — | — | — | **$160.50 (89.2% Savings)** |

---

## 📈 Confidence Calibration Analysis (`results/confidence_calibration.csv`)

| Confidence Bin | Documents | Avg Confidence | Total Fields | Exact Accuracy | Normalized Accuracy |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **0.90–1.00** | 39 | 0.968 | 258 | 92.2% | 92.2% |
| **0.80–0.89** | 26 | 0.856 | 177 | 86.4% | 86.4% |
| **0.70–0.79** | 25 | 0.741 | 173 | 88.4% | 88.4% |
| **< 0.70** | 0 | 0.000 | 0 | 0.0% | 0.0% |

---

## 🛠️ CLI Tools & Execution

### 1. Run Complete Pipeline Evaluation
```bash
python3 src/pipeline_evaluator.py --run
```
Outputs:
- `results/extraction_results.json`
- `results/field_level_accuracy.csv`
- `results/confidence_calibration.csv`
- `results/routing_and_cost_summary.json`

### 2. Generate Dataset
```bash
python3 src/dataset_generator.py --generate --verify
```

### 3. Validate Ground Truth Schemas
```bash
python3 src/schema_validator.py --validate-all
```

### 4. Run Automated Unit Tests (21 Tests)
```bash
python3 -m unittest discover -s tests
```
