from pydantic import BaseModel, EmailStr, ConfigDict, field_validator, constr
from typing import Optional, List
from datetime import datetime, date

HHMM = constr(pattern=r"^\d{2}:\d{2}$")

class Token(BaseModel):
    access_token: str
    token_type: str
    
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    role_id: int
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool

    class Config:
        orm_mode = True

class RoomBase(BaseModel):
    room_number: str
    building_id: int
    floor: int
    capacity: int
    room_type_id: int
    accessibility_id: int
    model_config = ConfigDict(extra="forbid")

class RoomCreate(RoomBase):
    pass

class RoomUpdate(BaseModel):
    room_number: Optional[str] = None
    building_id: Optional[int] = None
    floor: Optional[int] = None
    capacity: Optional[int] = None
    room_type_id: Optional[int] = None
    accessibility_id: Optional[int] = None
    model_config = ConfigDict(extra="forbid")

class RoomOut(RoomBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ReservationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    room_id: int
    start_time: datetime
    end_time: datetime

class ReservationCreateClock(BaseModel):
    room_id: int
    date: date
    start_hhmm: HHMM
    end_hhmm: HHMM

    @field_validator("start_hhmm")
    @classmethod
    def _v_start(cls, v: str) -> str:
        h_m = v.split(":")
        if len(h_m) != 2 or not all(p.isdigit() for p in h_m):
            raise ValueError("start_hhmm musi być HH:MM")
        h, m = map(int, h_m)
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError("start_hhmm spoza zakresu")
        return v

    @field_validator("end_hhmm")
    @classmethod
    def _v_end(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        h_m = v.split(":")
        if len(h_m) != 2 or not all(p.isdigit() for p in h_m):
            raise ValueError("end_hhmm musi być HH:MM")
        h, m = map(int, h_m)
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError("end_hhmm spoza zakresu")
        return v

class ReservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    room_id: int
    start_time: datetime
    end_time: datetime
    created_at: datetime
    reservation_status_id: int
    cancelled_at: Optional[datetime] = None
    cancel_reason: Optional[str] = None

class CancelBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: Optional[str] = None

class EquipmentBase(BaseModel):
    name: str

class EquipmentCreate(BaseModel):
    name: str

class EquipmentUpdate(EquipmentBase):
    model_config = ConfigDict(extra="forbid")

class EquipmentOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class RoomEquipmentUpsertItem(BaseModel):
    equipment_id: int
    quantity: int

class RoomEquipmentUpsert(BaseModel):
    items: List[RoomEquipmentUpsertItem]

class RoomEquipmentOut(BaseModel):
    id: int
    room_id: int
    equipment_id: int
    name: Optional[str] = None
    quantity: int

    class Config:
        from_attributes = True


class RoomSearchIn(BaseModel):
    date: date
    start_hhmm: str
    end_hhmm: str
    building_id: Optional[int] = None
    floor: Optional[int] = None
    min_capacity: Optional[int] = None
    equipment_ids: Optional[List[int]] = None

class RoomShortOut(BaseModel):
    id: int
    room_number: str
    building_id: int
    floor: int
    capacity: int

    class Config:
        from_attributes = True

class RoomSearchOut(BaseModel):
    total: int
    total_capacity: int
    items: List[RoomShortOut]


class ReportRange(BaseModel):
    date_from: date
    date_to: date