"""
ReadinessModalityService — score diário 0–100 por modalidade de exercício.

Algoritmo:
  base_score     = Daily Readiness Score já calculado (sono + FC + atividade + stress)
  muscle_penalty = penalidade proporcional à fadiga dos músculos exigidos pela modalidade
  hrv_bonus      = até +5 pontos quando HRV está disponível e acima da média do usuário
  training_load_penalty = penalidade por overtraining (>5 treinos intensos em 7 dias)
  final_score    = clamp(base_score - muscle_penalty - training_load_penalty + hrv_bonus, 0, 100)
"""
import uuid
from datetime import date, datetime, timedelta, timezone

from app.repositories.readiness_repo import ReadinessRepository
from app.repositories.health_data_repo import HealthDataRepository
from app.repositories.workout_repo import WorkoutRepository
from app.repositories.modality_readiness_repo import ModalityReadinessRepository
from app.domain.sports.exercise_bank import muscles_for_modality, MUSCLE_GROUPS

MODALITIES = ["crossfit", "corrida", "academia", "tenis", "pilates", "surfe", "yoga", "ciclismo"]

_STATUS_MAP = [
    (70, "green"),
    (40, "yellow"),
    (0,  "red"),
]

_RECOMMENDATIONS = {
    "crossfit": {
        "green":  "Ótimo dia para Crossfit — seu corpo está recuperado para esforço total.",
        "yellow": "Crossfit moderado hoje. Evite PRs e reduza a intensidade nos WODs.",
        "red":    "Crossfit não recomendado hoje. Seu corpo precisa de mais recuperação.",
    },
    "corrida": {
        "green":  "Dia excelente para correr. Bom momento para treinos de velocidade ou longa distância.",
        "yellow": "Prefira uma corrida leve ou de recuperação hoje.",
        "red":    "Descanso ou caminhada suave. Suas pernas precisam se recuperar.",
    },
    "academia": {
        "green":  "Ótimo para treinar na academia. Foco em progressão de carga.",
        "yellow": "Treine, mas reduza o volume. Evite exercícios dos músculos mais fatigados.",
        "red":    "Musculação leve ou descanso ativo. Evite treinar músculos ainda em recuperação.",
    },
    "tenis": {
        "green":  "Dia perfeito para o tênis. Bom para treinos técnicos e de competição.",
        "yellow": "Tênis recreativo ok, mas evite partidas muito longas.",
        "red":    "Evite o tênis hoje. Pernas e ombros precisam recuperar.",
    },
    "pilates": {
        "green":  "Ótimo para Pilates. Corpo preparado para trabalhar core e mobilidade.",
        "yellow": "Pilates moderado está ótimo para hoje.",
        "red":    "Pilates suave ou alongamento. Bom dia para focar na respiração.",
    },
    "surfe": {
        "green":  "Dia excelente para surfar — ombros e core estão prontos para o esforço.",
        "yellow": "Surfe com moderação. Atenção ao desgaste dos ombros no paddle.",
        "red":    "Descanso recomendado. Ombros e core precisam recuperar para um bom desempenho.",
    },
    "yoga": {
        "green":  "Ótimo dia para yoga. Considere práticas mais desafiadoras como Ashtanga.",
        "yellow": "Yoga moderado ou Yin Yoga são ideais hoje.",
        "red":    "Yoga restaurativo ou meditação. Respeite os limites do seu corpo hoje.",
    },
    "ciclismo": {
        "green":  "Ótimo para ciclismo. Bom dia para treinos de resistência ou subidas.",
        "yellow": "Ride moderado ok. Evite sprints e subidas muito pesadas.",
        "red":    "Ciclismo muito leve ou descanso. Quadríceps e flexores precisam recuperar.",
    },
}

# Peso de cada grupo muscular por modalidade (0–1)
# Quanto maior, maior a penalidade se o músculo estiver fatigado
_MODALITY_MUSCLE_WEIGHTS: dict[str, dict[str, float]] = {
    "crossfit":  {"quads": 0.20, "glutes": 0.15, "upper_back": 0.15, "chest": 0.15,
                  "core": 0.15, "front_shoulders": 0.10, "lower_back": 0.10},
    "corrida":   {"quads": 0.30, "hamstrings": 0.25, "calves": 0.25, "hip_flexors": 0.20},
    "academia":  {},  # calculado dinamicamente a partir dos treinos recentes
    "tenis":     {"quads": 0.30, "calves": 0.25, "front_shoulders": 0.25, "core": 0.20},
    "pilates":   {"core": 0.40, "lower_back": 0.30, "hip_flexors": 0.30},
    "surfe":     {"upper_back": 0.30, "front_shoulders": 0.30, "core": 0.25, "quads": 0.15},
    "yoga":      {"core": 0.35, "lower_back": 0.35, "hip_flexors": 0.30},
    "ciclismo":  {"quads": 0.35, "hip_flexors": 0.30, "hamstrings": 0.20, "calves": 0.15},
}


class ReadinessModalityService:
    def __init__(self):
        self.readiness_repo = ReadinessRepository()
        self.health_repo = HealthDataRepository()
        self.workout_repo = WorkoutRepository()
        self.modality_repo = ModalityReadinessRepository()

    async def calculate_all(self, user_id: str, date_str: str) -> list[dict]:
        """Calcula e persiste readiness para todas as modalidades."""
        base = await self.readiness_repo.get(user_id, date_str)
        base_score = float(base["readiness_score"]) if base else 50.0

        hr_rows = await self.health_repo.get_normalized(user_id, date_str, "heart_rate")
        hrv_available = False  # Google Fit raramente reporta HRV diretamente

        recent_workouts = await self.workout_repo.get_recent_workouts(user_id, days=7)
        muscle_fatigue = self._compute_muscle_fatigue(recent_workouts, date_str)
        training_load_penalty = self._training_load_penalty(recent_workouts)

        records: list[dict] = []
        for modality in MODALITIES:
            score, low_conf = self._modality_score(
                modality, base_score, muscle_fatigue,
                training_load_penalty, hrv_available,
            )
            status = self._to_status(score)
            records.append({
                "record_id":    str(uuid.uuid4()),
                "user_id":      user_id,
                "date":         date_str,
                "modality":     modality,
                "score":        score,
                "status":       status,
                "recommendation": _RECOMMENDATIONS[modality][status],
                "hrv_available":  int(hrv_available),
                "low_confidence": int(low_conf),
                "calculated_at":  datetime.now(timezone.utc).isoformat(),
            })

        await self.modality_repo.save_batch(records)
        return records

    async def get(self, user_id: str, date_str: str, filter_modalities: list[str] | None = None) -> list[dict]:
        existing = await self.modality_repo.get_by_date(user_id, date_str)
        if not existing:
            existing = await self.calculate_all(user_id, date_str)
        if filter_modalities:
            existing = [r for r in existing if r["modality"] in filter_modalities]
        return existing

    # -------------------------------------------------------------------------

    def _compute_muscle_fatigue(self, workouts: list[dict], target_date: str) -> dict[str, float]:
        """
        Retorna fatigue score 0–1 por grupo muscular, baseado nos treinos recentes.
        Quanto mais recente e mais intenso o treino, maior a fadiga.
        """
        fatigue: dict[str, float] = {m: 0.0 for m in MUSCLE_GROUPS}
        target = date.fromisoformat(target_date)

        intensity_multiplier = {"leve": 0.4, "moderado": 0.7, "intenso": 1.0}

        for w in workouts:
            try:
                workout_date = date.fromisoformat(w["date"])
            except (ValueError, KeyError):
                continue

            days_ago = (target - workout_date).days
            if days_ago <= 0:
                continue

            # Decaimento exponencial: 24h intenso = 1.0, 72h intenso = ~0.15
            decay = max(0.0, 1.0 - (days_ago * 0.33))
            intensity = intensity_multiplier.get(w.get("intensity", "moderado"), 0.7)
            modality = w.get("modality", "academia")
            weights = _MODALITY_MUSCLE_WEIGHTS.get(modality, {})

            for muscle, weight in weights.items():
                contribution = weight * intensity * decay
                fatigue[muscle] = min(1.0, fatigue[muscle] + contribution)

        return fatigue

    def _modality_score(
        self,
        modality: str,
        base_score: float,
        muscle_fatigue: dict[str, float],
        training_load_penalty: float,
        hrv_available: bool,
    ) -> tuple[float, bool]:
        weights = _MODALITY_MUSCLE_WEIGHTS.get(modality, {})
        if not weights:
            # academia sem treinos recentes: usa base_score diretamente
            return round(max(0.0, min(100.0, base_score - training_load_penalty)), 1), False

        # Penalidade muscular ponderada
        muscle_penalty = sum(
            fatigue * weight * 30.0  # até -30 pontos por músculo 100% fatigado
            for muscle, weight in weights.items()
            if (fatigue := muscle_fatigue.get(muscle, 0.0)) > 0
        )

        hrv_bonus = 3.0 if hrv_available else 0.0
        low_confidence = not hrv_available

        score = base_score - muscle_penalty - training_load_penalty + hrv_bonus
        return round(max(0.0, min(100.0, score)), 1), low_confidence

    def _training_load_penalty(self, workouts: list[dict]) -> float:
        """Penalidade por overtraining: >5 treinos em 7 dias ou >3 intensos."""
        if len(workouts) > 5:
            return 10.0
        intense = sum(1 for w in workouts if w.get("intensity") == "intenso")
        if intense >= 4:
            return 15.0
        if intense == 3:
            return 5.0
        return 0.0

    def _to_status(self, score: float) -> str:
        for threshold, status in _STATUS_MAP:
            if score >= threshold:
                return status
        return "red"
