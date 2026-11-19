
from app.database import SessionLocal
from app.services.roster_generator import generate_monthly_roster

db = SessionLocal()

try:
    result = generate_monthly_roster(
        db=db,
        month=12,
        year=2026,
    )

    print("Roster generated successfully!")
    print(result)

except Exception as error:
    db.rollback()
    print("Roster generation failed:")
    print(error)

finally:
    db.close()
