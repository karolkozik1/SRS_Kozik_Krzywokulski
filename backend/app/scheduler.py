from __future__ import annotations
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger


PL_TZ = ZoneInfo("Europe/Warsaw")

scheduler = BackgroundScheduler(timezone=str(PL_TZ))


def now_pl_naive() -> datetime:
    return datetime.now(PL_TZ).replace(tzinfo=None)


def update_reservation_statuses_pl() -> int:
    db: Session = SessionLocal()

    try:
        current_time = now_pl_naive()

        reservations_to_complete = (
            db.query(models.Reservation)
            .filter(
                models.Reservation.reservation_status_id == models.ResStatus.SCHEDULED,
                models.Reservation.end_time <= current_time,
            )
            .all()
        )

        changed_count = 0

        for reservation in reservations_to_complete:
            reservation.reservation_status_id = models.ResStatus.COMPLETED
            changed_count += 1

        if changed_count > 0:
            db.commit()
            print(
                f"[scheduler] Zmieniono status {changed_count} rezerwacji na zakończone. "
                f"Czas sprawdzenia: {current_time}"
            )
        else:
            print(
                f"[scheduler] Brak rezerwacji do zakończenia. "
                f"Czas sprawdzenia: {current_time}"
            )

        return changed_count

    except Exception as error:
        db.rollback()
        print(f"[scheduler] Błąd aktualizacji statusów rezerwacji: {error}")
        raise

    finally:
        db.close()


def start_scheduler():
    if scheduler.running:
        print("[scheduler] Scheduler już działa.")
        return

    scheduler.add_job(
        update_reservation_statuses_pl,
        trigger="interval",
        minutes=1,
        id="update_reservation_statuses",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.start()
    print("[scheduler] Scheduler wystartował. Aktualizacja statusów co 1 minutę.")

    # Jednorazowe przeliczenie przy starcie aplikacji
    update_reservation_statuses_pl()


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        print("[scheduler] Scheduler został zatrzymany.")


def is_scheduler_running() -> bool:
    return scheduler.running

# scheduler = BackgroundScheduler()

# def update_reservation_statuses_pl():
#     """Automatyczna aktualizacja statusów rezerwacji."""
#     print(f"[{datetime.now()}] Start aktualizacji rezerwacji...")
#     db: Session = SessionLocal()
#     try:
#         now = datetime.now()
#         # rezerwacje aktywne, które już się skończyły
#         q = (
#             db.query(models.Reservation)
#             .filter(models.Reservation.reservation_status_id == models.ResStatus.SCHEDULED)
#             .filter(models.Reservation.end_time < now)
#         )
#         updated = 0
#         for res in q.all():
#             res.reservation_status_id = models.ResStatus.COMPLETED
#             updated += 1
#         db.commit()
#         print(f"[{datetime.now()}] Zaktualizowano {updated} rezerwacji.")
#         return updated
#     except Exception as e:
#         print(f"[{datetime.now()}] Błąd w schedulerze: {e}")
#         db.rollback()
#     finally:
#         db.close()

# def start_scheduler():
#     """Startuje scheduler jeśli jeszcze nie działa."""
#     if not scheduler.running:
#         scheduler.add_job(
#             update_reservation_statuses_pl,
#             trigger=IntervalTrigger(minutes=5),
#             id="reservations-autofinish",
#             replace_existing=True,
#             coalesce=True,
#             max_instances=1,
#         )
#         scheduler.start()
#         print("Scheduler wystartował (aktualizacja co 5 minut).")

# def stop_scheduler():
#     """Zatrzymuje scheduler."""
#     if scheduler.running:
#         scheduler.shutdown()
#         print("Scheduler został zatrzymany.")


# try:
#     from apscheduler.schedulers.background import BackgroundScheduler
#     _HAS_APSCHEDULER = True
# except Exception:
#     BackgroundScheduler = None
#     _HAS_APSCHEDULER = False

# PL_TZ = ZoneInfo("Europe/Warsaw")

# def now_pl_naive() -> datetime:
#     return datetime.now(PL_TZ).replace(tzinfo=None)

# def update_reservation_statuses_pl(db: Optional[Session] = None) -> int:
#     own_session = False
#     if db is None:
#         db = SessionLocal()
#         own_session = True

#     try:
#         now_ = now_pl_naive()
#         q = (
#             db.query(models.Reservation)
#             .filter(
#                 models.Reservation.reservation_status_id == models.ResStatus.SCHEDULED,
#                 models.Reservation.end_time <= now_,
#             )
#         )
#         updated = q.update(
#             {models.Reservation.reservation_status_id: models.ResStatus.COMPLETED},
#             synchronize_session=False,
#         )
#         db.commit()
#         return int(updated or 0)
#     finally:
#         if own_session and db is not None:
#             db.close()

# _scheduler: Optional[BackgroundScheduler] = None

# def start_scheduler() -> None:
#     global _scheduler
#     if not _HAS_APSCHEDULER or _scheduler:
#         return

#     sched = BackgroundScheduler(timezone=PL_TZ)
#     sched.add_job(
#         update_reservation_statuses_pl,
#         "interval",
#         minutes=1,
#         id="reservations-autofinish",
#         replace_existing=True,
#         coalesce=True,
#         max_instances=1,
#     )
#     sched.start()
#     _scheduler = sched

# def stop_scheduler() -> None:
#     global _scheduler
#     if _scheduler:
#         _scheduler.shutdown(wait=False)
#         _scheduler = None
        