
from datetime import date, time

from sqlalchemy import (
    String, Integer, Boolean, ForeignKey,
    Date, Time, UniqueConstraint, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


# 1. PODS
class Pod(Base):
    __tablename__ = "pods"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    lead_employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id"), nullable=True
    )

    employees = relationship(
        "Employee",
        back_populates="pod",
        foreign_keys="Employee.pod_id"
    )

    lead = relationship(
        "Employee",
        foreign_keys=[lead_employee_id],
        post_update=True
    )


# 2. EMPLOYEES
class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(
        String(150), unique=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True
    )

    pod_id: Mapped[int | None] = mapped_column(
        ForeignKey("pods.id"), nullable=True
    )

    pod = relationship(
        "Pod",
        back_populates="employees",
        foreign_keys=[pod_id]
    )

    assignments = relationship(
        "Assignment",
        back_populates="employee",
        cascade="all, delete-orphan"
    )


# 3. BRANDS
class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(100), unique=True
    )
    description: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    assignments = relationship(
        "Assignment", back_populates="brand"
    )

    working_rules = relationship(
        "WorkingRule", back_populates="brand"
    )


# 4. PROCESSES
class Process(Base):
    __tablename__ = "processes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(100), unique=True
    )

    assignments = relationship(
        "Assignment", back_populates="process"
    )

    working_rules = relationship(
        "WorkingRule", back_populates="process"
    )


# 5. EMPLOYEE-BRAND-PROCESS ASSIGNMENTS
class Assignment(Base):
    __tablename__ = "assignments"

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "brand_id",
            "process_id",
            name="unique_employee_brand_process"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id")
    )

    brand_id: Mapped[int] = mapped_column(
        ForeignKey("brands.id")
    )

    process_id: Mapped[int] = mapped_column(
        ForeignKey("processes.id")
    )

    employee = relationship(
        "Employee", back_populates="assignments"
    )

    brand = relationship(
        "Brand", back_populates="assignments"
    )

    process = relationship(
        "Process", back_populates="assignments"
    )


# 6. BRAND-PROCESS WORKING RULES
class WorkingRule(Base):
    __tablename__ = "working_rules"

    __table_args__ = (
        UniqueConstraint(
            "brand_id",
            "process_id",
            name="unique_brand_process_rule"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    brand_id: Mapped[int] = mapped_column(
        ForeignKey("brands.id")
    )

    process_id: Mapped[int] = mapped_column(
        ForeignKey("processes.id")
    )

    # Monday = 0, Sunday = 6
    operating_days: Mapped[list] = mapped_column(
        JSON, default=lambda: list(range(7))
    )

    operates_public_holidays: Mapped[bool] = mapped_column(
        Boolean, default=False
    )

    min_staff: Mapped[int] = mapped_column(
        Integer, default=1
    )

    # Optional minimum staffing for individual weekdays
    # Example: {"0": 2, "6": 3}
    day_minimums: Mapped[dict] = mapped_column(
        JSON, default=dict
    )

    brand = relationship(
        "Brand", back_populates="working_rules"
    )

    process = relationship(
        "Process", back_populates="working_rules"
    )


# 7. EMPLOYEE WEEKLY OFFS
class EmployeeWeeklyOff(Base):
    __tablename__ = "employee_weekly_offs"

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "weekday",
            name="unique_employee_weekly_off"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id")
    )

    # Monday = 0, Sunday = 6
    weekday: Mapped[int] = mapped_column(Integer)

    employee = relationship("Employee")


# 8. EMPLOYEE LEAVES AND COMP-OFFS
class EmployeeTimeOff(Base):
    __tablename__ = "employee_time_off"

    id: Mapped[int] = mapped_column(primary_key=True)

    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id")
    )

    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)

    leave_type: Mapped[str] = mapped_column(
        String(30)
    )
    status: Mapped[str] = mapped_column(
        String(30), default="PENDING"
    )

    employee = relationship("Employee")


# 9. PUBLIC HOLIDAYS
class PublicHoliday(Base):
    __tablename__ = "public_holidays"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(100))
    holiday_date: Mapped[date] = mapped_column(Date)

    location: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )


# 10. MONTHLY ROSTERS
class Roster(Base):
    __tablename__ = "rosters"

    id: Mapped[int] = mapped_column(primary_key=True)

    month: Mapped[int] = mapped_column(Integer)
    year: Mapped[int] = mapped_column(Integer)

    status: Mapped[str] = mapped_column(
        String(30), default="DRAFT"
    )

    entries = relationship(
        "RosterEntry",
        back_populates="roster",
        cascade="all, delete-orphan"
    )


# 11. DAILY ROSTER ENTRIES
class RosterEntry(Base):
    __tablename__ = "roster_entries"

    id: Mapped[int] = mapped_column(primary_key=True)

    roster_id: Mapped[int] = mapped_column(
        ForeignKey("rosters.id")
    )

    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id")
    )

    assignment_id: Mapped[int | None] = mapped_column(
        ForeignKey("assignments.id"), nullable=True
    )

    work_date: Mapped[date] = mapped_column(Date)

    # WORK, OFF, LEAVE, COMP_OFF, HOLIDAY
    status: Mapped[str] = mapped_column(String(30))

    start_time: Mapped[time | None] = mapped_column(
        Time, nullable=True
    )

    end_time: Mapped[time | None] = mapped_column(
        Time, nullable=True
    )

    roster = relationship(
        "Roster", back_populates="entries"
    )

    employee = relationship("Employee")

    assignment = relationship("Assignment")
