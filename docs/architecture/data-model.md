# Modelo de Dados — Vytal

**Status**: Aguardando aprovação do Tech Lead  
**Agente**: Architect  
**Versão**: 0.1

---

## Camadas de Dados

```
Google Fit (raw SDK data)
        │
        ▼
   [ raw/ ]           ← dados brutos, imutáveis, como vieram do provider
        │
        ▼
[ normalized/ ]       ← dados limpos, tipados, em linguagem de negócio
        │
        ▼
  [ star/ ]           ← modelagem estrela para indicadores por usuário/data
```

---

## Camada `raw/`

Dados exatamente como chegam do Google Fit. Imutáveis. Nunca modificar.

### `raw_health_events`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `event_id` | STRING | UUID gerado na ingestão |
| `user_id` | STRING | ID do usuário |
| `provider` | STRING | ex: "google_fit" |
| `metric_type` | STRING | ex: "sleep", "steps", "heart_rate" |
| `raw_payload` | JSON | payload original do provider, sem alteração |
| `collected_at` | TIMESTAMP | quando o dado foi gerado no dispositivo |
| `ingested_at` | TIMESTAMP | quando chegou no sistema |
| `pipeline_run` | STRING | ID do pipeline que ingeriu |

---

## Camada `normalized/`

Dados transformados para linguagem de negócio. Um schema por tipo de métrica.

### `normalized_sleep`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `record_id` | STRING | UUID |
| `user_id` | STRING | |
| `date` | DATE | data do sono (dia de início) |
| `duration_minutes` | INTEGER | duração total em minutos |
| `deep_sleep_minutes` | INTEGER | sono profundo |
| `light_sleep_minutes` | INTEGER | sono leve |
| `rem_sleep_minutes` | INTEGER | sono REM |
| `awake_minutes` | INTEGER | tempo acordado durante a noite |
| `sleep_score` | FLOAT | score de qualidade 0-100 (quando disponível) |
| `source_event_id` | STRING | FK para `raw_health_events` |
| `normalized_at` | TIMESTAMP | |

### `normalized_steps`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `record_id` | STRING | |
| `user_id` | STRING | |
| `date` | DATE | |
| `total_steps` | INTEGER | total de passos no dia |
| `hourly_steps` | JSON | array com passos por hora `[{"hour": 8, "steps": 342}, ...]` |
| `source_event_id` | STRING | |
| `normalized_at` | TIMESTAMP | |

### `normalized_activity`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `record_id` | STRING | |
| `user_id` | STRING | |
| `date` | DATE | |
| `activity_type` | STRING | ex: "running", "walking", "cycling" |
| `duration_minutes` | INTEGER | |
| `intensity` | STRING | "low" \| "moderate" \| "high" |
| `calories_burned` | FLOAT | |
| `source_event_id` | STRING | |
| `normalized_at` | TIMESTAMP | |

### `normalized_heart_rate`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `record_id` | STRING | |
| `user_id` | STRING | |
| `date` | DATE | |
| `resting_bpm` | FLOAT | frequência cardíaca de repouso |
| `average_bpm` | FLOAT | média do dia |
| `max_bpm` | FLOAT | máximo do dia |
| `min_bpm` | FLOAT | mínimo do dia |
| `source_event_id` | STRING | |
| `normalized_at` | TIMESTAMP | |

### `normalized_stress`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `record_id` | STRING | |
| `user_id` | STRING | |
| `date` | DATE | |
| `stress_score` | FLOAT | score 0-100 (0 = sem estresse) |
| `available` | BOOLEAN | false quando o dispositivo não fornece |
| `source_event_id` | STRING | |
| `normalized_at` | TIMESTAMP | |

---

## Camada `star/` — Modelagem Estrela

### Tabela Fato: `fact_daily_readiness`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `readiness_id` | STRING | SK (surrogate key) |
| `user_id` | STRING | FK → `dim_user` |
| `date_id` | STRING | FK → `dim_date` |
| `readiness_score` | FLOAT | 0–100 |
| `readiness_category` | STRING | "rest" \| "light" \| "moderate" \| "intense" |
| `sleep_score_contribution` | FLOAT | contribuição do sono (0-100) |
| `hr_score_contribution` | FLOAT | contribuição da FC (0-100) |
| `activity_score_contribution` | FLOAT | contribuição da atividade prévia (0-100) |
| `stress_score_contribution` | FLOAT | contribuição do estresse (0-100, null se indisponível) |
| `insight_text` | STRING | recomendação gerada |
| `calculated_at` | TIMESTAMP | |

### Dimensão: `dim_user`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `user_id` | STRING | PK |
| `created_at` | TIMESTAMP | |
| `provider` | STRING | "google_fit" |

### Dimensão: `dim_date`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `date_id` | STRING | PK (formato YYYY-MM-DD) |
| `date` | DATE | |
| `day_of_week` | INTEGER | 0=Seg, 6=Dom |
| `day_name` | STRING | "Monday" |
| `week_of_year` | INTEGER | |
| `month` | INTEGER | |
| `year` | INTEGER | |
| `is_weekend` | BOOLEAN | |

---

## Lógica do Daily Readiness Score

Score calculado como média ponderada das contribuições:

```
readiness_score = (
    sleep_contribution    * 0.40 +   # sono tem maior peso
    hr_contribution       * 0.30 +   # FC de repouso elevada = sinal de fadiga
    activity_contribution * 0.20 +   # carga de treino recente
    stress_contribution   * 0.10     # estresse (peso menor, nem sempre disponível)
)
```

Quando `stress_contribution` não está disponível, o peso é redistribuído proporcionalmente entre os demais.

### Mapeamento para Categoria
| Score | Categoria | `readiness_category` |
|-------|-----------|----------------------|
| 80–100 | Treino intenso | `intense` |
| 50–79 | Cardio leve ou treino de força moderado | `moderate` |
| 30–49 | Cardio leve | `light` |
| 0–29 | Descanso | `rest` |

---

## Particionamento e Performance

- Todas as tabelas particionadas por `date` (BigQuery partition pruning)
- `fact_daily_readiness` clusterizada por `user_id`
- Queries de leitura sempre filtram por `user_id` + `date` para evitar full scans
