from typing import List, Optional, Set
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app import models, schemas, auth
from app.scheduler import update_reservation_statuses_pl  # patrz niżej

router = APIRouter()

PL_TZ = ZoneInfo("Europe/Warsaw")

def now_pl_naive() -> datetime:
    return datetime.now(PL_TZ).replace(tzinfo=None)

def to_pl_naive(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(PL_TZ).replace(tzinfo=None)

ALLOWED_RESERVATION_ROLES: Set[int] = {2, 3}   
ROOMTYPE_MAX_HOURS = {1: 4, 2: 3, 3: 2, 4: 2} 
MAINTENANCE_ACCESSIBILITY_ID = 3
def _duration_hours(start: datetime, end: datetime) -> float:
    return (end - start).total_seconds() / 3600.0

def _parse_hhmm(s: str) -> tuple[int, int]:
    h, m = s.split(":")
    return int(h), int(m)

def _create_reservation_core(
    *,
    room_id: int,
    start_pl: datetime,
    end_pl: datetime,
    user: models.User,
    db: Session,
) -> models.Reservation:

    if end_pl <= start_pl:
        raise HTTPException(400, "EndTime musi być po StartTime")
    if start_pl < now_pl_naive() - timedelta(minutes=1):
        raise HTTPException(400, "Nie można rezerwować w przeszłości")

    room = db.get(models.Room, room_id)
    if not room:
        raise HTTPException(404, "Sala nie istnieje")
    if room.accessibility_id == MAINTENANCE_ACCESSIBILITY_ID:
        raise HTTPException(400, "Sala jest w konserwacji")

    max_hours = ROOMTYPE_MAX_HOURS.get(room.room_type_id, 4)
    if _duration_hours(start_pl, end_pl) > max_hours:
        raise HTTPException(400, f"Maksymalny czas rezerwacji dla tej sali to {max_hours}h")

    conflict = db.query(models.Reservation).filter(
        models.Reservation.room_id == room_id,
        models.Reservation.reservation_status_id == models.ResStatus.SCHEDULED,
        models.Reservation.start_time < end_pl,
        models.Reservation.end_time > start_pl,
    ).first()
    if conflict:
        raise HTTPException(409, "W tym czasie sala jest już zarezerwowana")

    res = models.Reservation(
        user_id=user.id,
        room_id=room_id,
        start_time=start_pl,
        end_time=end_pl,
        created_at=now_pl_naive(),
        reservation_status_id=models.ResStatus.SCHEDULED,
    )
    db.add(res)
    db.commit()
    db.refresh(res)
    return res

@router.post("", response_model=schemas.ReservationOut, status_code=status.HTTP_201_CREATED)
def create_reservation(
    payload: schemas.ReservationCreate,               # start_time / end_time
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    if user.role_id not in ALLOWED_RESERVATION_ROLES:
        raise HTTPException(403, "Brak uprawnień do tworzenia rezerwacji")

    start_pl = to_pl_naive(payload.start_time)
    end_pl   = to_pl_naive(payload.end_time)

    return _create_reservation_core(
        room_id=payload.room_id,
        start_pl=start_pl,
        end_pl=end_pl,
        user=user,
        db=db,
    )

@router.post("/by-clock", response_model=schemas.ReservationOut, status_code=status.HTTP_201_CREATED)
def create_reservation_by_clock(
    payload: schemas.ReservationCreateClock,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    if user.role_id not in ALLOWED_RESERVATION_ROLES:
        raise HTTPException(403, "Brak uprawnień do tworzenia rezerwacji")

    sh, sm = _parse_hhmm(payload.start_hhmm)
    eh, em = _parse_hhmm(payload.end_hhmm)

    start_pl = datetime(payload.date.year, payload.date.month, payload.date.day, sh, sm, tzinfo=PL_TZ).replace(tzinfo=None)
    end_pl   = datetime(payload.date.year, payload.date.month, payload.date.day, eh, em, tzinfo=PL_TZ).replace(tzinfo=None)

    return _create_reservation_core(
        room_id=payload.room_id,
        start_pl=start_pl,
        end_pl=end_pl,
        user=user,
        db=db,
    )

@router.get("/my", response_model=List[schemas.ReservationOut])
def my_reservations(
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
    from_time: Optional[datetime] = Query(None),
    to_time: Optional[datetime]   = Query(None),
    include_cancelled: bool = Query(False),
):
    stmt = select(models.Reservation).where(models.Reservation.user_id == user.id)
    if not include_cancelled:
        stmt = stmt.where(models.Reservation.reservation_status_id == models.ResStatus.SCHEDULED)
    if from_time is not None:
        stmt = stmt.where(models.Reservation.end_time >= to_pl_naive(from_time))
    if to_time is not None:
        stmt = stmt.where(models.Reservation.start_time <= to_pl_naive(to_time))

    stmt = stmt.order_by(models.Reservation.start_time.desc())
    return db.execute(stmt).scalars().all()

# @router.get("/my", response_model=List[schemas.ReservationOut])
# def my_reservations(
#     db: Session = Depends(get_db),
#     user: models.User = Depends(auth.get_current_user),
#     from_time: Optional[datetime] = Query(None),
#     to_time: Optional[datetime]   = Query(None),
#     include_cancelled: bool = Query(False),
# ):
#     stmt = select(models.Reservation).where(models.Reservation.user_id == user.id)
#     if not include_cancelled:
#         stmt = stmt.where(models.Reservation.reservation_status_id == models.ResStatus.SCHEDULED)
#     if from_time is not None:
#         stmt = stmt.where(models.Reservation.end_time >= to_pl_naive(from_time))
#     if to_time is not None:
#         stmt = stmt.where(models.Reservation.start_time <= to_pl_naive(to_time))

#     stmt = stmt.order_by(models.Reservation.start_time.desc())
#     return db.execute(stmt).scalars().all()

@router.post("/{reservation_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
def cancel_reservation(
    reservation_id: int,
    body: Optional[schemas.CancelBody] = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    res = db.get(models.Reservation, reservation_id)
    if not res:
        raise HTTPException(404, "Rezerwacja nie istnieje")

    if res.reservation_status_id != models.ResStatus.SCHEDULED:
        raise HTTPException(400, "Rezerwacja nie jest aktywna")

    is_admin    = (user.role_id == 3)
    is_teacher  = (user.role_id == 2)
    is_owner    = (res.user_id == user.id)

    if not (is_admin or is_teacher):
        raise HTTPException(403, "Brak uprawnień")
    if is_teacher and not is_owner:
        raise HTTPException(403, "Nauczyciel może anulować tylko własne rezerwacje")
    if not is_admin and now_pl_naive() >= res.start_time:
        raise HTTPException(400, "Nie można anulować po rozpoczęciu rezerwacji")

    res.reservation_status_id = models.ResStatus.CANCELLED
    res.cancelled_at = now_pl_naive()
    res.cancel_reason = (body.reason if body else None)
    db.commit()
    return

@router.post("/_recalc", status_code=status.HTTP_204_NO_CONTENT, tags=["Reservations"])
def recalc_statuses(user: models.User = Depends(auth.get_current_user)):
    if user.role_id != 3:
        raise HTTPException(403, "Wymagane uprawnienia administratora")
    update_reservation_statuses_pl()
    return

# @router.get("/check", tags=["Reservations"])
# def check_availability(
#     room_id: int = Query(..., description="ID sali"),
#     start: datetime = Query(..., description="Początek rezerwacji (UTC+2, ISO 8601)"),
#     end: datetime = Query(..., description="Koniec rezerwacji (UTC+2, ISO 8601)"),
#     db: Session = Depends(get_db),
#     user: models.User = Depends(auth.get_current_user),
# ):
#     if start >= end:
#         raise HTTPException(400, "End musi być po Start")
#     if start < now_pl_naive():
#         raise HTTPException(400, "Nie można rezerwować w przeszłości")

#     conflict = db.query(models.Reservation).filter(
#         models.Reservation.room_id == room_id,
#         models.Reservation.reservation_status_id == models.ResStatus.SCHEDULED,
#         models.Reservation.start_time < end,
#         models.Reservation.end_time > start,
#     ).first()

#     return {"available": conflict is None}

@router.get("/all", response_model=List[schemas.ReservationOut])
def all_reservations(
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    # tylko admin i nauczyciel
    if user.role_id not in (1,2,3):
        raise HTTPException(403, "Brak uprawnień")

    q = (
        db.query(models.Reservation)
        .order_by(models.Reservation.start_time.desc())
    )
    return q.all()

## /check Adriana
@router.get("/check", tags=["Reservations"])
def check_availability(
    room_id: int = Query(..., description="ID sali"),
    start: datetime = Query(..., description="Początek rezerwacji (ISO 8601; może zawierać +02:00)"),
    end:   datetime = Query(..., description="Koniec rezerwacji (ISO 8601; może zawierać +02:00)"),
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    start_pl = to_pl_naive(start)
    end_pl   = to_pl_naive(end)

    if end_pl <= start_pl:
        raise HTTPException(400, "End musi być po Start")
    if start_pl < (now_pl_naive() - timedelta(minutes=1)):
        raise HTTPException(400, "Nie można rezerwować w przeszłości")

    room = db.get(models.Room, room_id)
    if not room:
        raise HTTPException(404, "Sala nie istnieje")
    # jeżeli chcesz blokować sale w konserwacji:
    # if room.accessibility_id == 3:
    #     raise HTTPException(400, "Sala jest w konserwacji")

    # 3) kolizja: istnieje rezerwacja aktywna, która zachodzi na [start_pl, end_pl]
    conflict = (
        db.query(models.Reservation)
          .filter(
              models.Reservation.room_id == room_id,
              models.Reservation.reservation_status_id == models.ResStatus.SCHEDULED,
              models.Reservation.start_time < end_pl,
              models.Reservation.end_time   > start_pl,
          )
          .first()
    )

    return {
        "available": conflict is None,
        "conflict_id": conflict.id if conflict else None
    }