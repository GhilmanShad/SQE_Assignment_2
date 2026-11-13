import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from registration import Course, Student, registration_decision


def student(**kwargs):
    data = {
        "student_id": "WB001",
        "completed_courses": set(),
        "current_credits": 0,
        "outstanding_dues": 0,
        "registered_courses": set(),
    }
    data.update(kwargs)
    return Student(**data)


def course(**kwargs):
    data = {
        "code": "CS201",
        "credit_hours": 3,
        "capacity": 30,
        "enrolled": 0,
        "prerequisites": set(),
        "waitlist": [],
    }
    data.update(kwargs)
    return Course(**data)


def test_wb01_dues_validation_has_priority_over_capacity_validation():
    """CFG P1: D=true; negative dues is checked before invalid capacity."""
    with pytest.raises(ValueError, match="Invalid dues"):
        registration_decision(
            student(outstanding_dues=-1),
            course(capacity=0, enrolled=0),
        )


def test_wb02_capacity_validation_short_circuits_when_enrolled_is_negative():
    """CFG P2 / condition A=false: B and C are not evaluated."""
    with pytest.raises(ValueError, match="Invalid capacity or enrollment"):
        registration_decision(student(), course(enrolled=-1))


def test_wb03_capacity_validation_short_circuits_when_enrolled_exceeds_capacity():
    """CFG P3 / condition A=true, B=false: C is not evaluated."""
    with pytest.raises(ValueError, match="Invalid capacity or enrollment"):
        registration_decision(student(), course(capacity=1, enrolled=2))


def test_wb04_zero_capacity_takes_right_operand_of_or():
    """CFG P4 / condition A=true, B=true, C=true."""
    with pytest.raises(ValueError, match="Invalid capacity or enrollment"):
        registration_decision(student(), course(capacity=0, enrolled=0))


def test_wb05_large_dues_take_dues_block_branch():
    """CFG P5: validation passes, then outstanding_dues > 1000 is true."""
    assert registration_decision(
        student(outstanding_dues=1001),
        course(),
    ) == "DUES_BLOCK"


def test_wb06_duplicate_registration_branch():
    """CFG P6: course code is already in registered_courses."""
    assert registration_decision(
        student(registered_courses={"CS201"}),
        course(),
    ) == "ALREADY_REGISTERED"


def test_wb07_missing_prerequisite_branch():
    """CFG P7: prerequisites_satisfied() returns false."""
    assert registration_decision(
        student(completed_courses=set()),
        course(prerequisites={"CS101"}),
    ) == "PREREQUISITES_MISSING"


def test_wb08_credit_limit_branch():
    """CFG P8: check_credit_limit() returns false."""
    assert registration_decision(
        student(current_credits=17),
        course(credit_hours=2),
    ) == "CREDIT_LIMIT"


def test_wb09_registered_path_and_unreachable_waitlist_false_branch():
    """CFG P10: all earlier decisions are false; enrolled > capacity is false."""
    assert registration_decision(
        student(current_credits=14),
        course(credit_hours=3, capacity=1, enrolled=0),
    ) == "REGISTERED"