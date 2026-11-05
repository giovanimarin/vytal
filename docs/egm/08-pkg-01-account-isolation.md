# PKG-01 — isolamento de contas v1: implementação para revisão

## Autorização e rastreabilidade

O Product Owner autorizou explicitamente, nesta tarefa, apenas PKG-01: correção do isolamento das APIs v1 e regressões automatizadas. O recorte corresponde ao backlog `06-implementation-packages.md` no commit `f300ebe6082043d7e7a29b2f8ce16816a99a9760`, D10/D19, S01, SEC-01 e T-01. Esta autorização delimitada satisfaz o gate de implementação somente deste pacote; não aprova integralmente o Elephant v0.2 nem os outros pacotes. Branch: `fix/pkg-01-account-isolation`, derivada desse commit. Merge, migração e deploy não realizados nem autorizados por esta entrega.

## Correção e operações verificadas

A política pura `app/auth/authorization.py` compara exatamente o identificador solicitado com o `sub` autenticado e retorna exclusivamente a identidade autenticada. A dependência de autorização atende path/query; handlers de corpos e o serviço OAuth usam a mesma política. O mapeamento HTTP central retorna `404 {"detail":"Not found"}` sem identificadores. Não há consulta para descobrir se a outra conta existe. Assinatura/tipo/expiração do JWT continuam validados pelo mecanismo existente; claims de identidade ausentes, vazios ou de tipo inválido agora falham com 401.

Todas as rotas abaixo têm prefixo `/api/v1`:

| Origem do identificador | Operações corrigidas |
|---|---|
| Query | GET `/connect/{provider}/auth-url` |
| State assinado | GET e POST `/connect/{provider}/callback` |
| Corpo | POST `/health-data/sync`, `/workouts`, `/wellness-feedback` |
| Path | GET `/health-data/{user_id}/summary` |
| Path | GET `/readiness/{user_id}`, `/readiness/{user_id}/history`, `/readiness/{user_id}/advanced`, `/readiness/modalities/{user_id}` |
| Path | GET `/workouts/{user_id}` |
| Path | GET `/muscles/{user_id}/recovery`, `/muscles/{user_id}/suggestion` |
| Path | GET `/wellness-feedback/{user_id}` |

São 15 operações. No OAuth, primeiro se valida formato/HMAC de state, depois sua conta contra a identidade autenticada, antes de obter connector, trocar código, salvar token ou assegurar usuário. `expected_user_id` passa a ser argumento obrigatório keyword-only de `OAuthService.handle_callback`; seus dois chamadores foram atualizados.

GET/PATCH `/users/me` já derivavam a conta do token: seus controles permanecem e recebem regressões com identidade manipulada no corpo/query. O catálogo de exercícios continua autenticado e acessível. Não há atualização/exclusão de recursos pessoais por ID nas demais rotas v1 montadas; PATCH de perfil e o upsert de feedback estão cobertos. Login/cadastro e refresh/logout recebem credenciais, não seletores de conta. O arquivo `api/v1/advanced_metrics.py` não é montado: o endpoint efetivo de métricas avançadas está em `readiness.py`, protegido neste pacote.

## Evidência de testes

1. Antes de editar código funcional, a primeira matriz de API estabilizada apresentou **45 falhas e 62 aprovações**: A→B, B→A e A→conta inexistente em cada uma das 15 operações. Feedback reproduziu POST 201 e GET 200 indevidos; callbacks também aceitavam state válido de outra conta. As assertions exigiam negação, sem xfail ou inversão para aceitar o defeito.
2. Após a correção, esses **107 cenários passaram**. A suíte foi ampliada com dados próprios não vazios, manipulação de perfil, catálogo e tokens inválidos.
3. Resultado final: **202 testes passaram**, sendo **66 existentes**, **123 de API** e **13 unitários da política pura**. Nenhum teste existente foi enfraquecido.
4. A API é exercitada com TestClient, cadastro real de duas contas, JWTs efetivamente assinados e SQLite efêmero. Apenas o provedor externo é sintético. Tokens expirados, assinatura incorreta, tipo refresh, sub vazio e email ausente/vazio são rejeitados. Não se substitui a dependência de autenticação.
5. As negações verificam zero chamadas a query/insert/provider e digest SQLite inalterado, inclusive para contas inexistentes. O processo ASGI separado recebe configuração, banco e chaves aleatórias antes de importar singletons, evitando interferência com a suíte existente. HTTP externo é bloqueado no worker; nenhum Fit/Garmin/produção é acessado. Credenciais sintéticas ficam ocultas no repr das fixtures.

Comando equivalente ao novo job CI, executado localmente em `backend/`:

```sh
ENVIRONMENT=local GOOGLE_CLIENT_ID=synthetic GOOGLE_CLIENT_SECRET=synthetic-ci \
  ../.venv/bin/pytest -q --junitxml=/tmp/pkg01-results.xml
```

Resultado: **202 passed**. O aviso existente de `asyncio_default_fixture_loop_scope` não foi alterado neste pacote. O workflow `account-isolation.yml` executa toda a suíte em PRs, em push desta branch e em master, com permissões de leitura e artefato JUnit; não aciona deploy. Execução remota/check obrigatório depende da configuração e acesso ao GitHub e não é declarada verificada por este resultado local.

OpenAPI comparado com o commit-base: **idêntico**, normalizando apenas a ordem dos parâmetros. `git diff --check` passou. Ruff: todos os arquivos novos de Python passaram; lint completo da aplicação passou de **102 para 98 diagnósticos preexistentes**, sem diagnósticos novos (comparação por arquivo, regra e mensagem). Não se alteraram regras nem se suprimiram falhas do CI existente.

## Compatibilidade e riscos residuais

- Mantidos caminhos, corpos públicos, respostas próprias e códigos existentes de ausência de Bearer (403), JWT inválido (401) e state inválido (400). Identificadores divergentes passam a retornar 404 genérico intencionalmente. Clientes com IDs fixos ou IDs de outra sessão devem usar a conta autenticada; não recebem bypass.
- Sem alterações em persistência, infraestrutura, fórmulas, Android ou web. Serviços internos continuam aceitando IDs explícitos; a fronteira HTTP e o OAuth são responsáveis pela autorização deste recorte. Novas rotas pessoais exigirão o mesmo guard.
- Secrets default, revogação de access JWT, refresh concorrente, CORS e fluxo OAuth de navegador continuam itens separados. O callback v1 ainda requer Bearer. Este pacote não declara produção segura por si só.
- `/dev/seed` permanece com o bloqueio de ambiente existente, sem ampliação ou bypass; não deve ser exposto em ambiente compartilhado configurado como desenvolvimento. Nenhum teste deste pacote usa essa rota.
- SQLite local não comprova comportamento transacional de PostgreSQL/GCP; não houve migração nem teste contra produção. A nova revisão/PR deve avaliar as alterações antes de merge.
