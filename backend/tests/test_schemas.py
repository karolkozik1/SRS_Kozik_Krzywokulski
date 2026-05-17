import pytest
from datetime import date
from pydantic import ValidationError

from app.schemas import UserCreate, ReservationCreateClock


def test_user_create_accepts_valid_email():
    user = UserCreate(
        email="jan.kowalski@example.com",
        password="Haslo123!",
        first_name="Jan",
        last_name="Kowalski"
    )

    assert user.email == "jan.kowalski@example.com"
    assert user.first_name == "Jan"


def test_user_create_rejects_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(
            email="niepoprawny-email",
            password="Haslo123!",
            first_name="Jan",
            last_name="Kowalski"
        )


def test_reservation_clock_accepts_valid_hours():
    reservation = ReservationCreateClock(
        room_id=1,
        date=date(2026, 5, 13),
        start_hhmm="10:00",
        end_hhmm="11:30"
    )

    assert reservation.start_hhmm == "10:00"
    assert reservation.end_hhmm == "11:30"


def test_reservation_clock_rejects_invalid_hour():
    with pytest.raises(ValidationError):
        ReservationCreateClock(
            room_id=1,
            date=date(2026, 5, 13),
            start_hhmm="25:00",
            end_hhmm="11:30"
        )