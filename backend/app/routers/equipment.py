from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, auth

router = APIRouter()

@router.get("", response_model=List[schemas.EquipmentOut])
def list_equipment(db: Session = Depends(get_db)):
    return db.query(models.Equipment).order_by(models.Equipment.name).all()

@router.post("", response_model=schemas.EquipmentOut, status_code=status.HTTP_201_CREATED)
def create_equipment(
    payload: schemas.EquipmentCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    if user.role_id != 3:
        raise HTTPException(status_code=403, detail="Tylko administrator może dodawać wyposażenie")
    eq = models.Equipment(name=payload.name)
    db.add(eq)
    db.commit()
    db.refresh(eq)
    return eq

@router.put("/{equipment_id}", response_model=schemas.EquipmentOut)
def update_equipment(
    equipment_id: int,
    payload: schemas.EquipmentCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    if user.role_id != 3:
        raise HTTPException(status_code=403, detail="Tylko administrator może edytować wyposażenie")
    eq = db.get(models.Equipment, equipment_id)
    if not eq:
        raise HTTPException(status_code=404, detail="Wyposażenie nie istnieje")
    eq.name = payload.name
    db.commit()
    db.refresh(eq)
    return eq

# @router.get("/equipments", response_model=List[schemas.EquipmentOut], tags=["List Equipment"])
# def list_equipments(
#     db: Session = Depends(get_db),
#     user: models.User = Depends(auth.get_current_user),
# ):
#     # np. dostęp dla nauczycieli i adminów – możesz ograniczyć
#     equipments = db.query(models.Equipment).all()
#     return equipments

@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user)
):
    # tylko admin (role_id == 3) może usuwać sprzęty globalne
    if user.role_id != 3:
        raise HTTPException(status_code=403, detail="Brak uprawnień")

    equipment = db.get(models.Equipment, equipment_id)
    if not equipment:
        raise HTTPException(status_code=404, detail="Sprzęt nie istnieje")

    # Uwaga: jeśli sprzęt jest powiązany z salami (Room_Equipment) -> FK constraint
    # Możesz wybrać jedno z podejść:
    # 1. Zablokować usuwanie, jeśli sprzęt jest przypisany do jakiejś sali:
    has_relation = db.query(models.RoomEquipment).filter(
        models.RoomEquipment.equipment_id == equipment_id
    ).first()
    if has_relation:
        raise HTTPException(status_code=400, detail="Sprzęt przypisany do sali – najpierw usuń powiązania")

    db.delete(equipment)
    db.commit()
    return