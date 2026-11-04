"""
Advanced metrics service: Social Jetlag, Personal Recovery Curve, Signal Quality.
"""
from datetime import date, timedelta

from app.repositories.health_data_repo import HealthDataRepository
from app.repositories.readiness_repo import ReadinessRepository


def _social_jetlag_interpretation(hours: float) -> str:
    if hours < 0.5:
        return f"Mínimo — diferença de {hours:.1f}h entre sono da semana e fim de semana"
    if hours < 1.0:
        return f"Leve — diferença de {hours:.1f}h entre sono da semana e fim de semana"
    if hours <= 2.0:
        return f"Moderado — diferença de {hours:.1f}h entre sono da semana e fim de semana"
    return f"Alto — pode afetar seu ritmo circadiano (diferença de {hours:.1f}h)"


class AdvancedMetricsService:
    def __init__(self):
        self.health_repo = HealthDataRepository()
        self.readiness_repo = ReadinessRepository()

    async def calculate(self, user_id: str, target_date: str) -> dict:
        social_jetlag = await self._social_jetlag(user_id, target_date)
        recovery_curve = await self._recovery_curve(user_id, target_date)
        signal_quality = await self._signal_quality(user_id, target_date)

        return {
            "user_id": user_id,
            "date": target_date,
            "social_jetlag": social_jetlag,
            "recovery_curve": recovery_curve,
            "signal_quality": signal_quality,
        }

    # -------------------------------------------------------------------------
    # Social Jetlag
    # -------------------------------------------------------------------------

    async def _social_jetlag(self, user_id: str, target_date: str) -> dict:
        """
        Computes social jetlag using the last 14 days of sleep data.
        Midpoint proxy: midnight minus half the sleep duration.
        """
        end = date.fromisoformat(target_date)
        start = end - timedelta(days=13)

        weekday_midpoints: list[float] = []  # minutes from midnight
        weekend_midpoints: list[float] = []

        current = start
        while current <= end:
            date_str = current.isoformat()
            rows = await self.health_repo.get_normalized(user_id, date_str, "sleep")
            if rows:
                sleep = rows[0]
                duration = sleep.get("duration_minutes") or 0
                if duration > 0:
                    # Midpoint proxy: midnight - (duration / 2) expressed as minutes-from-midnight
                    # Negative means before midnight, but for comparison purposes the absolute
                    # value and relative differences are what matter.
                    midpoint = -(duration / 2.0)
                    if current.weekday() < 5:
                        weekday_midpoints.append(midpoint)
                    else:
                        weekend_midpoints.append(midpoint)
            current += timedelta(days=1)

        if len(weekday_midpoints) < 3 or len(weekend_midpoints) < 1:
            return {
                "score": None,
                "interpretation": "Dados insuficientes para calcular o jetlag social",
                "available": False,
            }

        avg_weekday = sum(weekday_midpoints) / len(weekday_midpoints)
        avg_weekend = sum(weekend_midpoints) / len(weekend_midpoints)
        jetlag_minutes = abs(avg_weekend - avg_weekday)
        jetlag_hours = round(jetlag_minutes / 60.0, 2)

        return {
            "score": jetlag_hours,
            "interpretation": _social_jetlag_interpretation(jetlag_hours),
            "available": True,
        }

    # -------------------------------------------------------------------------
    # Personal Recovery Curve
    # -------------------------------------------------------------------------

    async def _recovery_curve(self, user_id: str, target_date: str) -> dict:
        """
        Finds bad nights (readiness < 45) in the last 30 days and measures
        how many days until readiness returns to >= 60.
        """
        end = date.fromisoformat(target_date)
        start = end - timedelta(days=29)
        start_str = start.isoformat()
        end_str = end.isoformat()

        history = await self.readiness_repo.get_history(user_id, start_str, end_str)
        # get_history returns DESC order; build a date→score map
        score_by_date: dict[str, float] = {
            row["date"]: float(row["readiness_score"]) for row in history
        }

        recovery_windows: list[int] = []
        dates_asc = sorted(score_by_date.keys())

        for i, d in enumerate(dates_asc):
            if score_by_date[d] < 45:
                # Count days until recovery
                days_to_recover = None
                for j in range(1, 8):  # cap at 7
                    future_date = (date.fromisoformat(d) + timedelta(days=j)).isoformat()
                    if future_date in score_by_date and score_by_date[future_date] >= 60:
                        days_to_recover = j
                        break
                if days_to_recover is not None:
                    recovery_windows.append(days_to_recover)

        if len(recovery_windows) < 3:
            return {
                "avg_recovery_days": None,
                "interpretation": "Dados insuficientes — continue usando o app para calibrar",
                "available": False,
            }

        avg_days = round(sum(recovery_windows) / len(recovery_windows))
        return {
            "avg_recovery_days": avg_days,
            "interpretation": f"Você leva em média {avg_days} dias para se recuperar de uma noite ruim",
            "available": True,
        }

    # -------------------------------------------------------------------------
    # Budget Watch Signal Quality
    # -------------------------------------------------------------------------

    async def _signal_quality(self, user_id: str, target_date: str) -> dict:
        """
        Assesses the quality of health data signals for the day.
        """
        issues: list[str] = []

        # Fetch all raw events for the day across all metric types
        all_raw: list[dict] = []
        for metric_type in ["sleep", "heart_rate", "steps", "activity", "stress"]:
            rows = await self.health_repo.get_raw_events(
                user_id, metric_type, target_date, target_date
            )
            all_raw.extend(rows)

        if len(all_raw) == 0:
            score = 20
            flag = "incomplete"
            issues.append("Nenhum dado recebido do dispositivo")
            return {
                "score": score,
                "flag": flag,
                "interpretation": "Dados insuficientes para análise precisa",
                "issues": issues,
            }

        # Fetch normalized data for quality checks
        sleep_rows = await self.health_repo.get_normalized(user_id, target_date, "sleep")
        hr_rows = await self.health_repo.get_normalized(user_id, target_date, "heart_rate")
        steps_rows = await self.health_repo.get_normalized(user_id, target_date, "steps")
        activity_rows = await self.health_repo.get_normalized(user_id, target_date, "activity")

        # Check sleep phase detection
        if sleep_rows:
            sleep = sleep_rows[0]
            duration = sleep.get("duration_minutes") or 0
            deep = sleep.get("deep_sleep_minutes") or 0
            light = sleep.get("light_sleep_minutes") or 0
            rem = sleep.get("rem_sleep_minutes") or 0
            if duration > 0 and (deep + light + rem) == 0:
                issues.append("Fases do sono não detectadas")

        # Check heart rate variance
        if hr_rows:
            hr = hr_rows[0]
            max_bpm = hr.get("max_bpm")
            min_bpm = hr.get("min_bpm")
            if max_bpm is not None and min_bpm is not None:
                if (max_bpm - min_bpm) < 10:
                    issues.append("Sinal de FC com variação suspeita")

        # Check steps vs activity
        if steps_rows:
            steps = steps_rows[0]
            total_steps = steps.get("total_steps") or 0
            if total_steps > 5000 and not activity_rows:
                issues.append("Atividade física não registrada")

        score = max(0, min(100, 100 - len(issues) * 20))

        if score >= 80:
            flag = "reliable"
            interpretation = "Dados do dia com boa qualidade"
        elif score >= 50:
            flag = "caution"
            interpretation = "Dados parciais — use com cautela"
        else:
            flag = "incomplete"
            interpretation = "Dados insuficientes para análise precisa"

        return {
            "score": score,
            "flag": flag,
            "interpretation": interpretation,
            "issues": issues,
        }
