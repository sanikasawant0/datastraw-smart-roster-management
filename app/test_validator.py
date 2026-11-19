
from app.database import SessionLocal
from app.services.roster_validator import validate_minimum_staffing

db = SessionLocal()

try:
    result = validate_minimum_staffing(
        db=db,
        roster_id=1,
    )

    print("Minimum staffing validation completed.")
    print("Coverage status:", result["coverage_status"])
    print("Total staffing gaps:", result["total_gaps"])

    for gap in result["gaps"][:10]:
        print(gap)

finally:
    db.close()
