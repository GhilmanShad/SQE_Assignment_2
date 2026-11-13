# Defect log (copy each block into a GitHub Issue — C3)

Status of all defects: **Open** until the `defect-fixes` PR is merged. Fix is in `docs/defect_fixes.patch`.

| ID | Req | Title | Failing test IDs (initial run) | Expected | Actual |
|----|-----|-------|-------------------------------|----------|--------|
| D1 | FR-01, FR-07 | Total of exactly 18 credits is rejected | `test_check_credit_limit_returns[BVA-04]`, `[BVA-06]`; `test_registration_decision_status[BVA-18]`, `[BVA-19]`, `[BVA-24]` | `check_credit_limit(14,4)` → `True` | `False` (code uses `< 18`) |
| D2 | FR-03, FR-06 | Prerequisites satisfied if ANY (not ALL) are completed | `test_prerequisites_satisfied[ECP-21]`; `test_registration_decision_status[ECP-10+DT-09]` | completed={CS101}, required={CS101,MATH101} → `False` / `PREREQUISITES_MISSING` | `True` / `REGISTERED` (uses `intersection`) |
| D3 | FR-04 | Dues block only above Rs. 1000, not above Rs. 0 | `test_registration_decision_status[BVA-11]`, `[BVA-13]`, `[DT-01]`, `[DT-11]`; `test_register_unsuccessful_does_not_change_state[SC-dues]` | dues=1 → `DUES_BLOCK` | `REGISTERED` (code uses `> 1000`) |
| D4 | FR-08, FR-12 | Full course never returns WAITLISTED; seat count can exceed capacity | `test_registration_decision_status[ECP-13+BVA-15+DT-05]`, `[BVA-17]`; `test_register_waitlisted_only_adds_to_waitlist`; `..._twice_no_duplicate_entry`; `test_register_full_course_never_exceeds_capacity` | enrolled==capacity → `WAITLISTED` | `REGISTERED`; enrolled becomes capacity+1, next call raises ValueError (code uses `>`; branch is dead code) |
| D5 | FR-13 | Withdrawal does not decrement `course.enrolled` | `test_withdraw_success_updates_state`; `test_register_then_withdraw_restores_original_state` | enrolled 11 → 10 | stays 11 |

Reproduction (D1): `python -c "from registration import check_credit_limit as f; print(f(14,4))"` → prints `False`, SRS says `True`.
