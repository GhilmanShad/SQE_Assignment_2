"""White-box (structural) tests for registration.py.

Each test documents the structure it targets (path / branch / condition).
Line numbers refer to registration.py as supplied (unmodified).
Expected values are still taken from the SRS.
"""
import os
import sys
from unittest import mock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from registration import (  # noqa: E402
    Course, Student, check_credit_limit, prerequisites_satisfied,
    register_course, registration_decision, withdraw_course,
)


def S(**kw):
    base = dict(student_id="S001", completed_courses=set(), current_credits=0,
                outstanding_dues=0, registered_courses=set())
    base.update(kw)
    return Student(**base)


def C(**kw):
    base = dict(code="CS201", credit_hours=3, capacity=30, enrolled=10,
                prerequisites=set(), waitlist=[])
    base.update(kw)
    return Course(**base)


# ---------------------------------------------------------------------------
# B1  Basis path set for registration_decision()  (V(G) = 10, atomic-condition
# convention).  P09 (enrolled > capacity -> WAITLISTED) is INFEASIBLE because
# line 48 already rejects enrolled > capacity; documented in the report.
# ---------------------------------------------------------------------------
def test_WB_P01_dues_negative_raises():                       # line 46 True
    with pytest.raises(ValueError, match="Invalid dues"):
        registration_decision(S(outstanding_dues=-1), C())


def test_WB_P02_enrolled_negative_raises():                   # line 48, cond A False
    with pytest.raises(ValueError, match="Invalid capacity or enrollment"):
        registration_decision(S(), C(enrolled=-1))


def test_WB_P03_enrolled_above_capacity_raises():             # line 48, A True, B False
    with pytest.raises(ValueError, match="Invalid capacity or enrollment"):
        registration_decision(S(), C(enrolled=31))


def test_WB_P04_capacity_zero_raises():                       # line 48, A True, B True, C True
    with pytest.raises(ValueError, match="Invalid capacity or enrollment"):
        registration_decision(S(), C(capacity=0, enrolled=0))


def test_WB_P05_dues_block_branch():                          # line 50 True
    assert registration_decision(S(outstanding_dues=1001), C()) == "DUES_BLOCK"


def test_WB_P06_already_registered_branch():                  # line 52 True
    assert registration_decision(S(registered_courses={"CS201"}), C()) == "ALREADY_REGISTERED"


def test_WB_P07_prerequisites_missing_branch():               # line 54 True
    assert registration_decision(S(), C(prerequisites={"CS101"})) == "PREREQUISITES_MISSING"


def test_WB_P08_credit_limit_branch():                        # line 56 True
    assert registration_decision(S(current_credits=16), C()) == "CREDIT_LIMIT"


def test_WB_P10_registered_path_all_false():                  # lines 46-58 all False -> 60
    assert registration_decision(S(), C()) == "REGISTERED"


# ---------------------------------------------------------------------------
# B3  MC/DC for line 48:   not (A and B) or C
#       A: 0 <= enrolled   B: enrolled <= capacity   C: capacity < 1
#   R1 (T,T,F)->no raise   R2 (T,T,T)->raise   R3 (T,F,NE)->raise   R4 (F,NE,NE)->raise
#   Independence pairs:  A:(R1,R4)   B:(R1,R3)   C:(R1,R2)
# ---------------------------------------------------------------------------
def test_WB_MCDC48_R1_all_valid_no_raise():
    assert registration_decision(S(), C(enrolled=10, capacity=30)) == "REGISTERED"


def test_WB_MCDC48_R2_only_C_true():
    with pytest.raises(ValueError, match="Invalid capacity or enrollment"):
        registration_decision(S(), C(enrolled=0, capacity=0))


def test_WB_MCDC48_R3_B_false_C_not_evaluated():
    with pytest.raises(ValueError, match="Invalid capacity or enrollment"):
        registration_decision(S(), C(enrolled=31, capacity=30))


def test_WB_MCDC48_R4_A_false_B_and_C_not_evaluated():
    with pytest.raises(ValueError, match="Invalid capacity or enrollment"):
        registration_decision(S(), C(enrolled=-1, capacity=30))


# MC/DC for line 30/32 range checks  (a: lo <= x,  b: x <= hi): 3 tests each
@pytest.mark.parametrize("cur,ok", [
    pytest.param(5, True, id="WB-MCDC30-T,T"),
    pytest.param(-1, False, id="WB-MCDC30-F,NE"),
    pytest.param(19, False, id="WB-MCDC30-T,F"),
])
def test_WB_MCDC30_current_credits_range(cur, ok):
    if ok:
        assert check_credit_limit(cur, 1) is True
    else:
        with pytest.raises(ValueError, match="Invalid current credits"):
            check_credit_limit(cur, 1)


@pytest.mark.parametrize("new,ok", [
    pytest.param(2, True, id="WB-MCDC32-T,T"),
    pytest.param(0, False, id="WB-MCDC32-F,NE"),
    pytest.param(5, False, id="WB-MCDC32-T,F"),
])
def test_WB_MCDC32_course_credits_range(new, ok):
    if ok:
        assert check_credit_limit(5, new) is True
    else:
        with pytest.raises(ValueError, match="Invalid course credits"):
            check_credit_limit(5, new)


# ---------------------------------------------------------------------------
# B2/B3  register_course line 70:  decision == "WAITLISTED" and sid not in waitlist
#   The WAITLISTED status is unreachable from valid input in the supplied code
#   (defect D4), so registration_decision is patched to isolate this decision.
#   X: decision == "WAITLISTED"    Y: id not in waitlist
#   T1 (T,T)->append   T2 (T,F)->no append   T3 (F,NE)->no append
#   Independence:  X:(T1,T3)   Y:(T1,T2)
# ---------------------------------------------------------------------------
def test_WB_MCDC70_T1_waitlisted_and_absent_appends():        # covers line 71
    s, c = S(), C(enrolled=30)
    with mock.patch("registration.registration_decision", return_value="WAITLISTED"):
        assert register_course(s, c) == "WAITLISTED"
    assert c.waitlist == ["S001"]


def test_WB_MCDC70_T2_waitlisted_but_already_listed_no_append():
    s, c = S(), C(enrolled=30, waitlist=["S001"])
    with mock.patch("registration.registration_decision", return_value="WAITLISTED"):
        assert register_course(s, c) == "WAITLISTED"
    assert c.waitlist == ["S001"]


def test_WB_MCDC70_T3_not_waitlisted_second_condition_not_evaluated():
    s, c = S(registered_courses={"CS201"}), C()     # ALREADY_REGISTERED: X is False
    assert register_course(s, c) == "ALREADY_REGISTERED"
    assert c.waitlist == []


def test_WB_BR66_registered_branch_updates_state():           # line 66 True
    s, c = S(), C()
    assert register_course(s, c) == "REGISTERED"
    assert (s.current_credits, c.enrolled, s.registered_courses) == (3, 11, {"CS201"})


# ---------------------------------------------------------------------------
# Branch tests for the small helpers
# ---------------------------------------------------------------------------
def test_WB_BR39_empty_required_short_circuits_true():        # line 39 True
    assert prerequisites_satisfied(set(), set()) is True


def test_WB_BR39_nonempty_required_all_present():             # line 39 False -> 41
    assert prerequisites_satisfied({"A", "B"}, {"A", "B"}) is True


def test_WB_BR39_nonempty_required_none_present():            # line 41 returns False
    assert prerequisites_satisfied({"X"}, {"A"}) is False


def test_WB_BR_withdraw_not_registered_returns_false():       # withdraw: if True
    s, c = S(), C()
    assert withdraw_course(s, c) is False


def test_WB_BR_withdraw_registered_returns_true():            # withdraw: if False
    s, c = S(current_credits=3, registered_courses={"CS201"}), C()
    assert withdraw_course(s, c) is True
    assert s.current_credits == 0
