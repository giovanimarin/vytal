# EGM — Fase 0: inventário do estado atual

Data: 2026-11-04. Repositório: `giovanimarin/vytal`.
Base auditada: `chore/agent-automation-bootstrap`, commit `25c0c31970f3974efa5f3a972ab87ec64d69a703`.
Aplicativo Android oficial: **`mobile/vytal-app/`**, conforme `AGENTS.md` e orientação do proprietário.

## 1. Resumo executivo e limites

Existe um produto com backend FastAPI, dois projetos Expo, frontend Next.js, normalização de dados de saúde e indicadores de prontidão/recuperação. O fluxo principal executa ingestão, normalização e cálculo dentro da requisição HTTP; os scripts Beam são caminhos separados. SQLite é a implementação local mais completa. Os adaptadores GCP e o Terraform existem, mas divergem do modelo e das operações realmente usados pelo backend.

O Android oficial tem login/cadastro, perfil, dashboard configurável, catálogo de indicadores e conexão Google Fit parcial. Não há equivalência entre todas as funcionalidades web e Android: registro de treinos, modalidades e mapa muscular aparecem na web e no candidato legado, mas não como telas equivalentes no app oficial. O código comprova funcionalidades presentes, não comprova uma release Android operacional nem a saúde da produção.

Os riscos prioritários são autorização por usuário ausente em APIs de saúde; contratos Android/API incompatíveis; OAuth incompleto para navegador; persistência GCP incompatível com os repositórios; e CI que não cobre a branch padrão `master`. Nenhum desses problemas foi corrigido nesta fase. Os 66 testes existentes passam, mas cobrem 33,59% das linhas do backend e não demonstram isolamento entre usuários ou integração real com Google.

Este documento executa apenas o inventário. Não aprova uma especificação, não implementa jejum, não altera código funcional, dependências ou configuração do projeto, não faz merge e não executa deploy. A análise inclui todos os diretórios versionados; caches/artefatos, imagens, PDF e lockfiles foram identificados, mas não tratados como fonte de comportamento funcional. O total na base é de 314 arquivos versionados, incluindo 84 sob `web/.next/`.

Legenda: **implementado** = caminho de código presente; **parcial** = lacuna conhecida de integração/contrato; **não conectado** = código presente fora do fluxo principal; **desconhecido** = depende de evidência externa ou execução não realizada. Implementado não significa validado em dispositivo ou produção.

## 2. Evidências principais

Os links são relativos à raiz desta branch e devem ser lidos no commit acima. Símbolos e nomes de rotas identificam a evidência mesmo após movimentação de linhas.

| Evidência | Local / símbolo | Constatação |
|---|---|---|
| Contrato de execução | [AGENTS.md](../../AGENTS.md), [prompt Fase 0](prompts/00-inventory.md) | Inventário antes de especificação e aprovação; Android oficial explicitado; nenhuma implementação autorizada |
| Entrada API | [main.py](../../backend/app/main.py), `lifespan`, `app.include_router` | FastAPI, inicialização do warehouse, prefixo `/api/v1`, CORS aberto |
| Registro efetivo de rotas | [router.py](../../backend/app/api/v1/router.py) | JWT aplicado por grupo; `/users/me` resolve identidade no próprio endpoint |
| Identidade | [dependencies.py](../../backend/app/auth/dependencies.py), [jwt_handler.py](../../backend/app/auth/jwt_handler.py) | Bearer JWT; o retorno da identidade não é consumido pelos handlers com IDs arbitrários |
| Entrada Android | [package.json](../../mobile/vytal-app/package.json), [layout](../../mobile/vytal-app/app/_layout.tsx) | `expo-router/entry`, AuthGate, QueryClient, Stack |
| Contratos Android | [api.ts](../../mobile/vytal-app/src/services/api.ts), [hooks](../../mobile/vytal-app/src/hooks/useReadiness.ts), [authStore](../../mobile/vytal-app/src/store/authStore.ts) | Token Bearer/refresh, endereços fixos, persistência SecureStore com fallback web |
| Dashboard oficial | [dashboard](../../mobile/vytal-app/app/%28dashboard%29/index.tsx), [dashboardStore](../../mobile/vytal-app/src/store/dashboardStore.ts) | Nove widgets selecionáveis; seleção apenas em memória |
| Ingestão | [health_data_service.py](../../backend/app/services/health_data_service.py), `sync` | Busca Google → raw → normalizado → readiness, tudo aguardado no request |
| Google Fit | [google_fit.py](../../backend/app/adapters/connectors/google_fit.py) | Aggregate/sessions, refresh, fases de sono estimadas, coleta de stress ausente |
| Persistência | [local.py](../../backend/app/adapters/cloud/local.py), `_SCHEMA_SQL`; [gcp.py](../../backend/app/adapters/cloud/gcp.py) | 16 tabelas SQLite; sem migrações versionadas; BigQuery não aplica parâmetros da consulta |
| Domínio | [health_metrics](../../backend/app/domain/health_metrics), [exercise_bank.py](../../backend/app/domain/sports/exercise_bank.py) | Cinco métricas; catálogo e mapeamento determinístico de músculos/exercícios |
| Algoritmos | [readiness_service.py](../../backend/app/services/readiness_service.py), [advanced_metrics_service.py](../../backend/app/services/advanced_metrics_service.py) | Heurísticas codificadas, sem evidência de validação clínica |
| Infraestrutura | [Terraform](../../infrastructure/terraform/environments/gcp/main.tf), [Dockerfile](../../backend/Dockerfile) | Cloud Run, BigQuery, Storage, Pub/Sub declarados; execução remota não inspecionada |
| Automação | [CI](../../.github/workflows/ci.yml), [deploy](../../.github/workflows/deploy.yml), [EGM README](README.md) | Workflows `main`/`staging`; EGM é bootstrap documental, sem scheduler verificado |

## 3. Arquitetura, entradas e fluxos

### 3.1 Componentes reais

| Componente | Entrada / responsabilidades | Estado e limites |
|---|---|---|
| Backend | `uvicorn app.main:app`, executado em `backend/`; routers → services → repositories → warehouse | Implementado; configuração carregada como singleton; factories escolhem `local` ou `gcp` |
| Android oficial | `mobile/vytal-app/package.json:main` → Expo Router → `app/_layout.tsx` → login/dashboard | Expo ~54, React 19.1, RN 0.81.5, Expo Router ~5; compatibilidade nativa dessa combinação não validada |
| Entradas alternativas oficiais | `mobile/vytal-app/index.ts` registra `App.tsx`, que ainda é template | Não são a entrada declarada em `package.json`; não confundir template com produto |
| Candidato legado | `mobile/package.json`, `mobile/app/`, `mobile/src/` | Outro app Expo, com tabs, modalidades, treinos e BodyMap; cliente API sem JWT; preservar até decisão explícita |
| Web | `web/package.json`, Next.js 14.2.5 App Router, `app/layout.tsx`, `app/page.tsx` → dashboard | Login, dashboard, dados, modalidades, treinos, body-map e settings; API Axios relativa `/api/v1` |
| Pipelines | `pipelines/pipeline_raw_normalized_health.py` e `pipeline_normalized_readiness_score.py` | CLI com usuário e intervalo; Beam DirectRunner/DataflowRunner; não disparados pelo sync HTTP; execução direta da raiz falha no import de app (§9.2) |
| Infra | Docker/Compose e módulos Terraform GCP | Definições versionadas; não representam prova de recursos implantados |
| Documentação | `README.md`, `docs/PRODUCT.md`, `docs/prd.md`, `docs/architecture/`, `ROADMAP.md`, `CLAUDE.md` | Misturam intenção, versões anteriores e estado atual; código prevalece para inventário |

### 3.2 Fluxo de dados efetivo

1. Cadastro/login grava `users`, gera JWT de acesso e refresh token. Android guarda tokens/perfil; web guarda acesso e identidade em localStorage.
2. OAuth gera URL e `state` assinado; callback troca código por tokens Google, grava `oauth_tokens` e garante `dim_user`.
3. `/health-data/sync` recupera tokens, consulta aggregate/sessions Google, grava `raw_health_events`, instancia as cinco métricas registradas e grava `normalized_*` válidos.
4. Para cada data do intervalo, calcula e grava `fact_daily_readiness`. A resposta HTTP é 202, porém o trabalho termina antes da resposta (`status: completed`); não existe job/consulta de progresso nesse caminho.
5. Consultas retornam dados/indicadores. Alguns GETs calculam e persistem sob demanda: readiness, modalidades e recuperação muscular. POST de treino grava treino/exercícios e recalcula recuperação muscular; não há transação única entre essas etapas nem invalidação universal de indicadores derivados.
6. Beam pode reler raw para normalizar e recalcular readiness em separado. Dead letters são encaminhadas para logs; não há sink durável de dead letters nesse código. Pub/Sub possui recursos Terraform, mas não há produtor/consumidor conectado ao fluxo HTTP inspecionado.

`StorageProvider` tem implementações filesystem/GCS, mas o fluxo de sync persiste no warehouse: não comprova a afirmação de um arquivo bruto original imutável no storage. O adapter transforma aggregate/sessions em payloads internos antes de chamar de raw.

### 3.3 Endereços e ambientes

- `web/next.config.js` reescreve `/api/*` para backend em loopback, porta **8003**.
- O Android oficial fixa uma URL Cloud Run para produção; a condição `typeof window !== 'undefined'` seleciona produção antes de `__DEV__`. No runtime nativo efetivo, isso precisa ser validado, pois `window` pode existir. O outro ramo de desenvolvimento usa IP LAN fixo/porta **8002**, não adequado como configuração universal.
- O candidato legado usa outro IP/porta **8001** em desenvolvimento e outro domínio em produção.
- `backend/Dockerfile` atende `${PORT:-8080}`. `backend/docker-compose.yml` mapeia 8001→8000 e verifica 8000, sem definir `PORT=8000`: divergência estática com o default do Dockerfile. O Compose de `infrastructure/` usa outro Dockerfile (Python 3.11, porta 8000, reload).
- `backend/config.yaml` seleciona **local**, independentemente de `ENVIRONMENT=production`. `load_cloud_config` recai em configuração local se o arquivo não existir. Não há evidência de que o deploy altere `cloud.provider` para GCP ou monte volume durável SQLite.
- Não foram feitas chamadas ao domínio de produção, à conta Google, ao EAS ou aos recursos GCP. Estado de releases, IAM efetivo, backup e variáveis remotas: desconhecido.

## 4. Matriz completa de endpoints e consumidores

Inventário confirmado pelo registro de rotas e pelo OpenAPI gerado da aplicação importada. São **24 operações de negócio/health**. Prefixo abaixo: `/api/v1`, exceto `/health`. O FastAPI ainda oferece `/openapi.json`, `/docs`, `/docs/oauth2-redirect` e `/redoc`, sem proteção configurada, fora dessa contagem.

**JWT-ID**: Bearer obrigatório no router, mas sem comparação entre `sub` e o usuário informado; aceita ID arbitrário autenticado. **JWT-me**: usa identidade do token. **Público**: sem Bearer, com outras condições indicadas. Nenhum handler declara `response_model`; retornos são dicionários/listas dos serviços/repositórios, sem schema forte de saída. Parâmetros sem default são obrigatórios; `?` indica opcional. M = Android oficial; W = web; L = candidato legado. Consumidor identificado é chamada no código, não tráfego observado.

| Método e caminho | Entrada / contrato de saída | Autenticação e autorização | Consumidores / evidência |
|---|---|---|---|
| GET `/health` | Sem corpo → `{status, version}` | Público | Healthchecks Docker; `main.py` |
| POST `/auth/register` | `RegisterRequest {email,password,name}` → 201, identidade plana, access/refresh, token_type | Público; senha mínima 8 no serviço; email é `str` | M `app/register.tsx`; `auth.py`, `AuthService.register` |
| POST `/auth/login` | `LoginRequest {email,password}` → identidade plana e tokens; 401 inválido | Público | M login, W login; `auth.py` |
| POST `/auth/refresh` | `RefreshRequest {refresh_token}` → novos tokens, revoga anterior | Público; valida refresh hash/expiração/revogação | Interceptor M `src/services/api.ts` |
| POST `/auth/logout` | `LogoutRequest {refresh_token}` → `{ok:true}` | Público; revoga token apresentado | Sem chamada explícita localizada em M/W; logout das UIs é local |
| GET `/users/me` | Sem corpo → usuário sem password_hash; modalidades desserializadas | JWT-me; 404 inexistente | M perfil/hooks; W login/settings |
| PATCH `/users/me` | `UpdateProfileRequest`: name,birth_date,weight_kg,height_cm,goal,gender,preferred_modalities opcionais → perfil | JWT-me; exclui `None`, não limpa campos com null | M profile-setup/perfil; W settings |
| GET `/connect/{provider}/auth-url` | query `user_id`, `redirect_uri?` → `{auth_url,state}` | JWT-ID | M fontes/connect, L connect; `connect.py` |
| GET `/connect/{provider}/callback` | query `code,state` → `{user_id,provider,connected,connected_at,message}` | JWT; usuário vem do state, sem vínculo ao token | Retorno de navegador Google; `connected_at` contém expires_at, não horário de conexão |
| POST `/connect/{provider}/callback` | `OAuthCallbackRequest {code,state,redirect_uri}` → conexão | JWT; usuário vem do state, sem vínculo ao token | M connect antigo; L connect |
| POST `/health-data/sync` | `SyncRequest {user_id,provider='google_fit',start_date,end_date,metric_types?}` → 202, sync_id, contagens, datas calculadas, status completed, started_at | JWT-ID | M sync, L sync; `health_data.py` |
| GET `/health-data/{user_id}/summary` | query `date` → user_id,date,sleep?,steps?,heart_rate?,stress?,activity[] | JWT-ID | M `useHealthSummary`, L hooks |
| GET `/readiness/{user_id}` | query `date?` → registro com contribuições planas; 422 sem sono/FC | JWT-ID | M readiness, W dashboard/data, L |
| GET `/readiness/{user_id}/history` | query `start_date,end_date` → lista `{date,readiness_score,readiness_category}` DESC | JWT-ID | M ScoreHistory, W dashboard/data, L |
| GET `/readiness/{user_id}/advanced` | query `date?` → social_jetlag,recovery_curve,signal_quality | JWT-ID | M AdvancedMetrics, W dashboard; handler registrado é `readiness.py` |
| GET `/readiness/modalities/{user_id}` | query `date?` → `{user_id,date,modalities[]}`; filtra preferências do usuário | JWT-ID | W modalities; L; não há tela equivalente no Android oficial |
| POST `/workouts` | `WorkoutIn` → 201, treino com exercises[] | JWT-ID no corpo | W workouts, L; valida modalidades/intensidades e duração >0 |
| GET `/workouts/{user_id}` | query `start_date,end_date` → treinos com exercises[] | JWT-ID | W workouts, L |
| GET `/workouts/exercises/catalog` | Sem corpo → `{name,primary,secondary}[]` | JWT, sem recurso pessoal | W workouts, L; não há colisão com `/{user_id}` por número de segmentos |
| GET `/muscles/{user_id}/recovery` | query `date?` → `{user_id,date,muscles[]}` | JWT-ID | W body-map, L BodyMap |
| GET `/muscles/{user_id}/suggestion` | query `date?` → `{suggestion,score?,message}` | JWT-ID | W body-map, L |
| POST `/wellness-feedback` | `WellnessFeedbackRequest` → 201 `{status:'saved',feedback_id}` | JWT-ID no corpo | M WellnessFeedback; backend aceita `feeling_score,workout_worthwhile,workout_readiness,energy_level,notes` opcionais, além de user_id/date |
| GET `/wellness-feedback/{user_id}` | query `date?` → registro, ou 404 | JWT-ID | M `useWellnessFeedback` |
| POST `/dev/seed` | Sem corpo → demo user, tokens, senha demo, 14 dias e intervalo | Público; permite apenas environment local/development/dev, caso contrário 403 | W botão demo; `dev_seed.py` reseta dados do usuário demo |

`WorkoutIn`: user_id, modality, intensity, duration_min, date?, notes?, exercises[] de `{name,sets?,reps?}`, free_text?. Datas são em grande parte strings, não tipos de domínio; não há validação comum de intervalo, máximo de dias, timezone ou paginação.

### 4.1 Divergências de contrato

| Divergência | Evidência / consequência |
|---|---|
| Login/cadastro Android espera `data.user`; backend retorna `user_id,email,name` no nível raiz | `app/login.tsx`, `app/register.tsx` vs `AuthService`; tokens são salvos, mas `setProfile` não roda nesse retorno e `userId` pode permanecer null. Perfil usa `/users/me`, porém não demonstra reparação automática de todo fluxo de login |
| Senha Android aceita 6 caracteres; backend exige 8 | `handleRegister` vs `AuthService.register`; cadastro com 6–7 falha apesar da validação cliente |
| Status e desconexão Google ausentes | `(dashboard)/data-sources.tsx` chama GET `/connect/google_fit/status` e DELETE `/connect/{source}`; nenhum handler registrado; status captura e ignora falha |
| Feedback incompatível | Hook M envia `trained_today` e `workout_worth_it`; backend não declara esses campos e os ignora. Tipo cliente usa `submitted_at`, backend grava `created_at` |
| Callback de navegador exige Bearer | `router.include_router(connect_router, dependencies=...)`; redirect Google não inclui normalmente o JWT da API; teste local sem Bearer retorna 403 |
| Conexão antiga usa usuário fixo e APIs web | `app/connect.tsx`: ID MVP, `window.open/window.location` e deep link com redirect construído no callback; não demonstra fluxo Android nativo correto nem URI consistente |
| Tipo de histórico Android mais amplo que resposta | `useReadinessHistory` tipa `ReadinessData[]`, mas repositório retorna apenas data/score/categoria; componentes atuais usam subconjunto |
| Documentação OpenAPI estática desatualizada | `docs/architecture/openapi.yaml` não cobre auth/users/feedback/dev/advanced atuais nem segurança Bearer; gerado da aplicação contém essas operações |
| Código de advanced duplicado | `api/v1/advanced_metrics.py` define a mesma rota, mas não é incluído no router; não é uma segunda operação publicada |

## 5. Funcionalidades e telas

### 5.1 Android oficial (`mobile/vytal-app/`)

| Tela / funcionalidade | Estado | Evidência e comportamento |
|---|---|---|
| Inicialização e gate | Parcial | `app/_layout.tsx`, `app/index.tsx`: hidrata tokens, redireciona por flags; presença de tokens é considerada autenticação, sem validação inicial no servidor |
| Login / cadastro | Parcial | `app/login.tsx`, `register.tsx`: telas completas, endpoints existentes, divergências de identidade/senha acima |
| Modo de teste | Parcial | Login/connect apenas fixam userId/isConnected, sem gerar tokens/dados; não equivalem ao seed real da web e não autenticam a API |
| Onboarding de perfil | Implementado, integração não exercitada em aparelho | `profile-setup.tsx`: dados opcionais, PATCH e skip; rota é considerada pública no gate, mas API requer JWT |
| Perfil | Implementado | `(dashboard)/profile.tsx`, `useProfile.ts`: GET/PATCH dados pessoais; formato de datas e faixas precisam contrato |
| Dashboard / catálogo | Implementado com limitações | `(dashboard)/index.tsx`, `app/catalog.tsx`, `dashboardStore.ts`: adicionar/remover, long press para edição; inicia vazio, seleção não persiste; função reorder existe no store, sem gesto de reordenação identificado |
| Readiness e histórico | Implementado no código | `ScoreRing`, `ScoreHistory`, hooks; diário, insight e gráfico; ausência de dados oculta widgets |
| Sono | Parcial quanto à semântica | `SleepDetails`: fases e duração; adapter Google fabrica percentuais de fases em vez de importar estágios medidos |
| Passos/calorias | Parcial | `StepsCalories`: meta fixa 10 mil; calorias somam atividades; adapter Google preenche calorias com zero |
| FC e zonas | Heurística implementada | `HRZones`: média/repouso/máxima/mínima; zonas derivadas da máxima observada, não de máxima fisiológica individual validada |
| Métricas avançadas | Heurísticas implementadas | `AdvancedMetrics`: jetlag, curva, qualidade; cada um dos três IDs de widget renderiza o mesmo componente completo, podendo duplicar os três blocos |
| Bem-estar subjetivo | Parcial | `WellnessFeedback`, hooks/types: formulário existe, campos não preservados integralmente; não há calibração dos pesos a partir dele |
| Fontes Google Fit | Parcial | `(dashboard)/data-sources.tsx`: abre navegador; status/disconnect inexistentes; `connect.tsx` conserva fluxo MVP |
| Sincronização | Parcial | `(dashboard)/_layout.tsx`, hooks: botão e banner para intervalo recente; não há sincronização periódica/background demonstrada |
| Fontes Apple/Fitbit/Samsung | Não implementadas | Cards `available:false`; factory backend só registra google_fit |
| Logout | Parcial | `SideMenu`/authStore removem estado/token local, sem chamar revogação backend nem limpar explicitamente todo cache React Query |
| Tabs anteriores internas | Código remanescente | `app/(tabs)/_layout.tsx`, `index.tsx`, `data.tsx` ainda existem no projeto oficial, mas navegação principal aponta para `(dashboard)`; não presumir remoção nem uso em release |
| Treinos/modalidades/mapa muscular | Ausentes como telas equivalentes oficiais | Não há essas telas na árvore oficial; backend e web as implementam, e o outro projeto mobile possui versões |
| Notificações / jejum / Health Connect | Não implementados no código inspecionado | Não há sessão/rota/tela de jejum, expo-notifications, agendamento ou adapter Health Connect; notificações constam como intenção no ROADMAP |

`app.json` declara esquema `vytal`, pacote Android `com.vytal.app`, nova arquitetura desabilitada. `eas.json` contém builds development/preview APK e production app-bundle. Não foi executado EAS build/submit, emulador ou APK; assinatura, publicação na loja e versão instalada permanecem desconhecidas.

### 5.2 Web e candidato legado

Web: `/login` autentica ou cria demo pelo seed; `/dashboard` exibe prontidão/histórico/avançadas; `/data` consulta histórico; `/modalities` consulta recomendações filtradas; `/workouts` lista catálogo, registra exercícios/texto livre e consulta histórico; `/body-map` exibe recuperação/sugestão; `/settings` edita perfil/gênero/modalidades. `AppShell` fornece navegação/gate cliente, não autorização da API. Não foi inferida integração Google funcional a partir da existência das telas.

O projeto `mobile/` externo ao oficial tem `(tabs)/index`, `data`, `modalities`, `workout-log`, componentes BodyMap e hooks próprios. Seu Axios não anexa JWT, incompatível com os routers atuais. É **candidato legado**, não material descartável; nenhuma remoção proposta como ação automática.

## 6. Modelo de dados e persistência

Fonte executável: `_SCHEMA_SQL` em `backend/app/adapters/cloud/local.py`. SQLite usa TEXT para UUID/datas/JSON, REAL para scores e INTEGER para inteiros/flags. Não há ORM, versionamento de schema/Alembic ou migrações incrementais localizadas. `CREATE TABLE IF NOT EXISTS` cria estrutura nova, mas não atualiza banco antigo quando colunas mudam.

| Entidade / chave | Dados persistidos | Escrita/leitura e integridade |
|---|---|---|
| `users` / user_id | Email único, nome, hash bcrypt, nascimento, peso, altura, objetivo, gênero, modalidades JSON, created/updated | `UserRepository`; resposta `/me` remove hash; identidade operacional |
| `dim_user` / user_id | Provider e created_at | Auth/OAuth → `ensure_user`; dimensão analítica separada de users, sem FK entre elas |
| `refresh_tokens` / token_id | user_id, hash SHA-256 único, expires_at, created_at, revoked | Gera UUID aleatório, guarda hash; refresh rotaciona; revogação via UPDATE |
| `oauth_tokens` / (user_id,provider) | Access/refresh Google em texto, expires_at | `TokenRepository`; sem criptografia de aplicação; SQLite substitui par existente |
| `raw_health_events` / event_id | Usuário/provider/tipo, payload JSON textual, collected/ingested, pipeline_run | Adapter → HealthDataRepository; UUID novo por evento/sync, sem chave de deduplicação do provider |
| `normalized_sleep` / record_id | user/date, duração, deep/light/REM/awake, sleep_score, source_event_id, normalized_at | HealthMetric; sem unicidade user/date; sono rotulado pela data inicial UTC |
| `normalized_steps` / record_id | user/date, total_steps, hourly_steps JSON, proveniência | Intervalos repetidos podem criar novas linhas do mesmo dia |
| `normalized_activity` / record_id | user/date, tipo, duração, intensidade, calorias, proveniência | Múltiplas atividades por dia; payload Google atualmente retém só primeira atividade do bucket |
| `normalized_heart_rate` / record_id | user/date, resting/average/max/min, proveniência | Repouso no adapter é aproximação pelo mínimo; summary pega primeira linha sem ORDER BY |
| `normalized_stress` / record_id | user/date, stress_score, available, proveniência | Modelo implementado; connector Google não fornece evento de stress |
| `fact_daily_readiness` / readiness_id | user/date único, score/categoria, quatro contribuições, insight, calculated_at | Calculado no sync ou GET; histórico retorna só três campos |
| `wellness_feedback` / feedback_id | user/date único, feeling, worthwhile, readiness, energy, notes, created_at | POST substitui feedback diário no SQLite; sem loop de aprendizado implementado |
| `fact_readiness_by_modality` / record_id | user/date/modality único, score,status,recommendation,hrv_available,low_confidence,calculated_at | Calculado em GET se não existe; cache persistido pode ficar obsoleto |
| `workout_history` / workout_id | user,date,modality,intensity,duration,notes,created_at | Registro independente de atividades Google; sem idempotency key |
| `workout_exercises` / exercise_id | workout_id, nome, grupos JSON, sets/reps | Única FK explícita é para workout_history; não há `PRAGMA foreign_keys=ON` no adapter |
| `muscle_recovery` / record_id | user/date/muscle único, score, last_workout_id, estimated_full_recovery_at, updated_at | Recalculado após treino ou GET sem cache; last_workout_id não tem FK declarada |

Índices explícitos: email de users, refresh por user, treinos por user/date, recovery por user/date e modalidade por user/date. Não há FK geral de saúde para usuário, nem política central de cascade/delete/export/retention localizada. A API não oferece exclusão/exportação de conta/dados ou revogação Google.

O adapter local abre conexão por operação, usa placeholders para valores e `INSERT OR REPLACE`. Tabelas/colunas SQL são interpoladas por código interno; isso não é evidência suficiente de SQL injection remoto. REPLACE não equivale a upsert universal e nenhuma transação engloba cadastro+dimensão, treino+exercícios+recuperação ou rotação completa de tokens. Sem unicidade natural em raw/normalizados, repetir sync pode duplicar dados; consultas de uma linha por dia podem retornar dados antigos.

### 6.1 Paridade GCP: lacunas verificáveis estaticamente

- `BigQueryWarehouseProvider.query(sql, params)` chama `client.query(sql)` e **ignora params**. Repositórios usam placeholders SQLite `:nome`/`?` e funções como `date('now', :offset)`, sem tradução nem parâmetros BigQuery.
- `insert_rows_json` é append, sem semântica `INSERT OR REPLACE`. `init_schema` não faz nada e delega tudo ao Terraform. Consultas sem qualificação de dataset/default dataset explícito também precisam adaptação.
- Terraform cria sete tabelas: `raw_google_fit_events`, normalized sleep/steps/heart_rate/activity, fact_daily_readiness e dim_user. Código usa `raw_health_events`; faltam normalized_stress, users, oauth_tokens, refresh_tokens, wellness_feedback, modalidades, treinos/exercícios e recuperação.
- O módulo BigQuery particiona todas as tabelas por `date`, e os schemas incluem essa coluna. Porém `dim_user.date` é REQUIRED no schema Terraform e não é enviado por `AuthService.register`/`ensure_user`. O schema de `raw_google_fit_events` exige também `date,data_type,start_time_ms,end_time_ms`, diferente do payload de `raw_health_events` escrito pelo repositório. Renomear a tabela isoladamente não resolve a paridade de contrato.
- Config padrão do backend usa dataset `vytal`; Terraform declara `vytal_${env}`. Dependências google-cloud-storage/bigquery não constam no requirements-prod; exigem instalação/configuração adicional para esse provider.
- `ENVIRONMENT=production` não muda `cloud.provider=local`; SQLite em filesystem efêmero de Cloud Run não constitui persistência durável/multi-instância. Terraform permite até três instâncias; risco depende da configuração implantada, não inspecionada.

Conclusão: a interface de abstração existe; intercambialidade operacional SQLite/BigQuery **não está demonstrada** e apresenta incompatibilidades concretas. Não foram executados Terraform plan/apply ou migrações remotas.

## 7. Algoritmos e limites semânticos

- **Daily Readiness** (`ReadinessService`): sono e FC obrigatórios; pesos 0,40/0,30/0,20/0,10; stress ausente redistribui peso; score limitado a 0–100. Categorias reais: intense ≥80, moderate ≥60, light ≥40, rest abaixo. O README descreve limiares 50/30, divergentes do código. Atividade é consultada para a **mesma data**, embora comentário/produto mencionem dia anterior. Sono usa faixas de duração e média com device_score; FC usa faixas absolutas, sem baseline individual.
- **Normalização**: métricas sleep, steps, activity, heart_rate e stress implementam `from_raw/is_valid/to_dict`. Validam alguns limites, mas sono não valida soma das fases ou faixa de sleep_score; datas/tipos externos não têm contrato completo. UUID é gerado a cada normalização.
- **Google Fit**: quatro scopes de leitura (sono, atividade, FC e corpo), aggregate diário de passos/FC/atividade e sessions de sono. Erros HTTP aggregate/sessions são logados e viram coleção vazia, podendo aparentar sync completed sem dados. Refresh é usado na chamada, mas o token atualizado não é persistido nesse fluxo. Não há paginação de sessions demonstrada. Fases de sono são frações fixas 20%/55%/20%/5%; calorias são zero; múltiplas atividades são reduzidas à primeira; passos zero são omitidos. Esses valores não devem ser apresentados como medições completas do relógio.
- **Modalidades** (`ReadinessModalityService`): oito modalidades, score base com fallback 50, penalidade por fadiga e carga recente, status green≥70/yellow≥40/red. `hrv_available=False`; academia possui mapa vazio e usa base/carga. Histórico recente ancora em data atual do banco, não necessariamente na data pedida; cálculo histórico precisa revisão. GET pode retornar score mesmo sem dados suficientes, apesar de descrição de erro 422.
- **Músculos** (`MuscleRecoveryService`): 13 grupos; última sessão, intensidade 24/48/72h, ajuste de sono 1–1,5. Usa dias inteiros×24 para tempo decorrido; estimativa de término ancora em `now`, inclusive em consulta histórica. Score ≥90 pode gerar mensagem de “100% recuperados”. É estimativa, não medição fisiológica.
- **Social jetlag** (`AdvancedMetricsService`): janela 14 dias, mínimo 3 úteis/1 fim de semana. Usa `-duration/2` como proxy de ponto médio, sem horário real de dormir/acordar; portanto mede diferença de duração, não deslocamento circadiano comprovado.
- **Recovery curve**: janela 30 dias, readiness<45 e retorno≥60 em até 7 dias, mínimo 3 janelas recuperadas; média arredondada. Não é ML nem baseline personalizado aprendido; janelas podem sobrepor-se.
- **Signal quality**: ausência total de raw→20/incomplete; caso contrário penaliza fases ausentes, FC com variação<10 e muitos passos sem atividade. Não implementa detecção temporal completa de gaps/sensibilidade do sensor descrita no roadmap.
- **Feedback** é armazenamento, não calibração de pesos. Catálogo mobile contém afirmações mais fortes que essas heurísticas e descreve fases Google como classificadas por sensores; precisa revisão de conteúdo e incerteza.

## 8. Segurança, privacidade e riscos

Severidade representa impacto potencial no produto; não comprova exploração em produção. **Confirmado local** usa somente dados sintéticos; **estático** deriva do código; **externo desconhecido** depende da implantação. Nenhum token, segredo real ou dado de saúde pessoal foi incluído no documento.

| ID / severidade | Evidência e risco | Certeza / incerteza | Validação mínima / dependência |
|---|---|---|---|
| S01 **Crítica** | `router.py` + handlers aceitam user_id arbitrário com JWT válido: leitura/escrita de dados de terceiros, inclusive sync/conexão | Confirmado local para POST/GET feedback; padrão estático nos demais JWT-ID. Exposição em produção não testada | Testes A/B para todas as operações; derivar owner de sub, negar IDs diferentes antes de persistir; especificar papéis administrativos se necessários |
| S02 **Alta** | `settings.py` fornece defaults previsíveis de assinatura JWT/state, sem bloqueio para produção; Terraform não declara JWT_SECRET_KEY | Estático; valores reais implantados desconhecidos. JWT previsível em produção agravaria S01 | Validar fail-closed em produção e provisão de segredo; nunca copiar valor real para relatório |
| S03 **Alta** | `TokenRepository` guarda OAuth access/refresh em texto; backups/banco contêm acesso Google e saúde | Estático; criptografia da infraestrutura, IAM, backups e rotação reais desconhecidos | Especificar proteção em repouso, acesso mínimo, revogação e retenção; revisar IAM sem ler tokens |
| S04 **Alta** | `OAuthService` assina state com nonce, mas não expira/consome nonce nem vincula solicitante autenticado; redirect_uri livre no request; callback exige JWT | Estático e callback sem Bearer=403 confirmado; provider pode impor redirect registrado | Definir fluxo nativo/web, validade/uso único/vínculo do state e allowlist redirect; testar replay e usuário trocado localmente |
| S05 **Alta** | Persistência GCP/Cloud Run divergente (§6.1), sem migração/backup demonstrado | Incompatibilidades estáticas; possível perda de SQLite efêmero depende do deploy | Escolher store transacional durável e migrações, testar restauração e paridade antes de produção |
| S06 **Alta** | Sono estimado como medido, recomendações assertivas e jetlag sem horário real | Estático: adapter, catálogo e serviços | Revisão de evidência/linguagem/contraindicações; marcar inferido/ausente; não transformar heurística em alegação individual |
| S07 **Alta** | Login Android não popula identidade esperada; URL API pode selecionar produção em dev; refresh recursivo | Estático: login/register/api.ts. Falha do próprio `/auth/refresh` pode entrar na fila enquanto isRefreshing=true e bloquear resolução | Contrato unificado, teste de sessão expirada e falha de refresh, garantir ambiente local isolado antes de smoke Android |
| S08 **Alta** | `/dev/seed` sem autenticação reseta usuário demo e devolve credenciais/tokens | Guarda de environment existe; não é endpoint irrestrito em production se variável correta. Default é local | Testar 403 em production, política de demo isolada e ausência em release; não chamar produção |
| S09 **Média** | CORS `*` para origens/métodos/headers (`main.py`) | Estático; não significa que CORS por si só revele tokens ou permita cookies cross-site | Definir origens por ambiente; testar preflight e rejeição esperada |
| S10 **Média** | Web guarda tokens em localStorage; Android logout não revoga servidor e caches não têm limpeza central; user-profile query key não inclui usuário | Estático; SecureStore é positivo no nativo; nenhuma exploração XSS demonstrada | Modelo de sessão, troca de conta, expiração, limpeza de cache e armazenamento; testar dispositivo compartilhado |
| S11 **Média** | Validação limitada: email string, senha cliente 6/backend 8, datas/faixas/notas sem limites consistentes; `date=None` no WorkoutIn pode alcançar coluna NOT NULL | Estático; bug de data não exercitado neste inventário | Contratos tipados, datas inválidas/futuras/invertidas, campos extra e duração/volume máximos; testes negativos |
| S12 **Média** | Sync sem deduplicação/transação; indicadores persistidos podem ficar obsoletos; intervalos não limitados | Estático; concorrência/carga não testadas | Idempotência, correção de dados, recalcular derivados, concorrência e limites de request |
| S13 **Média** | Logs Google incluem corpo de erro; dead letters Beam podem incluir payload/normalizados | Estático; logs reais não acessados | Redação/níveis/retention, captura sintética sem payload sensível; política de observabilidade |
| S14 **Média** | Mensagem de `connect.tsx` diz que dados ficam no dispositivo, mas backend os persiste; não há exclusão/exportação/consentimento granular implementados | Estático; obrigações e políticas jurídicas externas desconhecidas | Definir consentimento, finalidade, retenção, exclusão/exportação e textos de privacidade antes de novas categorias de saúde |
| S15 **Média** | CI não cobre master/bootstrap; lint falha; versão Next e bibliotecas antigas; 84 outputs Next versionados | Confirmação estática e lint local. Não houve auditoria completa de CVEs | Alinhar gatilhos/branch protection em tarefa autorizada, corrigir baseline e auditar dependências sem atualização automática nesta fase |

Controles existentes: bcrypt com custo 12, JWT com algoritmo configurado e expiração de 60 min, refresh hash/expiração de 7 dias e rotação, comparação HMAC constante do state, proteção `/users/me`, placeholders de valores no SQLite e guarda do seed por ambiente. Esses controles não substituem autorização por objeto. Não foram encontrados rate limiting, recuperação de senha, verificação de email, trilha de auditoria de acesso, controle de consentimento ou política operacional de backup nos caminhos inspecionados; controles externos podem existir.

## 9. Testes, CI/CD e verificação executada

### 9.1 Suítes e automação existentes

`backend/tests/unit/domain/`: sono, FC e stress. `backend/tests/unit/services/`: health_data, readiness, modalidades e músculos. Repositórios/conector são em grande parte mockados; os testes não equivalem a integração com SQLite, OAuth ou BigQuery. Não há suíte versionada de rotas/auth/autorização, contratos entre clientes, workout/feedback/advanced, E2E Android/web ou pipeline completo localizada.

`backend/pytest.ini`: asyncio auto, testpaths tests, pythonpath ponto. `requirements.txt` inclui testes e Beam; `requirements-prod.txt` exclui ambos. Frontend web não declara scripts de teste/lint; Android oficial não declara suíte de testes, CI executa `tsc --noEmit`. O candidato legado declara `jest`, mas não contém testes localizados e não é o alvo oficial.

`ci.yml`: push e pull_request somente em `main` e `staging`; Python 3.12, backend pytest com cobertura mínima **30%**, Ruff sem versão fixada e TypeScript do oficial com Node 20 e `npm install --legacy-peer-deps`. Não roda build web, teste E2E ou validação infra. O README dos workflows fala em 80%, divergente do YAML.

`git ls-remote --symref origin HEAD` confirmou **master** como padrão. Assim, PR para master ou para a branch bootstrap não aciona esse CI por esses gatilhos. Não foi possível consultar branch protection/checks remotos pela API nesta execução.

`deploy.yml`: push em main/staging gera imagem, autentica com chave de service account, faz push Artifact Registry e deploy Cloud Run; main→production, staging→staging (ambos recebem ENVIRONMENT=production). A existência de GitHub environments não comprova revisão obrigatória. README descreve Workload Identity Federation, mas YAML usa `credentials_json` de GCP_SA_KEY. Não existe workflow EGM/scheduler, publicação Android ou frontend separado demonstrado pelos dois YAMLs. Nenhum deploy foi disparado.

### 9.2 Resultados desta execução

| Verificação | Comando / método | Resultado e limite |
|---|---|---|
| Branch padrão | `git ls-remote --symref origin HEAD` | `refs/heads/master`; default remoto em `328f2bc01eec2272376f95396472f36c42326fff` no momento da consulta |
| Testes backend | Em backend: `GOOGLE_CLIENT_ID=inventory-offline GOOGLE_CLIENT_SECRET=inventory-offline ../.venv/bin/pytest --cov=app --cov-report=term-missing --cov-fail-under=30 -p no:cacheprovider` | **66 passaram**, 33,59% de cobertura (1.801 statements, 1.196 não cobertos), exit 0; sem credenciais Google reais |
| TypeScript web | `web/node_modules/.bin/tsc --noEmit --incremental false --project web/tsconfig.json` | **Passou**, exit 0; não é teste de interface ou build nesta fase |
| Dependências Android | Cópia temporária oficial em `/tmp`, `npm ci --legacy-peer-deps` com lockfile copiado | **Passou**; sem alterar manifest/lockfile do checkout |
| TypeScript Android oficial | Na cópia temporária: `./node_modules/.bin/tsc --noEmit --incremental false` | **Passou**, exit 0; não verifica runtime/compatibilidade Expo ou APK |
| Lint backend | Em backend: `ruff check app/`, ferramenta isolada em `/tmp`, Ruff **0.17.3** | **Falhou**, exit 1, **102 ocorrências**; sem `--fix`; baseline inclui imports não usados, atribuições não usadas e anotações Optional. CI não fixa versão, contagem futura pode variar |
| Contratos API/isolamento | `FastAPI TestClient`, config e SQLite exclusivos em `/tmp`, dois usuários sintéticos, sem rede externa | Health 200; A escreveu feedback de B com 201 e leu com 200; `trained_today/workout_worth_it` não persistidos; callback sem Bearer 403; register não contém objeto `user` |
| Rotas efetivas | OpenAPI de `app.openapi()` no mesmo processo local | 24 operações inventariadas e flags security conferidas; não depende do YAML estático |
| Entrada CLI de pipeline | Na raiz: `.venv/bin/python pipelines/pipeline_raw_normalized_health.py --help`, variáveis Google locais fictícias | **Falhou**, exit 1, `ModuleNotFoundError: No module named app`; sys.path inclui raiz, mas o pacote app está em backend. Requer PYTHONPATH/empacotamento apropriado; não executou pipeline nem alterou dados |
| Diff de produto | `git status`, comparação com base | Apenas este documento deve compor o PR; código, testes, manifests e configuração preservados |

O teste local temporário apenas reproduz contratos/risco, não foi adicionado à suíte e não é correção de produto. Nenhuma credencial ou registro sintético individual está versionado. Um primeiro ensaio TestClient sob sandbox não completou; a execução isolada com permissão de runtime completou e gerou os resultados acima.

Não executados: build web nesta fase (o build relatado no onboarding anterior não é reclassificado como validação desta branch), navegador E2E, APK/emulador/dispositivo, Google OAuth real, Beam com dataset representativo, BigQuery/GCS/Dataflow, Terraform plan/apply, performance/concorrência, auditoria integral de vulnerabilidades e inspeção de produção. Isso limita qualquer declaração de prontidão para release.

## 10. Jejum proposto: pontos de integração e decisões, sem implementação

Não há timer, sessão persistida ou estados de jejum existentes. As sugestões abaixo são insumos para Elephant/Goldfish, não contratos aprovados nem autorização para criar endpoints/tabelas/telas.

| Tema | Estado atual e integração possível | Questão para especificação / validação futura |
|---|---|---|
| Início/fim | JWT, `/users/me`, repository/service e catálogo de widgets existem | Usar identidade do token; comandos idempotentes start/stop; impedir sessões ativas concorrentes, decidir duplicata/retry e comportamento multi-dispositivo |
| Estados | Nenhuma máquina de estados de jejum | Decidir se apenas ativo/concluído/cancelado ou também planejado/pausado; transições válidas, edição retroativa, limites e auditoria de correções |
| Persistência | 16 tabelas existentes, nenhuma sessão de jejum; SQLite/GCP divergentes | Definir ID, owner, timestamps de início/fim, objetivo opcional, status, created/updated e versão; unicidade de sessão ativa e migrações; não inserir sessão fictícia no modelo atual |
| Tempo e timezone | Backend mistura UTC e date.today; clientes usam toISOString/date local; perfil não guarda timezone | Timestamp absoluto UTC + timezone IANA/contexto local; duração não baseada no contador de tela; casos DST, viagem, mudança manual do relógio, app fechado/reaberto e offline |
| Sincronização/offline | React Query e stores, sem fila offline de comandos ou controle de conflito | Decidir fonte de verdade, reconciliação, ações pendentes, conflito entre dispositivos e política de perda de rede |
| Notificações Android | Sem expo-notifications, permissão, canais, token push ou worker | Escolher local vs push, permissão Android, opt-out, reagendar/cancelar ao parar/editar, reboot/doze/restrições de background; nenhuma garantia de precisão sem ensaio nativo |
| Dashboard/UX | Catálogo e WidgetId são pontos de extensão; seleção hoje não persistida | Definir se é tela/widget, histórico, acessibilidade, formatos de tempo, estados vazios/erro e persistência por usuário; preservar indicadores atuais |
| Conteúdo educativo | Há catálogo e insights assertivos, não mecanismo de evidência/versionamento de textos | Explicações com fonte, população/contexto, limites e variação individual; fases metabólicas como estimativas educativas, sem prometer cetose/autofagia por hora para a pessoa |
| Segurança/contraindicações | Saúde sensível, autorização por objeto precisa correção antes de expandir | Revisão de riscos para menores, gestação/lactação, transtornos alimentares, diabetes/medicações e sintomas; definir saída segura/interrupção sem estímulo a prolongar; revisão clínica/editorial do conteúdo |
| Relação com readiness | Nenhum dado permite inferir resposta individual ao jejum | Decidir explicitamente se ficará independente; não recalibrar score nem recomendar treino/jejum a partir de correlação não validada |
| Privacidade | Não há export/delete/retention operacional definido | Consentimento/finalidade, retenção e exclusão das novas sessões/notificações; minimizar conteúdo sensível em lockscreen/logs |

Plano mínimo futuro: testes de transição/idempotência/concorrência; autorização A/B; retomada após encerramento do processo; relógio/timezone/DST; perda de rede e reconciliação; migração/restore; testes nativos de permissões/notificações; revisão independente Goldfish de segurança e das alegações educativas. Nada disso foi implementado nesta Fase 0.

## 11. Decisões pendentes do proprietário

1. O PR de inventário deve integrar primeiro a branch bootstrap e depois master? Este inventário usa bootstrap para incluir o contrato solicitado sem misturar os commits bootstrap em um PR supostamente só deste documento.
2. Qual é o fluxo/release Android que deve ser preservado como comportamento de referência: dashboard novo, tabs internas, e modo demo? Quais telas web devem ganhar equivalentes oficiais? `mobile/` permanece preservado até decisão/evidência de uso.
3. Qual é o backend realmente usado em desenvolvimento e produção? Qual store transacional durável deve guardar identidade, tokens e futuras sessões? BigQuery será somente analítico? Quais requisitos de migração/backup/restore?
4. Quais políticas de autorização, compartilhamento/roles e acesso administrativo são desejadas? Ausência de autorização por owner não deve virar comportamento aceito por omissão.
5. Google Fit continua sendo a fonte pretendida? Confirmar disponibilidade/scopes/credenciais e estratégia Health Connect com documentação atual do fornecedor, sem supor acesso futuro a partir do código antigo.
6. Quais políticas de consentimento, retenção, exportação, exclusão e conteúdo médico/educativo serão adotadas? Quem aprova evidência e contraindicações?
7. Para jejum: público elegível, objetivo e estados, limites/duração, edição/cancelamento, offline/multi-dispositivo e precisão desejada de notificação. Nenhuma escolha está aprovada neste documento.
8. Quem aprova a especificação versionada e quem autoriza releases? Quais proteções/revisores precisam existir para master e production? EGM continua sem automação autônoma configurada/verificada.

## 12. Recomendações ordenadas por dependências

1. **Revisar este inventário e resolver decisões de escopo/ambiente/dados.** Preservar o Android oficial e os recursos existentes; registrar destino e contrato de cada integração antes de prometer paridade.
2. **Definir invariantes de segurança e privacidade.** Autorização por owner, segredos obrigatórios, demo isolada, consentimento/retention e conteúdo com incerteza são pré-requisitos para expandir dados de saúde.
3. **Unificar contratos e persistência.** Especificar identidade na autenticação, feedback, OAuth/redirects e status/disconnect; decidir store operacional, migrações e semântica de idempotência/tempo; resolver divergências SQLite/GCP.
4. **Estabelecer validação reproduzível.** Alinhar CI à branch master e política de PR em tarefa autorizada; fixar ferramentas e tratar baseline lint; acrescentar testes A/B, contratos e integrações sintéticas e depois smoke Android isolado de produção.
5. **Produzir Elephant.** Requisitos funcionais/não funcionais, dados/APIs, critérios de aceitação, preservação das features e proposta de jejum com decisões explícitas; não usar este inventário como especificação já aprovada.
6. **Executar Goldfish independente e registrar resoluções.** Confrontar modelo temporal, falhas/retries, privacidade e limites científicos; obter aprovação explícita da versão final antes de código funcional.
7. **Somente após aprovação, implementar em PRs rastreáveis.** Nenhum merge automático. Release/deploy depende de autorização separada do proprietário.

## 13. Reprodutibilidade da revisão

Para revisar: conferir a base acima, os arquivos/símbolos referenciados, a matriz contra `app.openapi()` e os resultados da seção 9. Em validações sintéticas, usar banco/config exclusivos fora do checkout e nunca domínio de produção. Não reutilizar tokens reais, não alterar lockfiles e não executar `--fix`, Terraform apply, EAS submit ou pipeline de deploy como parte do inventário. Somente `docs/egm/00-inventory.md` é a entrega versionada desta fase.
