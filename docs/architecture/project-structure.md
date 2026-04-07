# Estrutura de Pastas — Vytal

**Status**: Aguardando aprovação do Tech Lead  
**Agente**: Architect  
**Versão**: 0.1

---

## Visão Geral dos Repositórios

```
Documents/
├── cloude-agents/          ← time de agentes genérico (separado)
└── Vytal/                  ← código do produto
    ├── CLAUDE.md
    ├── docs/               ← documentação (PRD, ADRs, specs)
    ├── mobile/             ← React Native app
    ├── backend/            ← FastAPI (API Gateway + Services)
    ├── pipelines/          ← Apache Beam pipelines
    ├── infrastructure/     ← Terraform + Docker
    └── config/             ← configurações por ambiente
```

---

## Estrutura Detalhada

### `mobile/` — React Native (Expo)
```
mobile/
├── app/
│   ├── (tabs)/
│   │   ├── index.tsx           ← tela principal (Daily Readiness)
│   │   └── data.tsx            ← visualização de dados coletados
│   └── connect.tsx             ← tela de conexão com Google Fit
├── components/
│   ├── ui/                     ← botões, cards, textos (atômicos)
│   └── features/
│       ├── ReadinessScore.tsx  ← componente do score
│       └── HealthDataCard.tsx  ← card de dado de saúde
├── hooks/
│   ├── useReadiness.ts         ← query do Daily Readiness
│   └── useHealthData.ts        ← query dos dados coletados
├── services/
│   └── api.ts                  ← configuração do axios + interceptors
├── store/
│   └── authStore.ts            ← estado de autenticação
└── types/
    └── health.ts               ← tipos TypeScript compartilhados
```

### `backend/` — FastAPI
```
backend/
├── app/
│   ├── main.py                 ← entry point FastAPI
│   ├── api/
│   │   └── v1/
│   │       ├── router.py       ← agrega todas as rotas
│   │       ├── health_data.py  ← endpoints de ingestão
│   │       ├── readiness.py    ← endpoints de indicadores
│   │       └── connect.py      ← endpoints OAuth (Google Fit)
│   ├── services/
│   │   ├── health_data_service.py
│   │   └── readiness_service.py
│   ├── repositories/
│   │   ├── health_data_repo.py
│   │   └── readiness_repo.py
│   ├── models/
│   │   ├── health_data.py      ← Pydantic schemas (request/response)
│   │   └── readiness.py
│   ├── adapters/
│   │   ├── connectors/
│   │   │   ├── base.py         ← interface HealthDataProvider (ABC)
│   │   │   └── google_fit.py   ← GoogleFitAdapter
│   │   └── cloud/
│   │       ├── base.py         ← interfaces cloud (ABC)
│   │       ├── gcp.py          ← GCP adapters
│   │       └── local.py        ← Local adapters (dev)
│   ├── domain/
│   │   └── health_metrics/
│   │       ├── base.py         ← interface HealthMetric (ABC)
│   │       ├── sleep.py        ← SleepMetric
│   │       ├── steps.py        ← StepsMetric
│   │       ├── activity.py     ← ActivityMetric
│   │       ├── heart_rate.py   ← HeartRateMetric
│   │       └── stress.py       ← StressMetric
│   └── config/
│       ├── settings.py         ← pydantic-settings
│       └── cloud_config.py     ← carrega config.yaml
├── tests/
│   ├── unit/
│   └── integration/
├── config.yaml                 ← provider: local | gcp
├── .env.example
└── requirements.txt
```

### `pipelines/` — Apache Beam
```
pipelines/
├── pipeline_googlefit_raw_ingest.py      ← Google Fit → raw/
├── pipeline_raw_normalized_health.py     ← raw/ → normalized/
├── pipeline_normalized_readiness_score.py ← normalized/ → star schema
├── transforms/
│   ├── sanitize.py             ← limpeza e validação
│   ├── normalize.py            ← conversão para linguagem de negócio
│   └── readiness.py            ← cálculo do Daily Readiness Score
├── schemas/
│   ├── raw/                    ← schemas BigQuery camada raw
│   ├── normalized/             ← schemas BigQuery camada normalized
│   └── star/                   ← schemas BigQuery star schema
└── tests/
    └── unit/                   ← testes com DirectRunner
```

### `backend/` — Docker (ambiente local)
```
backend/
├── Dockerfile                  ← imagem Python 3.12-slim (prod)
├── docker-compose.yml          ← sobe o backend + volume SQLite
├── .dockerignore
├── requirements.txt            ← todas as dependências (dev + prod)
└── requirements-prod.txt       ← somente dependências de produção
```

**Uso:**
```bash
cd backend
docker compose up -d            # sobe na porta 8001
docker compose logs -f          # acompanha logs
docker compose down             # para
```

O volume `./data:/app/data` persiste o SQLite entre restarts.

### `infrastructure/` — Terraform (GCP)
```
infrastructure/
└── terraform/
    ├── modules/
    │   └── gcp/
    │       ├── cloud_run.tf    ← backend containerizado
    │       ├── storage.tf      ← Cloud Storage (raw data)
    │       ├── bigquery.tf     ← warehouse
    │       └── pubsub.tf       ← streaming de eventos
    └── environments/
        └── gcp/
            ├── main.tf
            ├── variables.tf
            └── terraform.tfvars.example
```

### `config/` — Configurações por Ambiente
```
config/
├── local.yaml                  ← provider: local, DirectRunner
└── gcp.yaml                    ← provider: gcp, DataflowRunner
```

---

## ADR-001: Separação mobile / backend / pipelines

**Status**: Aceito  
**Contexto**: O projeto tem três domínios técnicos distintos — mobile, backend e data pipelines — com ciclos de deploy e responsabilidades diferentes.  
**Decisão**: Repositório monorepo com pastas separadas por domínio. Cada domínio tem seu próprio Dockerfile, requirements e testes.  
**Consequências**: Facilita trabalho paralelo entre agentes; requer convenção clara de versionamento entre as partes.

## ADR-002: config.yaml como único ponto de configuração de ambiente

**Status**: Aceito  
**Contexto**: O MVP precisa rodar localmente (desenvolvimento) e na GCP (produção), sem alterar código.  
**Decisão**: `config.yaml` define o provider ativo. O código nunca importa SDKs cloud diretamente — apenas via adapters carregados pela factory com base no config.  
**Consequências**: Adicionar novo provider = criar adapter + entrada no config. Zero impacto no código de aplicação.
