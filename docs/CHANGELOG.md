# Changelog — Vytal

## [Unreleased] — 2026-04-19

### Adicionado

#### Módulo 1 — Readiness por Modalidade
- `ReadinessModalityService` — calcula score 0–100 por modalidade (8 modalidades: Crossfit, Corrida, Academia, Tênis, Pilates, Surfe, Yoga, Ciclismo)
- Algoritmo considera: base readiness score, fadiga muscular por treinos recentes (decay exponencial), penalidade por overtraining, flag de baixa confiança quando HRV indisponível
- Repositório `ModalityReadinessRepository` + tabela `fact_readiness_by_modality`
- Rota `GET /readiness/modalities/{user_id}?date=`
- Tela mobile `modalities.tsx` com cards por modalidade, badge de status (Verde/Amarelo/Vermelho) e recomendação textual

#### Módulo 2 — Recuperação Muscular e Body Map
- `MuscleRecoveryService` — score 0–100 por grupo muscular (13 grupos), com tempo de recuperação baseado em intensidade do treino e qualidade do sono
- `WorkoutService` — registro de treinos com seleção de exercícios ou texto livre, banco de 50+ exercícios com mapeamento muscular
- Repositórios: `WorkoutRepository`, `MuscleRecoveryRepository`
- Tabelas: `workout_history`, `workout_exercises`, `muscle_recovery`
- Rotas: `POST /workouts`, `GET /workouts/{user_id}`, `GET /workouts/exercises/catalog`, `GET /muscles/{user_id}/recovery`, `GET /muscles/{user_id}/suggestion`
- Componente `BodyMap` — SVG interativo com silhueta anterior/posterior, cores dinâmicas por score de recuperação, bottom sheet ao tocar no músculo
- Tela `workout-log.tsx` com registro de treino + body map integrado
- Novas tabs de navegação: "Modalidades" e "Treino"

### Técnico
- 4 novas tabelas no schema local (SQLite) e DDL preparado para BigQuery
- 30 novos testes unitários (100% passando, zero regressões na suite completa de 66 testes)
- `react-native-svg` adicionado como dependência do mobile
- `pytest-asyncio` adicionado às dependências de teste
- OpenAPI spec atualizada com novos endpoints e schemas
