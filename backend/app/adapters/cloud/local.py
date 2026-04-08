"""
Adapters locais para desenvolvimento.
StorageProvider → filesystem local
WarehouseProvider → SQLite (via aiosqlite)
PipelineProvider → DirectRunner
"""
from pathlib import Path

import aiosqlite

from app.adapters.cloud.base import StorageProvider, WarehouseProvider, PipelineProvider
from app.config.cloud_config import LocalConfig

# DDL das tabelas do warehouse local (espelha o modelo de dados)
_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS raw_health_events (
    event_id      TEXT PRIMARY KEY,
    user_id       TEXT NOT NULL,
    provider      TEXT NOT NULL,
    metric_type   TEXT NOT NULL,
    raw_payload   TEXT NOT NULL,
    collected_at  TEXT NOT NULL,
    ingested_at   TEXT NOT NULL,
    pipeline_run  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS normalized_sleep (
    record_id            TEXT PRIMARY KEY,
    user_id              TEXT NOT NULL,
    date                 TEXT NOT NULL,
    duration_minutes     INTEGER,
    deep_sleep_minutes   INTEGER,
    light_sleep_minutes  INTEGER,
    rem_sleep_minutes    INTEGER,
    awake_minutes        INTEGER,
    sleep_score          REAL,
    source_event_id      TEXT,
    normalized_at        TEXT
);

CREATE TABLE IF NOT EXISTS normalized_steps (
    record_id        TEXT PRIMARY KEY,
    user_id          TEXT NOT NULL,
    date             TEXT NOT NULL,
    total_steps      INTEGER,
    hourly_steps     TEXT,
    source_event_id  TEXT,
    normalized_at    TEXT
);

CREATE TABLE IF NOT EXISTS normalized_activity (
    record_id        TEXT PRIMARY KEY,
    user_id          TEXT NOT NULL,
    date             TEXT NOT NULL,
    activity_type    TEXT,
    duration_minutes INTEGER,
    intensity        TEXT,
    calories_burned  REAL,
    source_event_id  TEXT,
    normalized_at    TEXT
);

CREATE TABLE IF NOT EXISTS normalized_heart_rate (
    record_id        TEXT PRIMARY KEY,
    user_id          TEXT NOT NULL,
    date             TEXT NOT NULL,
    resting_bpm      REAL,
    average_bpm      REAL,
    max_bpm          REAL,
    min_bpm          REAL,
    source_event_id  TEXT,
    normalized_at    TEXT
);

CREATE TABLE IF NOT EXISTS normalized_stress (
    record_id        TEXT PRIMARY KEY,
    user_id          TEXT NOT NULL,
    date             TEXT NOT NULL,
    stress_score     REAL,
    available        INTEGER,
    source_event_id  TEXT,
    normalized_at    TEXT
);

CREATE TABLE IF NOT EXISTS dim_user (
    user_id     TEXT PRIMARY KEY,
    provider    TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS oauth_tokens (
    user_id       TEXT NOT NULL,
    provider      TEXT NOT NULL,
    access_token  TEXT NOT NULL,
    refresh_token TEXT,
    expires_at    TEXT NOT NULL,
    PRIMARY KEY (user_id, provider)
);

CREATE TABLE IF NOT EXISTS fact_daily_readiness (
    readiness_id                 TEXT PRIMARY KEY,
    user_id                      TEXT NOT NULL,
    date                         TEXT NOT NULL,
    readiness_score              REAL NOT NULL,
    readiness_category           TEXT NOT NULL,
    sleep_score_contribution     REAL,
    hr_score_contribution        REAL,
    activity_score_contribution  REAL,
    stress_score_contribution    REAL,
    insight_text                 TEXT,
    calculated_at                TEXT NOT NULL,
    UNIQUE(user_id, date)
);
"""


class LocalStorageProvider(StorageProvider):
    def __init__(self, config: LocalConfig):
        self.base = Path(config.data_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    async def upload(self, path: str, data: bytes, content_type: str = None) -> str:
        full = self.base / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_bytes(data)
        return f"local://{full}"

    async def download(self, path: str) -> bytes:
        return (self.base / path).read_bytes()

    async def list(self, prefix: str) -> list[str]:
        return [str(p.relative_to(self.base)) for p in (self.base / prefix).rglob("*") if p.is_file()]


class LocalWarehouseProvider(WarehouseProvider):
    def __init__(self, config: LocalConfig):
        self.db_path = config.db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    async def init_schema(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(_SCHEMA_SQL)
            await db.commit()

    async def insert(self, table: str, rows: list[dict]) -> int:
        if not rows:
            return 0
        async with aiosqlite.connect(self.db_path) as db:
            cols = list(rows[0].keys())
            placeholders = ", ".join(["?" for _ in cols])
            col_names = ", ".join(cols)
            sql = f"INSERT OR REPLACE INTO {table} ({col_names}) VALUES ({placeholders})"
            values = [tuple(row[c] for c in cols) for row in rows]
            await db.executemany(sql, values)
            await db.commit()
            return len(rows)

    async def query(self, sql: str, params: dict = None) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if params:
                # Converte :param para ? e lista de valores
                import re
                keys = re.findall(r":(\w+)", sql)
                sql = re.sub(r":\w+", "?", sql)
                values = [params[k] for k in keys]
                cursor = await db.execute(sql, values)
            else:
                cursor = await db.execute(sql)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


class LocalPipelineProvider(PipelineProvider):
    def get_runner_name(self) -> str:
        return "DirectRunner"

    def get_runner_options(self) -> dict:
        return {}
