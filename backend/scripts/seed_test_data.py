"""
Seed de dados de teste para validar o MVP localmente.
Insere 30 dias de dados realistas para user-mvp-1, cobrindo:
- Social Jetlag (precisa de semana + fim de semana, 14 dias)
- Personal Recovery Curve (precisa de 3+ noites ruins em 30 dias)
- Signal Quality (precisa de raw events)
- ScoreHistory (7 dias)

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

# 30 dias de dados variados
# (offset, sleep_h, deep_sleep_pct, resting_bpm, steps, intensity, stress_score)
# Padrão: fins de semana dormem mais tarde (offset % 7 in [5,6] = sab/dom)
# Noites ruins intencionais em: -27, -20, -13, -6, -2 (para Recovery Curve ter dados)
DAILY_DATA = [
    (-29, 7.2, 0.22, 63, 7800, "moderate", 28),
    (-28, 7.5, 0.23, 62, 8200, "moderate", 25),
    (-27, 4.5, 0.12, 78, 2100, "low",      70),  # noite ruim
    (-26, 6.0, 0.17, 72, 4500, "low",      45),  # recuperando
    (-25, 7.0, 0.21, 65, 6800, "moderate", 30),  # recuperado
    (-24, 8.5, 0.28, 59, 9200, "high",     18),  # fim de semana (dorme mais)
    (-23, 9.0, 0.30, 57, 5100, "low",      15),  # fim de semana
    (-22, 7.3, 0.22, 63, 7600, "moderate", 27),
    (-21, 7.0, 0.20, 64, 8100, "moderate", 30),
    (-20, 4.0, 0.10, 80, 1800, "low",      75),  # noite ruim
    (-19, 5.5, 0.15, 74, 3900, "low",      50),  # recuperando
    (-18, 6.5, 0.19, 67, 6200, "moderate", 35),  # recuperando
    (-17, 7.5, 0.23, 62, 7900, "moderate", 25),  # recuperado
    (-16, 8.0, 0.26, 60, 8800, "high",     20),
    (-15, 9.5, 0.32, 56, 4800, "low",      12),  # fim de semana
    (-14, 8.8, 0.29, 58, 5200, "low",      16),  # fim de semana
    (-13, 4.8, 0.13, 77, 2500, "low",      65),  # noite ruim
    (-12, 6.2, 0.18, 71, 5100, "low",      42),  # recuperando
    (-11, 7.0, 0.21, 65, 7300, "moderate", 28),  # recuperado
    (-10, 7.8, 0.24, 61, 8500, "moderate", 22),
    (-9,  8.2, 0.27, 60, 9100, "high",     19),
    (-8,  9.0, 0.31, 57, 4600, "low",      14),  # fim de semana
    (-7,  8.5, 0.28, 59, 5000, "low",      17),  # fim de semana
    (-6,  4.2, 0.11, 79, 2000, "low",      72),  # noite ruim
    (-5,  6.0, 0.18, 68, 5100, "low",      40),  # recuperando
    (-4,  8.0, 0.25, 60, 9800, "high",     20),  # recuperado
    (-3,  7.5, 0.22, 62, 8200, "moderate", 25),
    (-2,  4.5, 0.12, 76, 2200, "low",      68),  # noite ruim
    (-1,  8.5, 0.28, 58, 6400, "low",      15),  # recuperando
    ( 0,  7.2, 0.21, 63, 4100, "moderate", 28),  # hoje
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

    sleep_rows, steps_rows, hr_rows, activity_rows, raw_rows = [], [], [], [], []

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
            "record_id":        str(uuid.uuid4()),
            "user_id":          USER_ID,
            "date":             d,
            "activity_type":    "walking",
            "duration_minutes": 45,
            "intensity":        intensity,
            "calories_burned":  float(steps * 0.04),
            "source_event_id":  evt_id,
            "normalized_at":    TODAY.isoformat(),
        })

        # Raw events para Signal Quality funcionar
        for metric in ["sleep", "steps", "heart_rate", "activity"]:
            raw_rows.append({
                "event_id":     str(uuid.uuid4()),
                "user_id":      USER_ID,
                "provider":     "google_fit",
                "metric_type":  metric,
                "raw_payload":  "{}",
                "collected_at": d + "T00:00:00",
                "ingested_at":  d + "T00:00:00",
                "pipeline_run": "seed",
            })

    await wh.insert("normalized_sleep",      sleep_rows)
    await wh.insert("normalized_steps",      steps_rows)
    await wh.insert("normalized_heart_rate", hr_rows)
    await wh.insert("normalized_activity",   activity_rows)
    await wh.insert("raw_health_events",     raw_rows)

    print(f"Inserted {len(sleep_rows)} days of data for user '{USER_ID}'")
    print(f"Dates: {(TODAY + timedelta(days=-29)).isoformat()} to {TODAY.isoformat()}")
    print("\nCalculating Daily Readiness for all days...")

    from app.services.readiness_service import ReadinessService
    svc = ReadinessService()
    for offset, *_ in DAILY_DATA:
        d = (TODAY + timedelta(days=offset)).isoformat()
        result = await svc.calculate(USER_ID, d)
        if result:
            print(f"  {d}: score={result['readiness_score']:.0f} | {result['readiness_category']} | {result['insight_text'][:55]}...")

    print("\nDone! Test the API:")
    print(f"  GET http://localhost:8000/api/v1/readiness/{USER_ID}")
    print(f"  GET http://localhost:8000/api/v1/readiness/{USER_ID}/advanced")
    print(f"  GET http://localhost:8000/api/v1/health-data/{USER_ID}/summary?date={TODAY.isoformat()}")


if __name__ == "__main__":
    asyncio.run(main())
