# CLAUDE.md — Vytal

## Sobre o Projeto
Vytal é um app mobile de análise de dados de saúde voltado para usuários de smartwatches populares (não Garmin). Coleta dados brutos de sono, atividades, batimentos e descanso via Google Fit / Apple HealthKit e outros providers, e gera relatórios e indicadores personalizados.

**Público-alvo**: pessoas com smartwatches acessíveis que querem insights de saúde sem pagar por plataformas premium.

---

## Time de Agentes

Este projeto usa o time genérico de agentes em `../cloude-agents/`.

Cada agente deve ler sua skill antes de iniciar qualquer tarefa:

| Agente | Skill |
|--------|-------|
| PM | `../cloude-agents/skills/pm/SKILL.md` |
| Architect | `../cloude-agents/skills/architect/SKILL.md` |
| Backend | `../cloude-agents/skills/backend/SKILL.md` |
| Frontend | `../cloude-agents/skills/frontend/SKILL.md` |
| Integrations | `../cloude-agents/skills/integrations/SKILL.md` |
| Data Engineer | `../cloude-agents/skills/data-engineer/SKILL.md` |
| QA | `../cloude-agents/skills/qa/SKILL.md` |
| DevOps | `../cloude-agents/skills/devops/SKILL.md` |
| Cloud | `../cloude-agents/skills/cloud/SKILL.md` |
| Docs | `../cloude-agents/skills/docs/SKILL.md` |

---

## Stack Definida

| Camada | Tecnologia |
|--------|------------|
| Mobile | React Native (Expo) |
| API Gateway | FastAPI (Python 3.11+) |
| Auth | JWT |
| Cloud (padrão) | GCP |
| Storage | Cloud Storage |
| Warehouse | BigQuery |
| Streaming | Pub/Sub |
| Pipelines | Apache Beam → Dataflow |
| IaC | Terraform |
| CI/CD | GitHub Actions |

---

## Arquitetura de Alto Nível

```
Mobile App (React Native)
       │
       ▼
API Gateway (FastAPI)
       │
       ├── Ingest Service     ← recebe dados do celular
       ├── Process Service    ← pipelines Beam
       └── Reports Service    ← indicadores + AI insights
       │
       ▼
Health Data Connector Hub     ← adapters por provider de saúde
       │
       ▼
Cloud Abstraction Layer       ← adapters por provedor cloud
       │
       ▼
GCP (Storage → BigQuery, Pub/Sub, Dataflow)
```

---

## Regras Específicas do Vytal

### Dados de Saúde
- Dados de saúde são sensíveis — nunca logar valores brutos em produção
- Sempre associar dados ao `user_id` — nunca armazenar sem identificação
- Dados do usuário nunca são compartilhados entre contas
- LGPD/GDPR: usuário pode exportar e deletar todos os seus dados

### Health Data Connector Hub
- Todo novo provider de smartwatch **deve** implementar a interface `HealthDataProvider`
- Nunca chamar SDKs de saúde (Google Fit, Apple Health, etc.) fora de um Adapter
- Dados brutos do provider são mapeados para modelos internos antes de qualquer processamento

### Cloud Abstraction Layer
- Nunca importar SDKs cloud (`google.cloud`, `boto3`, etc.) fora dos Cloud Adapters
- O provider é definido em `config.yaml` — nunca hardcoded no código
- Provider padrão: GCP

### Pipelines de Dados
- Seguir nomenclatura: `pipeline_{source}_{destination}_{type}.py`
- Camada `raw/` é imutável — nunca modificar dados já ingeridos
- Todo pipeline precisa de dead letter queue

### Mobile
- Um único codebase React Native para iOS e Android
- Dados de saúde são coletados via SDK no celular e enviados à API — nunca lidos diretamente do smartwatch pelo app

---

## Fluxo de Trabalho do Time

```
Tech Lead define tarefa
       │
       ▼
PM Agent → PRD + Histórias (aguarda aprovação)
       │
       ▼
Architect Agent → OpenAPI spec + modelo de dados (aguarda aprovação)
       │
       ├── Backend Agent  ←──────────────────────┐
       ├── Frontend Agent  (paralelo)             │
       ├── Integrations Agent (paralelo)          │
       └── Data Engineer Agent (paralelo)         │
                │                                 │
                ▼                                 │
          QA Agent valida                         │
                │                                 │
          falhou? ──────────────────────────────►─┘
                │
          passou?
                │
                ▼
          Docs Agent atualiza documentação
                │
                ▼
          DevOps Agent faz deploy
```

---

## Contexto de Negócio

- Não é concorrente do Garmin — é um produto para quem **não pode** pagar pelo Garmin
- Foco em acessibilidade: funcionar mesmo com dados imprecisos de relógios baratos
- Valor principal: organização + visualização + insights que o app nativo do relógio não oferece
- Monetização futura: freemium (relatórios básicos grátis, insights avançados pagos)

---

## Definition of Done

Uma feature está pronta quando:
- [ ] Critérios de aceite do PM Agent passam
- [ ] Testes do QA Agent passam (cobertura ≥ 80% em services)
- [ ] Documentação atualizada pelo Docs Agent
- [ ] PR aprovado pelo Tech Lead
- [ ] Deploy em staging com sucesso
