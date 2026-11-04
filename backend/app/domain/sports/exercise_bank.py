"""
Banco de exercícios com mapeamento para grupos musculares.
Cada exercício lista os músculos primários e secundários ativados.
"""
from typing import NamedTuple


class Exercise(NamedTuple):
    name: str
    primary: list[str]
    secondary: list[str]


# Grupos musculares canônicos usados no BodyMap
MUSCLE_GROUPS = [
    "chest",
    "front_shoulders",
    "rear_shoulders",
    "biceps",
    "triceps",
    "upper_back",
    "lower_back",
    "core",
    "glutes",
    "quads",
    "hamstrings",
    "calves",
    "hip_flexors",
]

EXERCISE_BANK: list[Exercise] = [
    # Peito
    Exercise("Supino reto",          ["chest"],        ["front_shoulders", "triceps"]),
    Exercise("Supino inclinado",      ["chest"],        ["front_shoulders", "triceps"]),
    Exercise("Crucifixo",             ["chest"],        ["front_shoulders"]),
    Exercise("Flexão de braço",       ["chest"],        ["triceps", "front_shoulders"]),
    Exercise("Paralelas",             ["chest"],        ["triceps", "front_shoulders"]),
    # Costas
    Exercise("Barra fixa",            ["upper_back"],   ["biceps", "rear_shoulders"]),
    Exercise("Remada curvada",        ["upper_back"],   ["biceps", "lower_back"]),
    Exercise("Puxada frontal",        ["upper_back"],   ["biceps"]),
    Exercise("Remada unilateral",     ["upper_back"],   ["biceps", "lower_back"]),
    Exercise("Levantamento terra",    ["lower_back", "glutes"], ["hamstrings", "upper_back"]),
    # Ombros
    Exercise("Desenvolvimento",       ["front_shoulders", "rear_shoulders"], ["triceps"]),
    Exercise("Elevação lateral",      ["front_shoulders"], []),
    Exercise("Elevação posterior",    ["rear_shoulders"], []),
    Exercise("Arnold press",          ["front_shoulders", "rear_shoulders"], ["triceps"]),
    # Bíceps
    Exercise("Rosca direta",          ["biceps"],       []),
    Exercise("Rosca martelo",         ["biceps"],       []),
    Exercise("Rosca concentrada",     ["biceps"],       []),
    # Tríceps
    Exercise("Tríceps testa",         ["triceps"],      []),
    Exercise("Tríceps corda",         ["triceps"],      []),
    Exercise("Tríceps francês",       ["triceps"],      []),
    # Core
    Exercise("Abdominal",             ["core"],         []),
    Exercise("Prancha",               ["core"],         ["lower_back"]),
    Exercise("Abdominal oblíquo",     ["core"],         []),
    Exercise("Dead bug",              ["core"],         ["hip_flexors"]),
    # Pernas
    Exercise("Agachamento",           ["quads", "glutes"], ["hamstrings", "lower_back"]),
    Exercise("Leg press",             ["quads", "glutes"], ["hamstrings"]),
    Exercise("Afundo",                ["quads", "glutes"], ["hamstrings"]),
    Exercise("Cadeira extensora",     ["quads"],        []),
    Exercise("Mesa flexora",          ["hamstrings"],   []),
    Exercise("Stiff",                 ["hamstrings"],   ["glutes", "lower_back"]),
    Exercise("Glúteo no cabo",        ["glutes"],       ["hamstrings"]),
    Exercise("Panturrilha em pé",     ["calves"],       []),
    Exercise("Panturrilha sentado",   ["calves"],       []),
    # Crossfit / funcionais
    Exercise("Burpee",                ["chest", "quads"], ["core", "front_shoulders"]),
    Exercise("Thruster",              ["quads", "front_shoulders"], ["core", "glutes"]),
    Exercise("Box jump",              ["quads", "glutes"], ["calves", "hamstrings"]),
    Exercise("Kettlebell swing",      ["glutes", "hamstrings"], ["lower_back", "core"]),
    Exercise("Clean and jerk",        ["quads", "glutes", "front_shoulders"], ["lower_back", "core"]),
    Exercise("Snatch",                ["quads", "glutes", "front_shoulders"], ["lower_back", "upper_back"]),
    Exercise("Pull-up",               ["upper_back"],   ["biceps"]),
    Exercise("Push-up",               ["chest"],        ["triceps", "front_shoulders"]),
    Exercise("Double under",          ["calves"],       ["quads"]),
    Exercise("Wall ball",             ["quads", "front_shoulders"], ["core", "glutes"]),
    Exercise("Row (remo)",            ["upper_back"],   ["biceps", "lower_back"]),
    Exercise("Rope climb",            ["biceps", "upper_back"], ["core"]),
    # Corrida / cardio
    Exercise("Corrida",               ["quads", "hamstrings", "calves"], ["glutes", "hip_flexors"]),
    Exercise("Ciclismo",              ["quads", "hip_flexors"], ["hamstrings", "calves", "glutes"]),
    Exercise("Surfe (paddling)",      ["upper_back", "front_shoulders"], ["core", "triceps"]),
    Exercise("Tênis",                 ["quads", "calves"], ["front_shoulders", "core"]),
]

# Índice nome → Exercise para lookup rápido
EXERCISE_BY_NAME: dict[str, Exercise] = {e.name.lower(): e for e in EXERCISE_BANK}


def muscles_for_modality(modality: str) -> list[str]:
    """Retorna os grupos musculares primários usados por cada modalidade."""
    _map = {
        "crossfit":  ["quads", "glutes", "upper_back", "chest", "core", "front_shoulders"],
        "corrida":   ["quads", "hamstrings", "calves", "hip_flexors"],
        "academia":  [],  # depende dos exercícios do dia
        "tenis":     ["quads", "calves", "front_shoulders", "core"],
        "pilates":   ["core", "lower_back", "hip_flexors"],
        "surfe":     ["upper_back", "front_shoulders", "core", "quads"],
        "yoga":      ["core", "lower_back", "hip_flexors"],
        "ciclismo":  ["quads", "hip_flexors", "hamstrings", "calves"],
    }
    return _map.get(modality.lower(), [])


def parse_free_text_muscles(text: str) -> list[str]:
    """
    Tenta mapear texto livre para grupos musculares.
    Fallback simples — em produção seria chamada Claude API.
    """
    text_lower = text.lower()
    found: list[str] = []
    keywords = {
        "peit":      "chest",
        "chest":     "chest",
        "ombro":     "front_shoulders",
        "shoulder":  "front_shoulders",
        "bícep":     "biceps",
        "bicep":     "biceps",
        "trícep":    "triceps",
        "tricep":    "triceps",
        "costas":    "upper_back",
        "back":      "upper_back",
        "lombar":    "lower_back",
        "abdôm":     "core",
        "abdom":     "core",
        "core":      "core",
        "glúteo":    "glutes",
        "glute":     "glutes",
        "quad":      "quads",
        "perna":     "quads",
        "posterior": "hamstrings",
        "hamst":     "hamstrings",
        "panturr":   "calves",
        "calf":      "calves",
        "calves":    "calves",
        "flexor":    "hip_flexors",
    }
    for kw, muscle in keywords.items():
        if kw in text_lower and muscle not in found:
            found.append(muscle)
    return found
