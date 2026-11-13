# SE3002 Assignment 2 — Student Course Registration System

This repository contains the black-box and white-box test suites for the supplied
`registration.py` implementation. Expected results come from `REQUIREMENTS.md`
(the SRS), not from the implementation.

## Structure

```
registration.py                  system under test
REQUIREMENTS.md                  software requirements specification
requirements.txt                 pytest and pytest-cov
tests/test_blackbox.py           ECP, BVA and decision-table tests
tests/test_whitebox.py           CFG, branch, condition and MC/DC tests
docs/                            test design sheets, CFG, evidence and report
.github/workflows/tests.yml      CI: pytest + coverage on every push/PR
```

## Run the tests

```bash
python -m pip install -r requirements.txt
python -m pytest tests/ -v
python -m pytest tests/ -v --cov=registration --cov-branch --cov-report=term-missing
```

## Current result

`122 passed` with 100% statement and branch coverage of `registration.py`.

The pre-fix evidence is kept in `docs/initial_blackbox_run.txt` and
`docs/final_run_before_fixes.txt`. Defects D1–D5, their GitHub issues and the
fix PR are listed in `docs/DEFECTS.md` and `docs/testing_report.pdf`.

## Links

- Repository: https://github.com/GhilmanShad/SQE_Assignment_2
- Actions: https://github.com/GhilmanShad/SQE_Assignment_2/actions/workflows/tests.yml
