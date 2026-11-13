"""Black-box tests for the Student Course Registration System.

Expected results are derived ONLY from REQUIREMENTS.md / the SRS, never from
the implementation.  Techniques: ECP, BVA, Decision Table (DT).

A5 (optimisation): every case lives in ONE registry.  A case that is an exact
duplicate across techniques (same inputs, same requirement, same expected
result) is executed once but keeps ALL its technique IDs in `traces`
(e.g. "ECP-05+DT-07"), so traceability is preserved.
"""
import copy
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from registration import (  # noqa: E402
    Course, Student, check_credit_limit, prerequisites_satisfied,
    register_course, registration_decision, withdraw_course,
)


# ---------------------------------------------------------------- helpers
def make_student(**kw):
    base = dict(student_id="S001", completed_courses=set(), current_credits=0,
                outstanding_dues=0, registered_courses=set())
    base.update(kw)
    return Student(**base)


def make_course(**kw):
    base = dict(code="CS201", credit_hours=3, capacity=30, enrolled=10,
                prerequisites=set(), waitlist=[])
    base.update(kw)
    return Course(**base)


def case_key(*parts):
    """Canonical form of a case's inputs + expected (used for duplicate check)."""
    def norm(v):
        if isinstance(v, dict):
            return tuple(sorted((k, norm(x)) for k, x in v.items()))
        if isinstance(v, (set, frozenset, list, tuple)):
            return tuple(sorted(map(str, v)))
        return v
    return tuple(norm(p) for p in parts)


# ------------------------------------------------ registry: decision cases
# (traces, requirement, description, student_kwargs, course_kwargs, expected)
DECISION_CASES = [
    # ---- dues (FR-04)
    ("ECP-05+DT-07", "FR-04", "dues positive (blocking class)",
     dict(outstanding_dues=5000), {}, "DUES_BLOCK"),
    ("ECP-06+ECP-12+BVA-12+DT-06", "FR-04/08", "dues = 0, seats free, no prereq, credits ok",
     {}, {}, "REGISTERED"),
    ("BVA-11", "FR-04", "dues = 1 (just above 0)", dict(outstanding_dues=1), {}, "DUES_BLOCK"),
    ("BVA-13", "FR-04", "dues = 1000", dict(outstanding_dues=1000), {}, "DUES_BLOCK"),
    # ---- availability (FR-08)
    ("ECP-13+BVA-15+DT-05", "FR-08", "enrolled == capacity (30/30)",
     {}, dict(enrolled=30), "WAITLISTED"),
    ("BVA-14", "FR-08", "enrolled = capacity-1 (29/30)", {}, dict(enrolled=29), "REGISTERED"),
    ("BVA-16", "FR-08", "capacity = 1 (min), enrolled = 0", {}, dict(capacity=1, enrolled=0), "REGISTERED"),
    ("BVA-17", "FR-08", "capacity = 1, enrolled = 1", {}, dict(capacity=1, enrolled=1), "WAITLISTED"),
    # ---- already registered (FR-05)
    ("ECP-16+DT-08", "FR-05", "already registered",
     dict(registered_courses={"CS201"}), {}, "ALREADY_REGISTERED"),
    # ---- prerequisites (FR-03/06)
    ("ECP-08", "FR-03/06", "course has NO prerequisites (student has others)",
     dict(completed_courses={"CS101"}), {}, "REGISTERED"),
    ("ECP-09", "FR-03/06", "ALL prerequisites completed",
     dict(completed_courses={"CS101", "MATH101"}), dict(prerequisites={"CS101", "MATH101"}), "REGISTERED"),
    ("ECP-10+DT-09", "FR-06", "SOME prerequisites completed (SRS scenario 3)",
     dict(completed_courses={"CS101"}), dict(prerequisites={"CS101", "MATH101"}), "PREREQUISITES_MISSING"),
    ("ECP-11", "FR-06", "NONE of the prerequisites completed",
     {}, dict(prerequisites={"CS101", "MATH101"}), "PREREQUISITES_MISSING"),
    # ---- credit limit (FR-01/07)
    ("ECP-02+DT-10", "FR-07", "16 + 3 = 19 > 18 (SRS scenario 2)",
     dict(current_credits=16), dict(credit_hours=3), "CREDIT_LIMIT"),
    ("BVA-18", "FR-07", "15 + 3 = 18 exactly (SRS scenario 1)",
     dict(current_credits=15), dict(credit_hours=3), "REGISTERED"),
    ("BVA-19", "FR-07", "14 + 4 = 18 exactly, max course credits",
     dict(current_credits=14), dict(credit_hours=4), "REGISTERED"),
    ("BVA-20", "FR-07", "15 + 4 = 19 just over limit",
     dict(current_credits=15), dict(credit_hours=4), "CREDIT_LIMIT"),
    ("BVA-21", "FR-07", "current credits = 18 (max) + 1",
     dict(current_credits=18), dict(credit_hours=1), "CREDIT_LIMIT"),
    ("BVA-22", "FR-07", "current credits = 0 (min), course = 1 (min)",
     dict(current_credits=0), dict(credit_hours=1), "REGISTERED"),
    ("BVA-23", "FR-07", "current credits = 0, course = 4 (max)",
     dict(current_credits=0), dict(credit_hours=4), "REGISTERED"),
    ("BVA-24", "FR-07", "17 + 1 = 18 exactly",
     dict(current_credits=17), dict(credit_hours=1), "REGISTERED"),
    # ---- decision table: priority combinations (FR-09)
    ("DT-01", "FR-09", "D,R,P,C,S all true -> dues wins",
     dict(outstanding_dues=1, registered_courses={"CS201"}, current_credits=18),
     dict(prerequisites={"CS101"}, enrolled=30), "DUES_BLOCK"),
    ("DT-02", "FR-09", "R,P,C,S true (no dues) -> already registered wins",
     dict(registered_courses={"CS201"}, current_credits=18),
     dict(prerequisites={"CS101"}, enrolled=30), "ALREADY_REGISTERED"),
    ("DT-03", "FR-09", "P,C,S true -> prerequisites win",
     dict(current_credits=18), dict(prerequisites={"CS101"}, enrolled=30), "PREREQUISITES_MISSING"),
    ("DT-04", "FR-09", "C,S true -> credit limit beats waitlist",
     dict(current_credits=16), dict(credit_hours=3, enrolled=30), "CREDIT_LIMIT"),
    ("DT-11", "FR-09", "D and R true -> dues wins",
     dict(outstanding_dues=1, registered_courses={"CS201"}), {}, "DUES_BLOCK"),
    ("DT-12", "FR-09", "R and P true -> already registered wins",
     dict(registered_courses={"CS201"}), dict(prerequisites={"CS101"}), "ALREADY_REGISTERED"),
    ("DT-13", "FR-09", "P and C true -> prerequisites win",
     dict(current_credits=18), dict(prerequisites={"CS101"}), "PREREQUISITES_MISSING"),
]

# (traces, requirement, description, student_kwargs, course_kwargs, message)
DECISION_RAISE_CASES = [
    ("ECP-07+BVA-25", "FR-15", "dues = -1 (negative)", dict(outstanding_dues=-1), {}, "Invalid dues"),
    ("ECP-14+BVA-26", "FR-15", "capacity = 0 (below min 1)", {}, dict(capacity=0, enrolled=0),
     "Invalid capacity or enrollment"),
    ("ECP-15", "FR-15", "enrolled well above capacity (35/30)", {}, dict(enrolled=35),
     "Invalid capacity or enrollment"),
    ("BVA-27", "FR-15", "enrolled = capacity+1 (31/30)", {}, dict(enrolled=31),
     "Invalid capacity or enrollment"),
    ("BVA-28", "FR-15", "enrolled = -1", {}, dict(enrolled=-1), "Invalid capacity or enrollment"),
    ("DT-15", "FR-15", "dues invalid AND capacity invalid -> dues validated first",
     dict(outstanding_dues=-1), dict(capacity=0, enrolled=0), "Invalid dues"),
]

# check_credit_limit: (traces, requirement, description, (current,new), expected)
CREDIT_CASES = [
    ("ECP-01", "FR-01", "valid, well under limit 10+3", (10, 3), True),
    ("ECP-03", "FR-01", "over limit 16+3", (16, 3), False),
    ("BVA-01", "FR-01", "min/min 0+1", (0, 1), True),
    ("BVA-02", "FR-01", "0+4", (0, 4), True),
    ("BVA-03", "FR-01", "18+1 (max current)", (18, 1), False),
    ("BVA-04", "FR-01", "14+4 = 18 exactly", (14, 4), True),
    ("BVA-05", "FR-01", "15+4 = 19", (15, 4), False),
    ("BVA-06", "FR-01", "17+1 = 18 exactly", (17, 1), True),
]
CREDIT_RAISE_CASES = [
    ("ECP-04", "FR-02", "current credits far above 18", (25, 2), "Invalid current credits"),
    ("ECP-18", "FR-02", "course credits far above 4", (5, 9), "Invalid course credits"),
    ("BVA-07", "FR-02", "current = -1", (-1, 1), "Invalid current credits"),
    ("BVA-08", "FR-02", "current = 19", (19, 1), "Invalid current credits"),
    ("BVA-09", "FR-02", "course = 0", (5, 0), "Invalid course credits"),
    ("BVA-10", "FR-02", "course = 5", (5, 5), "Invalid course credits"),
    ("BVA-29", "FR-02", "both invalid -> current checked first", (19, 0), "Invalid current credits"),
]
# (traces, requirement, description, completed, required, expected)
PREREQ_CASES = [
    ("ECP-19", "FR-03", "required empty", {"CS101"}, set(), True),
    ("ECP-20", "FR-03", "all required completed", {"CS101", "MATH101", "X"}, {"CS101", "MATH101"}, True),
    ("ECP-21", "FR-03", "only some required completed", {"CS101"}, {"CS101", "MATH101"}, False),
    ("ECP-22", "FR-03", "none of required completed", {"X"}, {"CS101", "MATH101"}, False),
]


def _p(row, n):
    """Turn a registry row into a pytest.param whose id is the trace string."""
    return pytest.param(*row[n:], id=row[0])


# =========================================================== function tests
@pytest.mark.parametrize("args,expected", [_p(r, 3) for r in CREDIT_CASES])
def test_check_credit_limit_returns(args, expected):
    assert check_credit_limit(*args) is expected


@pytest.mark.parametrize("args,msg", [_p(r, 3) for r in CREDIT_RAISE_CASES])
def test_check_credit_limit_raises(args, msg):
    with pytest.raises(ValueError, match=msg):
        check_credit_limit(*args)


@pytest.mark.parametrize("completed,required,expected", [_p(r, 3) for r in PREREQ_CASES])
def test_prerequisites_satisfied(completed, required, expected):
    assert prerequisites_satisfied(completed, required) is expected


# ======================================================= decision tests
@pytest.mark.parametrize("s_kw,c_kw,expected", [_p(r, 3) for r in DECISION_CASES])
def test_registration_decision_status(s_kw, c_kw, expected):
    student, course = make_student(**copy.deepcopy(s_kw)), make_course(**copy.deepcopy(c_kw))
    assert registration_decision(student, course) == expected


@pytest.mark.parametrize("s_kw,c_kw,msg", [_p(r, 3) for r in DECISION_RAISE_CASES])
def test_registration_decision_raises(s_kw, c_kw, msg):
    with pytest.raises(ValueError, match=msg):
        registration_decision(make_student(**s_kw), make_course(**c_kw))


@pytest.mark.parametrize("s_kw,c_kw,expected", [_p(r, 3) for r in DECISION_CASES])
def test_registration_decision_does_not_mutate(s_kw, c_kw, expected):
    """FR-10: the decision function must not change either object."""
    student, course = make_student(**copy.deepcopy(s_kw)), make_course(**copy.deepcopy(c_kw))
    before = copy.deepcopy((student, course))
    registration_decision(student, course)
    assert (student, course) == before


# ====================================================== state-change tests
def test_register_success_updates_state():  # FR-11
    s, c = make_student(current_credits=6), make_course(enrolled=10, credit_hours=3)
    assert register_course(s, c) == "REGISTERED"
    assert "CS201" in s.registered_courses
    assert s.current_credits == 9
    assert c.enrolled == 11
    assert c.waitlist == []


@pytest.mark.parametrize("s_kw,c_kw,status", [
    pytest.param(dict(outstanding_dues=1), {}, "DUES_BLOCK", id="SC-dues"),
    pytest.param(dict(registered_courses={"CS201"}, current_credits=3), {}, "ALREADY_REGISTERED", id="SC-dup"),
    pytest.param({}, dict(prerequisites={"CS101"}), "PREREQUISITES_MISSING", id="SC-prereq"),
    pytest.param(dict(current_credits=16), {}, "CREDIT_LIMIT", id="SC-credit"),
])
def test_register_unsuccessful_does_not_change_state(s_kw, c_kw, status):  # FR-12
    s, c = make_student(**s_kw), make_course(**c_kw)
    before = copy.deepcopy((s, c))
    assert register_course(s, c) == status
    assert (s, c) == before


def test_register_waitlisted_only_adds_to_waitlist():  # FR-08, FR-12
    s, c = make_student(current_credits=6), make_course(enrolled=30)
    assert register_course(s, c) == "WAITLISTED"
    assert c.waitlist == ["S001"]
    assert s.current_credits == 6
    assert s.registered_courses == set()
    assert c.enrolled == 30


def test_register_waitlisted_twice_no_duplicate_entry():  # FR-12 "only if absent"
    s, c = make_student(), make_course(enrolled=30)
    register_course(s, c)
    register_course(s, c)
    assert c.waitlist == ["S001"]


def test_register_full_course_never_exceeds_capacity():  # FR-08 consequence
    s, c = make_student(), make_course(enrolled=30)
    register_course(s, c)
    assert c.enrolled <= c.capacity


def test_withdraw_success_updates_state():  # FR-13 / SRS scenario 6
    s = make_student(current_credits=9, registered_courses={"CS201"})
    c = make_course(enrolled=11, credit_hours=3)
    assert withdraw_course(s, c) is True
    assert "CS201" not in s.registered_courses
    assert s.current_credits == 6
    assert c.enrolled == 10


def test_withdraw_not_registered_changes_nothing():  # FR-14
    s, c = make_student(current_credits=9, registered_courses={"MATH101"}), make_course(enrolled=11)
    before = copy.deepcopy((s, c))
    assert withdraw_course(s, c) is False
    assert (s, c) == before


def test_register_then_withdraw_restores_original_state():  # FR-11 + FR-13
    s, c = make_student(current_credits=6), make_course(enrolled=10)
    before = copy.deepcopy((s, c))
    register_course(s, c)
    withdraw_course(s, c)
    assert (s, c) == before


# =================================================== A5: duplicate control
def test_registry_has_no_exact_duplicates():
    """A5: each executed case is unique (inputs + requirement + expected)."""
    seen = {}
    for row in DECISION_CASES + DECISION_RAISE_CASES:
        k = case_key("decision", row[1], row[3], row[4], row[5])
        assert k not in seen, f"{row[0]} duplicates {seen[k]}"
        seen[k] = row[0]
    for row in CREDIT_CASES + CREDIT_RAISE_CASES:
        k = case_key("credit", row[1], row[3], row[4])
        assert k not in seen, f"{row[0]} duplicates {seen[k]}"
        seen[k] = row[0]
    for row in PREREQ_CASES:
        k = case_key("prerequisite", row[1], row[3], row[4], row[5])
        assert k not in seen, f"{row[0]} duplicates {seen[k]}"
        seen[k] = row[0]