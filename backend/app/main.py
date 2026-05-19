from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.database import engine, init_db, SessionLocal
from app.routers import users, rooms, reservations, equipment, room_equipment, reports
from app.scheduler import is_scheduler_running, start_scheduler, stop_scheduler
from datetime import datetime
from app import models

app = FastAPI(debug=True, title="System Rezerwacji Sal", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "http://frontend:8080",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    expose_headers=["Content-Disposition"],
)

app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(rooms.router, prefix="/rooms", tags=["Rooms"])
app.include_router(equipment.router,        prefix="/equipment",       tags=["Equipment"])
app.include_router(room_equipment.router,   prefix="/room-equipment",  tags=["RoomEquipment"])
app.include_router(reservations.router,  prefix="/reservations", tags=["Reservations"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])

@app.get("/")
def root():
    return {"message": "System Rezerwacji działa"}

@app.get("/health")
def health_check():
    started_at = datetime.now()

    result = {
        "status": "ok",
        "backend": {
            "status": "running",
            "service": "FastAPI",
            "version": app.version,
        },
        "database": {
            "status": "unknown",
            "connected": False,
        },
        "scheduler": {
            "running": is_scheduler_running(),
            "job": "update_reservation_statuses",
        "interval": "1 minute"
        },
        "statistics": {
            "users_count": None,
            "rooms_count": None,
            "reservations_count": None,
            "active_reservations_count": None,
        },
        "checked_at": started_at.isoformat(),
        "response_time_ms": None,
    }

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        result["database"]["status"] = "connected"
        result["database"]["connected"] = True

        db = SessionLocal()
        try:
            result["statistics"]["users_count"] = db.query(models.User).count()
            result["statistics"]["rooms_count"] = db.query(models.Room).count()
            result["statistics"]["reservations_count"] = db.query(models.Reservation).count()
            result["statistics"]["active_reservations_count"] = (
                db.query(models.Reservation)
                .filter(models.Reservation.reservation_status_id == models.ResStatus.SCHEDULED)
                .count()
            )
        finally:
            db.close()

    except Exception as error:
        result["status"] = "error"
        result["database"]["status"] = "disconnected"
        result["database"]["connected"] = False
        result["error"] = str(error)

    finished_at = datetime.now()
    result["response_time_ms"] = round(
        (finished_at - started_at).total_seconds() * 1000,
        2
    )

    return result


@app.on_event("startup")
def _startup():
    print("Uruchamianie aplikacji...")
    init_db()
    start_scheduler()
    print("Scheduler został uruchomiony")

@app.on_event("shutdown")
def _shutdown():
    print("Zamykanie aplikacji...")
    stop_scheduler()
    print("Scheduler został zatrzymany")