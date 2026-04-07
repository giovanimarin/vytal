"""
Seed de dados de teste para validar o MVP localmente.
Insere 7 dias de dados realistas para user-mvp-1.

Uso:
    python scripts/seed_test_data.py
"""
import asyncio
import sys
import os
from datetime import date, timedelta
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.adapters.cloud.factory import init_warehouse, get_warehouse

USER_ID = "user-mvp-1"
TODAY = date.today()

# 7 dias de dados variados para o Daily Readiness ter variação real
DAILY_DATA = [
    # date_offset, sleep_h, deep_sleep_pct, resting_bpm, steps, activity, stress
    (-6, 7.5, 0.22, 62, 8200, "moderate", 25),
    (-5, 6.0, 0.18, 68, 5100, "low",      40),
    (-4, 8.0, 0.25, 60, 9800, "high",     20),
    (-3, 5.0, 0.15, 75, 3200, "low",      55),  # dia ruim
    (-2, 7.0, 0.20, 64, 7600, "moderate", 30),
    (-1, 8.5, 0.28, 58, 6400, "low",      15),  # excelente recuperação
    ( 0, 7.2, 0.21, 63, 4100, "moderate", 28),  # hoje
]


async def main():
    await init_warehouse()
    wh = get_warehouse()

    # Garante que o usuário existe
    await wh.insert("dim_user", [{
        "user_id": USER_ID,
        "provider": "google_fit",
        "created_at": TODAY.isoformat(),
    }])

    sleep_rows, steps_rows, hr_rows, activity_rows = [], [], [], []

    for offset, sleep_h, deep_pct, resting_bpm, steps, intensity, stress_score in DAILY_DATA:
        d = (TODAY + timedelta(days=offset)).isoformat()
        total_min = int(sleep_h * 60)
        evt_id = str(uuid.uuid4())

        sleep_rows.append({
            "record_id":           str(uuid.uuid4()),
            "user_id":             USER_ID,
            "date":                d,
            "duration_minutes":    total_min,
            "deep_sleep_minutes":  int(total_min * deep_pct),
            "light_sleep_minutes": int(total_min * 0.55),
            "rem_sleep_minutes":   int(total_min * 0.20),
            "awake_minutes":       int(total_min * 0.05),
            "sleep_score":         round(min(100, sleep_h / 9 * 100), 1),
            "source_event_id":     evt_id,
            "normalized_at":       TODAY.isoformat(),
        })

        steps_rows.append({
            "record_id":       str(uuid.uuid4()),
            "user_id":         USER_ID,
            "date":            d,
            "total_steps":     steps,
            "hourly_steps":    "[]",
            "source_event_id": evt_id,
            "normalized_at":   TODAY.isoformat(),
        })

        hr_rows.append({
            "record_id":       str(uuid.uuid4()),
            "user_id":         USER_ID,
            "date":            d,
            "resting_bpm":     float(resting_bpm),
            "average_bpm":     float(resting_bpm + 12),
            "max_bpm":         float(resting_bpm + 60),
            "min_bpm":         float(resting_bpm - 5),
            "source_event_id": evt_id,
            "normalized_at":   TODAY.isoformat(),
        })

        activity_rows.append({
            "record_id":       str(uuid.uuid4()),
            "user_id":         USER_ID,
            "date":            d,
            "activity_type":   "walking",
            "duration_minutes": 45,
            "intensity":       intensity,
            "calories_burned": float(steps * 0.04),
            "source_event_id": evt_id,
            "normalized_at":   TODAY.isoformat(),
        })

    await wh.insert("normalized_sleep",      sleep_rows)
    await wh.insert("normalized_steps",      steps_rows)
    await wh.insert("normalized_heart_rate", hr_rows)
    await wh.insert("normalized_activity",   activity_rows)

    print(f"Inserted {len(sleep_rows)} days of data for user '{USER_ID}'")
    print(f"Dates: {(TODAY + timedelta(days=-6)).isoformat()} to {TODAY.isoformat()}")
    print("\nCalculating Daily Readiness for all days...")

    from app.services.readiness_service import ReadinessService
    svc = ReadinessService()
    for offset, *_ in DAILY_DATA:
        d = (TODAY + timedelta(days=offset)).isoformat()
        result = await svc.calculate(USER_ID, d)
        if result:
            print(f"  {d}: score={result['readiness_score']} | {result['readiness_category']} | {result['insight_text'][:60]}...")

    print("\nDone! Test the API:")
    print(f"  GET http://localhost:8000/api/v1/readiness/{USER_ID}")
    print(f"  GET http://localhost:8000/api/v1/health-data/{USER_ID}/summary?date={TODAY.isoformat()}")


if __name__ == "__main__":
    asyncio.run(main())
