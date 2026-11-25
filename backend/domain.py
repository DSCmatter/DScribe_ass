from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
import re
import sqlite3


DB_PATH = Path(__file__).resolve().parent / "data" / "patients.db"

GENDERS = ["Male", "Female", "Other"]
WARDS = ["General", "ICU", "Pediatrics", "Maternity", "Emergency", "Surgery"]
DEPARTMENTS = [
    "General Medicine",
    "Cardiology",
    "Neurology",
    "Orthopedics",
    "Pediatrics",
    "Dermatology",
]
DOCTORS = [
    "Dr. A Sharma",
    "Dr. R Iyer",
    "Dr. M Rao",
    "Dr. S Menon",
    "Dr. K Verma",
    "Dr. P Nair",
]
STATUSES = ["Admitted", "Discharged"]

OPTIONS = {
    "gender": GENDERS,
    "ward": WARDS,
    "department": DEPARTMENTS,
    "doctor": DOCTORS,
    "status": STATUSES,
}

NAME_PATTERN = re.compile(r"^[A-Za-z]+(?: [A-Za-z]+)*$")

COLUMNS = (
    "id",
    "name",
    "age",
    "gender",
    "ward",
    "department",
    "doctor",
    "admission_date",
    "status",
)


def validate_patient(payload):
    errors = {}
    clean = {}

    if not isinstance(payload, dict):
        return {}, {"form": "Request body must be a JSON object."}

    name = payload.get("name")
    if name is None or (isinstance(name, str) and not name.strip()):
        errors["name"] = "Name is required."
    elif not isinstance(name, str) or not NAME_PATTERN.fullmatch(name.strip()):
        errors["name"] = "Name must contain letters only."
    else:
        clean["name"] = name.strip()

    age = payload.get("age")
    if age is None or age == "":
        errors["age"] = "Age is required."
    elif isinstance(age, bool):
        errors["age"] = "Age must be a number between 0 and 120."
    else:
        try:
            parsed_age = int(age)
        except (TypeError, ValueError):
            parsed_age = None
        if parsed_age is None or not 0 <= parsed_age <= 120:
            errors["age"] = "Age must be a number between 0 and 120."
        else:
            clean["age"] = parsed_age

    for field, values in OPTIONS.items():
        value = payload.get(field)
        label = field.replace("_", " ").capitalize()
        if value is None or value == "":
            errors[field] = f"{label} is required."
        elif value not in values:
            errors[field] = f"Select a valid {label.lower()}."
        else:
            clean[field] = value

    admission_date = payload.get("admission_date")
    if admission_date is None or admission_date == "":
        errors["admission_date"] = "Admission date is required."
    else:
        try:
            parsed_date = datetime.strptime(str(admission_date), "%Y-%m-%d").date()
        except ValueError:
            parsed_date = None
        if parsed_date is None:
            errors["admission_date"] = "Enter a valid admission date."
        elif parsed_date > date.today():
            errors["admission_date"] = "Admission date cannot be in the future."
        else:
            clean["admission_date"] = parsed_date.isoformat()

    return clean, errors


@contextmanager
def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    with get_db() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                ward TEXT NOT NULL,
                department TEXT NOT NULL,
                doctor TEXT NOT NULL,
                admission_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Admitted'
            )
            """
        )


def to_patient(row):
    return {column: row[column] for column in COLUMNS}


def get_patient(connection, patient_id):
    row = connection.execute(
        "SELECT * FROM patients WHERE id = ?", (patient_id,)
    ).fetchone()
    return to_patient(row) if row else None


def list_patients(connection, search="", ward="", department="", doctor=""):
    clauses = []
    params = []
    if search:
        clauses.append("LOWER(name) LIKE ?")
        params.append(f"%{search.lower()}%")
    for column, value in (("ward", ward), ("department", department), ("doctor", doctor)):
        if value:
            clauses.append(f"{column} = ?")
            params.append(value)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = connection.execute(
        f"SELECT * FROM patients {where} ORDER BY id DESC", params
    ).fetchall()
    return [to_patient(row) for row in rows]
