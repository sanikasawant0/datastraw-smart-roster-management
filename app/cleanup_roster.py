
from app.database import SessionLocal
from app.models import Roster, RosterEntry

db = SessionLocal()

try:
    roster = (
        db.query(Roster)
        .filter_by(month=12, year=2026)
        .first()
    )

    if roster:
        db.query(RosterEntry).filter_by(
            roster_id=roster.id
        ).delete()

        db.delete(roster)
        db.commit()

        print("Old December 2026 test roster deleted.")
    else:
        print("No existing test roster found.")

finally:
    db.close()
