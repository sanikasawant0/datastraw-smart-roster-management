from datetime import date

from pydantic import BaseModel


class EmployeeUnavailabilityRequest(BaseModel):
    employee_id: int
    work_date: date
    reason: str = "Manual unavailability"