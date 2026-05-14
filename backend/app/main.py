from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.database import engine, init_db
from app.routers import users, rooms, reservations, equipment, room_equipment, reports
from app.scheduler import start_scheduler, stop_scheduler

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
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "backend": "running",
            "database": "connected"
        }

    except Exception as error:
        return {
            "status": "error",
            "backend": "running",
            "database": "disconnected",
            "details": str(error)
        }

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