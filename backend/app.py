from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from domain import (
    get_db,
    get_patient,
    init_db,
    list_patients,
    validate_patient,
)


app = FastAPI(title="Patient Admission Management API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"
ASSETS_DIR = FRONTEND_DIR / "assets"
INDEX_FILE = FRONTEND_DIR / "index.html"


def error_response(message, errors=None, status_code=400):
    content = {"message": message}
    if errors:
        content["errors"] = errors
    return JSONResponse(status_code=status_code, content=content)


async def read_json(request):
    try:
        return await request.json()
    except Exception:
        return None


@app.get("/api/patients")
def read_patients(search: str = "", ward: str = "", department: str = "", doctor: str = ""):
    with get_db() as connection:
        patients = list_patients(connection, search, ward, department, doctor)
    return {"patients": patients}


@app.post("/api/patients")
async def create_patient(request: Request):
    payload = await read_json(request)
    clean, errors = validate_patient(payload)
    if errors:
        return error_response("Please correct the highlighted fields.", errors)
    columns = ", ".join(clean)
    placeholders = ", ".join("?" for _ in clean)
    with get_db() as connection:
        cursor = connection.execute(
            f"INSERT INTO patients ({columns}) VALUES ({placeholders})",
            tuple(clean.values()),
        )
        patient = get_patient(connection, cursor.lastrowid)
    return JSONResponse(
        status_code=201,
        content={"message": "Patient added successfully.", "patient": patient},
    )


@app.put("/api/patients/{patient_id}")
async def update_patient(patient_id: int, request: Request):
    payload = await read_json(request)
    clean, errors = validate_patient(payload)
    if errors:
        return error_response("Please correct the highlighted fields.", errors)
    with get_db() as connection:
        if get_patient(connection, patient_id) is None:
            return error_response("Patient not found.", status_code=404)
        assignments = ", ".join(f"{column} = ?" for column in clean)
        connection.execute(
            f"UPDATE patients SET {assignments} WHERE id = ?",
            (*clean.values(), patient_id),
        )
        patient = get_patient(connection, patient_id)
    return {"message": "Patient updated successfully.", "patient": patient}


@app.patch("/api/patients/{patient_id}/discharge")
def discharge_patient(patient_id: int):
    with get_db() as connection:
        if get_patient(connection, patient_id) is None:
            return error_response("Patient not found.", status_code=404)
        connection.execute(
            "UPDATE patients SET status = 'Discharged' WHERE id = ?", (patient_id,)
        )
        patient = get_patient(connection, patient_id)
    return {"message": "Patient marked as discharged.", "patient": patient}


@app.delete("/api/patients/{patient_id}")
def delete_patient(patient_id: int):
    with get_db() as connection:
        if get_patient(connection, patient_id) is None:
            return error_response("Patient not found.", status_code=404)
        connection.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    return {"message": "Patient deleted successfully."}


if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")


@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend(full_path: str):
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    return JSONResponse(
        status_code=404,
        content={"message": "Frontend build not found. Run npm run build in frontend/."},
    )
