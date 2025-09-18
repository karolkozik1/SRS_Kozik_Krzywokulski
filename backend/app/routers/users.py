import re
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas, auth
from app.database import get_db
from fastapi.security import OAuth2PasswordRequestForm
from zoneinfo import ZoneInfo

def now_pl_naive() -> datetime:
    return datetime.now(ZoneInfo("Europe/Warsaw")).replace(tzinfo=None)

router = APIRouter()

@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(400, "Email już istnieje")

    local_part = user.email.split("@")[0]
    role_id = 1 if re.fullmatch(r"\d{6}", local_part) else 2

    new_user = models.User(
        email=user.email,
        password_hash=auth.hash_password(user.password),
        first_name=user.first_name,
        last_name=user.last_name,
        role_id=role_id,
        created_at=now_pl_naive(),
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=schemas.Token)
def login(form: OAuth2PasswordRequestForm = Depends(),
          db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form.username).first()
    if not user or not auth.verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Nieprawidłowy email lub hasło")
    
    user.last_login = now_pl_naive()
    db.commit()

    token = auth.create_access_token(user_id=user.id, role_id=user.role_id)
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserOut)
def me(current: models.User = Depends(auth.get_current_user)):
    return current