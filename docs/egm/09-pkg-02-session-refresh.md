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
- `execute_affected` expõe contagem de linhas comprometidas: SQLite real e implementação BigQuery com parâmetros vinculados. GCP foi testado com SDK/client simulados, não com serviço real; o pacote não certifica autenticação operacional GCP.
- `sessionRefresh.ts` em cada aplicação isola a promessa compartilhada, sem dependência entre empacotadores Android/Next. Adaptadores HTTP tratam status e versão da sessão; refresh nunca intercepta a si mesmo.
- Android usa a geração local já existente também no transporte, impedindo respostas anteriores a logout/login da mesma conta. Logout da UI deixa de esperar a animação para remover credenciais.
- Web passa o refresh retornado pelo backend ao estado **apenas em memória**, preservando a persistência existente de access. Limpa o Zustand persistido e aliases locais ao sair; descarta preferências de outra conta. Cache é limpo na mudança da sessão; perfil inclui userId na query key. Login/seed tardios não restauram sessão encerrada.
- Cache/credenciais não substituem autorização backend: toda a matriz PKG-01 continua executando. O OpenAPI v1 permanece compatível com master.

## Validação local

- **211 testes backend** passaram; cobertura **74,95%**, acima do gate existente de 30%. Incluem 9 casos novos de rotação, concorrência entre repositórios, replay/logout, usuário inexistente, refresh expirado/revogado/owner errado e falha de armazenamento.
- **32 testes Android** passaram, mantendo os antigos e cobrindo retry máximo, credencial ausente, rede/5xx/malformed, mesma conta após logout, cancelamento de sessão, logout remoto e coordenador isolado.
- **20 testes web** passaram, incluindo concorrência, rede, retry máximo, persistência limpa, refresh só em memória, login tardio e preferências entre contas.
- **1 integração cliente Android real + FastAPI/JWT/SQLite** passou, ampliada para recuperação concorrente de access inválido, replay de refresh e revogação por logout, além do isolamento A/B original.
- Instalação web limpa com npm ci/Node 22, typechecks, Ruff dos arquivos Python alterados, ESLint Android, contrato OpenAPI, bundle Android/Hermes e build Next.js passaram. Não se gerou/certificou APK/AAB nem se testou dispositivo.
- Workflow existente ampliado para a nova branch, testes web e lint dos componentes backend afetados; resultados remotos devem ser verificados no SHA publicado, sem inferência a partir dos testes locais.

## Limitações explícitas

Logout offline garante remoção local e rejeição de respostas antigas; revogação remota depende da entrega da chamada. JWT access emitido anteriormente continua com seu vencimento existente: revogação instantânea de access JWT/dispositivos exige contrato próprio e não foi anunciada como implementada. A coordenação de refresh é por instância de aplicação; múltiplos clientes concorrentes são arbitrados pelo consumo único backend, sem janela de replay nem promessa de sessão compartilhada entre abas. Falha definitiva exige reautenticação. Secrets default, fontes OAuth, PostgreSQL/GCP de produção e demais requisitos do Elephant continuam fora deste PR.
