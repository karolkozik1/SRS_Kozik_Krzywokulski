from sqlalchemy import Column, Integer, Unicode, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime
from enum import IntEnum

Base = declarative_base()

class User(Base):
    __tablename__ = "Users"

    id = Column("ID", Integer, primary_key=True, index=True)
    email = Column("Email", Unicode(100), unique=True, nullable=False)
    password_hash = Column("PasswordHash", Unicode(255), nullable=False)
    first_name = Column("FirstName", Unicode(100), nullable=False)
    last_name = Column("LastName", Unicode(100), nullable=False)
    role_id = Column("RoleId", Integer, ForeignKey("Roles.ID"), nullable=False)
    created_at = Column("CreatedAt", DateTime, default=datetime.utcnow)
    last_login = Column("LastLogin", DateTime, nullable=True)
    is_active = Column("IsActive", Boolean, default=True)

class Role(Base):
    __tablename__ = "Roles"

    id = Column("ID", Integer, primary_key=True, index=True)
    role_name = Column("RoleName", Unicode(100), nullable=False)

class Room(Base):
    __tablename__ = "Rooms"

    id = Column("ID", Integer, primary_key=True, index=True)
    room_number = Column("RoomNumber", Unicode(50), nullable=False)
    building_id = Column("BuildingID", Integer, ForeignKey("Buildings.ID"), nullable=False)
    floor = Column("Floor", Integer, nullable=False)
    capacity = Column("Capacity", Integer, nullable=False)
    room_type_id = Column("RoomTypeID", Integer, ForeignKey("RoomTypes.ID"), nullable=False)
    accessibility_id = Column("AccessibilityID", Integer, ForeignKey("Accessibility.ID"), nullable=False)

class Building(Base):
    __tablename__ = "Buildings"
    id = Column("ID", Integer, primary_key=True, index=True)
    building_name = Column("BuildingName", Unicode(50), nullable=False)

class RoomType(Base):
    __tablename__ = "RoomTypes"
    id = Column("ID", Integer, primary_key=True, index=True)
    room_type_name = Column("RoomTypeName", Unicode(100), nullable=False)

class Accessibility(Base):
    __tablename__ = "Accessibility"
    id = Column("ID", Integer, primary_key=True, index=True)
    accessibility_name = Column("AccessibilityName", Unicode(100), nullable=False)

class ResStatus(IntEnum):
    SCHEDULED = 1
    CANCELLED = 2
    COMPLETED = 3

class Reservation(Base):
    __tablename__ = "Reservations"
    id         = Column("ID", Integer, primary_key=True, index=True)
    user_id    = Column("UserId", Integer, ForeignKey("Users.ID"), nullable=False)
    room_id    = Column("RoomId", Integer, ForeignKey("Rooms.ID"), nullable=False)
    start_time = Column("StartTime", DateTime, nullable=False)
    end_time   = Column("EndTime", DateTime, nullable=False)
    created_at = Column("CreatedAt", DateTime, default=datetime.utcnow, nullable=False)
    reservation_status_id = Column("ReservationStatusId", Integer, default=ResStatus.SCHEDULED, nullable=False)
    cancelled_at  = Column("CancelledAt", DateTime, nullable=True)
    cancel_reason = Column("CancelReason", Unicode(200), nullable=True)

class Equipment(Base):
    __tablename__ = "Equipment"
    id   = Column("ID", Integer, primary_key=True, index=True)
    name = Column("EquipmentName", Unicode(100), nullable=False)

class RoomEquipment(Base):
    __tablename__ = "Room_Equipment"
    id           = Column("ID", Integer, primary_key=True, index=True)
    room_id      = Column("RoomId", Integer, ForeignKey("Rooms.ID"), nullable=False)
    equipment_id = Column("EquipmentId", Integer, ForeignKey("Equipment.ID"), nullable=False)
    quantity     = Column("Quantity", Integer, nullable=False)