from fastapi.testclient import TestClient

from raq.service.api import app

c = TestClient(app)


def test_results_and_gate():
    r = c.get("/api/results").json()
    assert "platform" in r["dev"]["designs"] and isinstance(r["gate"]["dev"], list)


def test_plan_puts_a_risky_cashout_change_first_and_covers_more_than_the_top_devices():
    r = c.post("/api/plan", json={"changes": [
        {"module": "payout_service", "lines": 800, "api_change": True, "new_author": True},
        {"module": "settings_ui", "lines": 30}]}).json()
    assert next(iter(r["flows"])) == "cashout"
    assert "payout_service" in r["contracts"]
    makers = {d["name"].split("_")[0] for d in r["devices"]}
    assert len(makers) >= 5 and max(r["exploratory"], key=r["exploratory"].get) == "cashout"


def test_plan_rejects_an_unknown_module():
    assert c.post("/api/plan", json={"changes": [{"module": "nope", "lines": 10}]}).status_code == 422


def test_triage_reads_a_ticket():
    r = c.post("/api/triage", json={"text": "Auszahlung hängt seit Tagen, PayPal"}).json()
    assert r == {"flow": "cashout", "symptom": "cashout_stuck", "source": "rules"}
