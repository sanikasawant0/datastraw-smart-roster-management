
from collections import defaultdict

from app.database import SessionLocal
from app.models import (
    Roster,
    RosterEntry,
    EmployeeWeeklyOff,
    EmployeeTimeOff,
    PublicHoliday,
    WorkingRule,
    Assignment,
)

db = SessionLocal()

try:
    rosters = db.query(Roster).order_by(Roster.id).all()

    weekly_offs = db.query(EmployeeWeeklyOff).all()
    approved_leaves = (
        db.query(EmployeeTimeOff)
        .filter(EmployeeTimeOff.status == "APPROVED")
        .all()
    )
    holidays = {
        h.holiday_date
        for h in db.query(PublicHoliday).all()
    }

    assignments = {
        a.id: a
        for a in db.query(Assignment).all()
    }

    rules = {
        (r.brand_id, r.process_id): r
        for r in db.query(WorkingRule).all()
    }

    weekly_off_map = defaultdict(set)

    for off in weekly_offs:
        weekly_off_map[off.employee_id].add(off.weekday)

    for roster in rosters:
        entries = (
            db.query(RosterEntry)
            .filter_by(
                roster_id=roster.id,
                status="SCHEDULED",
            )
            .all()
        )

        duplicate_count = defaultdict(int)
        leave_conflicts = []
        weekly_off_conflicts = []
        holiday_conflicts = []

        for entry in entries:
            duplicate_count[
                (entry.employee_id, entry.work_date)
            ] += 1

            if entry.work_date.weekday() in weekly_off_map[entry.employee_id]:
                weekly_off_conflicts.append(entry)

            for leave in approved_leaves:
                if (
                    leave.employee_id == entry.employee_id
                    and leave.start_date <= entry.work_date <= leave.end_date
                ):
                    leave_conflicts.append(entry)

            if entry.work_date in holidays:
                assignment = assignments.get(entry.assignment_id)

                if assignment:
                    rule = rules.get(
                        (assignment.brand_id, assignment.process_id)
                    )

                    if rule and not rule.operates_public_holidays:
                        holiday_conflicts.append(entry)

        duplicate_conflicts = sum(
            1 for count in duplicate_count.values() if count > 1
        )

        print(f"\nRoster: {roster.month}/{roster.year} (ID: {roster.id})")
        print("Employee-date conflicts:", duplicate_conflicts)
        print("Approved leave conflicts:", len(leave_conflicts))
        print("Weekly-off conflicts:", len(weekly_off_conflicts))
        print("Public holiday conflicts:", len(holiday_conflicts))

finally:
    db.close()
