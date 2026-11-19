
# import calendar
# from collections import defaultdict
# from datetime import date

# from app.models import (
#     Employee,
#     Assignment,
#     WorkingRule,
#     EmployeeWeeklyOff,
#     EmployeeTimeOff,
#     PublicHoliday,
#     Roster,
#     RosterEntry,
# )


# def generate_monthly_roster(db, month: int, year: int):
#     if month < 1 or month > 12:
#         raise ValueError("Month must be between 1 and 12.")

#     existing_roster = (
#         db.query(Roster)
#         .filter_by(month=month, year=year)
#         .first()
#     )

#     if existing_roster:
#         raise ValueError(
#             f"A roster already exists for {month}/{year}."
#         )

#     try:
#         roster = Roster(
#             month=month,
#             year=year,
#             status="DRAFT",
#         )

#         db.add(roster)
#         db.flush()

#         employees = (
#             db.query(Employee)
#             .filter(Employee.is_active == True)
#             .all()
#         )

#         assignments = db.query(Assignment).all()
#         working_rules = db.query(WorkingRule).all()
#         weekly_offs = db.query(EmployeeWeeklyOff).all()

#         time_off_records = (
#             db.query(EmployeeTimeOff)
#             .filter(EmployeeTimeOff.status == "APPROVED")
#             .all()
#         )

#         public_holidays = db.query(PublicHoliday).all()

#         employee_map = {
#             employee.id: employee
#             for employee in employees
#         }

#         weekly_off_map = defaultdict(set)

#         for off in weekly_offs:
#             weekly_off_map[off.employee_id].add(off.weekday)

#         rule_map = {
#             (rule.brand_id, rule.process_id): rule
#             for rule in working_rules
#         }

#         time_off_map = defaultdict(list)

#         for record in time_off_records:
#             time_off_map[record.employee_id].append(record)

#         holiday_dates = {
#             holiday.holiday_date
#             for holiday in public_holidays
#         }

#         # Track how often each assignment is scheduled.
#         assignment_schedule_count = defaultdict(int)

#         entries = []
#         skipped_assignments = 0

#         days_in_month = calendar.monthrange(year, month)[1]

#         for day in range(1, days_in_month + 1):
#             work_date = date(year, month, day)
#             weekday = work_date.weekday()

#             is_public_holiday = work_date in holiday_dates

#             # Collect eligible assignments for each employee.
#             eligible_by_employee = defaultdict(list)

#             for assignment in assignments:
#                 employee = employee_map.get(
#                     assignment.employee_id
#                 )

#                 if employee is None:
#                     continue

#                 rule = rule_map.get(
#                     (assignment.brand_id, assignment.process_id)
#                 )

#                 if rule is None:
#                     continue

#                 if weekday not in rule.operating_days:
#                     continue

#                 if (
#                     is_public_holiday
#                     and not rule.operates_public_holidays
#                 ):
#                     continue

#                 if weekday in weekly_off_map[employee.id]:
#                     continue

#                 unavailable = any(
#                     record.start_date <= work_date <= record.end_date
#                     for record in time_off_map[employee.id]
#                 )

#                 if unavailable:
#                     continue

#                 eligible_by_employee[employee.id].append(
#                     assignment
#                 )

#             # Select only one assignment for each employee per day.
#             for employee_id, employee_assignments in (
#                 eligible_by_employee.items()
#             ):
#                 employee_assignments.sort(
#                     key=lambda assignment: (
#                         assignment_schedule_count[assignment.id],
#                         assignment.id,
#                     )
#                 )

#                 selected_assignment = employee_assignments[0]

#                 entries.append(
#                     RosterEntry(
#                         roster_id=roster.id,
#                         employee_id=employee_id,
#                         assignment_id=selected_assignment.id,
#                         work_date=work_date,
#                         status="SCHEDULED",
#                     )
#                 )

#                 assignment_schedule_count[
#                     selected_assignment.id
#                 ] += 1

#                 skipped_assignments += (
#                     len(employee_assignments) - 1
#                 )

#         db.add_all(entries)
#         db.commit()

#         return {
#             "roster_id": roster.id,
#             "month": month,
#             "year": year,
#             "total_entries": len(entries),
#             "skipped_assignments": skipped_assignments,
#             "status": "DRAFT",
#         }

#     except Exception:
#         db.rollback()
#         raise





import calendar
from collections import defaultdict
from datetime import date

from app.models import (
    Employee,
    Assignment,
    WorkingRule,
    EmployeeWeeklyOff,
    EmployeeTimeOff,
    PublicHoliday,
    Roster,
    RosterEntry,
)


def generate_monthly_roster(db, month: int, year: int):
    if month < 1 or month > 12:
        raise ValueError("Month must be between 1 and 12.")

    existing_roster = (
        db.query(Roster)
        .filter_by(month=month, year=year)
        .first()
    )

    if existing_roster:
        raise ValueError(
            f"A roster already exists for {month}/{year}."
        )

    try:
        roster = Roster(
            month=month,
            year=year,
            status="DRAFT",
        )

        db.add(roster)
        db.flush()

        employees = (
            db.query(Employee)
            .filter(Employee.is_active == True)
            .all()
        )

        assignments = db.query(Assignment).all()
        rules = db.query(WorkingRule).all()
        weekly_offs = db.query(EmployeeWeeklyOff).all()

        approved_time_off = (
            db.query(EmployeeTimeOff)
            .filter(EmployeeTimeOff.status == "APPROVED")
            .all()
        )

        holidays = {
            holiday.holiday_date
            for holiday in db.query(PublicHoliday).all()
        }

        employee_map = {
            employee.id: employee
            for employee in employees
        }

        assignments_by_employee = defaultdict(list)

        for assignment in assignments:
            if assignment.employee_id in employee_map:
                assignments_by_employee[
                    assignment.employee_id
                ].append(assignment)

        rule_map = {
            (rule.brand_id, rule.process_id): rule
            for rule in rules
        }

        weekly_off_map = defaultdict(set)

        for off in weekly_offs:
            weekly_off_map[off.employee_id].add(off.weekday)

        time_off_map = defaultdict(list)

        for record in approved_time_off:
            time_off_map[record.employee_id].append(record)

        assignment_schedule_count = defaultdict(int)

        entries = []
        total_unfilled_positions = 0

        days_in_month = calendar.monthrange(year, month)[1]

        for day in range(1, days_in_month + 1):
            work_date = date(year, month, day)
            weekday = work_date.weekday()
            is_holiday = work_date in holidays

            # Find employees available on this date.
            available_employees = set()

            for employee in employees:
                if weekday in weekly_off_map[employee.id]:
                    continue

                if any(
                    record.start_date <= work_date <= record.end_date
                    for record in time_off_map[employee.id]
                ):
                    continue

                available_employees.add(employee.id)

            # Find operating processes and their staffing requirements.
            daily_requirements = []

            for rule in rules:
                if weekday not in rule.operating_days:
                    continue

                if is_holiday and not rule.operates_public_holidays:
                    continue

                required_staff = rule.day_minimums.get(
                    str(weekday),
                    rule.min_staff,
                )

                if required_staff <= 0:
                    continue

                candidates = [
                    assignment
                    for assignment in assignments
                    if (
                        assignment.brand_id == rule.brand_id
                        and assignment.process_id == rule.process_id
                        and assignment.employee_id in available_employees
                    )
                ]

                daily_requirements.append({
                    "rule": rule,
                    "required": required_staff,
                    "candidates": candidates,
                })

            # Prioritize processes with fewer available employees.
            daily_requirements.sort(
                key=lambda item: (
                    len(item["candidates"]) / item["required"],
                    len(item["candidates"]),
                    item["rule"].id,
                )
            )

            scheduled_employees = set()

            # Fill each process requirement without double-booking employees.
            for requirement in daily_requirements:
                rule = requirement["rule"]
                required_staff = requirement["required"]
                candidates = requirement["candidates"]

                scheduled_for_process = 0

                while scheduled_for_process < required_staff:
                    eligible_candidates = [
                        assignment
                        for assignment in candidates
                        if assignment.employee_id not in scheduled_employees
                    ]

                    if not eligible_candidates:
                        break

                    # Prefer employees with fewer alternative assignments.
                    eligible_candidates.sort(
                        key=lambda assignment: (
                            len([
                                other
                                for other in assignments_by_employee[
                                    assignment.employee_id
                                ]
                                if (
                                    other.employee_id in available_employees
                                    and other.employee_id not in scheduled_employees
                                )
                            ]),
                            assignment_schedule_count[assignment.id],
                            assignment.id,
                        )
                    )

                    selected = eligible_candidates[0]

                    entries.append(
                        RosterEntry(
                            roster_id=roster.id,
                            employee_id=selected.employee_id,
                            assignment_id=selected.id,
                            work_date=work_date,
                            status="SCHEDULED",
                        )
                    )

                    scheduled_employees.add(selected.employee_id)

                    assignment_schedule_count[selected.id] += 1
                    scheduled_for_process += 1

                total_unfilled_positions += (
                    required_staff - scheduled_for_process
                )

        db.add_all(entries)
        db.commit()

        return {
            "roster_id": roster.id,
            "month": month,
            "year": year,
            "total_entries": len(entries),
            "unfilled_positions": total_unfilled_positions,
            "status": "DRAFT",
        }

    except Exception:
        db.rollback()
        raise
