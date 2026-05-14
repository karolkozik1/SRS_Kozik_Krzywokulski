import os
import urllib.parse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base


DB_USER = os.getenv("SQLSERVER_USER", "sa")
DB_PASSWORD = os.getenv("SQLSERVER_PASSWORD", "TwojeSilneHaslo123!")
DB_HOST = os.getenv("SQLSERVER_HOST", "db")
DB_PORT = os.getenv("SQLSERVER_PORT", "1433")
DB_NAME = os.getenv("SQLSERVER_DB", "SystemRezerwacjiSal")

params = urllib.parse.quote_plus(
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={DB_HOST},{DB_PORT};"
    f"DATABASE={DB_NAME};"
    f"UID={DB_USER};"
    f"PWD={DB_PASSWORD};"
    f"TrustServerCertificate=yes;"
)

SQLALCHEMY_DATABASE_URL = f"mssql+pyodbc:///?odbc_connect={params}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()