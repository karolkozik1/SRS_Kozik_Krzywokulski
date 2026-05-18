from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app import auth, models


client = TestClient(app)


def _unique(value: str) -> str:
    return f"{value}_{uuid4().hex[:8]}"

def _unique_room_number(prefix: str = "T") -> str:
    """
    Krótki numer sali do testów integracyjnych.

    W przywróconej bazie danych kolumna Rooms.RoomNumber ma krótszy limit
    numer sali nie powinien przekraczać 10 znaków.
    """
    return f"{prefix}{uuid4().hex[:8]}"[:10]

@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def admin_user(db):
    """
    Użytkownik techniczny używany w testach jako administrator.
    Zakładamy, że w bazie istnieje rola o ID = 3.
    """
    user = models.User(
        email=f"admin_test_{uuid4().hex[:8]}@example.com",
        password_hash=auth.hash_password("TestoweHaslo123!"),
        first_name="Admin",
        last_name="Testowy",
        role_id=3,
        created_at=datetime.now(),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def teacher_user(db):
    """
    Użytkownik techniczny używany w testach jako nauczyciel/prowadzący.
    Rola 2 ma prawo tworzyć rezerwacje.
    """
    user = models.User(
        email=f"teacher_test_{uuid4().hex[:8]}@example.com",
        password_hash=auth.hash_password("TestoweHaslo123!"),
        first_name="Teacher",
        last_name="Testowy",
        role_id=2,
        created_at=datetime.now(),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def student_user(db):
    """
    Użytkownik techniczny z rolą studenta.
    """
    user = models.User(
        email=f"student_test_{uuid4().hex[:8]}@example.com",
        password_hash=auth.hash_password("TestoweHaslo123!"),
        first_name="Student",
        last_name="Testowy",
        role_id=1,
        created_at=datetime.now(),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _override_current_user(user):
    app.dependency_overrides[auth.get_current_user] = lambda: user


def _clear_overrides():
    app.dependency_overrides.clear()


def _get_or_create_building(db):
    building = db.query(models.Building).first()
    if building:
        return building

    building = models.Building(building_name="Budynek testowy")
    db.add(building)
    db.commit()
    db.refresh(building)
    return building


def _get_or_create_room_type(db):
    room_type = db.query(models.RoomType).first()
    if room_type:
        return room_type

    room_type = models.RoomType(room_type_name="Sala testowa")
    db.add(room_type)
    db.commit()
    db.refresh(room_type)
    return room_type


def _get_or_create_accessibility(db):
    accessibility = (
        db.query(models.Accessibility)
        .filter(models.Accessibility.id != 3)
        .first()
    )
    if accessibility:
        return accessibility

    accessibility = models.Accessibility(accessibility_name="Dostępna")
    db.add(accessibility)
    db.commit()
    db.refresh(accessibility)
    return accessibility


def _create_test_room(db, capacity=30):
    building = _get_or_create_building(db)
    room_type = _get_or_create_room_type(db)
    accessibility = _get_or_create_accessibility(db)

    room = models.Room(
        room_number=_unique_room_number("T"),
        building_id=building.id,
        floor=1,
        capacity=capacity,
        room_type_id=room_type.id,
        accessibility_id=accessibility.id,
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


def _create_test_equipment(db):
    equipment = models.Equipment(name=_unique("Projektor_testowy"))
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return equipment


def test_users_me_endpoint_returns_current_user(admin_user):
    _override_current_user(admin_user)

    response = client.get("/users/me")

    _clear_overrides()

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == admin_user.id
    assert data["email"] == admin_user.email
    assert data["role_id"] == 3


def test_rooms_create_get_list_and_search_endpoints(db, admin_user):
    _override_current_user(admin_user)

    building = _get_or_create_building(db)
    room_type = _get_or_create_room_type(db)
    accessibility = _get_or_create_accessibility(db)

    payload = {
        "room_number": _unique_room_number("S"),
        "building_id": building.id,
        "floor": 2,
        "capacity": 40,
        "room_type_id": room_type.id,
        "accessibility_id": accessibility.id,
    }

    create_response = client.post("/rooms", json=payload)
    assert create_response.status_code == 201

    created_room = create_response.json()
    room_id = created_room["id"]

    get_response = client.get(f"/rooms/{room_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == room_id

    list_response = client.get("/rooms", params={"min_capacity": 20})
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)

    search_payload = {
        "date": (date.today() + timedelta(days=30)).isoformat(),
        "start_hhmm": "10:00",
        "end_hhmm": "11:00",
        "building_id": building.id,
        "floor": 2,
        "min_capacity": 20,
        "equipment_ids": None,
    }

    search_response = client.post("/rooms/search", json=search_payload)
    assert search_response.status_code == 200

    search_data = search_response.json()
    assert "total" in search_data
    assert "total_capacity" in search_data
    assert "items" in search_data

    _clear_overrides()


def test_rooms_duplicate_create_returns_409(db, admin_user):
    _override_current_user(admin_user)

    building = _get_or_create_building(db)
    room_type = _get_or_create_room_type(db)
    accessibility = _get_or_create_accessibility(db)

    room_number = _unique("D")

    payload = {
        "room_number": room_number,
        "building_id": building.id,
        "floor": 1,
        "capacity": 25,
        "room_type_id": room_type.id,
        "accessibility_id": accessibility.id,
    }

    first_response = client.post("/rooms", json=payload)
    second_response = client.post("/rooms", json=payload)

    _clear_overrides()

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_equipment_create_list_update_delete_endpoints(admin_user):
    _override_current_user(admin_user)

    equipment_name = _unique("Kamera_testowa")

    create_response = client.post(
        "/equipment",
        json={"name": equipment_name}
    )
    assert create_response.status_code == 201

    created_equipment = create_response.json()
    equipment_id = created_equipment["id"]

    list_response = client.get("/equipment")
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)

    updated_name = _unique("Kamera_zaktualizowana")
    update_response = client.put(
        f"/equipment/{equipment_id}",
        json={"name": updated_name}
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == updated_name

    delete_response = client.delete(f"/equipment/{equipment_id}")
    assert delete_response.status_code == 204

    _clear_overrides()


def test_room_equipment_upsert_list_patch_delete_endpoints(db, admin_user):
    _override_current_user(admin_user)

    room = _create_test_room(db)
    equipment = _create_test_equipment(db)

    upsert_payload = {
        "items": [
            {
                "equipment_id": equipment.id,
                "quantity": 2,
            }
        ]
    }

    upsert_response = client.post(
        f"/room-equipment/rooms/{room.id}",
        json=upsert_payload
    )
    assert upsert_response.status_code == 201

    items = upsert_response.json()
    assert len(items) >= 1

    room_equipment_id = items[0]["id"]

    list_response = client.get(f"/room-equipment/rooms/{room.id}")
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)

    patch_response = client.patch(
        f"/room-equipment/{room_equipment_id}",
        json={
            "equipment_id": equipment.id,
            "quantity": 5,
        }
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["quantity"] == 5

    delete_response = client.delete(f"/room-equipment/{room_equipment_id}")
    assert delete_response.status_code == 200

    _clear_overrides()


def test_reservation_create_check_conflict_my_and_cancel_endpoints(db, teacher_user):
    _override_current_user(teacher_user)

    room = _create_test_room(db)

    reservation_date = date.today() + timedelta(days=40)

    payload = {
        "room_id": room.id,
        "date": reservation_date.isoformat(),
        "start_hhmm": "10:00",
        "end_hhmm": "11:00",
    }

    create_response = client.post("/reservations/by-clock", json=payload)
    assert create_response.status_code == 201

    reservation = create_response.json()
    reservation_id = reservation["id"]

    check_response = client.get(
        "/reservations/check",
        params={
            "room_id": room.id,
            "start": f"{reservation_date.isoformat()}T10:00:00",
            "end": f"{reservation_date.isoformat()}T11:00:00",
        }
    )
    assert check_response.status_code == 200
    assert check_response.json()["available"] is False
    assert check_response.json()["conflict_id"] == reservation_id

    conflict_response = client.post("/reservations/by-clock", json=payload)
    assert conflict_response.status_code == 409

    my_response = client.get("/reservations/my")
    assert my_response.status_code == 200
    assert isinstance(my_response.json(), list)

    cancel_response = client.post(
        f"/reservations/{reservation_id}/cancel",
        json={"reason": "Test anulowania rezerwacji"}
    )
    assert cancel_response.status_code == 204

    _clear_overrides()


def test_reservation_create_for_student_returns_403(db, student_user):
    _override_current_user(student_user)

    room = _create_test_room(db)
    reservation_date = date.today() + timedelta(days=50)

    payload = {
        "room_id": room.id,
        "date": reservation_date.isoformat(),
        "start_hhmm": "12:00",
        "end_hhmm": "13:00",
    }

    response = client.post("/reservations/by-clock", json=payload)

    _clear_overrides()

    assert response.status_code == 403


def test_reports_reservations_csv_endpoint(db, admin_user):
    _override_current_user(admin_user)

    room = _create_test_room(db)
    start_dt = datetime.combine(date.today() + timedelta(days=60), datetime.min.time()).replace(hour=9)
    end_dt = start_dt + timedelta(hours=1)

    reservation = models.Reservation(
        user_id=admin_user.id,
        room_id=room.id,
        start_time=start_dt,
        end_time=end_dt,
        created_at=datetime.now(),
        reservation_status_id=models.ResStatus.SCHEDULED,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    response = client.get(
        "/reports/reservations.csv",
        params={
            "date_from": start_dt.date().isoformat(),
            "date_to": end_dt.date().isoformat(),
        }
    )

    _clear_overrides()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "reservations.csv" in response.headers.get("content-disposition", "")