from datetime import datetime
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("Europe/Warsaw")
UTC_TZ   = ZoneInfo("UTC")

def now_utc() -> datetime:
    return datetime.utcnow()

def to_utc(aware_or_naive_local: datetime) -> datetime:
    dt = aware_or_naive_local
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=LOCAL_TZ)
    return dt.astimezone(UTC_TZ).replace(tzinfo=None)

def utc_to_local(naive_utc: datetime) -> datetime:
    return naive_utc.replace(tzinfo=UTC_TZ).astimezone(LOCAL_TZ)