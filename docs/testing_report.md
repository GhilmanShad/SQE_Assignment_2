# SE3002 Assignment 2 — Testing Report (draft; export to PDF as docs/testing_report.pdf)

**Group:** <names / roll numbers>  **Repository:** <GitHub URL>

## 1. Black-box design (Part A)
- Expected results derived from REQUIREMENTS.md only. Cases live in one registry in `tests/test_blackbox.py`; spreadsheets in `docs/blackbox_test_design.xlsx` and `docs/decision_table.xlsx` are generated from it.
- **ECP:** 21 cases (credit hours, dues, prerequisites, availability, validation). **BVA:** 29 cases (credits 0/18, course credits 1/4, 18-credit total, capacity/enrolled, dues 0/1). **Decision table:** 6 outcome rules + 2 invalid-input rules, 14 DT tests including priority pairs (D>R>P>C>S).
- **Optimisation (A5):** 64 technique IDs map to 53 executed tests; 11 exact duplicates (same inputs + requirement + expected) were merged, keeping all IDs in the test id (e.g. `ECP-06+ECP-12+BVA-12+DT-06`). Cases with equal outputs but different inputs/objectives (e.g. `BVA-11` dues=1 vs `ECP-05` dues=5000) were deliberately kept.
- **Initial result:** 93 black-box tests: 74 passed, 19 failed (`docs/initial_blackbox_run.txt`).

## 2. White-box analysis (Part B)
**CFG** (`docs/cfg.png`) of `registration_decision()`.
| Convention | N | E | V(G)=E−N+2 | decisions+1 |
|---|---|---|---|---|
| Compound `not 0<=e<=cap or cap<1` = 1 predicate | 16 | 22 | 8 | 7+1 = 8 |
| Each atomic condition = own node (A, B, C) | 18 | 26 | **10** | 9+1 = 10 |

**Basis paths (10):** P01 dues<0 · P02 A false · P03 A true,B false · P04 A,B true,C true · P05 DUES_BLOCK · P06 ALREADY · P07 PREREQ · P08 CREDIT · P09 WAITLISTED · P10 REGISTERED. **P09 is infeasible** (line 48 already rejects enrolled>capacity, so line 58 can never be true) → dead code caused by D4. Tests: `test_WB_P01…P10`.

**MC/DC, line 48** `not (A and B) or C` (A: 0<=enrolled, B: enrolled<=capacity, C: capacity<1), Python short-circuit shown as NE = not evaluated:
| Test | A | B | C | Decision | Data |
|---|---|---|---|---|---|
| R1 | T | T | F | False | enrolled 10, cap 30 |
| R2 | T | T | T | True | enrolled 0, cap 0 |
| R3 | T | F | NE | True | enrolled 31, cap 30 |
| R4 | F | NE | NE | True | enrolled −1, cap 30 |
Independence pairs: **A (R1,R4)**, **B (R1,R3)**, **C (R1,R2)**. Also done: lines 30/32 (3 tests each) and `register_course` line 70 (`X and Y`: pairs X (T1,T3), Y (T1,T2)).

**Coverage** (measured with a local tracer because pytest-cov was unavailable offline — re-run the real commands and paste the output here):
| Stage | Statement | Branch | Uncovered |
|---|---|---|---|
| Black-box only | 96.4% (53/55) | 92.3% (24/26) | line 59 `return "WAITLISTED"`; line 71 waitlist append |
| + white-box (`tests/test_whitebox.py`) | 98.2% (54/55) | 96.2% (25/26) | line 59 — unreachable until D4 is fixed |
| After D1–D5 fixes | 100% | 100% | none |
Line 71 was covered by `test_WB_MCDC70_T1` using `mock.patch` on `registration_decision`.

## 3. Defects (see docs/DEFECTS.md)
D1 credit `<18` · D2 prerequisites any-vs-all · D3 dues threshold 1000 · D4 waitlist condition `>` (dead code) · D5 withdraw doesn't decrement enrolled. Issues: <#1…#5>. Fix PR: <link>. After fixes: 121/121 pass.

## 4. GitHub Evidence and Contributions

**Repository:** https://github.com/GhilmanShad/SQE_Assignment_2

### Group Members and Contributions

| Group Member | Contributions |
|---|---|
| Ghilman Shad Ali | Black-Box Testing |
| Mohammad Ramzan | GitHub Workflows |
| Atiq-ur-Rehman | White-Box Testing |
