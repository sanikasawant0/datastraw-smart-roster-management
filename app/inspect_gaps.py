
from app.database import SessionLocal
from app.models import Brand, Process, Assignment, Employee

from app.services.roster_validator import validate_minimum_staffing

db = SessionLocal()

try:
    result = validate_minimum_staffing(db, roster_id=1)

    brands = {b.id: b.name for b in db.query(Brand).all()}
    processes = {p.id: p.name for p in db.query(Process).all()}
    employees = {e.id: e.name for e in db.query(Employee).all()}

    assignments = db.query(Assignment).all()

    assigned_staff = {}

    for assignment in assignments:
        key = (assignment.brand_id, assignment.process_id)

        assigned_staff.setdefault(key, []).append(
            employees.get(assignment.employee_id, "Unknown")
        )

    print("TOTAL COVERAGE GAPS:", result["total_gaps"])
    print("\nFIRST 15 COVERAGE GAPS:\n")

    for gap in result["gaps"][:15]:
        key = (gap["brand_id"], gap["process_id"])

        print("Date:", gap["date"])
        print("Brand:", brands.get(gap["brand_id"]))
        print("Process:", processes.get(gap["process_id"]))
        print("Required:", gap["required_staff"])
        print("Scheduled:", gap["scheduled_staff"])
        print("Assigned employees:", assigned_staff.get(key, []))
        print("-" * 45)

finally:
    db.close()
