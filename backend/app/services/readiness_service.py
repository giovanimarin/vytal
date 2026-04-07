import uuid
from datetime import datetime, timezone

from app.repositories.health_data_repo import HealthDataRepository
from app.repositories.readiness_repo import ReadinessRepository

# Pesos do Daily Readiness Score (somam 1.0)
_WEIGHTS = {
    "sleep":    0.40,
    "hr":       0.30,
    "activity": 0.20,
    "stress":   0.10,
}

_CATEGORY_MAP = [
    (80, "intense"),
    (50, "moderate"),
    (30, "light"),
    (0,  "rest"),
]

_INSIGHT_MAP = {
    "intense":  "Sua recuperação está ótima! Hoje é um bom dia para um treino intenso.",
    "moderate": "Você está bem recuperado. Um treino moderado ou cardio é recomendado.",
    "light":    "Seu corpo ainda está se recuperando. Prefira atividades leves hoje.",
    "rest":     "Seus indicadores sugerem que seu corpo precisa de descanso. Priorize o sono e a recuperação.",
}


class ReadinessService:
    def __init__(self):
        self.health_repo = HealthDataRepository()
        self.readiness_repo = ReadinessRepository()

    async def calculate(self, user_id: str, date: str) -> dict | None:
        """
        Calcula o Daily Readiness Score para user_id na data informada.
        Retorna None se não houver dados suficientes.
        """
        sleep_rows   = await self.health_repo.get_normalized(user_id, date, "sleep")
        hr_rows      = await self.health_repo.get_normalized(user_id, date, "heart_rate")
        activity_rows = await self.health_repo.get_normalized(user_id, date, "activity")
        stress_rows  = await self.health_repo.get_normalized(user_id, date, "stress")

        # Sleep e FC são obrigatórios para calcular
        if not sleep_rows or not hr_rows:
            return None

        sleep   = sleep_rows[0]
        hr      = hr_rows[0]
        stress  = stress_rows[0] if stress_rows else None

        sleep_contrib    = self._sleep_contribution(sleep)
        hr_contrib       = self._hr_contribution(hr)
        activity_contrib = self._activity_contribution(activity_rows)
        stress_contrib   = self._stress_contribution(stress)

        # Redistribui peso do stress se indisponível
        if stress_contrib is None:
            total_weight = 1.0 - _WEIGHTS["stress"]
            score = (
                sleep_contrib    * (_WEIGHTS["sleep"]    / total_weight) +
                hr_contrib       * (_WEIGHTS["hr"]       / total_weight) +
                activity_contrib * (_WEIGHTS["activity"] / total_weight)
            )
        else:
            score = (
                sleep_contrib    * _WEIGHTS["sleep"] +
                hr_contrib       * _WEIGHTS["hr"] +
                activity_contrib * _WEIGHTS["activity"] +
                stress_contrib   * _WEIGHTS["stress"]
            )

        score = round(max(0.0, min(100.0, score)), 1)
        category = self._to_category(score)

        record = {
            "readiness_id":                 str(uuid.uuid4()),
            "user_id":                      user_id,
            "date":                         date,
            "readiness_score":              score,
            "readiness_category":           category,
            "sleep_score_contribution":     round(sleep_contrib, 1),
            "hr_score_contribution":        round(hr_contrib, 1),
            "activity_score_contribution":  round(activity_contrib, 1),
            "stress_score_contribution":    round(stress_contrib, 1) if stress_contrib is not None else None,
            "insight_text":                 _INSIGHT_MAP[category],
            "calculated_at":               datetime.now(timezone.utc).isoformat(),
        }

        await self.readiness_repo.save(record)
        return record

    async def get(self, user_id: str, date: str) -> dict | None:
        record = await self.readiness_repo.get(user_id, date)
        if record:
            return record
        # Tenta calcular se ainda não foi calculado
        return await self.calculate(user_id, date)

    async def get_history(self, user_id: str, start_date: str, end_date: str) -> list[dict]:
        return await self.readiness_repo.get_history(user_id, start_date, end_date)

    # -------------------------------------------------------------------------
    # Cálculo de contribuições (0-100)
    # -------------------------------------------------------------------------

    def _sleep_contribution(self, sleep: dict) -> float:
        """Sono: 7-9h = 100, <4h = 0. Score do dispositivo tem peso extra se disponível."""
        duration_h = (sleep.get("duration_minutes") or 0) / 60
        if duration_h <= 0:
            return 0.0

        # Curva baseada em duração
        if duration_h >= 9:
            duration_score = 100.0
        elif duration_h >= 7:
            duration_score = 100.0
        elif duration_h >= 6:
            duration_score = 75.0
        elif duration_h >= 5:
            duration_score = 50.0
        elif duration_h >= 4:
            duration_score = 25.0
        else:
            duration_score = 0.0

        device_score = sleep.get("sleep_score")
        if device_score is not None:
            return duration_score * 0.5 + float(device_score) * 0.5
        return duration_score

    def _hr_contribution(self, hr: dict) -> float:
        """FC de repouso: menor é melhor para população geral. <60 = 100, >90 = 10."""
        resting = hr.get("resting_bpm") or 0
        if resting <= 0:
            return 50.0  # sem dado, score neutro

        if resting <= 55:
            return 100.0
        elif resting <= 65:
            return 90.0
        elif resting <= 72:
            return 75.0
        elif resting <= 80:
            return 55.0
        elif resting <= 90:
            return 35.0
        else:
            return 15.0

    def _activity_contribution(self, activities: list[dict]) -> float:
        """
        Atividade do dia anterior influencia a recuperação.
        Sem atividade = 70 (neutro). Alta intensidade = corpo pode precisar de recuperação.
        """
        if not activities:
            return 70.0

        intensity_scores = {"low": 90.0, "moderate": 70.0, "high": 40.0}
        scores = [intensity_scores.get(a.get("intensity", "low"), 70.0) for a in activities]
        return sum(scores) / len(scores)

    def _stress_contribution(self, stress: dict | None) -> float | None:
        """Stress: 0-100 do dispositivo → inverte para contribuição (baixo stress = alta contribuição)."""
        if not stress or not stress.get("available"):
            return None
        score = stress.get("stress_score")
        if score is None:
            return None
        return 100.0 - float(score)

    def _to_category(self, score: float) -> str:
        for threshold, category in _CATEGORY_MAP:
            if score >= threshold:
                return category
        return "rest"
