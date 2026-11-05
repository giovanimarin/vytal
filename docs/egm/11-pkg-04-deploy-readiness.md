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
| Cloud Run | módulo `modules/gcp/cloud_run`: serviço, min 0/max 3, CPU/memória, invoker público + JWT na API | Declarado; runtime/IAM/config bloqueados; porta usa PORT |
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
| GCP-07 | Alta | Workflow de deploy usa main/staging enquanto desenvolvimento/CI usa master; ownership dos caminhos de publicação não definido aqui | Registrar pré-condição; imagem respeita PORT (default 8080), portanto porta Terraform 8000 não é por si só um defeito. Container real não executado; deploy inalterado |
| GCP-08 | Alta | `TokenRepository.get` pressupunha expires_at string: compatibilidade com datetime nativo corrigida e testada sem alterar contrato; SQL e tipos de data/comparação/upsert requerem validação por operação | Parcialmente corrigido; restante da paridade real bloqueado. Não extrapolar OpenAPI para semântica SQL |
| GCP-09 | Alta | Secrets via `--set-env-vars` em deploy em vez de referências Secret Manager; `latest` nas referências Terraform não fixa versão para rollback | Risco conhecido; mudanças de credenciais/deploy fora desta execução |
| GCP-10 | Alta | Backup/restauração, proteção de dados OAuth em repouso por aplicação, observabilidade sem payload e rollback não exercitados | Checklist pendente, nenhuma alegação de recuperação validada |
| GCP-12 | Alta, corrigida na fonte | HCL preexistente inválido: semicolon no lifecycle GCS e bloco replication aninhado em linha única | Sintaxe corrigida, formatação normalizada e check Terraform offline no CI; não comprova validação por provider |
| GCP-11 | Média | GCP real, OAuth real, TLS/rede, APK assinado/dispositivo e browser integrado não exercitados | Validação manual futura autorizada, com orçamento e ambiente isolado |

### Esquema e concorrência de refresh_tokens

O candidato mantém `token_id`, `user_id`, `token_hash` como STRING REQUIRED; `created_at`/`expires_at` TIMESTAMP REQUIRED (UTC); `revoked` INT64 REQUIRED para preservar os predicados `= 0`/`= 1`. Sem token bruto. Não adicionar partição `date`: essa coluna não existe. Não registrar o candidato no `for_each` global, que particiona todas as tabelas por date. Sem defaults SQL/BOOL, PK/UNIQUE ou índices SQLite presumidos.

BigQuery não oferece índices B-tree/constraints UNIQUE equivalentes aos locais; PK/FK declarativas são NOT ENFORCED e não provam unicidade. Clustering por hash/user pode ajudar consultas, mas não é exclusão mútua. Um UPDATE é uma unidade atômica de mutação do BigQuery, porém isso sozinho não prova que o fluxo completo create/read/rotate/revoke é linearizável: são necessários unicidade, visibilidade, concorrência entre instâncias, comportamento de retries/conflitos e armazenamento sem restrições de streaming. `num_dml_affected_rows == 1` é condição necessária, não prova suficiente. Mocks do SDK verificam SQL/tipos/contagem e propagação de erro; não emulam o motor, fila, conflito ou streaming buffer.

**Decisão A, recomendação não aprovada:** separar persistência operacional transacional (direção PostgreSQL já registrada em D12) da analítica BigQuery. Engenharia deve propor interface de repositório/sessões, unicidade/CAS/transações, backfill/rollback e custo/serviço/topologia para aprovação. Não implementar essa arquitetura aqui.

**Alternativa B, não aprovada:** manter auth no BigQuery exige desenho explícito do caminho de escrita sem streaming legado, fonte de unicidade, contrato de jobs/retries/idempotência e testes de concorrência multi-instância em ambiente isolado autorizado. Uma flag de “validado”, mutex em memória, limitação a uma instância ou mock de UPDATE não resolve a garantia. Se a prova falhar, manter bloqueio. Não há autorização para chamadas pagas nesta tarefa.

Referências de semântica a conferir na validação futura: documentação Google Cloud sobre [DML](https://cloud.google.com/bigquery/docs/data-manipulation-language), [streaming legado](https://cloud.google.com/bigquery/docs/streaming-data-into-bigquery), [constraints](https://cloud.google.com/bigquery/docs/primary-foreign-keys), [transações](https://cloud.google.com/bigquery/docs/transactions). Não se afirma validação remota desses contratos nesta execução.

## 3. Verificações reproduzíveis e limites

`backend/scripts/readiness_audit.py` lê apenas fonte/HCL/JSON versionados, não `.env`, tfstate, credenciais, SDKs de rede ou configurações reais. Executa DDL local apenas em SQLite `:memory:`. Compara as 16 tabelas locais às sete declaradas e os campos/colunas adicionais obrigatórias. Não avalia providers, referências HCL arbitrárias, SQL no motor GCP, constraints efetivas ou infraestrutura provisionada. Não é um `terraform validate/plan` nem um gate completo de implantação. Os itens explícitos de arquitetura/IAM continuam bloqueados até revisão humana com evidências.

Comandos **offline** (na raiz; dependências de desenvolvimento já instaladas):

```sh
.venv/bin/python backend/scripts/readiness_audit.py
# Relatório emitido com sucesso; isso não significa pronto para deploy.
.venv/bin/python backend/scripts/readiness_audit.py --check
# Exit 1 esperado enquanto houver gaps. Nunca adicionar bypass para liberar deploy.
cd backend
ENVIRONMENT=test GOOGLE_CLIENT_ID=synthetic GOOGLE_CLIENT_SECRET=synthetic ../.venv/bin/pytest
```

Smoke `tests/api/test_readiness_smoke.py`: processo/config/SQLite temporários, JWT e serviços reais, fronteira OAuth/Fit sintética, transports HTTP externos proibidos, stdout só com resultado/contagem (sem corpos/tokens). O worker rejeita ambiente/provider diferentes de test/local antes de importar a aplicação. Cobre usuários A/B legítimos, dados insuficientes (422), login inválido (401), conexão OAuth sintética, sync (202) com raw/normalizados persistidos, métricas, score existente 86.7 para fixture fixa e insight não vazio, histórico, métricas avançadas, identidade após refresh, replay e logout rejeitados, acesso cruzado (404) e sync cruzado sem chamar provider, ausência de autenticação (403). Não há `/metrics`, `/insights` ou `/ingest` inventados: usam-se os endpoints existentes, `summary`, `advanced` e `insight_text`. A fórmula/mensagens de readiness permanecem intactas.

Testes de infraestrutura validam o esquema candidato e a linha gerada por `RefreshTokenRepository.create()`, binding SDK existente, resposta de timestamp nativo/ISO para OAuth, rejeição de schema incompatível/BOOL/STRING/NULLABLE/date/duplicação, comparação negativa de tabelas/colunas, propagação de conflitos e contagem desconhecida/duplicada sem credencial nova. Contagem >1 pode já ter mutado várias linhas: retornar falha não repara essa corrupção, reforçando o bloqueio de unicidade no BigQuery. Erros de insert não ecoam detalhes/payload do provider. Nenhum mock é apresentado como prova de concorrência real.

Correções independentes pequenas: `TokenRepository.get()` aceita datetime nativo além do formato ISO anterior; erros de insert BigQuery deixam de incluir conteúdo arbitrário da resposta. Sem alteração de API, algoritmo de rotação, esquema ativo, configuração de produção ou comportamento local legítimo.

## 4. Configuração e permissões (somente nomes)

- Backend obrigatórios em produção/staging: ENVIRONMENT, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SECRET_KEY, JWT_SECRET_KEY, GOOGLE_REDIRECT_URI, CONFIG_PATH. Opcionais com política PKG-03: CORS_ORIGINS, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS. ALLOW_DEV_SEED/DEMO_PASSWORD não permitidos em produção. PORT e K_SERVICE são sinais do runtime, não secrets.
- Campos YAML GCP a conferir: cloud.provider, gcp.project, gcp.region, gcp.storage_bucket, gcp.bigquery_dataset, gcp.pubsub_topic, gcp.dataflow_temp. Não assumir que a seção GCP é selecionada só porque ENVIRONMENT é production. Dataset deve corresponder ao ambiente Terraform. Não imprimir YAML efetivo se contiver material sensível.
- Android: EXPO_PUBLIC_API_URL (público, HTTPS de release, termina /api/v1), NODE_ENV para configuração de build. Sem secret/token/password em EXPO_PUBLIC_. Web: VYTAL_BACKEND_URL (server-only, origem HTTPS), NODE_ENV definido pelo Next; sem credenciais em NEXT_PUBLIC_. Erros de configuração não incluem valores.
- Terraform inputs: project_id, region, env, backend_image, backend_domain. Secrets referenciados, sem valores: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SECRET_KEY; JWT_SECRET_KEY falta na declaração atual. Workflow legado usa GCP_PROJECT_ID, GCP_SA_KEY e referências GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SECRET_KEY, GOOGLE_REDIRECT_URI, JWT_SECRET_KEY. Nenhum valor foi consultado.
- Engenharia deve propor identidade dedicada runtime separada de deploy/worker, acesso às versões necessárias de secrets, criação de jobs BigQuery e leitura/mutação só nos datasets/tabelas aprovados, GCS só nos buckets necessários. Criação de recursos/DDL fica com identidade de infraestrutura. Não conceder BigQuery Admin/Owner como atalho. Publicação/consumo PubSub, DLQ e execução Dataflow exigem identidades/bindings próprios conforme caminho efetivamente aprovado; não conceder por inferência. OAuth de usuário não substitui IAM do servidor.

## 5. Checklist de pré-deploy — não executado

1. [ ] Aprovar armazenamento operacional/garantia de refresh, plano de transição e critérios de concorrência/idempotência. Não liberar GCP auth só por criar a tabela.
2. [ ] Resolver tabelas/colunas/dialetos e unicidade/upsert por operação; escolher partição/clustering sem adicionar `date` inexistente. Revisar plano de dados e rollback, sem executar migração nesta tarefa.
3. [ ] Preparar imagem/config/SDKs, dataset/endpoint por ambiente e identidade IAM mínima. Validar sinteticamente a imagem selecionada, porta via PORT, lifespan e config fail-closed. SDK instalado em CI não prova dependências da imagem de produção.
4. [ ] Definir fonte única de configuração/deploy (Terraform vs workflow), branches/publicação, referências de secrets, versões fixadas e quem pode promover. Não enviar secrets em argumentos/logs. Confirmar versões via metadados autorizados, nunca conteúdo.
5. [ ] Com aprovação separada para ambiente/orçamento/acesso, comparar recursos reais e esquemas, disponibilidade do dataset/região/IAM e buffering, executar criação/uso/refresh/logout imediato, refresh concorrente entre instâncias (um vencedor), falha de job/resposta ambígua/retry/replay, exclusão/revogação, duplicatas e não perda de sessão. Definir critérios técnicos objetivos antes; não inventar tolerâncias, SLA, retry budget ou retenção.
6. [ ] Validar ingestão/normalização/readiness/insights, idempotência de resync e isolamento A/B no armazenamento escolhido; não transportar dados pessoais reais para testes.
7. [ ] Android em dispositivo e web no endpoint real autorizado: TLS, 401/403/404, refresh concorrente, token expirado/revogado, falha de rede, logout/armazenamento e CORS. Google Fit callback no browser precisa completar o fluxo autenticado; contrato sintético não prova UX OAuth real.
8. [ ] Definir backup/restore, auditoria redigida, alertas, responsáveis, disponibilidade/custo e evidências de recuperação. Health endpoint é liveness; não prova acesso a BigQuery/secrets.
9. [ ] Revisar evidências do CI e todos os gaps aplicáveis; aprovação por PR e autorização explícita de qualquer operação de produção. **Esta issue não concede essa autorização.**

### Rollback planejado, sem execução

Antes de promover, registrar digest imutável da imagem anterior, revisão Cloud Run, configuração/identidade e versões de secrets por referência (sem valores), compatibilidade de API/esquema/token e backup restaurável. Definir quem decide interrupção/rollback e critérios objetivos. Voltar tráfego à revisão anterior não desfaz escrita/dados ou migração e não restaura tokens rotacionados. Não voltar a versão que aceite o token antigo/revogado ou reintroduza defaults inseguros; avaliar continuidade de sessões antes. Mudanças de esquema devem permitir leitor antigo ou exigir plano aprovado separado. Não usar `latest`, rollback de secret ou `terraform destroy` como estratégia automática. Restauração e teste em ambiente autorizado continuam pendentes.

### Conferência GCP futura — não executada, exige autorização separada

Somente leituras de metadados sem conteúdo sensível, em identidade/projeto explicitamente selecionados: `gcloud run services describe` com formato restrito a imagem/porta/serviceAccount (não imprimir env); `gcloud projects get-iam-policy` com projeção de roles/members; `bq show --schema` para cada tabela aprovada; `gcloud secrets versions list` somente nomes/estado, nunca access; `gcloud storage buckets describe` somente metadados. Mesmo leituras exigem revisão de acesso e política; não executar queries SQL nem testes DML/streaming como se fossem gratuitos. Nenhum desses comandos cloud foi executado. Não copiar tokens/objetos OAuth ou tfstate para relatórios.

## 6. Decisões pendentes e próxima entrega

- **Bloqueia auth GCP:** escolher A (transacional, recomendada) ou justificar/provar B (BigQuery) e aprovar topologia/custo/migração/recuperação em tarefa própria. D12 não escolhe automaticamente serviço ou implantação.
- **Bloqueia deploy GCP:** aprovar identidade/limites IAM, fonte de configuração/publicação, dados/constraints/upsert e evidências reais com orçamento autorizado. Parte é desenho de engenharia; não precisa inventar decisão de produto, mas requer aprovação antes de alterar arquitetura/custos/produção.
- **Não bloqueia este PR:** suíte offline, comparação OpenAPI e clientes, candidato de schema, parser HCL, redaction de erro e compatibilidade timestamp. CI verde autoriza revisão deste escopo, não produção.

## 7. Evidências finais

Resultados da suíte e CI são reportados por SHA no PR. O relatório estático é anexado como artefato do job backend e conserva `ready_for_deploy=false`; `--check` é testado para sair com erro sem credenciais. Nenhum gate de deploy foi removido. Terraform 1.9.8 `fmt -check -recursive` passou após corrigir sintaxe preexistente de blocos replication e lifecycle e normalizar formatação. HCL dos 11 arquivos é analisado offline por python-hcl2; JSON candidato pelo SDK BigQuery. `terraform validate` com provider não foi executado; sem init/backend/plan/apply. Não há recurso adicionado/removido nem mudança de valores de configuração; somente sintaxe/formatação nos recursos existentes e um schema proposto isolado.

Validação local final: 332 testes backend passaram, cobertura 81.58%; 52 testes Android + integração real Android/FastAPI/SQLite, lint, typecheck e export Hermes passaram; 42 testes web, instalação limpa Node 22/npm 10, typecheck e build Next passaram. OpenAPI v1 compatível com master, Ruff dos arquivos alterados e `pip check` passaram. Terraform fmt e parser HCL passaram offline. Não houve validação GCP real.
