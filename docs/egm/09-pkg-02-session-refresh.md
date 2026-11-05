# PKG-02 — renovação de sessão e falhas de autenticação

Especificação executável: [issue #10](https://github.com/giovanimarin/vytal/issues/10), lida diretamente no GitHub. Esta issue define o escopo atual, que não é o antigo recorte documental de secrets. Base: `master` atualizada em `385d6a3`; branch `fix/pkg-02-session-refresh`. Sem migração, nova UX, nova fórmula, merge ou deploy.

## Inventário e defeitos confirmados antes da correção

| Componente | Comportamento na master | Evidência reproduzida |
|---|---|---|
| Backend | Login/cadastro emitem JWT e refresh opaco hashado; refresh lê, revoga e cria em operações distintas; logout revoga o refresh apresentado | Duas chamadas concorrentes com o mesmo refresh retornaram sucesso. Teste final força ambas além da leitura para provar o consumo único |
| Android oficial | Já tinha um refresh compartilhado e bypass de interceptação para endpoints auth; segundo 401 e ausência de refresh não encerravam sessão; resposta antiga era validada só por userId | Três testes novos falharam na master: segundo 401, refresh ausente e resposta anterior a logout/login da mesma conta |
| Web | Armazenava access token e perfil, descartava refresh retornado pelo login; todo 401 apagava duas chaves locais e redirecionava, deixando Zustand persistido intacto; cache de perfil não tinha owner | Teste de 401 falhou: userId/accessToken permaneciam no estado persistido/in-memory após o erro |

Não se alteraram os 202 testes de backend nem as assertions antigas do PKG-01 para acomodar a correção. Os testes de cliente/API existentes foram ampliados.

## Contrato de comportamento

| Evento | Resultado |
|---|---|
| Login/cadastro/refresh/logout retorna 401 | Não inicia refresh dentro desses endpoints. Login inválido não encerra uma sessão posterior ou outra conta |
| Primeiro 401 de recurso próprio | Se houver credenciais da mesma sessão, um refresh compartilhado; cada requisição original pode ser repetida uma única vez |
| Concorrência na mesma sessão | Um refresh em andamento por sessão/credencial no cliente. Backend faz substituição condicional atômica, com exatamente um consumidor aceito por refresh |
| Resposta/refresh atrasado após logout/login, inclusive mesma conta | Rejeitado por versão de sessão, inclusive antes de enviar uma renovação enfileirada; não entrega dados/cache nem instala credenciais antigas |
| Segundo 401 após retry, refresh ausente, recusado, resposta malformada, falha de rede ou 5xx durante refresh | Rejeita os aguardantes e limpa apenas a sessão correspondente. Não tenta novamente automaticamente: resultado de rotação pode ser incerto |
| Rede/5xx em requisição ordinária, sem 401 | Rejeita a requisição e preserva as credenciais válidas; não inicia refresh |
| Logout explícito | Limpa estado/cache imediatamente; tenta revogar o refresh capturado sem reinstalar estado em caso de falha/rede indisponível |
| Web legada ou após reload, sem refresh em memória | Access válido continua funcionando; próximo 401 exige login. Refresh web não é persistido em localStorage |

O timeout HTTP existente de 15s foi mantido. Não se criaram TTLs, tolerâncias de relógio, sid, famílias de token, grace periods ou políticas de revogação global.

## Implementação e compatibilidade

- Repositório troca hash e timestamps do refresh na **mesma linha existente e em um único UPDATE condicional** por hash anterior, usuário, expiração e não revogação. Não há janela de revogar sem instalar substituto nem dois vencedores. IDs internos não são contratos públicos; payloads/paths/status v1 permanecem.
- `execute_affected` expõe contagem de linhas comprometidas: SQLite real e implementação BigQuery com parâmetros vinculados. Após a revisão BigQuery, o SDK real valida a serialização e apenas client/jobs são simulados, sem serviço real; o pacote não certifica autenticação operacional GCP.
- `sessionRefresh.ts` em cada aplicação isola a promessa compartilhada, sem dependência entre empacotadores Android/Next. Adaptadores HTTP tratam status e versão da sessão; refresh nunca intercepta a si mesmo.
- Android usa a geração local já existente também no transporte, impedindo respostas anteriores a logout/login da mesma conta. Logout da UI deixa de esperar a animação para remover credenciais.
- Web passa o refresh retornado pelo backend ao estado **apenas em memória**, preservando a persistência existente de access. Limpa memória mesmo se o armazenamento negar escrita; limpa o Zustand persistido e aliases locais ao sair quando o navegador permite; descarta preferências de outra conta. Cache é limpo na mudança da sessão; perfil inclui userId na query key. Login/seed tardios não restauram sessão encerrada.
- Cache/credenciais não substituem autorização backend: toda a matriz PKG-01 continua executando. O OpenAPI v1 permanece compatível com master.

## Validação local

- **211 testes backend** passaram; cobertura **74,95%**, acima do gate existente de 30%. Incluem 9 casos novos de rotação, concorrência entre repositórios, replay/logout, usuário inexistente, refresh expirado/revogado/owner errado e falha de armazenamento.
- **32 testes Android** passaram, mantendo os antigos e cobrindo retry máximo, credencial ausente, rede/5xx/malformed, mesma conta após logout, cancelamento de sessão, logout remoto e coordenador isolado.
- **21 testes web** passaram, incluindo concorrência, rede, retry máximo, persistência limpa, refresh só em memória, login tardio e preferências entre contas.
- **1 integração cliente Android real + FastAPI/JWT/SQLite** passou, ampliada para recuperação concorrente de access inválido, replay de refresh e revogação por logout, além do isolamento A/B original.
- Instalação web limpa com npm ci/Node 22, typechecks, Ruff dos arquivos Python alterados, ESLint Android, contrato OpenAPI, bundle Android/Hermes e build Next.js passaram. Não se gerou/certificou APK/AAB nem se testou dispositivo.
- Workflow existente ampliado para a nova branch, testes web e lint dos componentes backend afetados; resultados remotos devem ser verificados no SHA publicado, sem inferência a partir dos testes locais.

## Limitações explícitas

Logout offline garante remoção local e rejeição de respostas antigas; revogação remota depende da entrega da chamada. JWT access emitido anteriormente continua com seu vencimento existente: revogação instantânea de access JWT/dispositivos exige contrato próprio e não foi anunciada como implementada. A coordenação de refresh é por instância de aplicação; múltiplos clientes concorrentes são arbitrados pelo consumo único backend, sem janela de replay nem promessa de sessão compartilhada entre abas. Falha definitiva exige reautenticação. Secrets default, fontes OAuth, PostgreSQL/GCP de produção e demais requisitos do Elephant continuam fora deste PR.

## Correção da revisão BigQuery no PR #11

`query()` e `execute_affected()` agora usam a mesma preparação de SQL e `QueryJobConfig`, sempre com default dataset e parâmetros vinculados. Dicionários suportam `:nome`/`@nome` repetidos; listas/tuplas usam parâmetros posicionais `?`, como os repositórios existentes de logout/perfil. Valores nunca são interpolados, literais/comentários são preservados e mistura/ausência/excesso de parâmetros falha antes de enviar o job.

Tipos vêm dos valores Python: datetime aware → TIMESTAMP UTC; datetime naive → DATETIME; date → DATE; bool/int/float → BOOL/INT64/FLOAT64; Decimal/bytes/time → NUMERIC/BYTES/TIME. Strings, inclusive ISO aparentes, continuam STRING. `QueryParameter(type_, value)` permite scalar explícito, inclusive NULL tipado; TIMESTAMP exige datetime aware. A rotação passou a fornecer `now`/`expires` como datetime UTC, não strings. SQLite serializa esses valores como ISO UTC com `T`, preservando a comparação com o armazenamento existente. Resultados TIMESTAMP nativos do SDK são aceitos na validação de expiração.

Foi mantido **um único UPDATE condicional** e uma única execução de job para o CAS. A contagem só é lida após `job.result()` e exatamente uma linha permite emitir o substituto; zero, desconhecido ou múltiplas linhas não concedem sucesso.

A inspeção de `infrastructure/terraform/modules/gcp/bigquery` confirmou campos DATE e TIMESTAMP nos schemas analíticos, mas **não existe definição versionada de refresh_tokens/users/oauth_tokens**. O contrato exigido para rotação GCP é token_id/user_id/token_hash STRING, created_at/expires_at TIMESTAMP e revoked INTEGER/INT64. Isto é pré-condição documentada, não afirmação sobre tabela real; nenhuma tabela, schema ou infraestrutura foi criada/alterada. Não se certifica operação completa de autenticação em GCP com este patch.

Os testes novos usam **google-cloud-bigquery 3.38.0 real**, fixado nos requirements, e apenas o cliente/job simulados, sem credenciais. Verificam SQL, JSON de serialização do SDK, tipos/timezones, parâmetros posicionais/nomeados, schema analítico versionado, falhas de job, contagem de linhas e timestamps nativos/SQLite. Os primeiros 11 casos reproduziram as falhas antes da correção. Os testes anteriores foram preservados. BigQuery real (IAM, schemas implantados, DML sobre streaming buffer e concorrência do serviço) permanece não validado; não houve dry-run, migração, merge ou deploy.

Resultado da correção: **253 testes backend passaram**, incluindo **42 casos novos** do binder/SDK, além da integração real Android/FastAPI/SQLite. Cobertura backend **76,01%**, Ruff e verificação OpenAPI v1 aprovados; `pip check` sem conflitos após resolução conjunta com Beam/protobuf. Os jobs remotos serão conferidos no commit publicado.
