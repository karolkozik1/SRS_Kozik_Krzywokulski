from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app import models, schemas, auth

router = APIRouter()

def _ensure_admin(user: models.User):
    if user.role_id != 3:
        raise HTTPException(status_code=403, detail="Wymagane uprawnienia administratora")

@router.get("/rooms/{room_id}", response_model=List[schemas.RoomEquipmentOut])
def list_room_equipment(
    room_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    rows = (
        db.query(
            models.RoomEquipment.id.label("id"),
            models.RoomEquipment.room_id.label("room_id"),
            models.RoomEquipment.equipment_id.label("equipment_id"),
            models.RoomEquipment.quantity.label("quantity"),
            models.Equipment.name.label("name"),
        )
        .join(models.Equipment, models.RoomEquipment.equipment_id == models.Equipment.id)
        .filter(models.RoomEquipment.room_id == room_id)
        .order_by(models.Equipment.name)
        .all()
    )
    return rows

@router.post("/rooms/{room_id}", response_model=List[schemas.RoomEquipmentOut], status_code=status.HTTP_201_CREATED)
def upsert_room_equipment(
    room_id: int,
    payload: schemas.RoomEquipmentUpsert,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    _ensure_admin(user)

    room = db.get(models.Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Sala nie istnieje")

    existing = {
        re.equipment_id: re
        for re in db.query(models.RoomEquipment).filter(models.RoomEquipment.room_id == room_id).all()
    }

    for item in payload.items:
        eq = db.get(models.Equipment, item.equipment_id)
        if not eq:
            raise HTTPException(status_code=400, detail=f"Wyposażenie o ID={item.equipment_id} nie istnieje")
        if item.quantity is None or item.quantity < 0:
            raise HTTPException(status_code=400, detail="Quantity musi być >= 0")

        if item.equipment_id in existing:
            existing[item.equipment_id].quantity = item.quantity
        else:
            re = models.RoomEquipment(
                room_id=room_id,
                equipment_id=item.equipment_id,
                quantity=item.quantity,
            )
            db.add(re)

    db.commit()

    rows = (
        db.query(
            models.RoomEquipment.id.label("id"),
            models.RoomEquipment.room_id.label("room_id"),
            models.RoomEquipment.equipment_id.label("equipment_id"),
            models.RoomEquipment.quantity.label("quantity"),
            models.Equipment.name.label("name"),
        )
        .join(models.Equipment, models.RoomEquipment.equipment_id == models.Equipment.id)
        .filter(models.RoomEquipment.room_id == room_id)
        .order_by(models.Equipment.name)
        .all()
    )
    return rows

@router.patch("/{room_equipment_id}", response_model=schemas.RoomEquipmentOut)
def update_room_equipment_quantity(
    room_equipment_id: int,
    payload: schemas.RoomEquipmentUpsertItem,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    _ensure_admin(user)

    re = db.get(models.RoomEquipment, room_equipment_id)
    if not re:
        raise HTTPException(status_code=404, detail="Pozycja wyposażenia sali nie istnieje")

    if payload.quantity is None or payload.quantity < 0:
        raise HTTPException(status_code=400, detail="Quantity musi być >= 0")

    re.quantity = payload.quantity
    db.commit()
    db.refresh(re)

    eq = db.get(models.Equipment, re.equipment_id)
    return {
        "id": re.id,
        "room_id": re.room_id,
        "equipment_id": re.equipment_id,
        "quantity": re.quantity,
        "name": (eq.name if eq else None),
    }
    
@router.delete("/{room_equipment_id}", response_model=schemas.RoomEquipmentOut)
def delete_room_equipment(
    room_equipment_id: int,
    db: Session = Depends(get_db),
    # user: models.User = Depends(auth.require_admin_dev),
):
    item = db.get(models.RoomEquipment, room_equipment_id)
    if not item:
        raise HTTPException(status_code=404, detail="Pozycja nie istnieje")
    db.delete(item)
    db.commit()
    return item