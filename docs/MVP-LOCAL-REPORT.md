# MVP local — relatório de execução e limites

Data: **2026-11-05**. Base: master **6506a64** (PR #23 integrada). Branch `codex/mvp-local-e2e`. Guia reproduzível: [LOCAL-MVP.md](LOCAL-MVP.md).

**Resultado: backend e web têm fluxo essencial executado com sucesso localmente; a homologação do MVP completo com interface Android permanece bloqueada.** Não houve uso de GCP, contratação, deploy, apply, migração PostgreSQL ou merge. Custo adicional de nuvem **US$0**. Download de dependências open source e CI GitHub não são provisionamento cloud do Vytal. Nenhuma fórmula de readiness foi alterada.

## Evidências por componente

| Componente / execução | Evidência concreta | Resultado e limite |
| --- | --- | --- |
| Launcher backend | `python scripts/local.py backend`; Uvicorn em 127.0.0.1:8000, lifespan e GET /health 200 | Executado neste ambiente Linux, SQLite em pasta privada local; sem credenciais reais |
| Launcher web | `python scripts/local.py web`; Next dev em localhost:3000; GET /login 200 | Executado, proxy explicitamente aponta para backend 8000; browser E2E usa portas próprias isoladas |
| Web UI E2E | `web/tests/local-e2e.cjs`, Node 22, Chromium real instalado, dois contextos browser e FastAPI/SQLite reais | **11 checkpoints passaram**; sem mock de respostas HTTP; repetido após corrigir hidratação; automação de navegador, **não teste manual humano** |
| Saúde simulada | `seed_local_account.py`, 14 dias de cinco métricas; RawEvent → normalização → persistência → readiness existente | Executado no fluxo E2E; dados fictícios local_demo, por conta; sem Fit/OAuth real |
| Android serviços JS/API | 52 testes de autenticação/configuração + 1 integração real Android auth client/FastAPI/JWT/SQLite | Passaram; não é execução de tela nativa |
| Android build | lint do conjunto existente, TypeScript, `expo export --platform android`, bundle Hermes 2.91 MB | Passaram; export não é APK instalado nem valida permissões/SecureStore nativo |
| Android Metro | `CI=1 python scripts/local.py android`, Expo Go + EXPO_OFFLINE=1, API emulator 10.0.2.2 | Bundler local iniciado sem serviço Expo remoto; não houve dispositivo conectado |
| Android UI | command -v adb/emulator sem resultado; Android SDK e /dev/kvm ausentes; nenhum dispositivo disponível | **Não executado**. Não afirmar cadastro/perfil/feedback visual ou sessão nativa manualmente testados |
| Windows/dispositivo físico | Script bat e caminhos foram ajustados, sem host Windows/telefone disponível | Instruções propostas e código revisado; não declarar validação desses ambientes |

As capturas são imagens reais de execução com contas **sintéticas**, não mockups. As páginas foram inspecionadas visualmente a partir das imagens, sem operador humano clicando na aplicação:

- [Dashboard, readiness, histórico e feedback](evidence/mvp-local/web-dashboard.png)
- [Métricas e insights](evidence/mvp-local/web-metrics.png)
- [Treinos e histórico](evidence/mvp-local/web-workouts.png)
- [Recuperação e Body Map](evidence/mvp-local/web-recovery.png)
- [Resumo legível por máquina](evidence/mvp-local/result.json)

## Fluxos exercitados no navegador e backend real

1. Cadastro web por e-mail/senha, identidade obtida da API v1 (sem identidade fixa/bypass).
2. Recarga completa da página, sessão preservada no limite atual de validade do access token, consulta de perfil autenticada.
3. Edição do perfil pela interface e confirmação via API; persistência na mesma conta.
4. Simulação de saúde para a conta A via CLI local: 14 dias, cinco métricas; endpoints summary/history e readiness verificaram dados reais no SQLite temporário.
5. Dashboard, histórico e insight renderizados; tela Dados exercitada. Valores mantêm as fórmulas atuais.
6. Feedback salvo pela interface e leitura confirmada (“4/5”).
7. Treino pela interface, registro/histórico/notas, recuperação consultada e Body Map renderizado.
8. Regressão específica POST /workouts date:null: 201 e data do dia; sem erro 500.
9. Logout e novo login com a mesma conta; identidade confirmada.
10. Contexto independente com conta B: dados/treinos vazios; B→A e A→B recebem 404; tentativa de feedback cruzado rejeitada.
11. Nenhum erro JavaScript inesperado no contexto principal ao terminar o roteiro. Browser bloqueia destinos que não sejam 127.0.0.1; backend usa provider local e simulação não chama connector remoto.

Roteiro de E2E cria bancos/config/chaves sintéticos descartáveis, fecha seus processos e remove a base temporária. Capturas/JSON são os únicos artefatos persistidos; não inclui JWT, senha, HAR, trace ou credenciais nos commits. `.local-vytal/` e diretórios de build dev ficam ignorados. A geração de demonstração é separada da autenticação e recusa dados não-demo no mesmo período.

## Defeitos confirmados e corrigidos

| Problema | Antes / evidência | Correção e regressão |
| --- | --- | --- |
| Treino com data null/omitida | T01 caracterizava HTTP 500: None chegava a coluna NOT NULL | Handler resolve dia atual **antes** de persistir e recalcular recuperação. Testes reais para null/omissão verificam 201 e histórico. Datas impossíveis/malformadas retornam 400 antes de escrita. OpenAPI v1 permaneceu compatível |
| Sessão web após reload | Duas execuções Chromium falharam em Perfil; URL final /login e tela capturada no artefato local de falha | AppShell aguarda hidratação da store antes de redirecionar. E2E repete reload, acesso a Perfil e navegações em servidor real; sem relaxar autenticação |
| Inicialização inconsistente | dev.bat usava backend 8002, Expo web 8083, seed distinto e não definia ENVIRONMENT | Launcher Python compartilhado: backend 8000, Next web 3000, API Android explícita; configuração SQLite e chaves locais estáveis; testes de ambiente inseguro/reuso de chave/conta demo |
| Web sem cadastro/feedback visuais | API já fornecia essas funções, interface exigia API/seed externo | Campos de cadastro na tela login, função register real e formulário diário de feedback. Teste unitário de contrato de cadastro + E2E UI para ambos |
| Seed compartilhado incompatível com execução segura | Botão visível em dev embora seed fosse bloqueado por padrão (403) | Oculto salvo opt-in explícito; roteiro usa CLI local por conta, sem habilitar endpoint anônimo ou senha compartilhada |
| Expo startup dependia de rede | Início tentou fetch remoto e falhou neste ambiente restrito | EXPO_OFFLINE=1 com host local/LAN (flag --offline e --localhost são mutuamente exclusivas); Metro inicializa sem API Expo |

Nenhuma migração, unidade de trabalho PostgreSQL ou correção incidental de semântica REPLACE/FK foi introduzida. O snapshot T01 que esperava a falha date:null foi substituído **por correção explicitamente autorizada nesta tarefa**, com asserts de sucesso/data/persistência e novos testes negativos; os demais snapshots mantidos.

## Testes e verificações

- Backend: **432 passed**, cobertura **84,24%** (antes: 418). Incremento de 14 casos: regressões de datas e testes do launcher/geração demo. Nenhum teste anterior enfraquecido para acomodar implementação.
- Web: **43 testes passed** (22 auth, 21 config), mais **11 checkpoints E2E** em Chromium/servidores reais. Cadastro tem teste de contrato; hidratação e feedback são cobertos na automação UI.
- Android: **52 testes passed + 1 integração API**, scoped ESLint, typecheck e export Hermes passaram. Nenhuma alegação de teste manual nativo.
- Web: instalação limpa **npm ci**, TypeScript e build Next de produção passaram com Node 22/npm 10, endpoint HTTPS sintético. Artefatos de build não são deploy.
- OpenAPI: comparação origin/master + snapshot T01 passou; sem alteração de paths/schemas. Ruff do CI/arquivos novos e verificação de whitespace passaram.
- CI existente estendido no job web para E2E Chromium+SQLite e upload de evidências; não criou workflow duplicado. Usa requirements-prod para inicializar o backend local do browser; nenhum serviço remoto configurado. Resultado remoto deve ser confirmado por SHA no PR, não presumido por este relatório local.

## Bloqueios e limitações remanescentes

- **Android UI não homologada**: falta dispositivo/emulador/SDK. Cliente compatível com SDK 54 precisa estar disponível/instalado; Expo Go atual de outro SDK pode não servir. O launcher não instala APK automaticamente em modo offline.
- **Paridade Android incompleta**: não há tela equivalente de registro/histórico de treinos nas rotas atuais. Esses fluxos foram validados via web/API; não declarar “tudo funciona no Android”. Implementação e homologação dessa tela ficam como trabalho específico, sem inventar evidência visual.
- Google Fit real, login Google, OAuth em navegador externo, permissões nativas e notificações não foram exercitados; o roteiro usa simulação autorizada de saúde e login e-mail/senha. Não inserir credenciais reais no launcher.
- Web mantém a política existente de refresh em memória; reload conserva access token, mas não promete renovar após sua expiração se o refresh foi perdido. Novo login é necessário nesse caso. Não alterou política de armazenamento para fazer E2E passar.
- REPLACE, FKs e transações entre chamadas continuam com limitações documentadas no T01/ADR. Isso não certifica prontidão de produção nem remove bloqueios GCP.
- Compose legado e Windows não executados. Não foram corrigidos como arquitetura de deploy; o caminho validado é launcher Python sem Docker.

**Critério de testabilidade:** usar backend/web para avaliação manual local seguindo o guia; manter a aprovação do MVP completo condicionada ao roteiro nativo Android e às lacunas explicitadas. Não promover este PR como deploy ou homologação de produção.
