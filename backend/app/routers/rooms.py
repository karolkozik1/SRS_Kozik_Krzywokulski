from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, select
from app.database import get_db
from app import models, schemas, auth
from datetime import datetime
from functools import reduce

router = APIRouter()

@router.get("", response_model=List[schemas.RoomOut])
def list_rooms(
    db: Session = Depends(get_db),
    building_id: Optional[int] = Query(None),
    room_type_id: Optional[int] = Query(None),
    accessibility_id: Optional[int] = Query(None),
    min_capacity: Optional[int] = Query(None),
    floor: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    stmt = select(models.Room)

    if building_id is not None:
        stmt = stmt.where(models.Room.building_id == building_id)
    if room_type_id is not None:
        stmt = stmt.where(models.Room.room_type_id == room_type_id)
    if accessibility_id is not None:
        stmt = stmt.where(models.Room.accessibility_id == accessibility_id)
    if min_capacity is not None:
        stmt = stmt.where(models.Room.capacity >= min_capacity)
    if floor is not None:
        stmt = stmt.where(models.Room.floor == floor)
        
    stmt = stmt.order_by(models.Room.id)
    if offset:
        stmt = stmt.offset(offset)
    stmt = stmt.limit(limit)

    rows = db.execute(stmt).scalars().all()
    return rows

@router.get("/{room_id}", response_model=schemas.RoomOut)
def get_room(room_id: int, db: Session = Depends(get_db)):
    room = db.get(models.Room, room_id)
    if not room:
        raise HTTPException(404, "Sala nie istnieje")
    return room

@router.post("", response_model=schemas.RoomOut, status_code=201)
def create_room(
    payload: schemas.RoomCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(auth.require_role({3})),
):
    exists = db.query(models.Room).filter(
        and_(models.Room.building_id == payload.building_id,
             models.Room.room_number == payload.room_number)
    ).first()
    if exists:
        raise HTTPException(409, "Sala o tym numerze istnieje już w tym budynku")

    room = models.Room(**payload.dict())
    db.add(room); db.commit(); db.refresh(room)
    return room

@router.put("/{room_id}", response_model=schemas.RoomOut)
def update_room(
    room_id: int,
    payload: schemas.RoomUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(auth.require_role({3})),
):
    room = db.get(models.Room, room_id)
    if not room:
        raise HTTPException(404, "Sala nie istnieje")

    data = payload.dict(exclude_unset=True)
    if "building_id" in data or "room_number" in data:
        b_id = data.get("building_id", room.building_id)
        r_no = data.get("room_number", room.room_number)
        clash = db.query(models.Room).filter(
            and_(models.Room.building_id == b_id,
                 models.Room.room_number == r_no,
                 models.Room.id != room_id)
        ).first()
        if clash:
            raise HTTPException(409, "Sala o tym numerze istnieje już w tym budynku")

    for k, v in data.items():
        setattr(room, k, v)

    db.commit(); db.refresh(room)
    return room

def _parse_hhmm(s: str) -> tuple[int, int]:
    h, m = s.split(":")
    return int(h), int(m)

MAINTENANCE_ACCESSIBILITY_ID = 3  # "W konserwacji"

@router.post("/search", response_model=schemas.RoomSearchOut, tags=["Rooms"])
def search_rooms(payload: schemas.RoomSearchIn, db: Session = Depends(get_db)):
    sh, sm = _parse_hhmm(payload.start_hhmm)
    eh, em = _parse_hhmm(payload.end_hhmm)
    start_dt = datetime(payload.date.year, payload.date.month, payload.date.day, sh, sm)
    end_dt   = datetime(payload.date.year, payload.date.month, payload.date.day, eh, em)
    if end_dt <= start_dt:
        raise HTTPException(400, "end_hhmm musi być po start_hhmm")

    q = db.query(models.Room).filter(models.Room.accessibility_id != MAINTENANCE_ACCESSIBILITY_ID)
    if payload.building_id is not None:
        q = q.filter(models.Room.building_id == payload.building_id)
    if payload.floor is not None:
        q = q.filter(models.Room.floor == payload.floor)
    if payload.min_capacity is not None:
        q = q.filter(models.Room.capacity >= payload.min_capacity)

    conflicting = (
        db.query(models.Reservation.room_id)
          .filter(
              models.Reservation.reservation_status_id == models.ResStatus.SCHEDULED,
              models.Reservation.start_time < end_dt,
              models.Reservation.end_time   > start_dt,
          )
          .subquery()
    )
    q = q.filter(~models.Room.id.in_(select(conflicting.c.room_id)))
    candidates: List[models.Room] = q.all()

    room_ids = [r.id for r in candidates] or [-1]
    equip_rows = (
        db.query(
            models.RoomEquipment.room_id,
            models.RoomEquipment.equipment_id,
            models.RoomEquipment.quantity
        )
        .filter(models.RoomEquipment.room_id.in_(room_ids))
        .all()
    )

    # map -> zbuduj mapę room_id -> zbiór wyposażenia (gdzie quantity > 0)
    equip_by_room = {}
    for rid, eid, qty in equip_rows:
        if qty and qty > 0:
            equip_by_room.setdefault(rid, set()).add(eid)

    # filter -> jeśli podano equipment_ids, bierzemy sale zawierające *wszystkie* wymagane elementy
    if payload.equipment_ids:
        required = set(payload.equipment_ids)
        candidates = list(
            filter(lambda r: required.issubset(equip_by_room.get(r.id, set())), candidates)
        )

    # reduce -> szybkie podsumowanie: liczba sal i łączna pojemność
    total, total_capacity = reduce(
        lambda acc, r: (acc[0] + 1, acc[1] + (r.capacity or 0)),
        candidates,
        (0, 0),
    )

    # map -> zbuduj lekki obiekt do odpowiedzi
    items = list(map(lambda r: schemas.RoomShortOut(
        id=r.id,
        room_number=r.room_number,
        building_id=r.building_id,
        floor=r.floor,
        capacity=r.capacity,
    ), candidates))

    return schemas.RoomSearchOut(total=total, total_capacity=total_capacity, items=items)
