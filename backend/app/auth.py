from __future__ import annotations
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Set
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # Jeśli python-dotenv nie jest zainstalowany, po prostu pomiń
    pass

# --- KONFIG z ENV (z bezpiecznymi defaultami DEV) ---
SECRET_KEY = os.getenv("SECRET_KEY", "2Kox3R19Qsom3MhQNnMFww02xDP3MOLglHjQijffQGgTlG8KDO0EcyDJ1Cp_R7HOQEGBjo9BuBjYRFYi0HmNcw")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

# --- hasła ---
def hash_password(raw: str) -> str:
    return pwd_context.hash(raw)

def verify_password(raw: str, hashed: str) -> bool:
    return pwd_context.verify(raw, hashed)

# --- JWT (kompatybilne API) ---
def create_access_token(
    *,
    # Nowy wariant:
    user_id: Optional[int] = None,
    role_id: Optional[int] = None,
    # Stary wariant (backward-compat):
    subject: Optional[str] = None,
    extra: Optional[dict] = None,
    expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES,
) -> str:
    now = datetime.now(timezone.utc)

    # Ustal 'sub'
    if user_id is not None:
        sub = str(user_id)
    elif subject is not None:
        sub = str(subject)
    else:
        raise ValueError("create_access_token: provide user_id or subject")

    claims = {
        "sub": sub,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }

    # rola (nowy wariant ma priorytet)
    if role_id is not None:
        claims["role"] = role_id
    elif extra and "role" in extra:
        claims["role"] = extra["role"]

    if extra:
        for k, v in extra.items():
            if k not in {"sub", "iat", "exp", "role"}:
                claims[k] = v

    return jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

# --- zależności ---
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    payload = decode_token(token)
    user_id = payload.get("sub")
    # role = payload.get("role")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token missing sub")
    try:
        user_id = int(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Token sub is not an integer")

    user = db.get(models.User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive or unknown user")
    # user.role_id = role or user.role_id 
    return user

def require_role(allowed: Set[int]):
    def _dep(user: models.User = Depends(get_current_user)) -> models.User:
        if user.role_id not in allowed:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user
    return _dep

def require_admin_dev(user: models.User = Depends(get_current_user)) -> models.User:
    if user.role_id != 3:
        raise HTTPException(status_code=403, detail="Admin only")
    return user