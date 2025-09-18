from datetime import datetime, timedelta, date
from io import StringIO, BytesIO
import csv
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, auth
from typing import List
from sqlalchemy import and_
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

router = APIRouter()

def _start_of_day(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, 0, 0, 0)

def _end_of_day(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, 23, 59, 59)

# ---------- CSV: lista rezerwacji w przedziale ----------
@router.get("/reservations.csv", tags=["Reports"])
def reservations_csv(
    date_from: date = Query(...),
    date_to:   date = Query(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.require_admin_dev),
):
    if date_to < date_from:
        raise HTTPException(400, "date_to < date_from")

    start_dt = _start_of_day(date_from)
    end_dt   = _end_of_day(date_to)

    rows = (
        db.query(models.Reservation, models.Room, models.User)
          .join(models.Room, models.Reservation.room_id == models.Room.id)
          .join(models.User, models.Reservation.user_id == models.User.id)
          .filter(models.Reservation.start_time >= start_dt,
                  models.Reservation.start_time <= end_dt)
          .order_by(models.Reservation.start_time.asc())
          .all()
    )

    f = StringIO()
    w = csv.writer(f, delimiter=';')
    w.writerow(["ReservationId","Status","UserEmail","Room","BuildingId","Start","End","Hours","CancelReason"])
    for res, room, usr in rows:
        hours = (res.end_time - res.start_time).total_seconds() / 3600.0
        w.writerow([
            res.id,
            res.reservation_status_id,
            usr.email,
            room.room_number,
            room.building_id,
            res.start_time.strftime("%Y-%m-%d %H:%M"),
            res.end_time.strftime("%Y-%m-%d %H:%M"),
            f"{hours:.2f}",
            res.cancel_reason or ""
        ])

    f.seek(0)
    return StreamingResponse(
        iter([f.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reservations.csv"}
    )

# ---------- PDF: prosty raport rezerwacji ----------
STATUS_LABELS = {1: "Aktywna", 2: "Anulowana", 3: "Zakończona"}

def _register_pl_font() -> str:
    app_dir = Path(__file__).resolve().parents[1]  # .../app
    dejavu = app_dir / "fonts" / "DejaVuSans.ttf"

    # 1) DejaVu z projektu
    try:
        if dejavu.exists():
            pdfmetrics.registerFont(TTFont("DejaVuSans", str(dejavu)))
            return "DejaVuSans"
    except Exception:
        pass

    # 2) Arial z Windows (polskie znaki)
    try:
        arial_path = Path(r"C:\Windows\Fonts\arial.ttf")
        if arial_path.exists():
            pdfmetrics.registerFont(TTFont("Arial", str(arial_path)))
            return "Arial"
    except Exception:
        pass

    return "Helvetica"

@router.get(
    "/reports/reservations.pdf",
    tags=["Reports"],
    responses={
        200: {
            "content": {"application/pdf": {"schema": {"type": "string", "format": "binary"}}},
            "description": "Raport rezerwacji (PDF)",
        }
    },
)
def reservations_pdf(
    date_from: date = Query(..., description="YYYY-MM-DD"),
    date_to:   date = Query(..., description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.require_admin_dev),
):
    # --- dane ---
    q = (
        db.query(models.Reservation, models.Room, models.User)
        .join(models.Room, models.Reservation.room_id == models.Room.id)
        .join(models.User, models.Reservation.user_id == models.User.id)
        .filter(
            and_(
                models.Reservation.start_time >= datetime.combine(date_from, datetime.min.time()),
                models.Reservation.end_time   <= datetime.combine(date_to,   datetime.max.time()),
            )
        )
        .order_by(models.Reservation.start_time)
    )
    rows = q.all()

    # --- PDF ---
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
        title="Raport rezerwacji",
    )
    story: List = []

    font_name = _register_pl_font()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitlePL", fontName=font_name, fontSize=16, leading=20, spaceAfter=12))
    styles.add(ParagraphStyle(name="NormalPL", fontName=font_name, fontSize=10, leading=12))

    story.append(Paragraph(f"Raport rezerwacji {date_from:%Y-%m-%d} – {date_to:%Y-%m-%d}", styles["TitlePL"]))
    story.append(Spacer(1, 6))

    data = [["ID", "Data/Godz.", "Sala", "Budynek", "Uzytkownik", "Status"]]
    for res, room, u in rows:
        time_str = f"{res.start_time:%Y-%m-%d %H:%M}–{res.end_time:%H:%M}"
        data.append([
            str(res.id),
            time_str,
            getattr(room, "room_number", str(room.id)),
            str(room.building_id),
            u.email,
            STATUS_LABELS.get(res.reservation_status_id, str(res.reservation_status_id)),
        ])

    total_width = A4[0] - 3.0*cm
    col_widths = [1.2*cm, 4.2*cm, 2.2*cm, 2.2*cm, total_width - (1.2+4.2+2.2+2.2+2.6)*cm, 2.6*cm]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('FONT', (0,0), (-1,-1), font_name, 9),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('ALIGN', (0,1), (0,-1), 'RIGHT'),   # ID
        ('ALIGN', (1,1), (1,-1), 'CENTER'),  # Data/Godz.
        ('ALIGN', (2,1), (3,-1), 'CENTER'),  # Sala, Budynek
        ('ALIGN', (5,1), (5,-1), 'CENTER'),  # Status
    ]))
    story.append(table)
    doc.build(story)

    buf.seek(0)
    filename = f"raport_rezerwacji_{date_from}_{date_to}.pdf"
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )