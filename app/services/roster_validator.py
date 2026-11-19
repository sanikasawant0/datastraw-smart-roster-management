
import calendar
from collections import defaultdict
from datetime import date

from app.models import (
    Roster,
    RosterEntry,
    Assignment,
    WorkingRule,
    PublicHoliday,
)


def validate_minimum_staffing(db, roster_id: int):
    roster = db.query(Roster).filter_by(id=roster_id).first()

    if roster is None:
        raise ValueError(f"Roster {roster_id} does not exist.")

    entries = (
    db.query(RosterEntry)
    .filter_by(
        roster_id=roster_id,
        status="SCHEDULED",
    )
    .all()
)

    assignments = {
        assignment.id: assignment
        for assignment in db.query(Assignment).all()
    }

    rules = db.query(WorkingRule).all()
    holidays = {
        holiday.holiday_date
        for holiday in db.query(PublicHoliday).all()
    }

    # Count unique scheduled employees per date, brand and process.
    staffing_counts = defaultdict(set)

    for entry in entries:
        assignment = assignments.get(entry.assignment_id)

        if assignment is None:
            continue

        key = (
            entry.work_date,
            assignment.brand_id,
            assignment.process_id,
        )

        staffing_counts[key].add(entry.employee_id)

    gaps = []

    days_in_month = calendar.monthrange(
        roster.year,
        roster.month,
    )[1]

    for day in range(1, days_in_month + 1):
        work_date = date(roster.year, roster.month, day)
        weekday = work_date.weekday()

        for rule in rules:

            # Ignore dates when the process does not operate.
            if weekday not in rule.operating_days:
                continue

            # Ignore public holidays when the process is closed.
            if (
                work_date in holidays
                and not rule.operates_public_holidays
            ):
                continue

            required_staff = rule.day_minimums.get(
                str(weekday),
                rule.min_staff,
            )

            if required_staff <= 0:
                continue

            key = (
                work_date,
                rule.brand_id,
                rule.process_id,
            )

            scheduled_staff = len(staffing_counts.get(key, set()))

            if scheduled_staff < required_staff:
                gaps.append({
                    "date": work_date.isoformat(),
                    "brand_id": rule.brand_id,
                    "process_id": rule.process_id,
                    "required_staff": required_staff,
                    "scheduled_staff": scheduled_staff,
                    "shortage": required_staff - scheduled_staff,
                })

    return {
        "roster_id": roster_id,
        "total_gaps": len(gaps),
        "coverage_status": (
            "PASS" if not gaps else "GAPS_FOUND"
        ),
        "gaps": gaps,
    }
