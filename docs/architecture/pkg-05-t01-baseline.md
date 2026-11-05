# PKG-05 / T01 — Baseline de contratos e regressões

Data: 2026-11-05. Base: `master` **f52d1ed552705c3fe8ed70481ac152df4c169ad7**, com PKG-04/ADR integrados. Escopo exclusivo [T01](pkg-05-execution-plan.md). Nenhum arquivo `backend/app/`, regra de negócio, fórmula, infraestrutura, configuração de produção ou dependência alterado. Não inicia T02/T03 nem PostgreSQL. Custo adicional de nuvem: **US$0**; somente SQLite temporário, processo ASGI local e doubles de provider. GitHub é usado para versionamento/CI, não para acessar serviços de saúde/cloud.

## 1. Inventário anterior e lacunas

332 testes backend passaram antes das mudanças (cobertura app 81,58%). Contagem de casos pytest parametrizados, não de funções/assertions:

| Arquivo existente em backend/tests | Casos | Evidência e lacuna inicial |
| --- | ---: | --- |
| api/test_account_isolation.py | 123 | A/A, B/B, A/B, B/A, conta desconhecida, sem auth/token inválido, 15 operações com efeitos contados; faltavam snapshots completos de resposta e mais validações negativas |
| api/test_readiness_smoke.py | 1 | Smoke integrado com dezenas de assertions auth→ingestão→readiness; não é um caso individual por assertion, não congelava toda serialização |
| unit/auth/test_authorization.py | 13 | Política de autorização isolada |
| unit/auth/test_bigquery_binding.py | 42 | SDK isolado/SQL/tipos, sem motor/cloud; não comprova concorrência BigQuery |
| unit/auth/test_refresh_rotation.py | 9 | Concorrência SQLite, replay, logout/rollback, expiração e erro; preservar sem enfraquecimento |
| unit/config/test_security.py | 58 | Configuração fail-closed/segredos/seed/logs e negativos |
| unit/domain/test_heart_rate_metric.py | 5 | Métrica isolada |
| unit/domain/test_sleep_metric.py | 6 | Métrica isolada |
| unit/domain/test_stress_metric.py | 5 | Métrica isolada |
| unit/readiness/test_infrastructure_contracts.py | 20 | Schema candidato, HCL, erros/conflitos de SDK; relatório explicitamente bloqueia produção |
| unit/services/test_health_data_service.py | 3 | Provider/repositórios substituídos; faltava congelar respostas públicas completas |
| unit/services/test_muscle_recovery_service.py | 11 | Regras isoladas de recuperação/sono/sugestão |
| unit/services/test_readiness_modality_service.py | 19 | Fórmulas/resultados de modalidade isolados |
| unit/services/test_readiness_service.py | 17 | Contribuições, ausência e resultado; complementar com resultados fixos sem HTTP/persistência |
| **Total anterior** | **332** | OpenAPI comparado apenas ao Git base; não havia baseline versionado da estrutura completa SQLite/JSON real |

O OpenAPI atual contém **21 paths v1 / 23 operações** (mais `/health` fora de v1). As **23 operações v1 têm sucesso sem schema explícito de saída** no OpenAPI. T01 não adiciona response_models, pois isso poderia alterar serialização/comportamento; complementa o contrato declarativo com 25 snapshots de respostas reais. Não confundir esse conjunto de exemplos observados com todos os ramos possíveis ou com schemas formais completos de saída.

## 2. Entregas e cobertura nova

| Arquivos / grupo | Casos novos | Cobertura |
| --- | ---: | --- |
| tests/baseline/test_api.py | 44 | Cadastro/login/refresh/logout e erros; replay e revogação; A/B e sem auth/token inválido; campos ausentes/null; feedback/upsert; treino/exercícios/histórico/recuperação/sugestão; perfil; ingestão Google Fit sintética, normalização, readiness 86.7, histórico/advanced/modalidades e dados insuficientes |
| tests/baseline/test_contracts.py | 8 | OpenAPI vivo vs baseline, esquema das 16 tabelas, REPLACE, FK não ativada, rollback de um lote e ausência de transação entre chamadas |
| tests/unit/contracts/test_openapi_checker.py | 26 | 15 mutações declarativas, nulabilidade query não ignorada, editorial/ordem, campos/defaults chamados description preservados; 7 mutações de serialização real |
| tests/unit/contracts/test_business_baseline.py | 8 | Quatro resultados fixos de readiness/categorias, duas ausências essenciais e dois contratos de treino/falha; chamados diretamente, sem HTTP/banco/provider |
| **Total novo / total final** | **86 / 418** | Nenhum teste anterior removido, relaxado ou marcado xfail/skip |

`tests/baseline/fixtures/` contém **27 JSONs**: OpenAPI, estrutura SQLite e 25 respostas. Snapshot de sucesso/erro inclui status e corpo; preserva campos, estruturas, arrays, números, datas UTC, null, mensagens e tipos JSON. Comparação de JSON canônico diferencia `false` de `0` e `1.0` de `1` (igualdade Python simples não diferencia). As respostas de feedback demonstram a representação atual inteira de workout_worthwhile; não alterar para boolean silenciosamente numa migração. Tokens e state são substituídos por `<redacted>` somente no canal de teste/snapshot; não há credenciais reais nem JWTs versionados.

### Fixtures e isolamento

- `tests/baseline/conftest.py` cria diretório, config e SQLite temporários e um processo próprio. Nenhum import de aplicação no processo pytest é necessário para o cliente RPC de testes.
- `tests/baseline/worker.py` exige ENVIRONMENT=test e provider local antes de importar a aplicação. Usa os handlers, regras, JWT e SQLite reais; apenas relógio/IDs e fronteira Google Fit são determinísticos. Chaves sintéticas só existem no harness test; não são configuração da aplicação.
- Clock fixo 2026-01-15T12:00:00+00:00, UUIDs sequenciais e contas sintéticas A/B. O relógio do validador JWT é igualmente congelado, sem remover assinatura, expiração, subject, tipo ou política de autorização. Não se faz override de dependência de autenticação.
- Uma cópia privada SQLite em memória após cadastro A/B é restaurada antes de **cada caso**, com reset de contadores/estado do provider. Não depende da ordem dos testes. SQLite real continua verificando escrita/consulta e erros de integridade.
- `socket.connect` é bloqueado no processo durante as requisições; a fronteira OAuth/Fit é sintética. Os processos existentes mantêm seus guards e doubles. Nenhum endpoint HTTP de teste é adicionado à aplicação; CONNECT é comando interno do harness que executa os endpoints reais de autorização/callback.
- As regras puras adicionais usam objetos de serviço com dependências AsyncMock/Mock e nenhuma construção de factory/banco; não se introduz interface de persistência ou unidade de trabalho nova (T02).

## 3. Verificadores versionados

`backend/scripts/check_v1_contract.py` continua comparando o app contra um Git base e agora aceita `--snapshot`. Preserva endpoints/métodos, status declarados, referências/schemas, required/opcional, defaults, nullable, formatos, bounds e segurança. Remove apenas descriptions editoriais e ordena parâmetros; **não normaliza nulabilidade opcional para string**, como fazia antes. Mapa de propriedades/campos e valores literais/defaults não podem perder um campo chamado description. `assert_wire_equal` compara JSON observado sem ignorar campo algum.

O comparador é **conservador**, não um classificador completo de compatibilidade OpenAPI: adição ou reordenação semântica fora das normalizações também pode exigir revisão. Não autoatualiza snapshots, não suprime diferenças e não oferece modo de aprovação no CI. Baseline alterado exige PR que explique antes/depois e intenção. Schemas ausentes no app não são inventados pelo verificador; mutações de corpo/serialização dos ramos observados são detectadas pelos snapshots/testes reais.

`backend/scripts/sqlite_contract.py` extrai somente `_SCHEMA_SQL` por AST e executa DDL em `:memory:`. Registra SQL, colunas/tipos/nullable/default/PK, índices nomeados/implícitos, UNIQUE e FKs de todas as 16 tabelas, além do default de enforcement de FK. Não importa settings, não abre banco do desenvolvedor, `.env` ou credenciais. Não migra nem altera o banco da aplicação. O PRAGMA de FK é o padrão da conexão usado atualmente pelo adapter, não garantia de integridade efetiva.

### Estrutura e semânticas atuais a considerar na evolução

| Tabelas / grupo | Contrato registrado |
| --- | --- |
| users | PK user_id; UNIQUE email; perfil/nullable/defaults; REPLACE por email pode substituir identidade no adapter, apesar do precheck do cadastro |
| refresh_tokens | PK token_id; UNIQUE token_hash; revoked inteiro, expiry/created strings UTC; CAS/concurrency/replay/revoke existentes continuam cobertos |
| oauth_tokens | PK(user_id,provider); upsert de segredo/expiração; nenhum segredo real no baseline |
| raw_health_events | PK event_id; provider/tipo/payload/datas/pipeline_run obrigatórios |
| normalized_sleep, normalized_steps, normalized_activity, normalized_heart_rate, normalized_stress | PK record_id; source_event_id lógico, dados nullable e datas; sem UNIQUE diário genérico |
| dim_user | PK user_id; provider/created_at; relação lógica, não cadastro mestre |
| fact_daily_readiness | PK readiness_id; UNIQUE(user_id,date); contribuições/insight/data de cálculo |
| fact_readiness_by_modality | PK record_id; UNIQUE(user_id,date,modality); flags inteiras |
| wellness_feedback | PK feedback_id; UNIQUE(user_id,date); valores null e upsert observados |
| workout_history, workout_exercises | PKs; FK de exercícios declarada mas não ativada; parent/children persistidos em chamadas separadas |
| muscle_recovery | PK record_id; UNIQUE(user_id,date,muscle_group); referência lógica ao último treino; timestamps/null |

Preservar o comportamento legítimo na migração não significa perpetuar as falhas abaixo: uma mudança deliberada de integridade/API exige correção autorizada e revisão do baseline correspondente, com explicação. Não trocar REPLACE por UPSERT genérico sem discutir IDs/conflitos, nem presumir transação global porque um lote local faz rollback.

## 4. Falhas conhecidas e lacunas remanescentes

1. **Treino com date:null → HTTP 500**: schema aceita null/default, mas o handler transmite None ao service e SQLite exige date NOT NULL. Teste de caracterização passa ao observar a falha atual; isso **não aprova** esse comportamento para produto/produção. Corrigir em tarefa autorizada separada; não adulterar regra nesta T01. A omissão também produz esse default; o teste fixa o caso explícito null.
2. **Atomicidade parcial**: falha no segundo insert não desfaz primeiro commit; FK de exercício não é ativada. Testes documentam o risco, não uma garantia de segurança. Dado órfão só é criado em fixture descartável. Criação de unidade de trabalho/ajuste de integridade é T02+ e não começou.
3. **REPLACE destrutivo**: chaves naturais podem substituir IDs/linhas. Cadastro tem precheck, mas o adapter não representa uma política segura de concorrência de contas. Não transplantar sem revisão ao PostgreSQL.
4. **Saídas OpenAPI genéricas**: as 23 operações não possuem schemas de sucesso específicos; 25 snapshots cobrem os ramos exercitados, não todas as combinações. Faltam contrato formal de saída, fuzzing/propriedades, todos os erros de provider/dados extremos, estabilidade do catálogo completo e matriz exaustiva de formatos de datas. Essas lacunas estão registradas, não declaradas resolvidas.
5. **Sem GCP/PostgreSQL real**: SDK mocks não provam streaming/concorrência/constraints; SQL/paridade entre engines permanece para tarefas futuras. Nenhuma dependência PostgreSQL adicionada.
6. **Tempo/payload**: novas fixtures são determinísticas; testes anteriores preservados podem usar relógio/UUID real e fixtures próprias. A repetição em ordem inversa valida isolamento do conjunto novo de API, não prova determinismo universal de toda a aplicação.
7. **Infra não pronta**: baseline verde não resolve os bloqueios PKG-04, ADR/aprovações de arquitetura, backups, RPO/RTO ou autoriza produção. Os warnings de dependências já existentes não foram suprimidos.

## 5. Execução local e CI

Na raiz, usando o ambiente Python de desenvolvimento já instalado. Valores abaixo são **sintéticos de teste**, nunca configuração de produção:

```sh
cd backend
ENVIRONMENT=test GOOGLE_CLIENT_ID=synthetic GOOGLE_CLIENT_SECRET=synthetic ../.venv/bin/pytest
ENVIRONMENT=test GOOGLE_CLIENT_ID=synthetic GOOGLE_CLIENT_SECRET=synthetic ../.venv/bin/pytest tests/baseline tests/unit/contracts
cd ..
.venv/bin/python backend/scripts/check_v1_contract.py --base origin/master --snapshot backend/tests/baseline/fixtures/openapi-v1.json
.venv/bin/python backend/scripts/sqlite_contract.py
```

O último comando apenas emite o contrato SQLite, **não sobrescreve fixtures**. A captura inicial foi uma operação local deliberada do autor, seguida de revisão e testes normais que só leem o baseline; não há updater automático nos scripts versionados. Para mudança futura, explicar a alteração, capturar de forma controlada com dados sintéticos, revisar o diff e executar testes negativos/positivos. Não atualizar golden só para deixar CI verde.

Foi estendido apenas `.github/workflows/account-isolation.yml`: pytest já descobre a nova pasta; a etapa OpenAPI também verifica o snapshot; lint inclui scripts/testes novos. Nenhum workflow duplicado, dependência nova, serviço de banco, cloud, permissionamento ou etapa de deploy criada. Jobs Android/web continuam no fluxo existente.

### Resultados locais

- Antes: **332 passed**, cobertura backend **81,58%**.
- Depois: **418 passed (332 anteriores + 86 novos)**, cobertura backend **83,13%**, limiar existente 30% preservado.
- Snapshot OpenAPI + comparação origin/master: **passou**.
- Ruff com a mesma seleção/lista do CI e `git diff --check`: **passaram**.
- Os **44 casos novos de API** foram repetidos em ordem inversa com sucesso, validando reset/isolamento contra os mesmos snapshots.
- Nenhuma fórmula, implementação de repositório ou comportamento intencionalmente alterado; sem xfail/skip novo. Resultado do CI remoto é reportado por SHA no PR, sem presumir sucesso por testes locais.

Não se executou deploy, apply, migração, infraestrutura/cloud, API Google Fit, serviço pago, acesso a credenciais reais ou PostgreSQL. T02/T03 permanecem fora do escopo autorizado.
