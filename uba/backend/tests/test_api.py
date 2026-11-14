from app import emailer
from tests.conftest import login


def test_health_and_ready(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/ready").json() == {"status": "ready"}


def test_must_be_logged_in(client):
    assert client.get("/api/destinations").status_code == 401
    assert client.get("/api/bookings").status_code == 401


def test_wrong_password_is_rejected(client):
    response = client.post("/api/auth/login", json={"username": "pax", "password": "wrong-password"})
    assert response.status_code == 401
    assert "uba_session" not in response.cookies


def test_register_and_login(client):
    data = {"role": "pax", "username": "zoe", "email": "zoe@example.com", "name": "Zoe Ali",
            "password": "zoepass123", "phone": "868-555-0100"}
    assert client.post("/api/auth/register", json=data).status_code == 201
    assert client.post("/api/auth/register", json=data).status_code == 409  # duplicate
    login(client, "zoe", "zoepass123")
    me = client.get("/api/auth/me").json()
    assert me["role"] == "pax" and "password_hash" not in me


def test_nobody_can_register_as_admin(client):
    data = {"role": "admin", "username": "sneaky", "email": "s@example.com", "name": "S", "password": "password123"}
    assert client.post("/api/auth/register", json=data).status_code == 422


def test_short_password_is_rejected(client):
    data = {"role": "pax", "username": "bob", "email": "bob@example.com", "name": "Bob", "password": "short"}
    assert client.post("/api/auth/register", json=data).status_code == 422


def test_roles_are_enforced(client):
    login(client, "pax", "password123")
    assert client.get("/api/users").status_code == 403
    assert client.post("/api/destinations", json={"name": "Mayaro", "fare": 250}).status_code == 403
    assert client.get("/api/bookings/pending").status_code == 403


def test_full_booking_lifecycle(client):
    login(client, "pax", "password123")
    destinations = {d["name"]: d for d in client.get("/api/destinations").json()}
    arima, couva = destinations["Arima"], destinations["Couva"]
    assert round(arima["latitude"], 2) == 10.64 and round(arima["longitude"], 2) == -61.28

    same = client.post("/api/bookings", json={"pickup_id": arima["id"], "destination_id": arima["id"]})
    assert same.status_code == 422

    booking = client.post("/api/bookings", json={"pickup_id": arima["id"], "destination_id": couva["id"]}).json()
    # The fare is now priced by the fare model, so it is at least the base
    # flat fare and may be higher with demand / time / traffic.
    assert booking["status"] == "pending" and booking["fare"] >= couva["fare"]
    assert booking["pickup_latitude"] == arima["latitude"] and booking["destination_longitude"] == couva["longitude"]
    booking_id = booking["id"]

    # the driver accepts, releases, accepts again and completes
    login(client, "driver", "password123")
    assert [b["id"] for b in client.get("/api/bookings/pending").json()] == [booking_id]
    assert client.post(f"/api/bookings/{booking_id}/accept").json()["driver_username"] == "driver"
    assert client.post(f"/api/bookings/{booking_id}/release").json()["status"] == "pending"
    assert client.post(f"/api/bookings/{booking_id}/accept").status_code == 200

    # a second driver is too late
    login(client, "driver2", "password123")
    assert client.post(f"/api/bookings/{booking_id}/accept").status_code == 409
    assert client.post(f"/api/bookings/{booking_id}/complete").status_code == 409

    login(client, "driver", "password123")
    assert client.post(f"/api/bookings/{booking_id}/complete").json()["status"] == "completed"

    # the passenger rates it, and the driver sees the rating
    login(client, "pax", "password123")
    assert client.post(f"/api/bookings/{booking_id}/cancel").status_code == 409
    assert client.post(f"/api/bookings/{booking_id}/rating", json={"rating": "up"}).json()["rating"] == "up"
    login(client, "driver", "password123")
    assert client.get("/api/bookings").json()[0]["rating"] == "up"


def test_pax_cannot_touch_someone_elses_booking(client):
    login(client, "pax", "password123")
    ids = [d["id"] for d in client.get("/api/destinations").json()]
    booking_id = client.post("/api/bookings", json={"pickup_id": ids[0], "destination_id": ids[1]}).json()["id"]

    client.cookies.clear()
    data = {"role": "pax", "username": "zoe", "email": "zoe@example.com", "name": "Zoe", "password": "zoepass123"}
    client.post("/api/auth/register", json=data)
    login(client, "zoe", "zoepass123")
    assert client.post(f"/api/bookings/{booking_id}/cancel").status_code == 404
    assert client.get("/api/bookings").json() == []


def test_driver_can_edit_vehicle(client):
    login(client, "driver", "password123")
    update = {"plate": "hdk 9999", "make": "Toyota", "model": "Corolla", "seats": 4}
    assert client.put("/api/vehicles/mine", json=update).json()["plate"] == "HDK 9999"
    update["plate"] = "HCZ 7734"  # belongs to driver2
    assert client.put("/api/vehicles/mine", json=update).status_code == 409


def test_admin_can_manage(client):
    login(client, "admin", "password123")
    new_driver = {"role": "driver", "username": "marcus", "email": "marcus@example.com",
                  "name": "Marcus Charles", "password": "marcus1234", "permit_no": "DP1"}
    driver = client.post("/api/users", json=new_driver)
    assert driver.status_code == 201
    vehicle = {"plate": "hdx 1", "make": "Honda", "model": "Fit", "seats": 4, "driver_id": driver.json()["id"]}
    assert client.post("/api/vehicles", json=vehicle).json()["plate"] == "HDX 1"
    assert client.post("/api/vehicles", json=vehicle).status_code == 409
    mayaro = client.post("/api/destinations", json={"name": "Mayaro", "fare": 250, "latitude": 10.2977, "longitude": -61.0057})
    assert mayaro.status_code == 201 and mayaro.json()["latitude"] == 10.2977
    assert client.post("/api/destinations", json={"name": "Nowhere", "fare": 10, "latitude": 500}).status_code == 422
    assert client.post("/api/destinations", json={"name": "mayaro", "fare": 250}).status_code == 409
    assert len(client.get("/api/users").json()) == 5


def test_forgot_password_flow(client, monkeypatch):
    sent = []
    monkeypatch.setattr("app.routers.auth.send_password_reset", lambda to, name, token: sent.append((to, token)))

    # an unknown email gets the same answer and sends nothing
    assert client.post("/api/auth/forgot-password", json={"email": "nobody@example.com"}).status_code == 202
    assert sent == []

    assert client.post("/api/auth/forgot-password", json={"email": "pax@example.com"}).status_code == 202
    to, token = sent[0]
    assert to == "pax@example.com"

    assert client.post("/api/auth/reset-password", json={"token": "wrong", "new_password": "newpass1234"}).status_code == 400
    assert client.post("/api/auth/reset-password", json={"token": token, "new_password": "newpass1234"}).status_code == 200
    # a link works once
    assert client.post("/api/auth/reset-password", json={"token": token, "new_password": "another1234"}).status_code == 400

    assert client.post("/api/auth/login", json={"username": "pax", "password": "password123"}).status_code == 401
    login(client, "pax", "newpass1234")


def test_metrics_are_exposed(client):
    client.get("/api/health")
    body = client.get("/metrics").text
    assert 'uba_http_requests_total{method="GET",path="/api/health",status="200"}' in body
    assert emailer is not None
