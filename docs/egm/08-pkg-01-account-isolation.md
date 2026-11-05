# PKG-01 — isolamento v1 e compatibilidade Android para revisão

## Escopo, autorização e base limpa

O Product Owner autorizou explicitamente o isolamento v1 e, nesta conclusão, a correção da identidade autenticada no Android, testes, builds, revisão Goldfish e PR draft contra master. Não há aprovação integral do Elephant nem autorização de merge/deploy.

Base: `master` em `328f2bc01eec2272376f95396472f36c42326fff`. Branch: `fix/pkg-01-account-isolation-clean`. Apenas o commit funcional `6f40ccbc814c648c2bba573cd477812886b6988a` foi aplicado por cherry-pick, como `3f678a7`; a compatibilidade Android/validação fica em commit adicional. As branches anteriores e PR #8 são preservados. Não foram trazidos os 13 commits e 14 arquivos de documentação/governança que inflavam o PR #8. Este arquivo é a evidência específica do pacote, já incluída no commit funcional, atualizada com os resultados finais.

Fontes mantidas nas branches originais: [backlog versionado](https://github.com/giovanimarin/vytal/blob/f300ebe6082043d7e7a29b2f8ce16816a99a9760/docs/egm/06-implementation-packages.md) e seus requisitos D10/D19, S01, SEC-01/T-01. Referenciá-los não equivale a aprovar ou incorporar toda a especificação em master.

## Backend: 15 operações

Política pura `auth/authorization.py`: comparação exata; retorna apenas a identidade autenticada. `auth/dependencies.py` valida claims obrigatórios e aplica a política a path/query. Handlers de corpo e OAuth usam a mesma política. Divergência: `404 {"detail":"Not found"}` antes de dados pessoais/efeito externo, sem consultar a existência de outra conta.

Todas as rotas têm prefixo `/api/v1`:

| Identidade solicitada | Operações protegidas |
|---|---|
| Query | GET `/connect/{provider}/auth-url` |
| State assinado | GET e POST `/connect/{provider}/callback` |
| Corpo | POST `/health-data/sync`, `/workouts`, `/wellness-feedback` |
| Path | GET `/health-data/{user_id}/summary` |
| Path | GET `/readiness/{user_id}`, `/readiness/{user_id}/history`, `/readiness/{user_id}/advanced`, `/readiness/modalities/{user_id}` |
| Path | GET `/workouts/{user_id}` |
| Path | GET `/muscles/{user_id}/recovery`, `/muscles/{user_id}/suggestion` |
| Path | GET `/wellness-feedback/{user_id}` |

OAuth: validar HMAC/formato de state → comparar conta → connector/exchange/save/ensure_user. `expected_user_id` obrigatório no serviço, fornecido pelos dois handlers. GET/PATCH `/users/me` continua derivando identidade do token; catálogo continua autenticado. Não há PUT/DELETE pessoal por ID nessas rotas montadas. `advanced_metrics.py` duplicado não é montado; a rota efetiva protegida está em `readiness.py`.

Mantidos paths, payloads, respostas próprias e códigos: Bearer ausente 403, JWT inválido 401 e state inválido 400. IDs divergentes passam intencionalmente a 404. Correções de lint nos arquivos do pacote tornam explícito `str | None` para query opcional já aceita pelo runtime, modernizam anotações/imports e especificam encadeamento de exceções. Não se alteram fórmulas, repositórios, esquema do banco ou infraestrutura. OpenAPI preserva interfaces, security e respostas; comparação normaliza apenas ordem, descrição editorial e nulabilidade explícita desses parâmetros opcionais, nunca identificadores obrigatórios ou corpos.

## Android oficial: identidade, sessão e compatibilidade

- Login e cadastro usam o contrato plano real v1 (`user_id/email/name/access_token/refresh_token`), validam campos obrigatórios e publicam perfil/credenciais juntos. Não esperam `data.user`. Cadastro usa o mínimo de oito caracteres já exigido pelo backend.
- As telas de conexão usam `getHealthAuthUrl`, com ID real da sessão e Bearer. Removidos ID `user-mvp-1`, setters arbitrários de identidade/autenticação e botões que simulavam login. Nenhum bypass ou role especial foi acrescentado. A tela antiga abre o navegador pela API Expo, em vez de `window.open` inexistente no Android.
- Uma gravação SecureStore armazena o registro completo da sessão, evitando pares de tokens/perfil parcialmente atualizados. Escritas são serializadas; logout e mudanças de sessão invalidam resultados atrasados. Falha de armazenamento não publica nova identidade.
- Migração local lê os tokens antigos e obtém a identidade por `/users/me`, ignorando perfil legado potencialmente desatualizado. O mesmo endpoint revalida a restauração antes de marcar a sessão autenticada. Sem validação disponível, permanece desautenticado; não se presume identidade a partir de dados locais. Isto exige rede na restauração; não é uma implementação de modo offline.
- As três chaves antigas são removidas após persistência do registro novo. Downgrade para cliente antigo pode exigir novo login; a API pública não mudou. Não há migração de banco/infraestrutura.
- Cache de saúde/perfil é limpo ao trocar conta ou sair; queries de perfil incluem userId. Respostas HTTP/perfil antigas não são entregues à nova conta. 401 de login/register/refresh não inicia refresh recursivo; refresh concorrente é compartilhado e não sobrescreve sessão nova. São correções necessárias às chamadas autenticadas, sem introduzir sid, nova família de refresh ou política backend de revogação.
- Web mantém código funcional intacto: usa resposta plana, ID real e Bearer. Build/typecheck foram executados; os artefatos gerados não integram o diff.

## Validação final e contraprovas

| Verificação | Resultado |
|---|---|
| Backend: unitários e APIs reais/JWT/SQLite temporário | **202 passaram**: 66 existentes + 13 da política + 123 API |
| Matriz v1 | A/A e B/B nas 15 operações; A/B, B/A e A/inexistente: 45 negações genéricas, zero query/insert/provider e digest SQLite inalterado |
| Contraprova independente anterior em master | Os mesmos **45 falharam**, reproduzindo inclusive feedback POST 201/GET 200 indevidos |
| Contraprova Goldfish repetida na versão final | Os **45 falharam** ao substituir a política por retorno irrestrito do requested_id somente em cópia temporária |
| Cliente Android — regressões reais dos serviços/store/interceptors | **22 passaram**: login, cadastro, chamadas próprias, rejeições, restauração/legado, cache, logout e concorrência/falha de refresh/storage |
| Cliente Android + FastAPI real | **1 integração passou**: login A/B, cadastro C, identidade/Bearer reais, chamadas próprias e tentativas de ler/gravar A com sessão B |
| Ruff — arquivos Python do pacote e script de contrato | Passou com regras explícitas iguais às configuradas no novo job |
| ESLint — arquivos Android/testes alterados | Passou |
| TypeScript Android e web | Passou |
| Expo export Android | Bundle Hermes de produção gerado; não é APK/AAB assinado nem teste em emulador |
| Next.js build web | Build de produção passou, incluindo typecheck e prerenderização |
| OpenAPI contra master | Compatível nos critérios descritos acima |
| `git diff --check` | Passou |

Os 66 testes antigos não foram enfraquecidos. Os testes usam dados sintéticos e armazenamento efêmero; não acessam produção ou Google Fit/Garmin reais. O cliente da integração usa os mesmos módulos de produção, adaptando apenas transporte ASGI e SecureStore nativo. Não há override de autenticação no backend. Nenhuma credencial real foi usada ou versionada.

Comandos reproduzíveis:

```sh
# Na raiz, com dependências Python/Node instaladas:
GOOGLE_CLIENT_ID=synthetic GOOGLE_CLIENT_SECRET=synthetic \
  .venv/bin/pytest backend/tests --cov=backend/app --cov-report=term --cov-fail-under=30
.venv/bin/python backend/scripts/check_v1_contract.py --base origin/master
npm test --prefix mobile/vytal-app
VYTAL_PYTHON="$PWD/.venv/bin/python" npm run test:api --prefix mobile/vytal-app
npm run lint:pkg01 --prefix mobile/vytal-app
npm run typecheck --prefix mobile/vytal-app
CI=1 EXPO_NO_TELEMETRY=1 npm run build:android --prefix mobile/vytal-app
# Em web/: npx tsc --noEmit --incremental false; npm run build
```

## Revisão final Goldfish

| Tema | Evidência / avaliação |
|---|---|
| Escopo acumulado do PR #8 | Resolvido na branch nova: base master + cherry-pick funcional + correções autorizadas; nenhum documento EGM ancestral adicional |
| Autorização antes de efeitos | 15 operações revisadas no código; spies/digest e contraprova da política confirmam o contrato |
| Identidade Android incorreta | Corrigida: resposta plana, sessão completa e conexão usando conta real; integração real passa |
| Perfil/cache de outra conta | Corrigidos: consulta vinculada ao userId, cache limpo e rejeição de respostas atrasadas; regressões passam |
| Refresh/login travado e troca de sessão | Corrigidos no cliente: refresh limitado, concorrente e vinculado à sessão original; regressões passam |
| Contrato v1 / usuários legítimos | Fluxos próprios passam; inputs/security/respostas preservados; ID divergente nunca é compatibilizado por bypass |
| Gates de CI | Workflow configurado com backend/API/OpenAPI/lint, cliente/integração/Android e build web. Resultado remoto precisa ser comprovado no SHA final; teste local não significa check remoto aprovado |

Não há bloqueador técnico local conhecido restante dentro deste recorte. A conclusão não é autoaprovação de merge. Se criação/consulta de PR continuar proibida pela rede, a entrega permanece bloqueada externamente até criar o draft e verificar seus checks.

Riscos residuais separados: secrets default/fail-closed, revogação backend/refresh transacional, CORS, callback browser OAuth v1 que continua exigindo Bearer, estado OAuth sem uso único/expiração e seed dependente de ambiente. Não foram ampliados nem são resolvidos por este pacote. Integração Google real, APK/AAB, testes em dispositivo/emulador, PostgreSQL/GCP e comportamento de produção não foram certificados. Não houve merge, deploy ou mudança da especificação de produto.
