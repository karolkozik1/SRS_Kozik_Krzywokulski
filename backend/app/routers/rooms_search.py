from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime
from typing import List

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/rooms-search", tags=["Rooms Search"])

def _parse_hhmm(s: str) -> tuple[int, int]:
    h, m = s.split(":")
    return int(h), int(m)

@router.post("", response_model=schemas.RoomSearchOut)
def search_rooms(payload: schemas.RoomSearchIn, db: Session = Depends(get_db)):
    """
    Wyszukiwanie wolnych sal na podstawie kryteriów (data, godziny, budynek, piętro, pojemność, wyposażenie).
    """
    # Tworzymy zakres daty/godziny
    sh, sm = _parse_hhmm(payload.start_hhmm)
    eh, em = _parse_hhmm(payload.end_hhmm)
    start_dt = datetime(payload.date.year, payload.date.month, payload.date.day, sh, sm)
    end_dt   = datetime(payload.date.year, payload.date.month, payload.date.day, eh, em)

    if end_dt <= start_dt:
        raise HTTPException(400, "Czas zakończenia musi być po rozpoczęciu")

    # Kwerenda bazowa — wszystkie sale
    q = db.query(models.Room)

    if payload.building_id:
        q = q.filter(models.Room.building_id == payload.building_id)
    if payload.floor is not None:
        q = q.filter(models.Room.floor == payload.floor)
    if payload.min_capacity:
        q = q.filter(models.Room.capacity >= payload.min_capacity)

    # Wykluczamy sale zajęte w tym przedziale czasu
    q = q.filter(~models.Room.id.in_(
        db.query(models.Reservation.room_id)
        .filter(
            models.Reservation.reservation_status_id == models.ResStatus.SCHEDULED,
            models.Reservation.start_time < end_dt,
            models.Reservation.end_time > start_dt,
        )
    ))

    # Filtr po wyposażeniu (jeśli podane)
    if payload.equipment_ids:
        for eq_id in payload.equipment_ids:
            q = q.filter(models.Room.id.in_(
                db.query(models.RoomEquipment.room_id)
                .filter(models.RoomEquipment.equipment_id == eq_id,
                        models.RoomEquipment.quantity > 0)
            ))

    rooms = q.all()

    # Budujemy wynik
    items = [schemas.RoomShortOut.model_validate(r) for r in rooms]
    total_capacity = sum(r.capacity for r in rooms)
    return schemas.RoomSearchOut(
        total=len(items),
        total_capacity=total_capacity,
        items=items
    )
