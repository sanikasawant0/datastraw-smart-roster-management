# Smart Roster Management System

A browser-based workforce scheduling application for managing employees, operational pods, brands, processes, monthly rosters, and staffing coverage.

## 1. Project Overview

This project was developed as part of the Datastraw Technologies Internship Assessment.

The Smart Roster Management System helps operations teams generate monthly employee schedules while considering brand-specific working rules, employee assignments, weekly offs, approved leave, public holidays, and minimum staffing requirements.

The application identifies scheduling conflicts and staffing shortages and allows managers to make manual availability changes and review their impact.

### Implemented sample dataset

| Resource | Count |
|---|---:|
| Employees | 32 |
| Operational pods | 4 |
| Brands | 24 |
| Processes | 6 |
| Employee assignments | 40 |
| Brand-process working rules | 32 |

Approximately 79.17% of the sample brands have a single dedicated employee, while the remaining brands have multiple assigned employees.

## 2. Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| Backend API | FastAPI |
| Frontend | Streamlit |
| Database | SQLite |
| ORM | SQLAlchemy |
| Data processing | Pandas |
| API documentation | Swagger UI |

## 3. Architecture Overview

The application uses a layered architecture.

- **Frontend:** Streamlit provides the browser-based dashboard for viewing employees, organizational assignments, monthly rosters, coverage gaps, and manual unavailability.
- **Backend:** FastAPI exposes endpoints for database status, roster validation, and employee unavailability updates.
- **Business logic:** Separate service modules handle roster generation and minimum staffing validation.
- **Database:** SQLAlchemy models represent employees, pods, brands, processes, assignments, working rules, availability records, and roster entries.

### Project structure

```text
datastraw-roster-management/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── init_db.py
│   ├── seed.py
│   ├── test_roster.py
│   ├── test_validator.py
│   ├── check_roster.py
│   ├── cleanup_roster.py
│   ├── inspect_gaps.py
│   │
│   └── services/
│       ├── roster_generator.py
│       └── roster_validator.py
│
├── frontend/
│   └── dashboard.py
│
├── tests/
│
├── requirements.txt
├── README.md
└── roster.db (generated locally)
```

## 4. Database Design

The database contains 11 tables:

| Table | Purpose |
|---|---|
| Pod | Stores operational pods and their leads |
| Employee | Stores employee information and pod membership |
| Brand | Stores client brand information |
| Process | Stores operational processes |
| Assignment | Maps employees to brands and processes |
| WorkingRule | Stores operating days and minimum staffing requirements |
| EmployeeWeeklyOff | Stores employee weekly-off days |
| EmployeeTimeOff | Stores leave and comp-off records |
| PublicHoliday | Stores public holiday dates |
| Roster | Stores monthly roster information |
| RosterEntry | Stores individual employee schedule entries |

The Assignment table connects employees, brands, and processes. This supports employees working across multiple assignments and multiple employees handling the same brand or process.

## 5. Scheduling Logic

The roster generator uses a deterministic, greedy scheduling heuristic.

For each date in the selected month, it:

1. Identifies active employees.
2. Excludes employees on weekly offs or approved leave.
3. Checks whether each brand-process combination operates on that date.
4. Applies public holiday rules.
5. Reads the minimum staffing requirement for each operating process.
6. Prioritizes processes with fewer available employees relative to their staffing requirements.
7. Assigns eligible employees without scheduling the same employee more than once on a date.
8. Tracks unfilled staffing positions.

The validator independently checks scheduled entries against the configured minimum staffing requirements.

When staffing is insufficient, the application reports coverage gaps instead of assigning employees in violation of availability constraints.

**Note:** The scheduling algorithm is a heuristic, not a globally optimal optimization solver. It may leave positions unfilled even when a different allocation strategy could potentially improve coverage.

## 6. Features

### Company Overview
- Employee, pod, brand, and process counts.
- Pod distribution.
- Monthly roster summary.

### Organizational Views
- Employee directory.
- Pod-level employee information.
- Brand-level employee assignments.
- Process-level brand and employee assignments.

### Monthly Roster
- Select a month and year.
- Generate a monthly roster.
- View generated schedules.
- Filter roster entries by status.
- Download roster data as CSV.

### Coverage Validation
- Validate minimum staffing requirements.
- Identify staffing gaps by date, brand, and process.
- Display required staff, scheduled staff, and shortages.

### Employee Unavailability
- Mark an employee unavailable for a scheduled date.
- Update the roster entry.
- Recalculate staffing coverage after the change.

### FastAPI Endpoints

Start the API and open `/docs` to explore the interactive Swagger documentation.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | API welcome message |
| GET | `/health` | Health check |
| GET | `/database-summary` | Database record counts |
| GET | `/rosters/{roster_id}/validation` | Validate roster coverage |
| POST | `/rosters/{roster_id}/unavailability` | Mark an employee unavailable |

## 7. Setup Instructions

### Prerequisites

- Python 3.11 or later recommended.
- Git.
- Visual Studio Code or another Python editor.

### Step 1: Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd datastraw-roster-management
```

### Step 2: Create a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Initialize the database

```bash
python -m app.init_db
```

### Step 5: Seed sample data

```bash
python -m app.seed
```

Run the seed command once against a fresh database.

### Step 6: Start the FastAPI backend

```bash
python -m uvicorn app.main:app --reload
```

API URL:

`http://127.0.0.1:8000`

Swagger documentation:

`http://127.0.0.1:8000/docs`

### Step 7: Start the Streamlit dashboard

Open a second terminal, activate the virtual environment, and run:

```bash
streamlit run frontend/dashboard.py
```

Dashboard URL:

`http://localhost:8501`

The API and dashboard use the same SQLite database.

## 8. Testing and Validation

The application was tested with two monthly rosters:

| Metric | December 2026 | January 2027 |
|---|---:|---:|
| Roster ID | 1 | 2 |
| Scheduled entries | 697 | 702 |
| Unfilled staffing positions | 209 | 203 |
| Validated staffing gaps | 211 | 203 |
| Employee-date conflicts | 0 | 0 |

The December generator and validator figures differ because the generator counts unfilled staffing positions, whereas the validator counts affected brand-process-date combinations.

Additional validation checks confirmed:

- No duplicate employee-date assignments.
- No approved leave conflicts.
- No weekly-off conflicts.
- No assignments on public holidays when the applicable process is closed.
- Manual unavailability changes persist in the database and affect coverage validation.

Two manual unavailability scenarios were demonstrated using the dashboard and verified in the database.

### Run validation scripts

```bash
python -m app.check_roster
python -m app.test_validator
```

## 9. Notes and Assumptions

- The sample dataset uses fictional employees, brands, and operational information.
- Weekdays use Python's weekday convention: Monday = 0 and Sunday = 6.
- Minimum staffing requirements are configured for each brand-process combination.
- Approved leave and weekly offs prevent an employee from being scheduled.
- Pending leave does not automatically block scheduling.
- Public holiday rules are evaluated separately for each process.
- An employee can have multiple assignments but cannot be scheduled for multiple assignments on the same date.
- Manual unavailability changes the status of an existing roster entry. It does not automatically regenerate the entire roster.
- The sample application uses SQLite for simplicity. A production deployment would benefit from a managed relational database.
- The current dashboard uses seeded organizational data; full CRUD management for employees, brands, processes, and assignments is not yet exposed.
- Staffing shortages are displayed for manager review. The application does not automatically resolve every shortage.

## 10. Tell Us How You Think

### 1. How did you model employees, brands, processes, pods, and their relationships?

I used a relational database design with separate tables for employees, pods, brands, processes, and assignments.

The Assignment table connects employees with brands and processes, allowing many-to-many relationships. Employees belong to operational pods, and each pod can have a designated lead.

WorkingRule stores process-specific operating days and minimum staffing requirements.

### 2. How does your system generate a roster and determine whether it satisfies the required constraints?

The generator evaluates each date and identifies available employees, operating processes, and staffing requirements.

It uses a greedy allocation strategy that prioritizes processes with fewer available resources. Employees are assigned only when they satisfy availability constraints and have not already been scheduled that day.

A separate validator compares scheduled employees against minimum staffing requirements and reports shortages.

### 3. How did you handle the difference between single-resource brands and brands with multiple employees?

I represented all employee-to-brand-to-process relationships through the Assignment table.

This allows a brand to have one dedicated employee or multiple employees assigned to different or shared processes.

The sample dataset contains 19 single-resource brands out of 24, approximately 79.17%.

### 4. What happens when an employee manages all processes for a brand but is unavailable on a required working day?

The generator excludes that employee from scheduling on the unavailable date.

If no other eligible employee is assigned to the required process, the system reports a staffing gap.

It does not override weekly offs or approved leave to force coverage.

### 5. How does your system handle conflicting requirements or insufficient staffing?

The generator prevents an employee from being scheduled more than once on the same date.

It also respects approved leave, weekly offs, and process operating calendars.

When the available workforce cannot meet a minimum staffing requirement, the system records unfilled positions and the validator reports coverage gaps for operational review.

### 6. Which parts of the process did you automate, and which did you leave under human control? Why?

Roster generation, availability filtering, staffing allocation, and coverage validation are automated.

Managers retain control over monthly roster generation, manual availability changes, and reviewing staffing gaps.

This approach allows the system to automate repetitive scheduling while keeping operational decisions under human supervision.

### 7. If the company doubled its team and brand count, what would you change about your solution?

I would migrate SQLite to PostgreSQL, introduce database migrations and stronger indexing, and improve query efficiency.

I would also consider a constraint optimization solver for larger scheduling problems, introduce role-based access control, and separate the API and frontend deployment environments.

### 8. If you had one additional week to work on this, what would you improve first?

I would first improve the scheduling algorithm to reduce staffing gaps through better resource allocation and backup recommendations.

I would also add complete employee and assignment management, automated tests for scheduling edge cases, approval workflows, and improved reporting.

## 11. Future Improvements

- Constraint-based roster optimization.
- Backup employee recommendations.
- Employee preference management.
- Fair distribution of weekly offs.
- Automatic roster regeneration after availability changes.
- Employee, brand, and process management screens.
- Roster approval workflows.
- Expanded automated test coverage.

## 12. Author

**Sanika Sawant**

Computer Engineering Graduate

University of Mumbai

LinkedIn: https://www.linkedin.com/in/sanika-ss/

GitHub: https://github.com/sanikasawant0/
