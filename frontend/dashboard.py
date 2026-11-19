
import calendar
import sys
from pathlib import Path
from datetime import date

import pandas as pd
import streamlit as st

# Add the project root to Python's import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.database import SessionLocal
from app.services.roster_validator import validate_minimum_staffing
from app.services.roster_generator import generate_monthly_roster
from app.models import (
    Pod,
    Employee,
    Brand,
    Process,
    Assignment,
    Roster,
    RosterEntry,
    WorkingRule,
)

st.set_page_config(
    page_title="Smart Roster Management",
    page_icon="📅",
    layout="wide",
)

st.title("Smart Roster Management System")
st.caption("Employee scheduling, workforce allocation and coverage monitoring")

db = SessionLocal()

try:
    # Sidebar navigation
    st.sidebar.title("Navigation")

    page = st.sidebar.radio(
        "Select a section",
        [
            "Company Overview",
            "Employees",
            "Brands & Processes",
            "Monthly Roster",
            "Coverage Validation",
            "Manage Unavailability",
        ],
    )

    # Company Overview
    if page == "Company Overview":
        st.header("Company Overview")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Employees", db.query(Employee).count())
        col2.metric("Pods", db.query(Pod).count())
        col3.metric("Brands", db.query(Brand).count())
        col4.metric("Processes", db.query(Process).count())

        st.subheader("Pod Distribution")

        pods = db.query(Pod).all()

        pod_data = []

        for pod in pods:
            count = (
                db.query(Employee)
                .filter_by(pod_id=pod.id)
                .count()
            )

            pod_data.append({
                "Pod": pod.name,
                "Employees": count,
            })

        st.dataframe(
            pd.DataFrame(pod_data),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Roster Summary")

        rosters = db.query(Roster).all()

        if rosters:
            roster_data = []

            for roster in rosters:
                entries = (
                    db.query(RosterEntry)
                    .filter_by(roster_id=roster.id)
                    .all()
                )

                roster_data.append({
                    "Roster ID": roster.id,
                    "Month": calendar.month_name[roster.month],
                    "Year": roster.year,
                    "Total Entries": len(entries),
                    "Status": roster.status,
                })

            st.dataframe(
                pd.DataFrame(roster_data),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No rosters generated yet.")

    # Employees
    elif page == "Employees":
        st.header("Employee Directory")

        employees = (
            db.query(Employee)
            .order_by(Employee.id)
            .all()
        )

        employee_data = []

        for employee in employees:
            assignment_count = (
                db.query(Assignment)
                .filter_by(employee_id=employee.id)
                .count()
            )

            employee_data.append({
                "ID": employee.id,
                "Name": employee.name,
                "Email": employee.email,
                "Pod": employee.pod.name if employee.pod else "Unassigned",
                "Active": employee.is_active,
                "Assignments": assignment_count,
            })

        st.dataframe(
            pd.DataFrame(employee_data),
            use_container_width=True,
            hide_index=True,
        )

    # Brands and Processes
    
    # Brands, Processes and Pod Views
    elif page == "Brands & Processes":
        st.header("Organizational Views")

        view = st.radio(
            "Choose a view",
            ["By Pod", "By Brand", "By Process"],
            horizontal=True,
        )

        if view == "By Pod":
            pods = db.query(Pod).order_by(Pod.name).all()

            for pod in pods:
                with st.expander(pod.name):
                    employees = (
                        db.query(Employee)
                        .filter_by(pod_id=pod.id)
                        .order_by(Employee.name)
                        .all()
                    )

                    rows = []

                    for employee in employees:
                        assignments = (
                            db.query(Assignment)
                            .filter_by(employee_id=employee.id)
                            .all()
                        )

                        rows.append({
                            "Employee": employee.name,
                            "Email": employee.email,
                            "Assignments": len(assignments),
                            "Active": employee.is_active,
                        })

                    st.dataframe(
                        pd.DataFrame(rows),
                        use_container_width=True,
                        hide_index=True,
                    )

        elif view == "By Brand":
            brands = db.query(Brand).order_by(Brand.name).all()

            for brand in brands:
                with st.expander(brand.name):
                    assignments = (
                        db.query(Assignment)
                        .filter_by(brand_id=brand.id)
                        .all()
                    )

                    rows = [
                        {
                            "Employee": assignment.employee.name,
                            "Process": assignment.process.name,
                        }
                        for assignment in assignments
                    ]

                    if rows:
                        st.dataframe(
                            pd.DataFrame(rows),
                            use_container_width=True,
                            hide_index=True,
                        )
                    else:
                        st.info("No assignments for this brand.")

        elif view == "By Process":
            processes = (
                db.query(Process)
                .order_by(Process.name)
                .all()
            )

            for process in processes:
                with st.expander(process.name):
                    assignments = (
                        db.query(Assignment)
                        .filter_by(process_id=process.id)
                        .all()
                    )

                    rows = [
                        {
                            "Brand": assignment.brand.name,
                            "Employee": assignment.employee.name,
                        }
                        for assignment in assignments
                    ]

                    if rows:
                        st.dataframe(
                            pd.DataFrame(rows),
                            use_container_width=True,
                            hide_index=True,
                        )
                    else:
                        st.info("No assignments for this process.")


    # Monthly Roster
    
    # Monthly Roster
    elif page == "Monthly Roster":
        st.header("Monthly Employee Roster")

        st.subheader("Generate a New Roster")

        col1, col2 = st.columns(2)

        with col1:
            selected_month = st.selectbox(
                "Select month",
                options=list(range(1, 13)),
                format_func=lambda m: calendar.month_name[m],
                index=0,
                key="generation_month",
            )

        with col2:
            selected_year = st.number_input(
                "Select year",
                min_value=2026,
                max_value=2035,
                value=2027,
                step=1,
                key="generation_year",
            )

        if st.button("Generate Roster", type="primary"):
            try:
                result = generate_monthly_roster(
                    db=db,
                    month=selected_month,
                    year=int(selected_year),
                )

                st.success(
                    f"Roster generated successfully! "
                    f"Roster ID: {result['roster_id']}"
                )

                st.write("Total scheduled entries:", result["total_entries"])
                st.write("Unfilled staffing positions:", result["unfilled_positions"])

            except ValueError as error:
                st.error(str(error))

            except Exception as error:
                st.error(f"Roster generation failed: {error}")

        st.divider()
        st.subheader("Existing Rosters")

        rosters = (
            db.query(Roster)
            .order_by(Roster.year, Roster.month)
            .all()
        )

        if not rosters:
            st.info("No rosters generated yet.")
        else:
            roster_options = {
                f"{calendar.month_name[r.month]} {r.year} (ID: {r.id})": r.id
                for r in rosters
            }

            selected_roster = st.selectbox(
                "Select roster to view",
                options=list(roster_options.keys()),
                key="view_roster",
            )

            roster_id = roster_options[selected_roster]

            entries = (
                db.query(RosterEntry)
                .filter_by(roster_id=roster_id)
                .order_by(
                    RosterEntry.work_date,
                    RosterEntry.employee_id,
                )
                .all()
            )

            roster_data = []

            for entry in entries:
                assignment = entry.assignment

                roster_data.append({
                    "Date": entry.work_date,
                    "Employee": entry.employee.name,
                    "Brand": assignment.brand.name if assignment else "N/A",
                    "Process": assignment.process.name if assignment else "N/A",
                    "Status": entry.status,
                })

            roster_df = pd.DataFrame(roster_data)

            status_filter = st.multiselect(
                "Filter by status",
                options=sorted(roster_df["Status"].unique()),
                default=sorted(roster_df["Status"].unique()),
            )

            filtered_df = roster_df[
                roster_df["Status"].isin(status_filter)
            ]

            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True,
            )

            st.download_button(
                "Download roster CSV",
                data=filtered_df.to_csv(index=False),
                file_name="monthly_roster.csv",
                mime="text/csv",
            )


    # Coverage Validation
    elif page == "Coverage Validation":
        st.header("Coverage Validation")

        rosters = db.query(Roster).order_by(Roster.id).all()

        if not rosters:
            st.info("Generate a roster before checking coverage.")
        else:
            selected_roster = st.selectbox(
                "Select roster ID",
                options=[r.id for r in rosters],
            )

            entries = (
                db.query(RosterEntry)
                .filter_by(roster_id=selected_roster)
                .all()
            )

            roster = next(
                r for r in rosters if r.id == selected_roster
            )

            staffing_counts = {}

            for entry in entries:
                if entry.status != "SCHEDULED":
                    continue

                if entry.assignment is None:
                    continue

                key = (
                    entry.work_date,
                    entry.assignment.brand_id,
                    entry.assignment.process_id,
                )

                staffing_counts[key] = staffing_counts.get(key, 0) + 1

            
            validation = validate_minimum_staffing(
                db,
                selected_roster,
            )

            col1, col2 = st.columns(2)

            col1.metric("Total Staffing Gaps", validation["total_gaps"])
            col2.metric("Coverage Status", validation["coverage_status"])

            if validation["gaps"]:
                st.warning("Some processes do not meet minimum staffing requirements.")

                gap_rows = []

                for gap in validation["gaps"]:
                    brand = db.query(Brand).filter_by(id=gap["brand_id"]).first()
                    process = db.query(Process).filter_by(id=gap["process_id"]).first()

                    gap_rows.append({
                        "Date": gap["date"],
                        "Brand": brand.name if brand else "Unknown",
                        "Process": process.name if process else "Unknown",
                        "Required": gap["required_staff"],
                        "Scheduled": gap["scheduled_staff"],
                        "Shortage": gap["shortage"],
                    })

                st.dataframe(
                    pd.DataFrame(gap_rows),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.success("All processes meet their minimum staffing requirements.")



    
    # Manage Unavailability
    elif page == "Manage Unavailability":
        st.header("Mark Employee Unavailable")

        st.write(
            "Select an employee and date to update the generated roster."
        )

        roster = (
            db.query(Roster)
            .filter_by(id=1)
            .first()
        )

        if roster is None:
            st.warning("Generate a roster before managing unavailability.")
        else:
            employees = (
                db.query(Employee)
                .filter(Employee.is_active == True)
                .order_by(Employee.name)
                .all()
            )

            employee_options = {
                f"{employee.name} (ID: {employee.id})": employee.id
                for employee in employees
            }

            with st.form("unavailability_form"):
                selected_employee = st.selectbox(
                    "Select employee",
                    options=list(employee_options.keys()),
                )

                unavailable_date = st.date_input(
                    "Unavailable date",
                    value=date(2026, 12, 2),
                    min_value=date(roster.year, roster.month, 1),
                    max_value=date(
                        roster.year,
                        roster.month,
                        calendar.monthrange(roster.year, roster.month)[1],
                    ),
                )

                reason = st.text_input(
                    "Reason",
                    value="Manual unavailability",
                )

                submitted = st.form_submit_button(
                    "Mark Unavailable"
                )

            if submitted:
                employee_id = employee_options[selected_employee]

                entry = (
                    db.query(RosterEntry)
                    .filter_by(
                        roster_id=roster.id,
                        employee_id=employee_id,
                        work_date=unavailable_date,
                        status="SCHEDULED",
                    )
                    .first()
                )

                if entry is None:
                    st.error(
                        "No scheduled entry found for this employee on this date."
                    )
                else:
                    entry.status = "UNAVAILABLE"
                    db.commit()

                    st.success(
                        f"{selected_employee} marked unavailable on "
                        f"{unavailable_date}."
                    )

                    validation = validate_minimum_staffing(
                        db,
                        roster.id,
                    )

                    st.metric(
                        "Updated Staffing Gaps",
                        validation["total_gaps"],
                    )

                    st.write(
                        "Coverage Status:",
                        validation["coverage_status"],
                    )

                    

finally:
    db.close()
