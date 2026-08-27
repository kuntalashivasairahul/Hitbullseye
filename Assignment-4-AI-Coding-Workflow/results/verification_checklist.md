# Pre-Merge AI Code Verification Checklist

> **Mandatory Verification Discipline Specification**  
> **Target Audience**: Software Engineers, Technical Leads, and Code Reviewers  
> **Governance Policy**: Zero Unreviewed AI Code in Production (100% Committer Ownership)

---

## The 6-Point Verification Checklist

Every engineer reviewing AI-generated code must execute this **6-Point Verification Checklist** prior to approving or merging a pull request:

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                 PRE-MERGE AI CODE VERIFICATION CHECKLIST                  │
├───────────────────────────────────────────────────────────────────────────┤
│ [ ] 1. BOUNDARY & EDGE-CASE FUZZING                                       │
│        Test inputs of size 0, 1, len(arr), None, empty strings, and max.  │
│ [ ] 2. SECURITY & CONSTANT-TIME CHECKS                                    │
│        Verify hmac.compare_digest for secrets, reject 'alg: none'.        │
│ [ ] 3. CONCURRENCY & STATE INVARIANTS                                     │
│        Ensure locks (RLock) guard atomic check-then-act operations.       │
│ [ ] 4. IDEMPOTENCY & SIDE-EFFECT GUARDING                                 │
│        Verify idempotency keys prevent duplicate payments/actions.        │
│ [ ] 5. LICENSING & SECRET LEAK AUDIT                                      │
│        Check for hallucinated API keys, credentials, or GPL code.        │
│ [ ] 6. INDEPENDENT TEST-FIRST DISCIPLINE                                  │
│        Author unit tests independently of viewing the generated code.     │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Check Verification Protocols

### 1. Boundary & Edge-Case Fuzzing
- **Array & Index Offsets**: Verify prefix sums, sub-array ranges (`[0, 0]`, `[0, len-1]`), and off-by-one boundary conditions.
- **Null & Empty Handling**: Ensure `None`, empty lists `[]`, empty strings `""`, and single-item collections do not cause unhandled exceptions.
- **Numeric Precision**: Check for floating-point rounding errors on currency calculations (use `Decimal` or rounded arithmetic) and zero-division guards.

### 2. Security & Constant-Time Cryptographic Checks
- **Timing Side-Channel Protection**: Forbid naive string equality (`==`) on HMAC digests, signatures, and authentication tokens. Mandate `hmac.compare_digest()`.
- **Algorithm Enforcement**: Verify that insecure algorithm downgrade attacks (e.g. `'alg': 'none'`) are strictly rejected.
- **Clock Skew Tolerances**: Ensure replay attack guards check absolute time differences `abs(now - timestamp) > max_drift` to prevent negative drift exploits.

### 3. Concurrency & State Invariants
- **Atomic Synchronization**: Inspect shared mutable state across threads/tasks. Verify that re-entrant locks (`threading.RLock`) guard check-then-act sequences.
- **Cache Stampede Prevention**: In `get_or_compute` memoization patterns, ensure double-checked locking prevents duplicate expensive computations under load.
- **Socket & Resource Exhaustion**: Bound unbounded asynchronous operations (`asyncio.gather`) using `asyncio.Semaphore`.

### 4. Idempotency & Side-Effect Guarding
- **Idempotency Key Caching**: Ensure idempotency parameters are persisted in an atomic store before dispatching external side effects (e.g. Stripe/payment charges).
- **Duplicate Mutation Prevention**: Replayed requests with the same idempotency key must return cached results without re-executing transactions.

### 5. Licensing & Secret Leak Audit
- **Hallucinated Credentials**: Scan generated code for fake or leaked API keys, tokens, hardcoded private keys, or passwords.
- **IP Compliance**: Verify generated code does not replicate copyrighted, GPL-licensed, or proprietary third-party libraries incompatible with repository licenses.

### 6. Independent Test-First Discipline
- **Confirmation Bias Elimination**: Write unit test assertions independently—ideally *before* prompting the AI—to avoid mirroring the AI's internal assumptions.
- **Negative & Failure Path Verification**: Explicitly assert invalid inputs, expired tokens, terminal state transitions, and exception raising.

---

## Verification Execution Commands

Before submitting any code incorporating AI assistance, run the automated verification suite:
```bash
# Execute isolated unit test suite
python3 -m unittest discover -s tests

# Verify all 10 engineering tasks
python3 src/task_manager.py --verify-all
```
