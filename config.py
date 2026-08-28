import sqlite3
import asyncio
from pathlib import Path

class DB:
    def __init__(self, path):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = asyncio.Lock()

    def conn(self):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        return c

    async def init(self):
        async with self.lock:
            c = self.conn()
            try:
                c.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sparks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_id INTEGER NOT NULL,
                    partner_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    accepted_at TEXT,
                    UNIQUE(owner_id, partner_id)
                );
                CREATE TABLE IF NOT EXISTS activity (
                    spark_id INTEGER NOT NULL,
                    day TEXT NOT NULL,
                    owner_active INTEGER NOT NULL DEFAULT 0,
                    partner_active INTEGER NOT NULL DEFAULT 0,
                    counted INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY(spark_id, day)
                );
                CREATE TABLE IF NOT EXISTS state (
                    spark_id INTEGER PRIMARY KEY,
                    streak INTEGER NOT NULL DEFAULT 0,
                    last_counted_day TEXT
                );
                """)
                c.commit()
            finally:
                c.close()

    async def upsert_user(self, u, now):
        async with self.lock:
            c=self.conn()
            try:
                c.execute("""INSERT INTO users(user_id,username,first_name,created_at)
                             VALUES(?,?,?,?)
                             ON CONFLICT(user_id) DO UPDATE SET username=excluded.username,
                             first_name=excluded.first_name""",
                          (u.id, u.username or "", u.first_name or "", now))
                c.commit()
            finally: c.close()

    async def get_user(self, uid):
        async with self.lock:
            c=self.conn()
            try: return c.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
            finally: c.close()

    async def get_spark(self, owner, partner, include_pending=True):
        async with self.lock:
            c=self.conn()
            try:
                q="SELECT * FROM sparks WHERE owner_id=? AND partner_id=?"
                if not include_pending: q += " AND status='active'"
                return c.execute(q,(owner,partner)).fetchone()
            finally: c.close()

    async def create_spark(self, owner, partner, now):
        async with self.lock:
            c=self.conn()
            try:
                c.execute("INSERT OR IGNORE INTO sparks(owner_id,partner_id,status,created_at) VALUES(?,?,?,?)",
                          (owner,partner,"pending",now))
                c.commit()
            finally: c.close()

    async def accept_spark(self, spark_id, now):
        async with self.lock:
            c=self.conn()
            try:
                c.execute("UPDATE sparks SET status='active',accepted_at=? WHERE id=?",
                          (now,spark_id))
                c.execute("INSERT OR IGNORE INTO state(spark_id,streak) VALUES(?,0)",(spark_id,))
                c.commit()
            finally: c.close()

    async def decline_spark(self, spark_id):
        async with self.lock:
            c=self.conn()
            try:
                c.execute("DELETE FROM sparks WHERE id=?",(spark_id,))
                c.commit()
            finally: c.close()

    async def active_for_user(self, uid):
        async with self.lock:
            c=self.conn()
            try:
                return c.execute(
                    "SELECT * FROM sparks WHERE status='active' AND (owner_id=? OR partner_id=?)",
                    (uid,uid)).fetchall()
            finally: c.close()

    async def all_active(self):
        async with self.lock:
            c=self.conn()
            try: return c.execute("SELECT * FROM sparks WHERE status='active'").fetchall()
            finally: c.close()

    async def mark_activity(self, spark_id, day, side):
        async with self.lock:
            c=self.conn()
            try:
                c.execute("INSERT OR IGNORE INTO activity(spark_id,day) VALUES(?,?)",(spark_id,day))
                col="owner_active" if side=="owner" else "partner_active"
                c.execute(f"UPDATE activity SET {col}=1 WHERE spark_id=? AND day=?",(spark_id,day))
                row=c.execute("SELECT * FROM activity WHERE spark_id=? AND day=?",(spark_id,day)).fetchone()
                became=bool(row["owner_active"] and row["partner_active"] and not row["counted"])
                if became:
                    c.execute("UPDATE activity SET counted=1 WHERE spark_id=? AND day=?",(spark_id,day))
                c.commit()
                return became, row
            finally: c.close()

    async def state(self, spark_id):
        async with self.lock:
            c=self.conn()
            try: return c.execute("SELECT * FROM state WHERE spark_id=?",(spark_id,)).fetchone()
            finally: c.close()

    async def set_state(self, spark_id, streak, last_day):
        async with self.lock:
            c=self.conn()
            try:
                c.execute("""INSERT INTO state(spark_id,streak,last_counted_day) VALUES(?,?,?)
                    ON CONFLICT(spark_id) DO UPDATE SET streak=excluded.streak,last_counted_day=excluded.last_counted_day""",
                    (spark_id,streak,last_day))
                c.commit()
            finally: c.close()

    async def today_activity(self, spark_id, day):
        async with self.lock:
            c=self.conn()
            try: return c.execute("SELECT * FROM activity WHERE spark_id=? AND day=?",(spark_id,day)).fetchone()
            finally: c.close()
