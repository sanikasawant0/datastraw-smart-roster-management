
from datetime import date

from app.database import SessionLocal
from app.models import (
    Pod,
    Employee,
    Brand,
    Process,
    Assignment,
    WorkingRule,
    EmployeeWeeklyOff,
    EmployeeTimeOff,
    PublicHoliday,
)


def seed_database():
    db = SessionLocal()

    try:
        print("Starting database seeding...")

        
        # Prevent duplicate or incomplete seed data
        if db.query(Employee).first():
            print("Database already contains employees. Seeding cancelled.")
            return

        # Remove orphaned pods from an incomplete previous initialization
        if db.query(Pod).first():
            print("Removing incomplete pod records...")
            db.query(Pod).delete(synchronize_session=False)
            db.commit()

        # 1. Create pods
        pod_names = [
            "Customer Support",
            "Operations",
            "Quality & Training",
            "Escalations",
        ]

        pods = [Pod(name=name) for name in pod_names]

        db.add_all(pods)
        db.flush()

        # 2. Create 24 brands
        brand_names = [
            "Brand Alpha", "Brand Beta", "Brand Gamma", "Brand Delta",
            "Brand Epsilon", "Brand Zeta", "Brand Eta", "Brand Theta",
            "Brand Iota", "Brand Kappa", "Brand Lambda", "Brand Mu",
            "Brand Nu", "Brand Xi", "Brand Omicron", "Brand Pi",
            "Brand Rho", "Brand Sigma", "Brand Tau", "Brand Omega",
            "Brand Upsilon", "Brand Phi", "Brand Chi", "Brand Psi",
        ]

        brands = [
            Brand(name=name, description=f"Fictional brand: {name}")
            for name in brand_names
        ]

        db.add_all(brands)
        db.flush()

        # 3. Create processes
        process_names = [
            "Email Support",
            "Chat Support",
            "Voice Support",
            "Order Management",
            "Returns & Refunds",
            "Technical Support",
        ]

        processes = [
            Process(name=name) for name in process_names
        ]

        db.add_all(processes)
        db.flush()

        # 4. Create 32 employees
        employee_names = [
            "Aarav Sharma", "Diya Patel", "Rohan Mehta", "Ananya Rao",
            "Ishaan Shah", "Meera Nair", "Kabir Joshi", "Sara Khan",
            "Arjun Desai", "Ira Kulkarni", "Vivaan Gupta", "Aditi Verma",
            "Reyansh Singh", "Myra Iyer", "Dev Malhotra", "Kiara Das",
            "Advik Menon", "Saanvi Kapoor", "Krish Bhat", "Anvi Reddy",
            "Atharv Jain", "Tara Sinha", "Neil Thomas", "Riya Chavan",
            "Yash Patil", "Avni Mishra", "Dhruv Shetty", "Nisha Roy",
            "Omkar Sawant", "Pooja Naik", "Karan Gill", "Simran Kaur",
        ]

        employees = []

        for index, name in enumerate(employee_names):
            employee = Employee(
                name=name,
                email=f"employee{index + 1}@example.com",
                is_active=True,
                pod_id=pods[index // 8].id,
            )
            employees.append(employee)

        db.add_all(employees)
        db.flush()

        # Assign one lead to each pod
        for index, pod in enumerate(pods):
            pod.lead_employee_id = employees[index * 8].id

        db.flush()

        print("32 employees and 4 pods created.")

        # 5. Create employee assignments

        # First 19 brands: one dedicated employee each
        for index in range(19):
            db.add(
                Assignment(
                    employee_id=employees[index].id,
                    brand_id=brands[index].id,
                    process_id=processes[index % 6].id,
                )
            )

        # Last 5 brands: shared employee groups
        # Employee counts: 3, 3, 3, 2, 2
        shared_groups = [
            [19, 20, 21],
            [22, 23, 24],
            [25, 26, 27],
            [28, 29],
            [30, 31],
        ]

        for group_index, employee_group in enumerate(shared_groups):
            brand_index = 19 + group_index

            for employee_index in employee_group:
                db.add(
                    Assignment(
                        employee_id=employees[employee_index].id,
                        brand_id=brands[brand_index].id,
                        process_id=processes[0].id,
                    )
                )

        db.flush()

        # Additional process assignments
        extra_assignments = [
            (0, 0, 1),
            (2, 2, 3),
            (4, 4, 5),
            (21, 19, 1),
            (24, 20, 1),
            (27, 21, 1),
            (28, 22, 2),
            (30, 23, 2),
        ]

        for employee_index, brand_index, process_index in extra_assignments:
            db.add(
                Assignment(
                    employee_id=employees[employee_index].id,
                    brand_id=brands[brand_index].id,
                    process_id=processes[process_index].id,
                )
            )

        db.flush()

        print("Employee assignments created.")

        # 6. Create working rules based on assignments
        assignments = db.query(Assignment).all()

        assignment_counts = {}

        for assignment in assignments:
            key = (assignment.brand_id, assignment.process_id)
            assignment_counts[key] = assignment_counts.get(key, 0) + 1

        for (brand_id, process_id), staff_count in assignment_counts.items():

            brand_index = next(
                index
                for index, brand in enumerate(brands)
                if brand.id == brand_id
            )

            if brand_index % 3 == 0:
                operating_days = [0, 1, 2, 3, 4, 5, 6]
            elif brand_index % 3 == 1:
                operating_days = [0, 1, 2, 3, 4, 5]
            else:
                operating_days = [0, 1, 2, 3, 4]

            min_staff = 2 if staff_count >= 3 else 1

            db.add(
                WorkingRule(
                    brand_id=brand_id,
                    process_id=process_id,
                    operating_days=operating_days,
                    operates_public_holidays=False,
                    min_staff=min_staff,
                    day_minimums={
                        str(day): min_staff if day in operating_days else 0
                        for day in range(7)
                    },
                )
            )

        db.flush()

        print("Working rules created.")

        # 7. Create weekly offs
        weekly_offs = []

        for index, employee in enumerate(employees):
            weekly_offs.append(
                EmployeeWeeklyOff(
                    employee_id=employee.id,
                    weekday=index % 7,
                )
            )

        db.add_all(weekly_offs)
        db.flush()

        print("Weekly offs created.")

        # 8. Create public holidays
        holidays = [
            PublicHoliday(
                name="Christmas",
                holiday_date=date(2026, 12, 25),
                location="India",
            ),
        ]

        db.add_all(holidays)
        db.flush()

        print("Public holidays created.")

        # 9. Create leave and comp-off records
        time_off_records = [
            EmployeeTimeOff(
                employee_id=employees[4].id,
                start_date=date(2026, 12, 8),
                end_date=date(2026, 12, 10),
                leave_type="PLANNED_LEAVE",
                status="APPROVED",
            ),
            EmployeeTimeOff(
                employee_id=employees[12].id,
                start_date=date(2026, 12, 15),
                end_date=date(2026, 12, 15),
                leave_type="COMP_OFF",
                status="APPROVED",
            ),
            EmployeeTimeOff(
                employee_id=employees[20].id,
                start_date=date(2026, 12, 18),
                end_date=date(2026, 12, 20),
                leave_type="PLANNED_LEAVE",
                status="PENDING",
            ),
        ]

        db.add_all(time_off_records)
        db.flush()

        print("Leave and comp-off records created.")

        # 10. Commit all records
        db.commit()

        print("Database seeding completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error while seeding database: {e}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
