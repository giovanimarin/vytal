# PKG-04 — Integração e prontidão (sem deploy)

Fonte: issue #20; base `master` `aaa6682`. Revisão offline, sem credenciais reais, chamadas cloud, apply, migração, rotação, merge ou deploy. **Não pronto para produção GCP.** Estados: validado = evidência local/estática apenas; pendente = validação real não executada; bloqueado = gap conhecido ou decisão necessária. CI verde não libera infraestrutura.

## 1. Inventário e matriz requisito × evidência × status

| Requisito/integração | Evidência no repositório | Estado |
| --- | --- | --- |
| API/auth v1 e isolamento | `backend/app/api/v1/`, `auth/authorization.py`, testes API A/A, B/B, A/B, B/A; JWT e SQLite reais | Validado local; GCP bloqueado |
| Cadastro/login/refresh/logout | `services/auth_service.py`, `repositories/refresh_token_repo.py`; PKG-02 testa concorrência SQLite e binding SDK isolado | Validado local; garantias GCP pendentes |
| Ingestão → normalização → métricas → readiness/insight | `health_data_service.py`, `health_data_repo.py`, `readiness_service.py`; `/health-data/sync`, `/health-data/{user_id}/summary`, `/readiness/{user_id}`, `/history`, `/advanced` | Smoke integrado offline acrescentado na etapa 3; GCP bloqueado |
| Android oficial | `mobile/vytal-app/`; API URL explícita, SecureStore, refresh single-flight/retry limitado, testes de erro de armazenamento/401/logout | Validado com transporte sintético e integração SQLite; dispositivo/rede reais pendentes |
| Web | `web/next.config.js`, `lib/api.ts`, `lib/sessionRefresh.ts`; proxy, refresh, limpeza de sessão; armazenamento local acessível a JS | Validado offline; revisão de risco XSS pendente, sem troca de mecanismo nesta issue |
| Startup fail-closed | `config/settings.py`, `config/security.py`, testes PKG-03; ambiente explícito, secrets/HTTPS/CORS/seed | Validado sintético; valores reais não inspecionados |
| Cloud Run | módulo `modules/gcp/cloud_run`: serviço, min 0/max 3, CPU/memória, invoker público + JWT na API | Declarado; runtime/IAM/porta/config bloqueados |
| GCS | módulo storage: raw versionado e processed, uniform access, lifecycle, sem force-destroy | Declarado; IAM, acesso e retenção efetiva pendentes |
| BigQuery | dataset `vytal_${env}` e sete tabelas; deletion protection, partição DAY/date | Declarado; incompatível com conjunto operacional atual |
| Pub/Sub | health events, subscription, DLQ e subscription DLQ | Declarado; permissões de dead-letter/worker não declaradas; ligação à ingestão não comprovada |
| Dataflow | provider retorna opções de runner; pipelines fora da imagem backend | Jobs, worker SA, staging/temp/IAM e empacotamento pendentes; não há job Terraform |
| Deploy/CI | `.github/workflows/deploy.yml` usa main/staging, imagem backend/Dockerfile, porta padrão 8080; testes master/codex em account-isolation.yml | Deploy não executado; ownership/master↔main e pré-condições bloqueados |
| SDK GCP da imagem | requirements-prod não inclui BigQuery/GCS; requirements de testes inclui BigQuery | Bloqueado: sucesso do SDK em testes não prova imagem GCP funcional |
| Configuração da imagem | `backend/config.yaml` seleciona local; produção exige CONFIG_PATH explícito, mas não impõe GCP | Bloqueado: imagem existente pode operar em SQLite efêmero se configuração não for substituída |
| IAM/runtime identity | Cloud Run não fixa service_account; não há bindings de Secret Accessor, BigQuery, Storage/Dataflow/PubSub para identidade runtime | Bloqueado até identidade e privilégio mínimo aprovados/verificados |
| Secrets declarados | Terraform define client ID/secret e SECRET_KEY; falta JWT_SECRET_KEY; versões não são criadas | Bloqueado; não ler nem criar versões nesta tarefa |
| Dependências externas | Google Fit OAuth/API, Artifact Registry, backend de estado GCS, Secret Manager; Garmin não implementado aqui | Disponibilidade/acessos reais pendentes; nenhum serviço habilitado |

## 2. Gaps e severidade

| ID | Gravidade | Evidência e impacto | Tratamento nesta issue |
| --- | --- | --- | --- |
| GCP-01 | Crítica, bloqueia auth GCP | `refresh_tokens` ausente no mapa Terraform. SQLite exige token_id PK, token_hash UNIQUE, user_id, created_at/expires_at, revoked inteiro; BigQuery não impõe unicidade | Esquema candidato isolado + testes; não ativar tabela nem declarar rotação segura |
| GCP-02 | Crítica, decisão arquitetural | BigQuery `insert_rows_json` usa streaming legado; create → rotate/logout faz UPDATE sobre linhas recentes. Streaming buffer pode impedir DML; insertIds/best-effort não garantem unicidade/exactly-once | Bloquear auth GCP; opções e provas requeridas abaixo |
| GCP-03 | Crítica | Outros recursos operacionais ausentes: users, oauth_tokens, raw_health_events, normalized_stress, wellness_feedback, fact_readiness_by_modality, workout_history, workout_exercises, muscle_recovery | Inventário reproduzível; sem migração ou criação especulativa de todas as tabelas |
| GCP-04 | Alta | raw_google_fit_events não é raw_health_events e exige campos diferentes; dim_user exige date não enviado; campos normalizados devem ser comparados; SQLite INSERT OR REPLACE não existe no insert streaming BigQuery | Relatório de campos/tabelas; bloqueio para idempotência de ingestão/readiness e duplicação de usuários/sessões |
| GCP-05 | Crítica | Identidade runtime e bindings mínimos ausentes; versões de secrets e JWT_SECRET_KEY ausentes no Terraform | Desenhar/autorizar bindings e provisionamento em tarefa separada; startup deve continuar falhando fechado |
| GCP-06 | Alta | Imagem usa requirements-prod sem SDKs GCP e config local embutida; dataset padrão `vytal` diverge de `vytal_${env}` | Bloqueio de configuração/empacotamento; nenhuma seleção silenciosa de infraestrutura nova |
| GCP-07 | Alta | Cloud Run declara porta 8000 enquanto imagem padrão escuta 8080; workflow main/staging diverge de master | Registrar pré-condição; não executar ou modificar deploy nesta tarefa |
| GCP-08 | Alta | `TokenRepository.get` pressupõe expires_at string, SDK BigQuery pode retornar datetime; SQL SQLite (`json`, funções, LIMIT/date) e tipos requerem validação por operação | Bloqueio de paridade real; não extrapolar validação OpenAPI para semântica SQL |
| GCP-09 | Alta | Secrets via `--set-env-vars` em deploy em vez de referências Secret Manager; `latest` nas referências Terraform não fixa versão para rollback | Risco conhecido; mudanças de credenciais/deploy fora desta execução |
| GCP-10 | Alta | Backup/restauração, proteção de dados OAuth em repouso por aplicação, observabilidade sem payload e rollback não exercitados | Checklist pendente, nenhuma alegação de recuperação validada |
| GCP-11 | Média | GCP real, OAuth real, TLS/rede, APK assinado/dispositivo e browser integrado não exercitados | Validação manual futura autorizada, com orçamento e ambiente isolado |

### Esquema e concorrência de refresh_tokens

O candidato mantém `token_id`, `user_id`, `token_hash` como STRING REQUIRED; `created_at`/`expires_at` TIMESTAMP REQUIRED (UTC); `revoked` INT64 REQUIRED para preservar os predicados `= 0`/`= 1`. Sem token bruto. Não adicionar partição `date`: essa coluna não existe. Não registrar o candidato no `for_each` global, que particiona todas as tabelas por date. Sem defaults SQL/BOOL, PK/UNIQUE ou índices SQLite presumidos.

BigQuery não oferece índices B-tree/constraints UNIQUE equivalentes aos locais; PK/FK declarativas são NOT ENFORCED e não provam unicidade. Clustering por hash/user pode ajudar consultas, mas não é exclusão mútua. Um UPDATE é uma unidade atômica de mutação do BigQuery, porém isso sozinho não prova que o fluxo completo create/read/rotate/revoke é linearizável: são necessários unicidade, visibilidade, concorrência entre instâncias, comportamento de retries/conflitos e armazenamento sem restrições de streaming. `num_dml_affected_rows == 1` é condição necessária, não prova suficiente. Mocks do SDK verificam SQL/tipos/contagem e propagação de erro; não emulam o motor, fila, conflito ou streaming buffer.

**Decisão A, recomendação não aprovada:** separar persistência operacional transacional (direção PostgreSQL já registrada em D12) da analítica BigQuery. Engenharia deve propor interface de repositório/sessões, unicidade/CAS/transações, backfill/rollback e custo/serviço/topologia para aprovação. Não implementar essa arquitetura aqui.

**Alternativa B, não aprovada:** manter auth no BigQuery exige desenho explícito do caminho de escrita sem streaming legado, fonte de unicidade, contrato de jobs/retries/idempotência e testes de concorrência multi-instância em ambiente isolado autorizado. Uma flag de “validado”, mutex em memória, limitação a uma instância ou mock de UPDATE não resolve a garantia. Se a prova falhar, manter bloqueio. Não há autorização para chamadas pagas nesta tarefa.

Referências de semântica a conferir na validação futura: documentação Google Cloud sobre [DML](https://cloud.google.com/bigquery/docs/data-manipulation-language), [streaming legado](https://cloud.google.com/bigquery/docs/streaming-data-into-bigquery), [constraints](https://cloud.google.com/bigquery/docs/primary-foreign-keys), [transações](https://cloud.google.com/bigquery/docs/transactions). Não se afirma validação remota desses contratos nesta execução.
