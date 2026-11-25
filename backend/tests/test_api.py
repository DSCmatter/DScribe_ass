import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

import app as api
import domain


VALID = {
    "name": "Jane Smith",
    "age": 34,
    "gender": "Female",
    "ward": "General",
    "department": "Cardiology",
    "doctor": "Dr. A Sharma",
    "admission_date": "2026-11-20",
    "status": "Admitted",
}


class PatientApiTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        domain.DB_PATH = Path(self.temp.name) / "data" / "patients.db"
        domain.init_db()
        self.client = TestClient(api.app)

    def tearDown(self):
        self.temp.cleanup()

    def create(self, **overrides):
        payload = {**VALID, **overrides}
        return self.client.post("/api/patients", json=payload)

    def test_create_list_and_persist_in_new_process(self):
        response = self.create()
        self.assertEqual(response.status_code, 201)
        created = response.json()["patient"]
        self.assertEqual(created["name"], "Jane Smith")
        self.assertEqual(created["status"], "Admitted")

        script = (
            "import sys\n"
            "from pathlib import Path\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "import domain\n"
            "domain.DB_PATH = Path(sys.argv[2])\n"
            "with domain.get_db() as connection:\n"
            "    print(len(domain.list_patients(connection)))\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script, str(BACKEND_DIR), str(domain.DB_PATH)],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(result.stdout.strip(), "1")

    def test_validation_is_rejected_with_clear_messages(self):
        cases = [
            ({"name": "Jane123"}, "name"),
            ({"name": ""}, "name"),
            ({"age": 121}, "age"),
            ({"age": -1}, "age"),
            ({"age": "abc"}, "age"),
            ({"gender": "Unknown"}, "gender"),
            ({"ward": "Ward 9"}, "ward"),
            ({"department": "Heart"}, "department"),
            ({"doctor": "Dr. Who"}, "doctor"),
            ({"admission_date": "2099-01-01"}, "admission_date"),
            ({"admission_date": "not-a-date"}, "admission_date"),
            ({"status": "Waiting"}, "status"),
        ]
        for overrides, field in cases:
            with self.subTest(overrides=overrides):
                response = self.create(**overrides)
                self.assertEqual(response.status_code, 400)
                body = response.json()
                self.assertIn("Please correct the highlighted fields.", body["message"])
                self.assertIn(field, body["errors"])

    def test_edit_discharge_and_delete(self):
        patient_id = self.create().json()["patient"]["id"]

        updated = self.client.put(
            f"/api/patients/{patient_id}",
            json={**VALID, "name": "John Smith", "age": 45},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["patient"]["name"], "John Smith")

        discharged = self.client.patch(f"/api/patients/{patient_id}/discharge")
        self.assertEqual(discharged.status_code, 200)
        self.assertEqual(discharged.json()["patient"]["status"], "Discharged")

        again = self.client.patch(f"/api/patients/{patient_id}/discharge")
        self.assertEqual(again.status_code, 200)

        deleted = self.client.delete(f"/api/patients/{patient_id}")
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(self.client.get("/api/patients").json()["patients"], [])
        self.assertEqual(
            self.client.delete(f"/api/patients/{patient_id}").status_code, 404
        )

    def test_filters_and_name_search(self):
        self.create(name="Jane Smith", ward="ICU", department="Cardiology")
        self.create(name="John Smith", ward="General", department="Neurology")
        self.create(name="Mary Jones", ward="ICU", department="Cardiology")

        def names(query):
            response = self.client.get("/api/patients", params=query)
            return [item["name"] for item in response.json()["patients"]]

        self.assertEqual(len(names({})), 3)
        self.assertEqual(names({"search": "jane"}), ["Jane Smith"])
        self.assertEqual(names({"ward": "ICU"}), ["Mary Jones", "Jane Smith"])
        self.assertEqual(names({"department": "Neurology"}), ["John Smith"])
        self.assertEqual(
            names({"ward": "ICU", "department": "Cardiology", "doctor": "Dr. A Sharma"}),
            ["Mary Jones", "Jane Smith"],
        )

    def test_frontend_is_served(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Patient Admissions", response.text)


if __name__ == "__main__":
    unittest.main()
