from datetime import datetime, timezone

from app.fare_model import (
    MAX_DEMAND_MULTIPLIER,
    demand_factor,
    distance_km,
    estimate_fare,
    time_factor,
    traffic_factor,
)
from tests.conftest import login

# Fixed moments so the time-based parts are deterministic.
WEEKDAY_RUSH = datetime(2026, 11, 16, 7, 30, tzinfo=timezone.utc)   # Monday 7:30am
WEEKDAY_MIDDAY = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)  # Monday noon
LATE_NIGHT = datetime(2026, 11, 16, 3, 0, tzinfo=timezone.utc)      # Monday 3am


def test_distance_uses_coordinates():
    # Port of Spain to San Fernando is roughly 45 km.
    km = distance_km(10.6549, -61.5019, 10.2796, -61.4589)
    assert 40 < km < 55


def test_distance_is_none_without_coordinates():
    assert distance_km(10.0, -61.0, None, None) is None


def test_time_and_traffic_factors():
    assert time_factor(LATE_NIGHT).value > 1.0
    assert time_factor(WEEKDAY_MIDDAY).value == 1.0
    assert traffic_factor(WEEKDAY_RUSH).value > traffic_factor(WEEKDAY_MIDDAY).value


def test_demand_rises_with_scarcity_but_is_capped():
    calm = demand_factor(waiting_riders=0, free_drivers=3)
    busy = demand_factor(waiting_riders=6, free_drivers=2)
    assert calm.value == 1.0
    assert busy.value > calm.value
    # Even absurd demand never exceeds the surge cap.
    assert demand_factor(waiting_riders=1000, free_drivers=1).value == MAX_DEMAND_MULTIPLIER


def test_estimate_is_base_at_a_quiet_midday():
    quote = estimate_fare(
        base_fare=100,
        pickup=(10.65, -61.50),
        destination=(10.28, -61.46),
        waiting_riders=0,
        free_drivers=5,
        when=WEEKDAY_MIDDAY,
    )
    assert quote["final_fare"] == 100
    assert quote["surge"] is False
    assert quote["distance_km"] is not None


def test_estimate_marks_surge_and_raises_price():
    quote = estimate_fare(
        base_fare=100,
        pickup=(10.65, -61.50),
        destination=(10.28, -61.46),
        waiting_riders=8,
        free_drivers=2,
        when=WEEKDAY_RUSH,
    )
    assert quote["final_fare"] > 100
    assert quote["surge"] is True


# ---------- the endpoint ----------

def test_fare_estimate_endpoint(client):
    login(client, "pax", "password123")
    destinations = {d["name"]: d for d in client.get("/api/destinations").json()}
    arima, couva = destinations["Arima"], destinations["Couva"]

    response = client.get(f"/api/fare/estimate?pickup_id={arima['id']}&destination_id={couva['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["base_fare"] == couva["fare"]
    assert body["final_fare"] >= body["base_fare"]
    assert body["distance_km"] is not None

    same = client.get(f"/api/fare/estimate?pickup_id={arima['id']}&destination_id={arima['id']}")
    assert same.status_code == 422


def test_fare_estimate_requires_login(client):
    assert client.get("/api/fare/estimate?pickup_id=1&destination_id=2").status_code == 401
