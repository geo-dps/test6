import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    token: str
    timezone: str
    db_path: str
    reminder_hour: int
    reminder_minute: int

def load_config():
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is not set")
    return Config(
        token=token,
        timezone=os.getenv("TIMEZONE", "Europe/Berlin"),
        db_path=os.getenv("DB_PATH", "/data/ogonek.db"),
        reminder_hour=int(os.getenv("REMINDER_HOUR", "20")),
        reminder_minute=int(os.getenv("REMINDER_MINUTE", "0")),
    )
