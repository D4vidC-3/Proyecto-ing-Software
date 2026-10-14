from fastapi.testclient import TestClient
import main

client = TestClient(main.app)


def test_invalid_salary_preserves_saved_profile_and_international_phone(database):
    original = {"phone": "+57 300 000 0000", "years_experience": 0,
                "preferences": {"salary_min_cop": 100, "salary_max_cop": 200}}
    saved = client.post("/api/v1/profiles", json=original).json()
    path = f'/api/v1/profiles/{saved["candidate_id"]}'
    invalid = {**original, "preferences": {"salary_min_cop": 300, "salary_max_cop": 200}}
    assert client.put(path, json=invalid).status_code == 422
    assert client.post("/api/v1/profiles", json=invalid).status_code == 422
    read = client.get(path).json()
    assert read["profile"] == saved["profile"]
    assert read["profile"]["phone"] == original["phone"]
    assert read["profile"]["years_experience"] == 0
    assert len(client.get("/api/v1/profiles").json()) == 1
    original["phone"] = "+1 202 555 0100"
    assert client.put(path, json=original).json()["profile"]["phone"] == original["phone"]
