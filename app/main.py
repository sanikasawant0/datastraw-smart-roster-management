
from fastapi import FastAPI, HTTPException

from app.database import SessionLocal
from app.models import Employee, Brand, Process, Roster, RosterEntry
from app.schemas import EmployeeUnavailabilityRequest
from app.services.roster_validator import validate_minimum_staffing

app = FastAPI(
    title="Smart Roster Management System",
    description="Employee scheduling and roster validation system",
    version="1.0.0",
)


@app.get("/")
def home():
    return {
        "message": "Smart Roster Management System API is running."
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/database-summary")
def database_summary():
    db = SessionLocal()

    try:
        return {
            "employees": db.query(Employee).count(),
            "brands": db.query(Brand).count(),
            "processes": db.query(Process).count(),
            "rosters": db.query(Roster).count(),
            "database_status": "connected",
        }
    finally:
        db.close()


@app.get("/rosters/{roster_id}/validation")
def roster_validation(roster_id: int):
    db = SessionLocal()

    try:
        result = validate_minimum_staffing(db, roster_id)
        return result

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    finally:
        db.close()


@app.post("/rosters/{roster_id}/unavailability")
def mark_employee_unavailable(
    roster_id: int,
    request: EmployeeUnavailabilityRequest,
):
    db = SessionLocal()

    try:
        roster = db.query(Roster).filter_by(id=roster_id).first()

        if roster is None:
            raise HTTPException(
                status_code=404,
                detail="Roster not found.",
            )

        employee = (
            db.query(Employee)
            .filter_by(id=request.employee_id)
            .first()
        )

        if employee is None:
            raise HTTPException(
                status_code=404,
                detail="Employee not found.",
            )

        if (
            request.work_date.month != roster.month
            or request.work_date.year != roster.year
        ):
            raise HTTPException(
                status_code=400,
                detail="The date must belong to the selected roster month.",
            )

        entry = (
            db.query(RosterEntry)
            .filter_by(
                roster_id=roster_id,
                employee_id=request.employee_id,
                work_date=request.work_date,
                status="SCHEDULED",
            )
            .first()
        )

        if entry is None:
            raise HTTPException(
                status_code=404,
                detail="No scheduled entry found for this employee on this date.",
            )

        entry.status = "UNAVAILABLE"

        db.flush()

        validation = validate_minimum_staffing(db, roster_id)

        db.commit()

        return {
            "message": "Employee marked unavailable successfully.",
            "employee_id": request.employee_id,
            "employee_name": employee.name,
            "work_date": request.work_date.isoformat(),
            "reason": request.reason,
            "updated_entry_status": entry.status,
            "updated_validation": validation,
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
