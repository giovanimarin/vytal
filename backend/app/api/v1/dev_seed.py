"""
Endpoint de seed para desenvolvimento — cria usuário demo e insere 14 dias
de dados mockados realistas para testar todas as funcionalidades via web.

Disponível apenas em ambiente local/dev (não em produção).
"""
import random
import uuid
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException

from app.adapters.cloud.factory import get_warehouse
from app.config.settings import settings
from app.services.auth_service import AuthService
from app.services.readiness_service import ReadinessService
from app.services.readiness_modality_service import ReadinessModalityService
from app.services.muscle_recovery_service import MuscleRecoveryService
from app.services.workout_service import WorkoutService
from app.repositories.health_data_repo import HealthDataRepository
from app.domain.health_metrics.sleep import SleepMetric
from app.domain.health_metrics.heart_rate import HeartRateMetric
from app.domain.health_metrics.activity import ActivityMetric
from app.domain.health_metrics.stress import StressMetric
from app.domain.health_metrics.steps import StepsMetric

router = APIRouter(prefix="/dev", tags=["dev"])

DEMO_EMAIL = "demo@vytal.app"
DEMO_PASSWORD = "demo1234"
DEMO_NAME = "Demo User"

# Plano semanal: (modality_PT, intensity_PT, intensity_EN, duration_min, exercises[])
_WORKOUT_PLAN = {
    0: ("academia",  "moderado", "moderate", 55, ["Supino reto", "Puxada frontal", "Desenvolvimento", "Rosca direta"]),
    1: ("corrida",   "intenso",  "high",     40, []),
    2: ("academia",  "moderado", "moderate", 50, ["Agachamento", "Leg press", "Stiff", "Panturrilha em pé"]),
    3: None,
    4: ("crossfit",  "intenso",  "high",     45, []),
    5: ("yoga",      "leve",     "low",      60, []),
    6: None,
}


@router.post("/seed")
async def seed_demo_data():
    """
    Cria o usuário demo e insere 14 dias de dados mockados.
    Idempotente: limpa dados anteriores do usuário e reinicia.
    """
    if settings.environment not in ("local", "development", "dev"):
        raise HTTPException(status_code=403, detail="Seed only available in local/dev environment.")

    auth = AuthService()
    wh = get_warehouse()

    # ── 1. Criar/recuperar usuário demo ──────────────────────────────────────
    import json as _json
    try:
        auth_data = await auth.register(DEMO_EMAIL, DEMO_PASSWORD, DEMO_NAME)
        user_id = auth_data["user_id"]
    except HTTPException as e:
        if e.status_code == 409:
            rows = await wh.query("SELECT user_id FROM users WHERE email = :e", {"e": DEMO_EMAIL})
            user_id = rows[0]["user_id"]
        else:
            raise

    # Set demo profile defaults
    from datetime import datetime, timezone as _tz
    await wh.query(
        "UPDATE users SET gender = ?, preferred_modalities = ?, updated_at = ? WHERE user_id = ?",
        ["male", _json.dumps(["academia", "corrida", "crossfit", "yoga"]),
         datetime.now(_tz.utc).isoformat(), user_id],
    )

    # Limpa dados anteriores desse usuário para seed idempotente
    for table in [
        "normalized_sleep", "normalized_heart_rate", "normalized_activity",
        "normalized_stress", "normalized_steps",
        "fact_daily_readiness", "fact_readiness_by_modality",
        "muscle_recovery",
    ]:
        await wh.query(f"DELETE FROM {table} WHERE user_id = ?", [user_id])
    # workout_exercises links via workout_id, not user_id
    await wh.query(
        "DELETE FROM workout_exercises WHERE workout_id IN (SELECT workout_id FROM workout_history WHERE user_id = ?)",
        [user_id],
    )
    await wh.query("DELETE FROM workout_history WHERE user_id = ?", [user_id])

    # ── 2. Inserir 14 dias de dados ───────────────────────────────────────────
    today = date.today()
    repo = HealthDataRepository()
    readiness_svc = ReadinessService()
    modality_svc = ReadinessModalityService()
    recovery_svc = MuscleRecoveryService()
    workout_svc = WorkoutService()

    random.seed(42)
    inserted_days = []

    for offset in range(13, -1, -1):
        day = today - timedelta(days=offset)
        day_str = day.isoformat()
        day_date = day
        weekday = day.weekday()

        # ── Sono ──
        duration_min = int(random.gauss(430, 45))
        duration_min = max(240, min(540, duration_min))
        deep  = int(duration_min * random.uniform(0.15, 0.25))
        rem   = int(duration_min * random.uniform(0.20, 0.28))
        light = int(duration_min * 0.50)
        awake = max(0, duration_min - deep - rem - light)
        sleep_score = float(min(100, max(40, int(
            (duration_min / 480) * 70 + (deep / max(1, duration_min)) * 30
        ))))

        await repo.save_normalized(SleepMetric(
            _user_id=user_id, _date=day_date,
            duration_minutes=duration_min,
            deep_sleep_minutes=deep, light_sleep_minutes=light,
            rem_sleep_minutes=rem, awake_minutes=awake,
            sleep_score=sleep_score, source_event_id=None,
        ))

        # ── Frequência Cardíaca ──
        plan_yesterday = _WORKOUT_PLAN.get((weekday - 1) % 7)
        resting = 58.0
        if plan_yesterday and plan_yesterday[2] == "high":
            resting += random.uniform(3, 8)
        resting = round(resting + random.gauss(0, 2), 1)
        resting = max(45.0, min(90.0, resting))

        await repo.save_normalized(HeartRateMetric(
            _user_id=user_id, _date=day_date,
            resting_bpm=resting,
            average_bpm=round(resting + random.uniform(12, 20), 1),
            max_bpm=round(resting + random.uniform(60, 90), 1),
            min_bpm=round(max(40.0, resting - random.uniform(2, 5)), 1),
            source_event_id=None,
        ))

        # ── Passos ──
        base_steps = 9000 if _WORKOUT_PLAN.get(weekday) else 5500
        total_steps = max(1000, int(base_steps + random.gauss(0, 1200)))

        await repo.save_normalized(StepsMetric(
            _user_id=user_id, _date=day_date,
            total_steps=total_steps,
            hourly_steps=[],
            source_event_id=None,
        ))

        # ── Stress ──
        stress_val = random.uniform(20, 55)
        if duration_min < 360:
            stress_val += 20
        await repo.save_normalized(StressMetric(
            _user_id=user_id, _date=day_date,
            stress_score=round(min(100.0, stress_val), 1),
            available=True,
            source_event_id=None,
        ))

        # ── Atividade ──
        plan = _WORKOUT_PLAN.get(weekday)
        if plan:
            modality_pt, intensity_pt, intensity_en, dur, exercises = plan
            await repo.save_normalized(ActivityMetric(
                _user_id=user_id, _date=day_date,
                activity_type=modality_pt,
                duration_minutes=dur,
                intensity=intensity_en,
                calories_burned=round(dur * random.uniform(7, 12), 1),
                source_event_id=None,
            ))
            # Registra no workout_history para readiness/recovery
            await workout_svc.register(user_id, {
                "modality":     modality_pt,
                "intensity":    intensity_pt,
                "duration_min": dur,
                "date":         day_str,
                "notes":        None,
                "exercises":    [{"name": ex} for ex in exercises],
                "free_text":    None,
            })

        # ── Daily Readiness ──
        await readiness_svc.calculate(user_id, day_str)
        inserted_days.append(day_str)

    # ── 3. Métricas derivadas para hoje ──────────────────────────────────────
    today_str = today.isoformat()
    await modality_svc.calculate_all(user_id, today_str)
    await recovery_svc.calculate(user_id, today_str)

    # ── 4. Retorna credenciais ────────────────────────────────────────────────
    login_result = await auth.login(DEMO_EMAIL, DEMO_PASSWORD)

    return {
        "ok": True,
        "user_id": user_id,
        "email": DEMO_EMAIL,
        "password": DEMO_PASSWORD,
        "access_token": login_result["access_token"],
        "refresh_token": login_result["refresh_token"],
        "days_seeded": len(inserted_days),
        "date_range": {"from": inserted_days[0], "to": inserted_days[-1]},
        "message": "Demo data ready. Use the credentials to login.",
    }
