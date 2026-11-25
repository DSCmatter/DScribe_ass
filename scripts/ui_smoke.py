from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "docs" / "screenshots"
SHOTS.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8000"


PATIENTS = [
    {
        "name": "Aarav Mehta",
        "age": "42",
        "gender": "Male",
        "ward": "ICU",
        "department": "Cardiology",
        "doctor": "Dr. A Sharma",
        "admission_date": "2026-11-20",
    },
    {
        "name": "Priya Nair",
        "age": "29",
        "gender": "Female",
        "ward": "General",
        "department": "Neurology",
        "doctor": "Dr. S Menon",
        "admission_date": "2026-11-22",
    },
    {
        "name": "Rohan Verma",
        "age": "8",
        "gender": "Male",
        "ward": "Pediatrics",
        "department": "Pediatrics",
        "doctor": "Dr. K Verma",
        "admission_date": "2026-11-24",
    },
]


def reset_data():
    with httpx.Client(base_url=BASE) as client:
        for patient in client.get("/api/patients").json()["patients"]:
            client.delete(f"/api/patients/{patient['id']}")


def fill_form(page, patient):
    page.locator('.modal [name="name"]').fill(patient["name"])
    page.locator('.modal [name="age"]').fill(patient["age"])
    page.locator('.modal [name="admission_date"]').fill(patient["admission_date"])
    for field in ("gender", "ward", "department", "doctor"):
        page.locator(f'.modal [name="{field}"]').select_option(patient[field])


def add_patient(page, patient, expected_count):
    page.get_by_role("button", name="Add patient").first.click()
    fill_form(page, patient)
    page.locator(".modal button[type=submit]").click()
    expect(page.locator(".patient-row")).to_have_count(expected_count)


def wait_for_rows(page, count):
    expect(page.locator(".patient-row")).to_have_count(count)


def main():
    errors = []
    reset_data()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(BASE, wait_until="networkidle")

        assert page.get_by_text("No patients found.").is_visible()

        page.get_by_role("button", name="Add patient").first.click()
        page.locator(".modal button[type=submit]").click()
        assert page.locator(".field-error").count() >= 6
        page.screenshot(path=str(SHOTS / "validation.png"), full_page=True)
        page.get_by_role("button", name="Cancel").click()

        for index, patient in enumerate(PATIENTS, start=1):
            add_patient(page, patient, index)

        page.screenshot(path=str(SHOTS / "desktop-list.png"), full_page=True)

        page.set_viewport_size({"width": 820, "height": 1180})
        page.screenshot(path=str(SHOTS / "tablet-list.png"), full_page=True)
        page.set_viewport_size({"width": 1440, "height": 1000})

        page.get_by_role("button", name="Add patient").first.click()
        fill_form(page, PATIENTS[0])
        page.screenshot(path=str(SHOTS / "patient-form.png"), full_page=True)
        page.get_by_role("button", name="Cancel").click()

        search = page.get_by_label("Search patients by name")
        search.fill("priya")
        wait_for_rows(page, 1)
        assert "Priya Nair" in page.locator(".patient-row").first.inner_text()
        search.fill("")
        wait_for_rows(page, 3)

        page.get_by_label("All wards").select_option("ICU")
        wait_for_rows(page, 1)
        assert "Aarav Mehta" in page.locator(".patient-row").first.inner_text()
        page.get_by_role("button", name="Clear filters").click()
        wait_for_rows(page, 3)

        first_row = page.locator(".patient-row").first
        first_row.get_by_role("button", name="Edit").click()
        page.locator('.modal [name="name"]').fill("Aarav Sharma")
        page.locator(".modal button[type=submit]").click()
        expect(first_row).to_contain_text("Aarav Sharma")

        first_row.get_by_role("button", name="Discharge").click()
        expect(first_row.locator(".badge")).to_have_text("Discharged")

        first_row.get_by_role("button", name="Delete").click()
        assert page.get_by_text("Delete this patient?").is_visible()
        page.get_by_role("button", name="Delete patient").click()
        wait_for_rows(page, 2)

        page.set_viewport_size({"width": 390, "height": 844})
        page.reload(wait_until="networkidle")
        wait_for_rows(page, 2)
        page.screenshot(path=str(SHOTS / "mobile-list.png"), full_page=True)

        browser.close()

    if errors:
        print("Browser errors:", errors)
        raise SystemExit(1)
    print("UI smoke passed. Screenshots written to", SHOTS)


if __name__ == "__main__":
    main()
