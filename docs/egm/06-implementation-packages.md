# Vytal — pacotes pequenos para iniciar desenvolvimento

**Base de código/spec:** `edee1012053022d743e5b88c2de2845a6c4f16f6`. **Parecer associado:** [revalidação Goldfish](05-goldfish-v0.2-revalidation.md). **Q classificadas:** [decisões e engenharia](07-owner-decisions-and-engineering.md).

## 1. Resposta direta e condição de liberação

**Primeiro PR recomendado:** `fix(authz): enforce v1 account ownership with API regressions` — **PKG-01**. Corrigir o acesso entre contas existente e provar que ele foi negado antes de efeitos colaterais. Não começar por jejum, API v2 ou migração PostgreSQL.

**Podem receber aprovação delimitada agora:** PKG-00 a PKG-07, nos escopos restritos abaixo. São tecnicamente delimitáveis sem resolver todas as Q de produto. **Ainda não estão autorizados para execução por esta revisão.** Nenhuma alteração funcional foi feita; este documento não é aprovação do PO.

O contrato [AGENTS.md](../../AGENTS.md) exige aprovação explícita de especificação versionada antes de código funcional: “No product-code implementation before this gate.” Gate **G-A**: o PO precisa aprovar os requisitos/aceites do pacote como recorte versionado e registrar como isso satisfaz o gate. Se o processo exigir aprovação integral, o PO deve autorizar formalmente o recorte/ajuste de processo antes do código; o revisor não cria essa exceção. Merge/release permanecem gates separados. **Não há nenhuma Q de produto que, por si só, bloqueie todo e qualquer pacote abaixo; há esse gate formal comum.**

“Apto tecnicamente” significa objetivo/contrato observável já fechado para o recorte, testes factíveis e dependências explícitas. Não significa produção segura, feature completa, CI remoto verificado ou nova versão integral aprovada. Propostas técnicas novas precisam revisão no PR, mesmo sem serem escolhas de produto.

| Pacote | Prioridade | Situação técnica / autorização | Dependência real |
|---|---|---|---|
| PKG-01 | P0 — primeiro PR | Apto para aprovação delimitada; G-A pendente | Testes de API isolados; mínimo PKG-00 pode acompanhar o PR |
| PKG-00 | P0 — suporte ao primeiro PR | Apto para aprovação delimitada; G-A pendente | Permissões de CI/proteção de branch para merge, não para escrever testes |
| PKG-02 | P0 | Apto no recorte de rejeitar segredo ausente/default conhecido; G-A pendente | Sem escolher novo TTL/entropia/infraestrutura |
| PKG-03 | P1 | Apto para corrigir contrato Android atual; G-A pendente | Harness de teste cliente; não depende de Google login/perfil novo |
| PKG-04 | P1 | Apto para corrigir refresh cliente; G-A pendente | Harness de teste do cliente; PKG-03 recomendável, não requisito lógico |
| PKG-05 | P1 | Apto, predominantemente testes de contrato; aprovação do trabalho pendente | Fixture de auth/dados isolados reutilizável do PKG-01 |
| PKG-06 | P1 | Apto para retirar payload sensível dos logs; G-A pendente | Sem criar nova telemetria ou política de retenção |
| PKG-07 | P2 | Apto só como laboratório/UoW e CI PostgreSQL efêmero; aprovação pendente | Decisão PostgreSQL D12 já existe; não ativar provider runtime |
| PKG-08 | Depois de definição específica | **Bloqueado** como correção completa de feedback | Q-14 sobre perguntas/schema/nullability e persistência de trained_today |
| PKG-09 | Depois dos contratos/dados | **Bloqueado** como sessão v2/remote revoke runtime e migração operacional | Q-05/Q-06/Q-07/Q-12 e fronteira transacional/migração aprovadas |

Não há estimativa de esforço, prazo ou métrica de segurança inventada. Cada pacote pode ser PR separado; não juntar todos no primeiro.

## 2. PKG-01 — owner guard em todas as operações pessoais v1

**Objetivo:** impedir leitura/escrita/coleta de dados de B por token válido de A, sem alterar payload de sucesso, versões ou fórmulas. D10/D19; S01; SEC-01; T-01. Evidência: `router.py` aplica JWT, mas handlers recebem IDs livres; nesta revisão A escreveu feedback B com 201 e o leu com 200 em banco temporário.

**Escopo e arquivos:**
- `backend/app/auth/dependencies.py` e/ou helper pequeno de autorização dedicado: usar a identidade já validada por `get_current_user`, não confiar no corpo/path/query.
- Routers `backend/app/api/v1/{connect,health_data,readiness,modality_readiness,workouts,muscles,wellness_feedback}.py` para os pontos abaixo.
- `backend/app/services/oauth_service.py`: receber o usuário esperado e comparar com o usuário do state **depois de validar assinatura/formato e antes** de chamar connector/exchange/persistência. Comparar `token.user_id` só depois do retorno de handle_callback é tarde.
- Novos testes sob `backend/tests/` (sugestão `tests/api/test_user_ownership.py`, fixture de app/banco/usuários em diretório temporário). Mínimo de job de regressão PKG-00, se ainda ausente.

**15 operações do recorte, sem esquecer callbacks:**

| Vetor de identidade | Operações pessoais a proteger |
|---|---|
| Query | GET `/connect/{provider}/auth-url?user_id=...` |
| State validado | GET e POST `/connect/{provider}/callback` |
| Corpo | POST `/health-data/sync`, `/workouts`, `/wellness-feedback` |
| Path | GET `/health-data/{user_id}/summary`; `/readiness/{user_id}`, `/readiness/{user_id}/history`, `/readiness/{user_id}/advanced`; `/readiness/modalities/{user_id}`; `/workouts/{user_id}`; `/muscles/{user_id}/recovery`, `/muscles/{user_id}/suggestion`; `/wellness-feedback/{user_id}` |

**Contrato técnico recomendado para aprovação do pacote:** comparação exata do ID solicitado/extraído com o usuário autenticado; divergência retorna **404 genérico antes de chamar serviço/repositório/provider**, sem revelar existência de B. Não criar role admin ou exceção demo. Preservar os status atuais de token ausente/inválido e state malformado, evitando mudar 403/401/400 indiscriminadamente. Sucesso A/A mantém shape/status v1. `/users/me` continua derivando identidade do token e `/workouts/exercises/catalog` continua catálogo autenticado, não recurso pessoal com ID “exercises”. A escolha do 404 é recomendação técnica alinhada ao desenho v0.2, não nova política de produto já assinada.

**Fora do escopo:** callback público de navegador, OAuth v2, PKCE/expiração de state, Google login, novo JWT/sid, refresh atômico, PostgreSQL, CORS, dados históricos de timezone e qualquer alteração de fórmula. O callback v1 continua exigindo Bearer; não remover a dependência para “consertar o OAuth” nesse PR.

**Critérios de aceite/testes:**
1. A/A passa no contrato atual e A/B é negado nas 15 operações, com payloads sintaticamente válidos. Contar rotas reais, não só quantidade de funções de teste.
2. Além do HTTP de negação, spies/fixtures demonstram **zero consulta/escrita pessoal e zero chamada externa** para B; contagens e registros B permanecem iguais.
3. Callbacks com state B validamente assinado + Bearer A são negados antes de exchange/save/ensure_user; state adulterado continua rejeitado. Não usar apenas string inválida para testar autorização.
4. Um fluxo com autenticação real de duas contas sintéticas verifica ligação JWT→sub→guard, além de testes com dependência substituída. Tokens/chaves não são impressos.
5. Banco/config/app e singletons isolados desde a inicialização; nenhuma consulta a banco já existente, Fit, Garmin ou produção. Provar que a ordem de testes não reutiliza warehouse de outro fixture.
6. Regressões `/users/me`, catálogo, paths de readiness/modalities e respostas próprias passam; 66 testes atuais continuam passando. Testes novos falham no baseline vulnerável pelo comportamento esperado de segurança e passam com a correção; não comitar assertions invertidas ou xfail como “solução”.

**Dependências/bloqueadores:** nenhuma Q de jejum, TTL ou banco de produção. Aprovar G-A e a semântica de negação do pacote. CI mínimo precisa executar o novo conjunto no PR; se branch protection remota estiver inacessível, registrar limitação, não fingir check obrigatório.

**Regressão/limitações:** IDs MVP fixos que não coincidem com a sessão serão negados corretamente; não conceder bypass. Verificar efeitos OAuth antecipados e dependência FastAPI cacheada, sem presumir que JWT no router injeta owner no handler. Defaults de JWT e revogação continuam problemas separados: este PR melhora isolamento por identidade válida, não torna produção segura sozinho. Sem deploy automático autorizado.

## 3. PKG-00 — CI de regressão com fixture segura

**Objetivo/escopo:** fazer o PR de segurança realmente executar seus testes nas branches de revisão e em master, sem pipeline de deploy. OPS-01/NFR-07/D20. Pode ser pequeno pré-requisito ou job mínimo no PKG-01.

**Componentes:** `.github/workflows/ci.yml` ou novo workflow de regressão de segurança; `backend/tests/conftest.py`/fixtures; comandos pytest existentes. Proposta: evento pull_request abrangendo a base efetiva, permissões mínimas, credenciais sintéticas em job e config/SQLite temporários. Não depender de secrets de produção; não alterar `.github/workflows/deploy.yml`. Harness Android/web será introduzido no pacote cliente específico, sem escolher múltiplos frameworks no primeiro PR.

**Aceite/testes:** job descobre/executa os casos de PKG-01 com contagem/exit status; fixture não compartilha DB/singletons; testes não têm tráfego externo; PR para a base atual não fica sem job por filtros main/staging. Baseline lint falho deve continuar reportado separadamente: não desabilitar regra, reduzir threshold, usar continue-on-error para parecer aprovado nem corrigir as 102 ocorrências históricas registradas no inventário (não recontadas nesta revisão) como mudanças não relacionadas neste PR.

**Dependências/bloqueadores:** G-A/aprovação do trabalho; governança de required checks/branch protection Q-12 para merge, não escolha funcional. Se lint preexistente impedir merge, registrar bloqueio e tratar baseline em PR próprio; não chamar pipeline todo verde porque só o job novo passou.

**Regressão:** ampliar gatilho aumenta consumo e pode revelar falhas antigas; limitar instalação ao alvo do job e inspecionar ausência de triggers de release. Situação: **apto tecnicamente, aprovação pendente**.

## 4. PKG-02 — rejeitar segredos conhecidos de desenvolvimento em produção

**Objetivo:** impedir startup com secret_key/jwt_secret_key ausentes ou iguais aos defaults públicos conhecidos quando o ambiente está configurado como production. SEC-02/S02/D19.

**Arquivos:** `backend/app/config/settings.py`, novos testes de settings/startup; documentação de configuração estritamente necessária no PR futuro. Não mudar banco, Docker/Cloud Run, emitir segredo, consultar vault ou copiar credencial.

**Aceite/testes:** subprocess/fixture independente testa production com ausência/default→erro fechado, production com valores de teste não-default→passa essa validação, local/teste preserva o fluxo previsto; logs/erros não expõem valores. Não inventar mínimo de comprimento, entropia, TTL ou rotação: validação adicional precisa proposta técnica e aprovação específica.

**Dependência/bloqueio:** G-A, ambiente declarado confiável; classificação completa de ambientes/infraestrutura permanece OPS-02/Q-07/Q-12. O pacote não resolve operador marcando ambiente de produção incorretamente como local, nem configura produção por conta própria.

**Regressão:** configuração insegura antes tolerada passa a falhar — intencional; não realizar deploy surpresa. Situação: **apto no recorte delimitado**, sem declarar toda SEC-02 concluída.

## 5. PKG-03 — identidade Android no contrato v1 real

**Objetivo:** concluir login/cadastro com userId correto, sem esperar um `data.user` inexistente. FR-01/03, API-01/S07.

**Arquivos:** `mobile/vytal-app/app/login.tsx`, `app/register.tsx`, `src/store/authStore.ts`, tipo/helper de resposta v1 e testes de cliente. Evidência: `AuthService.login/register` retorna user_id/email/name no nível raiz; `setTokens` atualmente marca authenticated antes de haver userId.

**Escopo/aceite:** ler o contrato plano atual, efetuar transição de sessão com identidade/tokens coerentes e limpar identidade anterior; hidratar perfil completo via `/users/me` sem inventar campo recebido. Falha de perfil opcional não converte identidade de outra conta em atual nem exige novo envelope no backend. Não implementar Google login, biometria ou múltiplos objetivos. Pode alinhar texto/validação de senha do cliente aos **8 já exigidos pelo backend v1**, sem escolher uma política futura de senha para Q-14.

**Testes:** mocks do HTTP no boundary real do cliente/store, login/cadastro plano, resposta incompleta, falha de `/users/me`, reidratação/troca de conta e 7 versus 8 caracteres conforme baseline atual; TypeScript e smoke de navegação oficial. Harness mínimo é definição de engenharia revisada, não decisão de produto; dependências dev devem ser explícitas/lockadas, não ignorar testes porque hoje só existe tsc.

**Dependências:** G-A; PKG-01 antes de chamar ambiente compartilhado real. **Riscos:** AuthGate/SecureStore assíncronos, perfil antigo e modo MVP sem token. Não usar produção para testar. Situação: **apto tecnicamente**.

## 6. PKG-04 — encerrar o ciclo recursivo de refresh no cliente

**Objetivo:** nenhuma promessa presa porque `/auth/refresh` entrou na própria fila. FR-02/SEC-07/S07; não é rotação atômica servidor de GF-09.

**Arquivos:** `mobile/vytal-app/src/services/api.ts`, eventual factory pequena de cliente testável, testes de interceptor/store. Hoje o mesmo `api.post('/auth/refresh')` cai no interceptor enquanto isRefreshing=true.

**Aceite:** refresh não se enfileira em refresh; 401 de login/cadastro não dispara renovação de sessão anterior; pendências terminam com sucesso ou erro finito; finally limpa estado e fila. Um refresh válido atende concorrentes uma vez; refresh rejeitado/network error encerra todos e aplica logout local consistente. Não alterar TTL, política de replay servidor, URL de produção ou contrato de tokens.

**Testes:** adapter HTTP controlado com duas requisições 401 simultâneas, refresh 200/401/timeout, ausência de refresh token e 401 no login; confirmar número de chamadas, promises resolvidas/rejeitadas e ausência de loop. Limite do teste é mecanismo de detecção do deadlock, não nova tolerância operacional de produto.

**Dependências:** G-A/harness do cliente. **Riscos:** interceptar endpoints públicos indevidamente, reenviar POST que já ocorreu, duplicar retries, limpar conta incorreta. Restringir retry ao fluxo atual explicitamente e não implementar fila offline nova. Situação: **apto tecnicamente**.

## 7. PKG-05 — regressões dos contratos v1 preservados

**Objetivo:** proteger agora arrays, identidade plana, data final inclusiva e respostas próprias, sem começar API v2. GF-11/12, INT-01/FR-12.

**Componentes:** novos testes API/contrato em backend; fixtures e consumidores/testes de web/Android quando aplicável. `ReadinessRepository.get_history` usa BETWEEN e retorna apenas date/score/category; cliente oficial tipa mais campos do que recebe.

**Aceite/testes:** inserir fatos sintéticos nos dias de início/fim, consultar autenticado e receber array com ambos os dias e ordenação atual; identidade auth plana; tabela verdade sono/FC; rotas de modalidades sem captura incorreta por genéricos; nenhuma coluna/envelope/fuso é alterado. Capturar comportamento legítimo, não congelar vazamento ou alegação falsa como golden snapshot. Resultado não depende de Google ou dados reais.

**Dependências:** G-A do trabalho; fixtures PKG-01. **Riscos:** chamar caracterização de “novo contrato aprovado” ou introduzir timezone local para fazer teste passar. Q-09 não bloqueia preservar a semântica v1 existente. Situação: **apto, sobretudo testes**, sem autorização de alteração funcional incidental.

## 8. PKG-06 — sanitização dos logs existentes

**Objetivo:** retirar tokens/corpos de resposta/dados de saúde dos logs de erro/dead letter, mantendo diagnóstico técnico mínimo. S13/SEC-03/NFR-06; não criar plataforma de auditoria nova.

**Arquivos:** `backend/app/adapters/connectors/google_fit.py` (warnings com resp.text), `pipelines/pipeline_raw_normalized_health.py`, `pipeline_normalized_readiness_score.py`, `pipelines/transforms/sanitize.py` e `readiness.py` onde payload/exception podem ser logados. Pode dividir em PR conector e PR pipeline se o diff crescer.

**Aceite/testes:** mensagens usam etapa/status/tipo de erro e correlação técnica minimizada, sem raw_payload/nota/token/score/data individual por default; exceção não reintroduz body. Canários sintéticos em respostas/erros/dead letters não aparecem no capture de logs. Não alterar retorno de ingestão, runners, scoring ou sink de dados para “consertar o teste”.

**Dependências:** G-A; nenhuma decisão sobre prazo de retenção é necessária para parar de imprimir um token. Q-06/Q-15 continuam necessários para auditoria/telemetria futura. **Riscos:** perder diagnóstico útil ou modificar fluxo de exceção; preservar nível/etapa/status sem logar payload. Situação: **apto tecnicamente**.

## 9. PKG-07 — laboratório transacional PostgreSQL, sem ativação runtime

**Objetivo:** preparar fixture de PostgreSQL efêmero e prova pequena de unidade de trabalho (UoW), pois D12 já escolheu o banco operacional. Não fingir que `WarehouseProvider.insert/query` atual tem transação multioperação.

**Componentes propostos:** dependências/harness de teste separados, fixture PostgreSQL em CI/local isolado, módulo UoW não conectado ao factory atual e testes de commit/rollback/locks básicos. Engenharia pode propor driver com suporte transacional explícito e versão pinada. Tabelas-probe só do teste; nenhum schema/dado da aplicação migrado ou endpoint novo selecionando PostgreSQL.

**Aceite/testes:** duas conexões reais exercitam commit/rollback e CAS/constraint em fixtures mínimas; erro na segunda escrita não deixa a primeira confirmada; conexão é fechada; instalação reproduzível e isolada; nenhuma rota/runtime seleciona o novo módulo. SQLite não substitui esse teste. Não implementar ON CONFLICT genérico assumindo chaves naturais desconhecidas, nem declarar compatibilidade completa de todas as 16 tabelas.

**Dependências:** aprovação do recorte técnico e CI PKG-00; engine/driver/versionamento são propostas de engenharia, não dependem de escolher RPO/custos de produção. **Riscos:** laboratório virar migração disfarçada ou adapter incompleto anunciado pronto. Produção/topologia/restore e família de tokens permanecem bloqueados Q-07/Q-05/Q-12. Situação: **apto apenas no escopo de preparação isolada**.

## 10. PKG-08 — feedback completo (ainda bloqueado)

**Objetivo/arquivos:** fazer formulário oficial, tipos/hook e `wellness_feedback.py`/repo/schema preservarem todas as respostas, incluindo significado de trained_today, worthwhile e timestamps. FR-11/API-08/Q-14.

**Bloqueio:** o cliente envia trained_today/workout_worth_it, backend aceita workout_worthwhile/workout_readiness. Equivalência do boolean de “valeu a pena” é clara como correção estreita, mas não define onde guardar trained_today nem autoriza remover pergunta para esconder perda. Correção integral não está liberada só por existir formulário.

**Aceite/testes necessários:** dicionário de perguntas e mapeamento aprovados; round-trip true/false/null/ausente, revisão diária e data; sem campo ignorado silenciosamente e sem afirmar “tudo salvo” quando parte é descartada. Se precisar coluna, plano de migration/compatibilidade separado e autorizado.

**Regressão/dependências:** versões antigas e schema local existente, Q-14 e base de migração. Um sub-PR somente do alias boolean pode ser proposto, mas precisa aceite delimitado e não fecha FR-11; não é o primeiro pacote recomendado. Situação: **depende de definição/aprovação específica**.

## 11. PKG-09 — sessões v2/refresh servidor/ativação PostgreSQL (ainda bloqueado)

**Objetivo/arquivos futuros:** auth sessions/devices, refresh families com parent único, claims/sid, repos/UoW, factory/config e migrations, endpoints de revogação. FR-22/SEC-07/GF-08/09/DAT-01. Não incluir tudo num PR gigante; este rótulo identifica a fronteira a decompor depois das decisões.

**O que está fechado:** nenhuma conta acessa outra; revogação efetiva no backend; no máximo um sucessor por parent; PostgreSQL transacional. Pode preparar testes/experimento no PKG-07.

**O que bloqueia runtime:** Q-05 (sessão/reset/reuso), Q-06 (tokens/keys/retention), Q-07 (migração/recuperação), Q-12 (tokens/clientes v1 e rollout). O código atual não tem sid/family/parent nem transação compartilhada, logo não basta adicionar um lock em uma função.

**Aceite/testes necessários:** duas instâncias, refresh×refresh/revoke, retry após resposta perdida, account deletion, compatibilidade e migration/restore; prova de que access antigo realmente perde autorização segundo contrato aprovado. **Riscos:** logout falso, perda de sessões e tokens órfãos, downgrade inseguro. Situação: **bloqueado para implementação runtime completa; não liberado pela resolução documental de GF-09**.

## 12. Funcionalidades que não devem iniciar como produto completo

| Funcionalidade | Bloqueio aplicável / por que não é o primeiro PR |
|---|---|
| Jejum offline/edições/notas e API v2 correspondente | RV-01/RV-02 e Q-02/Q-03/Q-04/Q-05/Q-06; conteúdo/eligibilidade Q-01. Não programar protocolo final com defaults inventados |
| Exclusão integral/portabilidade/restore | Q-06/Q-07 e GF-15/16, sem promessa de apagar backups e sem export UI inicial |
| Garmin/importação/dedup entre fontes | Verificação oficial de acesso e Q-10; não criar integração não oficial ou fingir provider available |
| Correlações/fórmula nova/sugestões e novo calendário | Q-09 e revisão adequada Q-01; testes da baseline podem começar sem mudar método |
| Notificações completas | Q-11, privacidade/conteúdo Q-06/Q-01; canais já escolhidos não escolhem gatilhos/expiry/transport Android |
| Perfil ampliado e estatísticas definitivas | Q-14/Q-09 para schemas/unidades/semântica; não impede reparar login plano existente |
| Produção/migração GCP | Q-07/Q-08/Q-12, testes críticos D19/D20 e autorização separada; nenhum pacote acima recebe deploy por esta revisão |

## 13. Primeiro PR: definição pronta para aprovação do recorte

**Título proposto:** `fix(authz): enforce v1 account ownership with API regressions`.

**Conteúdo permitido do PKG-01:** helper de owner, integração nos 15 handlers pessoais, validação do owner do state antes do exchange/persist e testes isolados A/A/A-B/sem token/efeitos colaterais. Mínimo de CI de regressão pode acompanhá-lo se necessário. Sem v2, banco novo, TTL, segredo de produção, fórmula, feature de jejum ou flexibilização de callback público.

**Definição de pronto para revisão de código:** inventário de rotas cobertas, repro vulnerável transformada em negação sem efeitos, casos próprios preservados, callback sem gravação antecipada, suíte atual+novos casos executados com relatório e diff contido. Nenhuma assertion que aceite 201/200 no caso A→B. Falhas preexistentes de lint/CI declaradas, não ocultadas. Merge/release não automáticos.

**Registro de aprovação sugerido ao PO (ainda não concedido):** aprovar explicitamente o PKG-01 e seu recorte SEC-01/D10/D19 versionados neste backlog, incluindo testes e semântica de negação, como gate para um PR de implementação separado; esclarecer que isso não aprova o Elephant inteiro, a implantação ou os demais pacotes. Registrar a conformidade desse recorte com AGENTS antes do código, em vez de presumir autorização pela existência deste texto.

Depois desse aceite, há caminho concreto para código sem outra rodada genérica: PKG-01 → PKG-02, e PKG-03/04/05/06 conforme dependências; PKG-07 prepara somente laboratório. A aprovação integral permanece bloqueada pelos achados aplicáveis da revalidação.
