# Vytal — especificação mestre Elephant v0.2

**Versão documental:** 0.2.0, 2026-11-04. **Estado:** consolidada para nova revisão Goldfish; **não aprovada para implementação ou release**.
**Base de trabalho:** `docs/egm-approved-product-decisions`, commit `3d00ffa3e1d5aeb5259cdd06a926f33df460bf38`.

## 1. Fontes, autoridade e significado dos estados

Todas as fontes foram verificadas como acessíveis **antes de editar**:

| Fonte obrigatória | Branch / commit verificado | Papel |
|---|---|---|
| [Elephant 0.1.0 original](https://github.com/giovanimarin/vytal/blob/2722445bb889160390d79e2932f876bebbd03870/docs/egm/01-master-spec.md) | `docs/egm-phase-1-elephant` / `2722445bb889160390d79e2932f876bebbd03870` | Baseline dos IDs e proposta anterior, não decisão de produto |
| [Goldfish original](02-goldfish-review.md) | `docs/egm-phase-2-goldfish` / `a8a85b578c08c47f73b8cc5035a83aed0c9342a6` | 20 achados, incluindo 17 bloqueadores, preservados sem alteração |
| [Registro aprovado](03-approved-product-decisions.md) | `docs/egm-approved-product-decisions` / `3d00ffa3e1d5aeb5259cdd06a926f33df460bf38` | Fonte literal D01–D20 e mapeamento muitos-para-muitos |
| [Inventário](00-inventory.md), [AGENTS.md](../../AGENTS.md) | Disponíveis no commit de decisões acima | Evidência atual, riscos S01–S15 e gates EGM |
| [Prompt Elephant](prompts/01-elephant.md), [prompt Goldfish](prompts/02-goldfish.md) | Disponíveis na mesma base | Requisitos do processo documental |

Classificação obrigatória:
- **ATUAL:** fatos CUR-01–CUR-15 do inventário; nenhuma implementação nova é inferida.
- **PRODUTO APROVADO:** escolhas literais D01–D20. Aprovação dessas escolhas não aprova este desenho técnico, métricas clínicas, rollout ou implementação.
- **CONTRATO v0.2 PARA REVISÃO:** desenho técnico proposto para cumprir as D e responder GF. “Deve” define aceitação futura, não autorização de executar código.
- **ABERTO:** Q-01–Q-15 são decisões/políticas/parâmetros ainda necessários. Não existe fallback silencioso, limite numérico inventado ou presunção de consentimento.

D01 não equivale a DEC-01. A seção 13 mantém os 20 DEC originais e referencia a matriz do registro. IDs CUR/FR/FST/SEC/INT/DAT/NFR/OPS/EDU/API/T anteriores são preservados; novos IDs estendem os grupos. Um ID mantido pode ter seu conteúdo atualizado pela D correspondente, sem reescrever evidência histórica. A [matriz de resposta Goldfish](04-elephant-v0.2-goldfish-resolution.md) registra correção, contrato, cenários e aceite de todos os GF.

“Resolvido na especificação” é avaliação **do autor**, restrita ao defeito textual/contratual descrito; não fecha o documento Goldfish original, não comprova código/teste e requer reavaliação independente. “Parcialmente resolvido” e “pendente” não podem ser tratados como autorização para preencher Q com defaults. Aprovação do inventário e desta versão, revisão independente e autorizações de merge/release continuam sendo gates.

## 2. Escopo de produto consolidado

**Plataformas:** API centraliza regras/dados; Android oficial é `mobile/vytal-app/`; web e Android recebem jejum na entrega inicial e paridade de treinos, recuperação e mapa corporal. Preservar fontes/capacidades existentes, inclusive evidência do candidato legado `mobile/`, sem prometer suporte irrestrito a binários inseguros ou excluir código. A matriz de migração está na seção 10.

**Incluído pelas D:** jejum livre contínuo, sem pausa/alvo obrigatório; edição histórica, notas, cronômetro/timeline educativa/histórico/estatísticas; offline completo de jejum Android; correlações descritivas com saúde; Fit mantido e Garmin condicionado à API oficial; dashboard ordenável por conta; evolução validada/versionada do readiness; treinos manuais/importados deduplicados; exclusão individual/conta e dados privados; notificações opcionais Android e avisos web in-app; PostgreSQL operacional, BigQuery analítico quando necessário e produção GCP; autenticação e perfil ampliados; períodos 7/30/90 e personalizados, comparação e gráficos individuais; temas claro/escuro/sistema, pt-BR e acessibilidade; segurança e CI/gates incrementais.

**Excluído:** Health Connect, pausa de jejum, diário alimentar/controle nutricional de calorias, relatórios consolidados/PDF, exportação pela interface inicial, browser push, notificações específicas de falha de sync e compartilhamento entre usuários. Excluir export UI não elimina obrigações legais de acesso/portabilidade. Excluir diário alimentar não remove calorias de atividade existentes. Estados de erro/retry de sync na UI são preservados. Nenhuma integração de Garmin é declarada disponível sem verificação. Não inferir protocolo clínico, dieta, diagnóstico, gamificação, nova fórmula ou meta obrigatória.

Perfis de uso para revisão (não pesquisa validada): pessoa que consulta dados próprios; pessoa que registra treinos/jejum em múltiplas plataformas; pessoa com rede intermitente; pessoa que administra suas credenciais e direitos. Operação de infraestrutura/conteúdo tem acesso mínimo a definir em Q-06, não um produto de compartilhamento/admin clínico aprovado.

Jornadas aceitas para especificação/testes futuros:
1. Autenticar por e-mail/senha ou Google → identificar conta → configurar perfil/fontes → sincronizar e consultar dados próprios com qualidade.
2. Adicionar/remover/reordenar widgets e retomar preferências da conta em Android/web; jejum tem tela dedicada e widget opcional.
3. Iniciar/acompanhar/encerrar/corrigir/anotar jejum no Android offline → recuperar rede → sincronizar automaticamente ou apresentar conflito preservando intenção.
4. Consultar histórico/estatísticas e comparar períodos; correlações só quando dados suficientes segundo método validado, sem causalidade nem coeficiente direto de jejum no readiness.
5. Importar ou registrar treino, consultar mapa/estimativas e receber avisos opcionais; desconectar fonte mantém histórico, excluir é ação separada.
6. Revisar sessões/dispositivos, encerrar sessão remotamente e excluir registros/conta; recuperação de senha e biometria local não bypassam autorização.

## 3. ATUAL — baseline de preservação

As linhas abaixo são a evidência histórica da Fase 0, não comportamento futuro aprovado. O resumo CUR continua limitado pelo inventário, que não certifica produção/APK/Garmin.

| ID | Comportamento atual / fonte | Limite ou lacuna a preservar como evidência, não como requisito desejado |
|---|---|---|
| CUR-01 | `backend/app/main.py`, routers/services/repositories; FastAPI `/api/v1` e `/health` | JWT de grupo não compara owner em rotas com user_id; apenas `/users/me` deriva owner |
| CUR-02 | `auth_service.py`, `auth/*`, `refresh_token_repo.py`: bcrypt, access JWT, refresh hash/rotação; GET/PATCH perfil | Login/cadastro retornam identidade plana; Android espera `data.user`; senhas cliente 6/backend 8; logout UI é local |
| CUR-03 | Android oficial `mobile/vytal-app/`, Expo Router, login/cadastro/onboarding/perfil/dashboard/catalog/fontes | APK/runtime e combinação de versões não validados; `App.tsx/index.ts` alternativos são template; tabs antigas ainda existem |
| CUR-04 | `dashboardStore.ts`, nove widgets: readiness, histórico, sono, passos/calorias, FC, jetlag, curva, qualidade e feedback | Seleção não persiste; IDs advanced rendem componente completo repetido; teste mode não cria token real |
| CUR-05 | `google_fit.py`, `OAuthService`, `TokenRepository`: URL, callback, aggregate/sessions, refresh | Status/disconnect não existem; callback browser exige JWT; fases são percentuais fixos, calorias zero, stress não coletado; refresh Google não persistido nesse fluxo |
| CUR-06 | `HealthDataService.sync`: raw → normalização → readiness aguardados no request | Retorna 202/completed; não há job HTTP; sem deduplicação natural; falhas Google podem virar coleção vazia |
| CUR-07 | Readiness 0–100; pesos sono 40%, FC 30%, atividade 20%, stress 10%; redistribui stress ausente | Sono/FC obrigatórios; cortes reais 80/60/40; usa atividade da mesma data; sem baseline clínico individual |
| CUR-08 | `AdvancedMetricsService`, modalidades (8), recuperação (13 grupos) e banco de exercícios | Jetlag usa duração sem horário real; curva é heurística; HRV indisponível; cache e datas históricas têm lacunas |
| CUR-09 | Feedback diário com sentimento e outros campos no backend; formulário Android | `trained_today/workout_worth_it` enviados não são persistidos; nenhum aprendizado ajusta readiness |
| CUR-10 | Web: login/demo/dashboard/data/modalities/workouts/body-map/settings | Sem equivalência de todas as telas no Android; web armazena acesso em localStorage; demo é seed local/dev |
| CUR-11 | `mobile/` externo: tabs, BodyMap, modalidades e treino; cliente sem JWT | Candidato legado, não Android oficial; não excluir ou migrar silenciosamente |
| CUR-12 | SQLite com 16 tabelas, DDL na inicialização, INSERT OR REPLACE, adapters filesystem/GCS/BigQuery | Sem migrações incrementais; GCP ignora parâmetros e tem schemas/nomes divergentes; Cloud Run com SQLite durável não demonstrado |
| CUR-13 | Duas CLIs Beam, Terraform GCP, Docker/Compose, workflows CI/deploy | CLI da raiz falhou importando app; CI/deploy só main/staging, embora padrão seja master; deploy operacional não inspecionado |
| CUR-14 | Testes Fase 0: 66 passaram, cobertura 33,59%; TypeScript web/Android passou; Ruff 102 ocorrências | Resultados históricos do inventário, não reexecutados aqui; sem E2E/APK/Google/GCP; acesso cruzado a feedback confirmado com usuários sintéticos |
| CUR-15 | Não há sessões/rotas/timer/histórico/worker de jejum nem módulo de notificações | Todo jejum abaixo é proposto; ausência de código não autoriza implementação |


Aprovação de produto posterior não muda esses fatos: jejum e várias funções novas ainda não existem no código. Os 66 testes/cobertura/TypeScript e lint citados são da Fase 0, não reexecutados nesta tarefa. Preservar funcionalidade não significa preservar vazamento, imputação oculta ou alegação clínica. Mudanças semânticas usam versões e migração, não reinterpretação silenciosa.

## 4. Requisitos funcionais rastreáveis

Todos os critérios abaixo serão verificados na fase autorizada; Q aplicável bloqueia fechamento do desenho. T identifica grupo futuro; casos TS detalhados estão na seção 12.

| ID / origem | Requisito v0.2 | Critério de aceite e teste futuro |
|---|---|---|
| FR-01 / CUR-02, D13 | Cadastro/login e perfil com identidade canônica; e-mail/senha preservados e Google acrescentado | sub/conta/perfil coincidem; falha não deixa flag autenticada; contrato novo não obriga cliente v1 a ler envelope v2. T-02; Q-05/Q-14 |
| FR-02 / D13, D19 | Renovação sem recursão, logout local explícito e revogação backend de sessão identificável | Refresh concorrente não emite dois sucessores; remoto revogado não faz commit posterior; fila offline permanece protegida/pendente, não é enviada como outra conta. T-02/T-11 |
| FR-03 / D14 | Perfil existente e onboarding preservados, com evolução para múltiplos objetivos e histórico | PATCH ausente mantém; null limpa somente campo anulável; migrar goal singular sem inventar objetivo novo; hash nunca retorna. T-03/T-22; Q-14 |
| FR-04 / D07 | Nove widgets existentes mais widget opcional de jejum; adicionar/remover/reordenar por conta, sincronizado Android/web | IDs únicos, ordem preservada e CAS em concorrência; novo campo não remove widget conhecido do outro cliente; painel vazio/loading/erro/dado distintos. T-03/T-19 |
| FR-05 / D06, D10 | Status/conectar/desconectar fonte com estado verdadeiro; manter histórico ao desconectar salvo exclusão | Barreira de geração invalida resultados/callbacks antigos antes do commit; revogação externa pendente é visível. T-04/T-05 |
| FR-06 / D06, D17 | Sync de saúde honesto, deduplicado e com resultado/proveniência | Erro externo não vira sucesso vazio; repetir evento não duplica medida; progresso/status corresponde à execução real. T-05; Q-10 decide síncrono/job de saúde, não D04 |
| FR-07 / D08 | Readiness, contribuições, insight/histórico versionados; evolução só comparativamente validada | Na versão atual, se faltar sono **ou** FC não calcula; quatro casos de presença testados; limiares 40/60/80 e stress ausente preservados por versão. Nova fórmula exige validação registrada, não só novo ID. T-06 |
| FR-08 / D17 | Origem/qualidade/cobertura por medida; sem preencher automaticamente ausentes | Zero observado difere de zero placeholder; ausência tem value=null; estágios sintéticos legados não viram medidos. T-05/T-06; contrato seção 8 |
| FR-09 / D08, D17 | Preservar advanced, qualificar proxies e explicar limites | Jetlag por duração não afirma deslocamento circadiano medido; disponibilidade/método/versão explícitos; cálculo novo precisa evidência/validação. T-06/T-13 |
| FR-10 / D09 | Treinos manuais/importados, modalidades, recuperação e mapa corporal interativo com paridade Android/web | Treino/exercícios atomicamente gravados; deduplicação revisável; período histórico não depende de now; estimativa não é diagnóstico. T-07/T-21 |
| FR-11 / CUR-09 | Feedback existente faz round-trip sem descartar resposta | false/null/ausente distintos; campos cliente/servidor mapeados explicitamente; sem treino automático dos pesos. T-08; Q-14 |
| FR-12 / D01, D09, D20 | Preservar capacidades e realizar migração explícita por versão/plataforma | v1 mantém arrays/datas inclusivas; v2 não promete funcionar no cliente sem autenticação; fonte legada não é apagada; versões de suporte definidas em Q-12. T-16/T-18 |
| FR-13 / D16 | Históricos 7/30/90, personalizados, comparação de períodos/indicadores e gráficos individuais | Cada série informa período/calendário/versão/cobertura; sem PDF/relatório consolidado ou dados de outra conta. T-23; Q-09/Q-10 |
| FR-14 / D05 | Relacionar jejum a sono/FC/atividade/readiness e produzir insights descritivos personalizados com dados suficientes | Método/janelas/cobertura rastreáveis; se critério de suficiência não aprovado, insight indisponível; sem causalidade ou alteração direta do score. T-20; Q-01/Q-09 |
| FR-15 / D13 | Login Google separado da autorização Fit | Identidade por issuer/sub verificados; e-mail coincidente não vincula conta automaticamente; desconectar Fit não destrói identidade Google. T-24; vinculação em Q-05 |
| FR-16 / D13 | Biometria Android desbloqueia somente sessão local autenticada | Sem JWT novo por biometria; token revogado/expirado exige fluxo de autenticação válido; fallback e invalidation do SO explicitados em Q-05. T-24 |
| FR-17 / D13 | Recuperação de senha por e-mail, com prova de posse e proteção de enumeração/replay | Resposta pública não revela existência de conta; token de finalidade reset e uso único; segredo nunca em log. T-24; TTL/efeito sobre outras sessões em Q-05 |
| FR-18 / D14 | Objetivos simultâneos/evolutivos, histórico de peso/medidas, metas de frequência/volume e sugestões não médicas por tendências | Mudança de objetivo não apaga histórico; medidas têm unidade e instante; não criar nutrição por inferência; sugestão só com método/cobertura aprovados. T-22; Q-09/Q-14 |
| FR-19 / D18 | Temas light/dark/system, pt-BR inicial e consistência respeitando plataforma | Alteração de tema não perde dados; contraste, ajuste de fonte e leitor testados em ambos; persistência do tema e padrão mensurável em Q-13. T-14 |
| FR-20 / D17 | Prioridade de fonte por indicador, com dedup rastreável | Escolha fica vinculada à conta/versão; original de cada fonte é preservado; faltar prioridade não autoriza preencher com número ou escolher fallback silencioso. T-05/T-19; Q-10 |
| FR-21 / D11 | Avisos opcionais de jejum/recuperação/resumo readiness, quiet hours; Android e web in-app | Sem browser push nem família de alerta de falha sync; negar permissão não bloqueia registro; agendamentos revogados/obsoletos não executam ações. T-12; Q-11 |
| FR-22 / D19 | Listar dispositivos/sessões próprias e encerrar sessão remotamente | Não expor token; backend nega leitura/escrita da sessão revogada inclusive com access JWT ainda assinado; conta B não lista/revoga A. T-01/T-02/T-25 |

## 5. Jejum: estados, tempo, correção e offline

### 5.1 Requisitos

| ID / origem | Requisito v0.2 | Aceite futuro |
|---|---|---|
| FST-01 / D01–D04 | Início livre em API/Android/web, sem alvo obrigatório; Android aceita intenção offline | Uma identidade de sessão por comando; local e confirmado distinguidos; sem depender de Fit/Garmin/readiness. T-09/T-11 |
| FST-02 / D03, D04 | Cronômetro por instantes registrados e âncora monotônica quando contínua | Kill/reboot não reinicia registro; mostrar client_reported/needs_review, nunca tempo negativo ou diagnóstico pelo timer. T-10 |
| FST-03 / D02, D04 | Encerrar é sempre acessível localmente, sem meta nem motivo clínico obrigatório | Parada local permanece registrada se rede/token/servidor falhar; servidor continua exigindo autenticação para sincronizar. T-09/T-11 |
| FST-04 / D02, D10 | Distinguir encerramento, correção e exclusão; cancelamento permanece decisão aberta | Não reintroduzir pausa; não tratar exclusão como concluída nem cancelar como apagar; contrato cancel não é habilitado sem Q-03. T-09/T-17 |
| FST-05 / D02, D04 | Concorrência e sobreposição são verificadas no servidor segundo política versionada | Proposta uma ativa por conta e intervalos sem sobreposição aguarda Q-03; colisão nunca sobrescreve sessão/intenção. T-09/T-11 |
| FST-06 / D12 | Persistir sessão/comando/revisão de forma transacional em PostgreSQL | ACK somente após commit; crash de processo com banco preservado não perde confirmados; desastre tem garantia separada em seção 11/Q-07. T-15 |
| FST-07 / D03, D16 | Histórico/estatísticas com detalhe, edição e períodos aprovados | Ordem/cursor estáveis por snapshot; corrigidos não são dupla contagem; duração e estatística informam versão/calendário. T-10/T-23 |
| FST-08 / D04 | Android offline para iniciar/acompanhar/encerrar/corrigir/anotar e sync automática | DAG de comandos, IDs estáveis, retries e conflitos preservam conteúdo; rejeição não vira confirmação nem gera nova chave automaticamente. T-11 |
| FST-09 / D03, D11 | Lembretes opcionais e invalidação em stop/correção/exclusão/logout | Sem disparo por meta obrigatória; nenhuma garantia de entrega exata; considerar quiet hours e estado canônico. T-12 |
| FST-10 / D03 | Timeline educativa geral, sem “fase clínica atual” | Contador não afirma cetose/autofagia individual; texto com versão/evidência/revisão; sem fonte aprovada, explicação não publicada. T-13 |
| FST-11 / D10, D19 | Sessões/notas/comandos somente próprios, com exclusão e direitos aplicáveis | Filtro owner e geração da conta em cada operação; excluir não ressuscita via fila/restore. T-01/T-11/T-17 |
| FST-12 / D05, D08 | Permitir correlação descritiva, sem efeito direto do jejum na fórmula readiness | Fixtures de readiness invariantes ao adicionar sessão; séries comparativas não viram inferência causal. T-06/T-20 |
| FST-13 / D02, D04 | Corrigir início/fim inclusive histórico e offline | Preservar revisão anterior, intenção declarada, versão base e qualidade temporal; conflito exige resolução explícita; não reabrir completed como efeito colateral. T-09/T-11 |
| FST-14 / D03, D04 | Anotações por sessão, inclusive offline | Texto íntegro em fila protegida; duas edições divergentes não usam last-write-wins; nunca colocar nota em log/lockscreen. Limites e retenção Q-06/Q-08. T-11/T-17 |
| FST-15 / D03, D16 | Estatísticas individuais de jejum e comparações | Fórmula/unidade, amostra e período explícitos; não incluir sessões pendentes/rejeitadas como confirmadas; quais agregados usar em Q-09. T-23 |

### 5.2 Máquina de estados e revisão

Desenho mínimo para revisão: servidor guarda `active` ou `completed`, mais marca de exclusão separada. Sem `paused` e sem planejamento/protocolo inventado. `completed` significa registro encerrado, não êxito médico. `cancelled` da v0.1 fica **reservado/desabilitado**, sem endpoint publicado até Q-03; não converter dados legados silenciosamente se existir tal estado em outra versão.

Estado de sync local é separado: `pending`, `confirmed`, `conflict`, `rejected`, `blocked_auth`, `needs_review`. Nada na UI muda um pending para confirmed por timeout. Guardar projeção local e snapshot canônico separados.

| Comando | Pré-condição | Resultado técnico / efeito |
|---|---|---|
| start | Conta autorizada; política Q-03 satisfeita | Nova active, revisão inicial e recibo no mesmo commit; nenhuma ativa local é criada só por abrir tela |
| stop | active e versão esperada | completed com fim declarado validado; invalida lembretes; se falhar remoto, intenção de parada continua visível localmente |
| amend_times | active/completed e versão esperada | Nova revisão; active altera início, completed altera início/fim; não muda estado nem implica pausa/reabertura |
| amend_note | active/completed e versão esperada | Nova revisão de nota protegida; conteúdo anterior não é descartado na resolução de conflito |
| delete | Owner e versão esperada | Tombstone/fluxo de exclusão; invalida mensagens e descendentes que tentem editar recurso excluído; sem reimport silencioso |
| Qualquer replay | Mesmo epoch/seq/key e fingerprint | Mesmo recibo, sem nova transição; merge do recurso atual somente por revisão monotônica |
| Novo stop de completed / recurso excluído / versão divergente | Não atende máquina/CAS | Erro definitivo tipado, nenhuma mudança; correção consciente exige novo comando após reconciliação |

Cada correção registra revision, previous_revision, command_id, instantes declarados/efetivos, qualidade e motivo técnico (não história clínica obrigatória). Auditoria não duplica notas em logs. Schema e regras de retenção de revisões são Q-06. Sobreposição, múltiplas ativas, cancelamento e tratamento de datas futuras são **Q-02/Q-03**, não decisões aprovadas. A restrição técnica proposta só poderá virar constraint de produto após essa resolução.

### 5.3 Relógios e instante efetivo

Separar `client_recorded_at` (hora civil declarada), `server_received_at` (metadado de recepção), `effective_started_at/effective_ended_at` (instantes aceitos do registro) e `time_quality`. Todos os instantes exigem RFC 3339 com offset; persistência normaliza UTC sem perder offset/timezone IANA de contexto. Datas civis não são instantes. Precisão/mapeamento de duração e arredondamento devem ser explícitos no schema; nenhuma duração clínica é prescrita.

Correção técnica de GF-04: **não usar o relógio de recepção do backend para sobrescrever início/fim ou calcular duração**. Hora declarada/confirmada pelo usuário é entrada do registro, online e offline; “confirmado” significa commit, não medição do corpo nem relógio exato. `server_received_at` não participa do intervalo. Duas instâncias com wall clocks diferentes não produzem fim<início por causa da recepção.

No processo contínuo, projetar elapsed pela última âncora e tempo monotônico; um ajuste de wall clock não altera elapsed já observado. Após reboot/perda de âncora ou relógio incompatível com evidência disponível, preservar declaração como `needs_review`; nunca truncar para zero ou somar horas até reconnect sem aviso. Parada local não depende da revisão remota.

Modelo candidato de qualidade temporal: `client_reported` (declaração), `monotonic_anchored` (elapsed com âncora contínua, não prova de horário absoluto), `needs_review` (inconsistência/âncora perdida não reconciliada). Permitir início/fim com `end >= start`; entradas negativas/sem offset são rejeitadas antes do commit. Isso não define se datas futuras, backdating ou divergências devem ser aceitas automaticamente: **Q-02**. Caso de parada às 10h offline/reconnect às 14h deve retornar os instantes solicitados, os aceitos e eventual conflito; nunca usar 14h como fim automático. Troca de timezone muda apresentação, não o intervalo; timestamp ambíguo em DST exige offset explícito.

### 5.4 Protocolo offline e dependências

A proibição de start offline do modo A v0.1 é retirada por D04. Android cria comandos locais persistentes/protegidos para todas as operações FST; web usa os mesmos contratos online, sem promessa adicional de web offline. Uma conta previamente autenticada é necessária para vincular a fila; não há modo anônimo/biometria que emita credencial backend.

Cada comando contém `command_id` estável, `client_session_id`, `sync_epoch` emitido pelo servidor para a instalação/conta, `sequence` monotônico, `depends_on[]`, `base_revision` quando aplicável, `operation`, `payload` e instantes declarados. IDs provisórios/canônicos de sessão usam o mesmo UUID proposto pelo cliente, validado como recurso próprio no servidor; o servidor nunca confia nesse UUID para autorização. ID já pertencente a outro owner é negado sem revelar dados.

DAG obrigatório: start(A)→stop(A); para próximo intervalo start(B) depende também de stop(A), quando a regra aprovada impedir simultaneidade; stop(B) depende de start(B); edição/notas dependem da revisão que editam. Validar ciclos/referências ausentes. Se chegada fora de ordem, retornar `dependency_pending` sem aplicar; o cliente reenvia o **mesmo** comando depois da dependência, não outra chave. Rejeição de predecessor bloqueia descendentes para resolução explícita, não descarta payload.

Máquina da fila: pending→confirmed após recibo; falha de transporte permanece pending; 401/session_revoked→blocked_auth; stale revision/overlap→conflict; validação/estado impossível→rejected; declaração temporal ambígua→needs_review. Erro transitório de banco não consome chave. Retentar pending automaticamente quando a rede/credencial permitirem; backoff/limites e duração offline suportada dependem Q-04/Q-08, sem defaults inventados. Reautenticar a **mesma conta** desbloqueia envio; outra conta não adota a fila. Logout remove segredos/visibilidade e interrompe envio; conservar ou expurgar intenções protegidas exige política Q-05/Q-06, sem perda silenciosa.

Conflito retorna ID/revisão/estado atual próprios e quais campos divergiram, não mescla nota/horário silenciosamente. UI permite consultar ambas as intenções, descartar conscientemente ou submeter nova revisão com novo command_id após resolução. A regra exata de conflito de intervalos/edição depende Q-02/Q-03; não confirmar localmente como remoto. Uma fila com stop(A), start(B), stop(B), correção e nota precisa sobreviver a kill e entrega fora de ordem sem duplicação (TS-05/06).

### 5.5 Idempotência, retenção e merge

Chave lógica `(owner_generation, sync_epoch, sequence)` tem command_id/fingerprint únicos. `Idempotency-Key` transporta command_id; retry mantém todos esses valores. Fingerprint inclui método/recurso, operação, JSON tipado canônico, dependências e precondição de revisão. Mutação, receipt, revisão, watermark e invalidação/outbox gravam na mesma transação PostgreSQL; concorrência serializa por agregado/conta conforme invariante, não depende do lock de um aparelho.

Epoch deve estar no conjunto ativo emitido para a conta/instalação, com geração atual; epoch desconhecido/revogado não é aceito como chave nova. Manter piso contíguo de sequências terminadas e resolver lacunas antes de avançá-lo. Depois de expurgar receipt, sequência <=piso retorna `reconciliation_required`, **não executa novamente**. Sequência >piso sem receipt não avança automaticamente sobre lacuna pendente. Requests para epoch retirado não o recriam. Retenção de receipt, piso/epoch e expurgo de conta precisam política coerente Q-04/Q-06; recuperação de disaster precisa Q-07. Assim, a proposta técnica impede o replay ingênuo após expurgo, mas GF-05 não é fechado integralmente enquanto essas garantias não forem aprovadas.

Receipt é resultado imutável do comando (`applied|rejected`, resulting_revision/error_code), **não snapshot atual da sessão**. Resposta distingue receipt de `resource_current` lido após autorização, com sua revisão; não devolve snapshot v1 ativo como se fosse atual após completed v2. Cliente nunca aplica revisão inferior à já conhecida, nem ressuscita tombstone por resposta atrasada. Retorno de receipt sem recurso atual não inicia timer/notificação; buscar estado canônico. Edições de nota seguem mesma regra.

Reautorização e owner checks ocorrem antes de ler receipt, cursor e recursos, inclusive em replay/exclusão. Chave com fingerprint diferente dá 409; payload inválido sintaticamente não é gravado como receipt. Rejeição definitiva de domínio pode gravar receipt rejeitado; corrigir corpo/base_revision exige novo command_id explícito. Respostas perdidas depois do commit são recuperáveis sem produzir outra sessão.

## 6. Segurança, autenticação e barreiras de autorização

### 6.1 Requisitos e sessão operacional

| ID / origem | Contrato técnico para revisão | Aceite futuro |
|---|---|---|
| SEC-01 / S01, D10, D19 | Owner vem de sub; consulta/commit filtram owner e geração da conta, incluindo receipts/cursors/notas | A não lista/lê/altera B; UUID não concede acesso; entrada user_id v1 divergente é rejeitada antes de consulta pessoal. T-01 |
| SEC-02 / S02 | Produção fail-closed sem banco/provider/segredos válidos; sem default previsível | Config inválida não fica pronta; não recair silenciosamente em SQLite; teste negativo sem imprimir segredo. T-16 |
| SEC-03 / D19 | TLS, criptografia em repouso de dados/backups, proteção específica de tokens/notas/filas e acesso mínimo | Nenhum token/payload sensível em log/URL/analytics; chaves/gestão/rotação a fechar Q-06/Q-07; SQL parametrizado. T-17 |
| SEC-04 / D06, D13 | Transações OAuth independentes para login Google e Fit/Garmin, com purpose/state de uso único e vínculo de conta/redirect | Callback browser autorizado pela transação, não por JWT no redirect; rejeitar replay/redirect não aprovado; sem token em deep link. T-04/T-24; Q-05/Q-10 |
| SEC-05 / D10 | Privacidade, exclusão e acesso/portabilidade legal via processo autenticado; sem export UI inicial | Desconectar não apaga importados; delete não ressuscita; processo tem recibo e estado, sem prometer prazo não aprovado. T-17; Q-06 |
| SEC-06 / S08/S09 | Demo isolada e CORS explícito por ambiente; sem acesso dev automático à produção | Seed negado antes de escrita em produção; origens e URL construídas por config explícita. T-01/T-16 |
| SEC-07 / D13, D19 | Cada sessão backend tem sid, owner_generation, estado active/revoked; access exige sessão/conta ativas | Revogação lineariza no banco e bloqueia próximo commit; token assinado de sessão revogada não autoriza operação. Cache/fila/avisos segregados. T-02/T-11 |
| SEC-08 / S11/S12 | Validar tipos, payload, ownership, header, timezone, intervalo e volumes; limites explícitos e aprovados | Campo desconhecido v2 é rejeitado, não perdido; não fabricar limite ou aceitar SQL arbitrário; parâmetros Q-08/Q-14 faltantes bloqueiam aceite correspondente. T-01/T-09 |
| SEC-09 / D13 | Identidades externas e reset vinculados por provas verificadas, não só endereço e-mail | Google iss/aud/nonce/sub verificados; purpose de login não autoriza Fitness; reset único/protegido e resposta anti-enumeração. T-24 |
| SEC-10 / D19 | Auditoria de acessos sensíveis/segurança minimizada e protegida | Registrar ação/ator técnico/recurso opaco/resultado/revisão sem notas/medidas/tokens; acesso/retenção/chaves em Q-06; ação de auditoria não concede papel de compartilhamento. T-17/T-25 |

Toda operação protegida verifica credencial e estado da conta/sid antes de ler e **novamente na transação de escrita**, sob lock/CAS que serialize contra revogação/exclusão. Revogar uma sessão remotamente é operação idempotente: após seu commit, pedidos daquela sessão não podem fazer novos commits. Um pedido concluído antes da barreira não é desfeito. Nenhuma leitura posterior à checagem de revogação aceita pode ignorar estado ativo; limites de pedidos em voo/leitura já entregue precisam política Q-05, não promessa de apagar bytes já recebidos.

JWT futuro carrega sid/generation além de sub e purpose; verificar campos obrigatórios/tipos/algoritmo/issuer/audience conforme contrato aprovado, não somente assinatura. Token antigo sem vínculo de sessão não é “reparado” por confiar no user_id enviado. V2 exige reautenticação/refresh válido para criar sessão rastreável; janela de coexistência dos tokens v1 e clientes incapazes de refresh é Q-12, com fail-closed e migração explícita, nunca reabrir dados de terceiros.

Logout local limpa segredos e fecha visibilidade de cache/avisos, sem afirmar revogação remota offline já realizada. Stop local permanece disponível como intenção protegida, mesmo em blocked_auth. Nenhum envio ocorre com conta diferente; reautenticação da mesma identidade permite reconciliação. Retenção/remoção dessas intenções, resposta a reset de senha e encerramento de todas as sessões são Q-05/Q-06. Biometria é exclusivamente desbloqueio do material local; não fabrica sid ou prova de autorização remota.

### 6.2 Refresh atômico e recuperação de senha

Refresh transacional: localizar hash do token/família/sid, bloquear sessão e token, verificar conta/sessão active, consumir token por CAS, criar **no máximo um sucessor por parent**, e gravar resultado de comando/estado no mesmo commit. Constraint única de parent e checagem da sessão impedem duas conexões de criar filhos distintos. Logout/remote revoke usa a mesma ordem de locks: se refresh vence primeiro, sucessor ainda será negado após revogação; se revoke vence, não há filho novo autorizado.

V2 refresh usa chave idempotente vinculada à sessão e fingerprint do pedido. Retry da mesma chave só recupera o mesmo resultado protegido enquanto sessão/token sucessor e receipt forem válidos; nunca cria outro filho. Receipt inválido/expirado leva a reautenticação ou reconciliação, não duplicação. V1 sem chave pode receber erro finito de token consumido/reautenticação; não prometer retry transparente impossível. Reuso de token com outra chave não emite sucessor; política adicional de encerrar toda família/avisar usuário depende Q-05. TTLs/grace periods não foram definidos.

Reset por e-mail: token opaco de purpose único, hash/proteção em repouso, consumo atômico, validação de destinatário e sem e-mail/senha/token em auditoria. Resposta pública uniforme para existência de conta; rate limits e prazo Q-05/Q-08. Link de reset não autoriza leitura de saúde. Vincular conta Google existente exige reautenticação/prova de posse das identidades; regras de linking/unlinking/recovery e efeito nas outras sessões precisam Q-05 antes de disponibilizar essa transição.

### 6.3 Conexões de fonte e exclusão concorrente

Cada `health_connection` tem owner, provider, generation e estado. Criar OAuth transaction captura account_generation, connection_generation, provider, purpose, redirect e nonce; expiração e PKCE conforme Q-05/Q-10. Desconectar incrementa generation sob lock, muda estado local e invalida transações/jobs/bindings dependentes. Revogação no provider pode ficar pending; status distingue desligamento local e revogação externa.

Sync/refresh/callback obtêm geração e a **revalidam no commit**, no mesmo domínio de serialização de disconnect/delete. Resposta antiga do provider após a barreira não insere raw/normalizados/tokens; operação relata `connection_revoked`, não sucesso vazio. Dados já importados antes da barreira permanecem (D10); coleta/gravação posterior exige conexão nova autorizada, não callback antigo. Exclusão da conta incrementa account_generation/bloqueia login/escritas e intents antes da remoção; afeta todos os providers. Não efetuar chamada externa dentro de uma transação longa: usar estado/outbox e revalidação curta.

## 7. Contratos HTTP, modelo operacional e persistência

### 7.1 v1 preservada; v2 para contratos novos

Contrato técnico escolhido para revisão: manter `/api/v1` com shapes e semântica de calendário atuais; publicar desenhos novos em `/api/v2`. Não trocar array por envelope ou end_date inclusivo por exclusivo no mesmo endpoint v1. Correções obrigatórias de owner/segurança valem para ambos e não têm bypass por compatibilidade. Duração de suporte/minimum client e rollout são Q-12.

V2: Bearer/sessão ausente/revogada →401; recurso alheio/inexistente →404; JSON/header malformado →400; tipos/campos/domínio de entrada inválidos →422; fingerprint/estado/overlap →409; stale revision →412; If-Match obrigatório ausente →428; indisponibilidade transitória →503/timeout retryable. Callback OAuth é exceção explícita ao Bearer: valida transação/purpose/owner/generation segura. Erros: `{code,message,field_errors?,request_id,retryable}`, sem payload sensível. Não usar código HTTP como classificação de fato clínico.

ETag forte em recurso v2: string opaca entre aspas, exemplo sintético `"fs:<uuid>:<revision>"`; resposta GET/mutação inclui ETag da **resource_current**, não do receipt antigo. If-Match deve conter um ETag forte único do mesmo tipo/ID; wildcard/lista/fraco não suportados retornam 400. Revisão é inteiro monotônico gerado pelo servidor, não contador do relógio.

O protocolo epoch/sequence de fila abaixo aplica-se aos comandos de jejum; outros recursos autenticados usam seus próprios contratos de chave/CAS. Login/cadastro e request de recuperação são públicos com proteção antiabuso; callbacks validam purpose/transação e refresh segue §6.2. Não exigir um epoch ou sid pré-existente para criar a primeira sessão autenticada. Isso não torna dados pessoais públicos.

Ordem de processamento dos comandos autenticados v2:
1. Validar envelope/header/JSON estruturalmente; autenticar/scope/owner/generation sem vazar recurso.
2. Validar epoch e receipt/key; fingerprint diferente dá 409; replay autorizado retorna receipt, sem reaplicar CAS.
3. Para comando novo: exigir If-Match quando devido (428), comparar revisão (412), validar dependências e transição/regra de domínio (409).
4. Em transação, repetir barreiras de autorização/conexão/versão e aplicar ou rejeitar; receipt definitivo não é produzido por erro de transporte/banco.
5. Falha 400/422 de parse/schema não consome chave; rejeição definitiva de domínio/CAS grava outcome e erro. Corrigir uma rejeição definitiva exige novo command_id após decisão consciente. Se estado terminal e versão também divergirem, 412 precede 409 invalid_transition.

V2 listas: `{items,next_cursor,as_of_revision}`, ordenação estável por campo+ID e cursor vinculado a owner, filtro e snapshot lógico; usar sequência de commit monotônica da conta/coleção e revisões visíveis naquele snapshot, não relógio de parede como versão; recursos excluídos são reautorizados e não vazam em snapshot. Página não repete itens por correção concorrente; expiração de cursor exige reiniciar snapshot explicitamente (prazo Q-08). Intervalos absolutos usam `from_inclusive,to_exclusive` com RFC3339; filtros civis exigem calendário/timezone e regra de atribuição. V1 continua seu intervalo inclusivo e array conforme inventário.

### 7.2 Mapa de contratos e capacidades

| ID / versões | Operações e contrato para revisão | Requisitos / validação |
|---|---|---|
| API-01 | v1 auth register/login/refresh/logout mantém identidade plana; v2 retorna `{user,session,tokens}` com propósito/claims e rotação do §6 | FR-01/02, SEC-07; T-02/T-18 |
| API-02 | v1 GET/PATCH users/me preservado; v2 perfil tipado, ausência mantém/null só em campo anulável; objetivos/históricos em recursos próprios | FR-03/18; T-03/T-22; Q-14 para campos/faixas/perguntas |
| API-03 | v1 conecta/callback mantém campos; novos clients v2 usam auth-url e callback transacional; GET status e DELETE connection com estado local/remote_revocation separado | FR-05, SEC-04; T-04/T-05 |
| API-04 | v1 sync 202/completed não vira job por renome; v2 sync tem execução/contagens/status honestos, summary com qualidade por medida | FR-06/08; síncrono ou job Q-10; T-05 |
| API-05 | v1 readiness/history/advanced/modalities mantém formatos/dias; v2 distingue registro/série, algoritmo/calendário/qualidade e insuficiência | FR-07/09/13; T-06/T-18 |
| API-06 | v1 workouts/histórico/catalog preservado; v2 owner implícito, source links, exercícios/unidades/data tipados, dedup e CAS | FR-10; T-07/T-21; Q-09/Q-10/Q-14 |
| API-07 | Muscles recovery/suggestion preserva grupos e formato v1; v2 identifica estimativa, versão e data de referência | FR-10, EDU-01; T-06/T-07 |
| API-08 | Feedback v1 adapter explícito dos campos existentes; v2 schema por pergunta, round-trip e timestamp único, sem calibrar fórmula automaticamente | FR-11; T-08; Q-14 sem descarte silencioso |
| API-09 | Health mínimo sem dado pessoal; readiness de infraestrutura distinto; seed só ambiente isolado, negado em produção | SEC-02/06, OPS-02; T-01/T-16 |
| API-10 | v2 fasting sessions/commands/revisions, detalhados abaixo; sem endpoint pause ou meta obrigatória | FST-01 a FST-15; T-09/T-10/T-11 |
| API-11 | v2 GET/PATCH preferences com ETag: widgets/order e prioridades; alterações por campo/revisão, conflito explícito | FR-04/20; T-19 |
| API-12 | v2 goals, body-measurements e training-targets: criar/ler/revisar/excluir próprios, instantes/unidades/versão, sem nutrição | FR-18, DAT-07; T-22; Q-14 fecha schema |
| API-13 | v2 auth/google start/callback, password-recovery request/confirm, biometria só no cliente; sem consentimento Fit implícito | FR-15/16/17, SEC-09; T-24; Q-05 |
| API-14 | v2 DELETE records/{type}/{id}, DELETE users/me e privacy requests operacionais autenticados | SEC-05, DAT-05; T-17; §11/Q-06 |
| API-15 | v2 conexões/providers/import jobs, regras de prioridade/links de fonte; Garmin só disponível após prova de API oficial | INT-07/08, FR-05/20; T-04/T-21; Q-10 |
| API-16 | v2 individuais history/compare/insights com amostra/método/calendário/versão; sem PDF nem população cruzada | FR-13/14, FST-15; T-20/T-23; Q-09 |
| API-17 | v2 notification-preferences, device-bindings se push, notifications in-app e acknowledgements | FR-21, FST-09; T-12; §9/Q-11 |
| API-18 | v2 GET sessions e DELETE sessions/{id}; dados de dispositivo mínimos, sem credenciais; revogação atômica | FR-22, SEC-07/10; T-25 |

Os recursos novos de perfil/insights/providers têm contratos de envelope, owner, CAS e qualidade comuns, mas enumerações/faixas/métodos não fornecidos permanecem Q. Não publicar OpenAPI fingindo finalização de campo em aberto. Nenhuma das operações v2 existe atualmente por esta descrição.

### 7.3 FastingSession, Command e endpoints

`FastingSession`: id, revision, status (active/completed), effective_started_at, effective_ended_at nullable, declared_started_at/declared_ended_at, timezone/offset de contexto, time_quality, created_at/updated_at, deleted flag/geração e vínculos das revisões. Instantes UTC serializados com milissegundos; duração base em milissegundos inteiros; seconds é conversão exata, apresentação/arredondamento não altera base. Owner interno, não campo editável. Notas protegidas em revisão própria/vínculo, com note_current próprio (id, texto simples UTF-8 e revisão) ou null na leitura autorizada, nunca metadado de log. amend_times e amend_note avançam a revisão do agregado da sessão; a revisão filha de nota não substitui o If-Match desse agregado. Não há target_duration obrigatório nem fase clínica persistida.

Envelope comum de mutação: `{command_id,client_session_id,sync_epoch,sequence,depends_on,base_revision?,payload}` + Idempotency-Key. payload temporal declara timestamp/offset/timezone e evidência de âncora quando disponível; o servidor não aceita “timezone” como prova de relógio correto. Resposta: `{receipt:{command_id,outcome,resulting_revision?,error_code?},resource_current?,server_received_at,reconciliation?}`. reconciliation descreve campos solicitados/aceitos e conflito técnico, sem corrigir silenciosamente. Receipt rejected não é 2xx de sucesso de sessão: status HTTP reflete erro de domínio, inclusive no replay.

| Endpoint v2 | Método / precondição | Entrada / resposta e efeitos |
|---|---|---|
| /fasting-sessions | POST, key+epoch/seq, sem If-Match inicial | payload start com declared_started_at/timezone; cria ID próprio ou erro de conflito; 201 aplicado, 409 domínio; receipt/revisão/outbox atômicos |
| /fasting-sessions/active | GET | `{resource_current:null ou Session}`; se política permitir múltiplas, schema será revisto em Q-03, não presumir escolha aprovada |
| /fasting-sessions/{id} | GET | Recurso próprio atual + ETag; 404 alheio/excluído; não inicia nem calcula sessão por GET |
| /fasting-sessions/{id}/stop | POST, key+If-Match | payload declared_ended_at; completed; invalida reminder; idempotente sem alterar fim por hora de recebimento |
| /fasting-sessions/{id}/revisions | POST, key+If-Match | operação amend_times/amend_note, campos solicitados e base_revision; nova revisão, estado não reaberto, conflito preservado |
| /fasting-sessions/{id}/revisions | GET | Revisões próprias conforme política de retenção/privacidade, sem expor notas de outra conta |
| /fasting-sessions/{id} | DELETE, key+If-Match | Fluxo de exclusão/tombstone; sem conversão implícita para completed/cancelled; ativo depende Q-03 |
| /fasting-sessions | GET | Listagem por snapshot/intervalo/status; calendário e filtro por início/interseção definidos em Q-09; não herdar BETWEEN v1 |
| /fasting-commands/{command_id} | GET | Receipt autorizado + referência/estado atual; hash/key não permite buscar comando de outra conta |
| /sync/epochs e /sync/reconcile | POST autenticado | Emitir epoch e negociar recovery de fila/versões; não reautoriza epoch desconhecido nem recria comando expirado como novo; detalhes de retenção/recovery Q-04/Q-07 |

### 7.4 Modelo de dados e regras de persistência

PostgreSQL é a fonte operacional/transacional (D12). BigQuery recebe analítico quando necessário; não é autoridade de sessão/token/command e não simula upsert via insert streaming. SQLite dev/teste é permitido só se invariantes realmente testadas; passar em SQLite não prova serialização/locks/constraints PostgreSQL.

| ID | Requisito técnico | Aceite futuro |
|---|---|---|
| DAT-01 | Transações/locks/constraints PostgreSQL para owner, CAS, refresh e invariantes | T-09/T-15 com duas conexões/instâncias; não substituir por lock de UI |
| DAT-02 | Origem/revisão/dedup e FKs efetivamente aplicadas | Repetir import não duplica fato; conflito entre fontes mantém originais e vínculo canônico auditável. T-05/T-21 |
| DAT-03 | Commit conjunto de sessão, revisão, receipt/piso, tombstone e intents | Crash antes do commit não confirma; após commit recupera o mesmo resultado; expurgo não habilita replay. T-09/T-11/T-15 |
| DAT-04 | Versionar dados/calendário/algoritmo/conteúdo e preservar histórico | Correção cria revisão; backfill não reinterpreta score antigo silenciosamente; desconhecido não vira observado. T-06/T-15 |
| DAT-05 | Delete e direitos de acesso/portabilidade abrangem cache/fila/analítico/backup conforme política | Sem export UI inicial; processo seguro com recibo; restore reaplica exclusões antes de servir. T-17; Q-06 |
| DAT-06 | Migração expand/contract versionada com inventário/dry-run/restore | Teste de schema antigo, falha/retomada, contagens e compatibilidade; nenhuma migração autorizada aqui. T-15 |
| DAT-07 | Objetivos, histórico corporal, metas, notas e preferências têm owner/revisão/unidade/proveniência | Nova meta não apaga anterior; nenhuma nota em fila/log como campo público; campos pendentes Q-14 não são preenchidos por default. T-19/T-22 |

Entidades a acrescentar/adaptar após aprovação: auth_sessions/devices e refresh_families; identity_links e password_reset_transactions separados de health_oauth_transactions; health_connections com generation; fasting_sessions/revisions/notes, commands/epochs/watermarks; preferences; goal_revisions/body_measurements/training_targets; canonical_events/source_links e deletion_tombstones; notification_preferences/intents/bindings/in-app; content_manifest e security_audit. As 16 tabelas atuais permanecem no plano de preservação do inventário §6; não é autorização de drop/rename.

Constraints técnicas: UUID/recurso só sob owner; revision monotônica por recurso; parent_refresh único; epoch/sequence e command_id únicos na conta/geração; FKs de sessão/revisão/source link; impossibilidade de completed sem fim ou fim<início; revisions imutáveis com política de retenção; nenhuma FK é assumida só por estar escrita em DDL. Índices owner+data/ID para leitura própria, chave fonte/event/revisão para dedup e outbox por estado. Constraint de uma ativa/overlap é proposta aguardando Q-03, não escolha fechada.

## 8. Saúde, qualidade, correlações e algoritmos

### 8.1 Integrações e qualidade por medida

| ID / origem | Contrato técnico | Aceite futuro |
|---|---|---|
| INT-01 / D01, S07/S11 | Schemas v1/v2 distintos, modelos de saída e contract tests reais | JSON de cada cliente faz round-trip sem campo perdido; Q-14 bloqueia schema não escolhido. T-18 |
| INT-02 / D06, D13 | Conexão/provider OAuth e refresh persistido com geração | Browser/nativo, desconexão e corrida externa testados separadamente de Google login. T-04/T-05 |
| INT-03 / D12 | Adapter operacional não anuncia equivalência BigQuery/SQLite indevida | Mesmas invariantes em PostgreSQL; analítico tem pipeline/schema próprios; testes remotos separados se autorizados. T-15 |
| INT-04 / D06, D09, D17 | Dedup preserva eventos originais, revisões e links para canônico; inválida derivados por versão | Evento repetido não soma passos/treino novamente; manual/importado não é apagado por matching incerto. T-05/T-21 |
| INT-05 / CUR-13 | Beam/CLI e dead letters, se mantidos, têm import/empacotamento e sink seguros | CLI de fixture executa no diretório documentado; sem payload saúde no log; runner suportado depende Q-10. T-16 |
| INT-06 / D01, D18 | Ambiente/URL explícitos em Android/web | Build de teste não escolhe produção por window/IP fixo; runtime Android testado, não só TypeScript. T-16/T-26 |
| INT-07 / D06 | Fit mantido; Garmin oficial condicionado; Health Connect fora | Prova documentada de condições/scopes/acesso e métricas Garmin antes de marcar available; indisponibilidade não é escondida como integração pronta. T-21; Q-10 |
| INT-08 / D09 | Importação automática de treino e registro manual com dedup revisável | Origem/método e vínculos preservados; conflito não elimina informação; alterações manuais não somem no próximo sync. T-07/T-21 |

Schema v2 de cada medida: `{value: valor tipado ou null,unit,kind,source_records[],method_id?,method_version?,recorded_at?,calendar_basis,missing_reason?,coverage}`. kind é `observed|estimated|derived|absent|unknown`; providers incluem `google_fit|garmin_connect|manual`. Cada source_record tem ID opaco/revisão/provedor; só owner acessa detalhes, não logs. Um registro com duração observada e fases estimadas usa quality por **campo**, não uma flag “medido” no objeto inteiro.

Regras inequívocas:
- absent → value=null e motivo tipado; desconhecido não é ausência nem zero observado. Coverage com denominador desconhecido é unknown, não 100%.
- observed preserva medição/declarado manual com fonte/método; manual não vira sensor. Zero realmente observado mantém value=0.
- estimated só pode representar estimativa legada identificada ou método explicitamente aprovado com entradas conhecidas; não preencher medida ausente para satisfazer D17.
- derived exige entradas/método/versão. Readiness é indicador derivado, não medida bruta fabricada. Regras neutras/redistribuição históricas ficam versionadas e visíveis, não são lançadas como observação.
- Desconhecido legado conserva valor/proveniência desconhecida; não inferir que fases foram medidas por terem números. placeholders zero de calorias legadas não são rotulados observados sem prova.
- coverage: `{status:known|unknown,available_count,expected_count:null ou contagem,definition_id}`; suficiência/confiabilidade e thresholds de insights dependem Q-09. Não inventar dados para produzir tendência.

Prioridade por indicador e source links ficam na conta, versionados. Falta da fonte prioritária é reportada; fallback/matching temporal e tratamento de divergência exigem Q-10. Nenhuma D autoriza descartar a fonte secundária ou somar medições duplicadas.

### 8.2 Readiness e dia civil

A fórmula atual é baseline comparativa, não fórmula clínica validada: sono 40%, FC 30%, atividade 20%, stress 10%; sem stress redistribui; categorias 80/60/40. Se faltar sono OU FC, não calcula. Tabela verdade: ambos presentes→tentar cálculo; só sono→indisponível; só FC→indisponível; nenhum→indisponível. Dado inválido não conta como presente válido. Atividade da mesma data e demais heurísticas atuais são identificadas como `algorithm_version=legacy` na migração, não corrigidas por renome.

V1 preserva suas datas atuais. V2 identifica `calendar_basis={kind:legacy_utc|civil_iana,timezone,assignment_rule,version}`. Séries migradas legadas são rotuladas legacy_utc; não tratá-las como “hoje local”. Novo dia civil, atribuição de sono que cruza meia-noite, comparação 7/30/90 e associação temporal de treino/correlação dependem Q-09. Não converter silenciosamente timestamps sem offset na migração. Testar São Paulo em horário local já diferente do dia UTC, DST de outro fuso e viagem.

D08 permite evolução somente com comparação documentada de versões, mesmas fixtures/períodos/qualidade, impacto de categorias/cobertura e critério aprovado antes da publicação. Histórico conserva versão anterior ou ambas claramente identificadas; backfill nunca substitui silenciosamente. D05 proíbe fator direto de jejum nessa fórmula. Nenhum coeficiente, validação clínica ou threshold de correlação é aprovado aqui.

Correlações descrevem associação da mesma pessoa, com tamanho/cobertura/janelas, incerteza e versão do método; não dizem “jejum causou” nem recomendam protocolo. Até Q-09 definir método e suficiência e EDU revisar linguagem, retornar unavailable com motivo, não gerar insight por heurística inventada. Sono/FC/atividade/readiness são as relações aprovadas; não criar nutrição ou exames por inferência.

## 9. Preferências, notificações, perfil e conteúdo

Preferências por conta têm revision/ETag, widget_ids/order e prioridade por indicador. PATCH requer base; alteração concorrente de mesma ordem retorna conflito com ambas as intenções, sem last-write-wins. Campos novos/IDs desconhecidos de outro cliente são preservados via negociação da versão, não descartados. Estado inicial/migração de ordem e persistência de tema precisam Q-12/Q-13, não escolhas aleatórias.

Notificações: preferências `{families:{fasting,muscle_recovery,readiness_daily},quiet_hours:{enabled,start_local,end_local,timezone},revision}`; cada família tem estado explícito de opt-in, nunca habilitada só por permissão do SO. No canal web, `GET notifications` serve caixa própria e `POST notifications/{id}/ack` registra leitura idempotente; não há subscription/service worker de browser push. Android local/push/híbrido e triggers por família ainda são Q-11; jejum livre não cria lembrete de meta obrigatória por padrão.

Binding de instalação Android, se necessário ao mecanismo escolhido: device_id opaco + owner/sid/generation, token protegido/canal, permissão e revision. Registrar/rotacionar/revogar só autenticado; trocar A→B revoga binding A e não entrega payload A a B. Outbox/intents usam resource_revision/schedule_version; stop/correção/delete/logout invalidam antes de envio. Revalidar estado/geração no worker. ACK de entrega não prova leitura nem ação de saúde. Mensagem atrasada consulta estado atual ao tocar e não reabre sessão. Conteúdo de lockscreen não inclui nota/saúde identificável.

Quiet hours impede envio/apresentação de aviso intrusivo no período configurado; caixa web pode ser consultada explicitamente. DST/viagem, adiar versus descartar e expiração são Q-11: não acumular automaticamente avisos obsoletos como se fossem instruções atuais. Nenhuma família específica de falha de sync é criada; UI preserva erro/retry/status.

Perfil: histórico corporal separado do valor atual; instantes/unidades, revisão, fonte manual e objetivo de referência. Metas de frequência/volume e múltiplos objetivos coexistem/evoluem; não converter goal singular em metas inventadas. Unidades/ranges/taxonomia/sugestões e efeito de correção em gráficos precisam Q-09/Q-14. Não incluir comida, ingestão ou diário de calorias.

| ID | Requisito de conteúdo educativo | Aceite futuro |
|---|---|---|
| EDU-01 / D03, D17 | Toda afirmação publicada tem método/origem, fonte/contexto, versão, revisor e limitações | Manifesto mapeia UI/API/histórico/avisos a versão revisada; sem evidência, conteúdo não é publicado. T-13 |
| EDU-02 / D03 | Fases do jejum são educação geral, não estado individual calculado por horas | Timeline distingue contador de assunto educativo; nunca afirma início de cetose/autofagia da pessoa em hora exata. T-13 |
| EDU-03 / D02, D05, D09, D14 | Sem incentivo a prolongar/competir, diagnóstico ou causalidade; parar acessível | Sem culpa por encerrar, prescrição, limite clínico inventado ou pressão por meta; avisos não comandam decisão médica. T-13 |
| EDU-04 / D03 | Elegibilidade/contraindicações e sinais de interrupção exigem revisão adequada | Público, gestação/lactação, menores, diabetes/medicações e transtornos alimentares não recebem liberação automática por checkbox. Responsável/textos Q-01. T-13 |

Roteiro educativo mantido para revisão, **sem faixa horária aprovada**: período após refeição (digestão/absorção não detectadas pelo timer), período sem nova ingestão (variação geral, não prova de uso de substrato), discussão de adaptações prolongadas (não “mais tempo = mais benefício”) e encerramento (fim de registro, não resultado clínico nem prescrição de realimentação). Cada explicação precisa fonte/revisão Q-01; nenhum texto clínico novo está validado nesta tarefa.

Correção de GF-18: manifesto editorial obrigatório por superfície, inclusive legada:
| Superfície atual | Tratamento de versão/migração | Evidência futura |
|---|---|---|
| ReadinessService._INSIGHT_MAP e insight persistido | Qualificar linguagem assertiva; preservar origem/versão do histórico e renderização revisada, sem substituir resultado numérico | Snapshot API/web/Android e histórico com “corpo recuperado” avaliado por revisão |
| Catálogo Android e advanced | Retirar “exatamente”/fases medidas quando sintéticas; identificar proxy e educação | Manifesto texto→evidência/revisor/versão, leitor de tela e offline |
| Timeline/avisos/sugestões de treino/perfil | Linguagem não médica, sem causalidade ou faixa fisiológica individual | Testes de copy e acessibilidade por locale/canal |
| Clientes antigos/caches | Não declarar texto antigo aprovado por estar em cache; cliente/conteúdo mínimo faz parte de Q-12 | Teste de versão antiga e rollout editorial, sem bypass do gate de evidência |

Temas/pt-BR/acessibilidade são produto aprovado; padrão mensurável e matriz de SO/leitores Q-13. UI sempre diferencia loading/vazio/dado/desatualizado/erro, sessão local/confirmada/conflito/rejeitada, token expirado, conteúdo sem revisão e permissão negada. Cronômetro não anuncia cada tick ao leitor; cor não é único indicador; escala/foco/contraste/controles são testados em Android e web.

## 10. Compatibilidade e migração explícita

| Cliente/capacidade | Baseline atual | Caminho técnico da v0.2 | Gate que não pode ser presumido |
|---|---|---|---|
| Web atual / Android oficial atual | Shapes v1, auth plano; Android tem lacunas reais de identity/refresh | Manter rotas/shapes v1 e corrigir consumidores em incrementos; adotar v2 para funções novas; comparar fixtures por versão | Versões mínimas e janela Q-12; não fingir que cliente antigo ganha jejum sem atualização |
| Novo web/Android oficial | Escopo aprovado D01/D09 | Ambos usam v2 e mesmos recursos/owner; paridade de jejum/treino/recuperação/mapa na entrega da funcionalidade | API primeiro isolada não conta como release inicial completa para usuário |
| mobile/ candidato legado e tabs remanescentes | Fonte preservada; cliente externo não tem JWT | Não excluir; não dar acesso anônimo para compatibilizar; atualizar auth ou retirar suporte mediante decisão explícita | Q-12 define suporte/retirada e comunicação; sem aprovação não afirmar que está suportado |
| Token v1 sem sid rastreável | JWT atual não tem vínculo operacional de sessão | v2 exige sessão rastreável criada por login/refresh seguro; cliente obtém resposta finita de reautenticação, nunca token inventado | Q-05/Q-12 fecham coexistência/revogação de tokens v1 e rollout do fix de refresh |
| Histórico e preferências existentes | Data UTC/arrays; seleção Android em memória, goal singular | Marcar legado, preservar arrays/v1 e dias inclusivos; v2 com schemas/versionamento e migração aditiva | Default de novas preferências, calendário/metas e backfill Q-09/Q-12/Q-14 |
| Texto/insight antigo | Copy inline/persistida pode ser assertiva | Manifesto editorial, renderização qualificada e versão de conteúdo; forma do campo v1 preservada | Sem reclassificar copy antiga como revisada; mínimo cliente/conteúdo Q-01/Q-12 |

Migração futura em fases autorizadas: inventariar implantação/schema e clientes → backup/restore em cópia segura → expandir tabelas/colunas/revisões/source links → backfill rastreável/quarentena de ambíguos → disponibilizar adapters v1/v2 → atualizar clientes e verificar coexistência → liberar internamente/beta/produção com gates → considerar contract/drop somente em outra mudança explicitamente aprovada. Nenhum rename de raw em BigQuery resolve sozinho sua divergência com o operacional.

V1 arrays continuam arrays, end_date inclusivo continua inclusivo e as três colunas do histórico não viram objeto maior sem versão. JSON de auth e booleans de feedback precisam adapters explícitos, não casts TypeScript. Correção de owner e ausência de segredo fraco são mandatórias para os dois contratos, não funcionalidades opcionalmente negociadas. Retirada de cliente inseguro exige decisão de suporte, não exceção de autorização.

## 11. Privacidade, qualidade operacional e lançamento

### 11.1 Exclusão e direitos

Exclusão individual usa registro canônico por tipo e ID próprio: fasting, workout, feedback, fasting_note, body_measurement, goal ou evento de origem, com semântica de derivados/fonte explicitada no schema. DELETE v2 exige sessão autorizada, chave e If-Match; retorna 202 com operation_id enquanto efeitos distribuídos não terminaram, não “apagado de todo backup” imediatamente. Concluir retorna estado verificável, não prazo inventado. Excluir active, política de reimportação de evento apagado e dependências de revisão precisam Q-03/Q-06 antes de ativar essas transições.

Excluir conta bloqueia novas autorizações/commits, incrementa geração, revoga sessões/conexões/bindings e cancela intents em transação; remoção operacional/analítica segue operação rastreada, idempotente e com recibos saneados. Conta A não apaga B. Dados pré-existentes não são apagados por mero disconnect. Manter tombstone mínimo por identidade de origem/geração conforme política para impedir recriação por fila/import; não armazenar saúde ou segredo no tombstone por conveniência.

Sem exportação na UI inicial. Processo de acesso/portabilidade aplicável pode ser operacional autenticado, com request_id, prova de identidade, escopo e entrega protegida; API técnica candidata `privacy/requests` separa access/portability/account_deletion e acompanhamento próprio. Canal, responsável, base de tratamento, prazos e formato legal são Q-06; não inventar política jurídica nem prometer que endpoint por si cumpre obrigação.

Restore deve reconciliar ledger de exclusão/revogação/gerações antes de abrir leitura/escrita/import/avisos. Como esse ledger sobrevive ao domínio de falha, por quanto tempo e sob qual chave precisa Q-06/Q-07. Na ausência de evidência de reconciliação, sistema restaurado fica em quarentena, sem enviar reminders ou revalidar epochs/creds antigos por default. Não confundir quarentena técnica de dados com obrigar pessoa a continuar jejum; stop local permanece possível.

### 11.2 Requisitos não funcionais

| ID | Contrato para revisão | Critério de aceite futuro |
|---|---|---|
| NFR-01 | Separar durabilidade de commit, crash de processo, rollback de software e desastre | Processo perdido com PostgreSQL preservado recupera mesmos recibos; desastre só promete RPO/RTO aprovados. TS-36/37; Q-07 |
| NFR-02 | Tempo/ordem não dependem do wall clock do servidor | Metadata recebida não altera intervalo; time_quality e revisão evitam regressão/silêncio. T-10 |
| NFR-03 | SLO/latência/capacidade/limites explícitos, não inventados | Q-07/Q-08 precisam valores antes de ensaio de carga/gate; teste não pode passar com parâmetro ausente |
| NFR-04 | Contraste/fontes/leitor/foco/controles acessíveis nas duas plataformas | TalkBack/leitor web percorrem fluxos sem depender só de cor/tick; padrão/matriz Q-13. T-14 |
| NFR-05 | pt-BR e calendário explícito por versão | Formatos corretos; UTC não é anunciado como dia local; locale novo não é presumido. T-10/T-23 |
| NFR-06 | Observabilidade e auditoria minimizadas, sem telemetry clínica por inferência | Canários de notas/tokens/medidas não aparecem em logs; auditoria de acesso protegida por finalidade/retenção. T-17; Q-06/Q-15 |
| NFR-07 | Reprodutibilidade e verificação por cenários, não só IDs/cobertura | Locks/toolchain/fixtures/clock fake e camadas reais; testes PostgreSQL e runtime Android/web além de mocks. T-16/T-26 |

Criptografia em repouso/transporte é aprovada; serviço de chaves, rotação, custo e topologia GCP não foram escolhidos. SQLite de teste não satisfaz teste de concorrência PostgreSQL por substituição. Não há SLO, limite de notas, rate limit, expiração de epoch/receipt, tolerância de skew ou mínimo de amostra aprovado; são Q, não placeholders que o código possa completar arbitrariamente.

### 11.3 Rollout, rollback e analytics

| ID | Requisito consolidado | Aceite futuro |
|---|---|---|
| OPS-01 / D20 | CI unitário/integrado/API/Android/web/regressão por PR e evidências | Gatilhos para master/branches de revisão, proteções e baseline lint comprovados; doc PR não dispara deploy. T-16 |
| OPS-02 / D12, D19 | Ambiente explícito, health/readiness e porta/provider/segredos coerentes | Produção sem PostgreSQL/config válida falha fechada; teste nunca escolhe produção por heurística. T-16 |
| OPS-03 / D12 | Migrações aditivas, backup/dry-run/restore antes de release autorizado | Contagens, invariantes, recuperação e compatibilidade avaliadas; sem migração executada nesta tarefa. T-15 |
| OPS-04 / D20 | Interna→beta→produção, rollback seguro e compatível | Desabilitar novo start/import não remove caminho de parar/reconciliar dados/histórico; não fazer downgrade para bypass inseguro; limites/coortes Q-12. T-16 |
| OPS-05 / D19, D20 | Aprovação por fase e produção bloqueada até testes críticos aprovados; autorizações separadas | Evidências e responsável/versionamento registrados; spec, merge e deploy não são a mesma aprovação. Q-12 e nova Goldfish obrigatórios |

Rollback de aplicação deve manter schema expandido e receipt/versões compatíveis, sem apagar sessão confirmada com store preservado. **Restore de desastre não recebe promessa automática de perda zero:** RPO/RTO/topologia são Q-07. Se snapshot puder perder confirmação, o runbook deve explicitar detecção/reconciliação de versões e comunicação, nunca restaurar sessão ativa/reminder como atual sem verificar ledger. Sem resposta aprovada a essa pergunta, GF-16 permanece pendente e produção bloqueada.

Flag de release atua separadamente em novos starts, importação, escrita/reconciliação, leitura/histórico e entrega de avisos, com política revisada. Não desligar “tudo” impedindo stop local ou restaurar worker antigo que ignora generation/schedule_version. Critérios de avanço/recuo e incidentes exigem números e responsáveis Q-07/Q-12, não contagem arbitrária de dias/coortes.

Analytics operacional técnico é distinto de correlações individuais aprovadas D05/D16. Nenhuma aprovação para marketing/telemetry de saúde é inferida. Eventos/rastreadores de produto, finalidade/base/retention e consentimento são Q-15. Auditoria D19 pode registrar ator técnico/ação/resultado/versão sob proteção e necessidade, sem copiar corpo de saúde. Logs/dead letters não contêm token, nota ou payload clínico; metrics agregadas não garantem anonimato por si.

## 12. Plano testável: grupos preservados e casos com oráculos

**Nenhum teste abaixo foi executado nesta tarefa.** É desenho para implementação futura autorizada. Camadas indicadas não são ambientes acessados. Cada caso terá fixture sintética, clock/provider controlado e artefato atual do runner com exit status; dependência Q não resolvida fica **bloqueada**, não “passou”, “pulou” ou resultado esperado inventado.

| Grupo estável | Abrangência / casos específicos |
|---|---|
| T-01 | Owner/conta, credenciais, seed/CORS e barreiras; TS-18, TS-24, TS-25, TS-34, TS-45 |
| T-02 | Auth/login/refresh/logout remoto e concorrência; TS-18 a TS-23 |
| T-03 | Perfil/painel/round-trip de preferências; TS-48, TS-49 |
| T-04 | OAuth purpose/state/provider e disconnect; TS-20, TS-24, TS-25, TS-51 |
| T-05 | Ingestão/dedup/qualidade; TS-24, TS-30, TS-31, TS-51, TS-52 |
| T-06 | Algoritmos/contribuições/históricos e versão; TS-29, TS-30, TS-31, TS-32, TS-50, TS-56 |
| T-07 | Treino/exercícios/mapa/recuperação; TS-44, TS-52 |
| T-08 | Feedback round-trip/nullability; TS-57 |
| T-09 | Máquina/headers/idempotência de jejum; TS-03 a TS-06, TS-09, TS-14 a TS-17 |
| T-10 | Tempo/calendário/listagem/histórico; TS-02, TS-07, TS-08, TS-27, TS-32, TS-53 |
| T-11 | Offline/fila/replay/conta; TS-02 a TS-06, TS-09 a TS-13, TS-19, TS-33, TS-35, TS-59 |
| T-12 | Android avisos e web in-app; TS-38 a TS-40 |
| T-13 | Educação/copy/estimativas/sem causalidade; TS-41, TS-42, TS-50 |
| T-14 | Temas/pt-BR/acessibilidade; TS-54 |
| T-15 | PostgreSQL/constraints/migration/restore; TS-09 a TS-11, TS-21 a TS-25, TS-35 a TS-37 |
| T-16 | CI/branches/ambiente/builds/regressão/rollout; TS-43 a TS-45, TS-51, TS-55 |
| T-17 | Exclusão/portabilidade/logs/tokens; TS-33 a TS-35, TS-38, TS-47, TS-58 |
| T-18 | Coexistência v1/v2 e migração; TS-26 a TS-28, TS-43 |
| T-19 | Preferências por conta/ordem/prioridade; TS-49 |
| T-20 | Correlações individuais; TS-50 |
| T-21 | Viabilidade provider/import/dedup treino; TS-51, TS-52 |
| T-22 | Objetivos/medidas/metas evolutivas; TS-48 |
| T-23 | Históricos/estatísticas/períodos e comparações; TS-53 |
| T-24 | Google login, biometria e recuperação; TS-20, TS-46, TS-47 |
| T-25 | Dispositivos/sessões/auditoria; TS-18, TS-19, TS-22, TS-38, TS-58 |
| T-26 | Jornadas runtime Android oficial/web; TS-44, TS-59 |

| Caso | Fixture/ação e camada | Resultado esperado / artefato futuro |
|---|---|---|
| TS-01 | Documental: cruzar D/DEC/GF/Q e aprovação da versão | Sem D perdida/equivalência numérica; Q aberto bloqueia aceite associado; assinatura/versão não presumidas |
| TS-02 | API+Android: stop declarado 10h offline, reconnect 14h | Preserva 10h solicitado e quality; aceita segundo regra Q-02 ou apresenta revisão, nunca substitui silenciosamente por 14h |
| TS-03 | API: completed recebe amend_times/amend_note; repetir stop | Corrige por revisão sem reabrir; stop terminal dá conflito; sem pause; limites/overlap Q-02/Q-03 não inferidos |
| TS-04 | Integrado PostgreSQL+fila: stop(A)→start(B)→stop(B), entrega fora de ordem | Dependências aguardam; IDs/revisões canônicos consistentes; nenhum B confirmado antes de predecessor necessário |
| TS-05 | Offline: predecessor rejeitado, kill/restart, correção e nota descendentes | Conteúdo íntegro e bloqueado para resolução; não descartar descendentes nem trocar chave automaticamente |
| TS-06 | Duas instalações alteram mesma sessão/nota ou ordem de intervalos | CAS aceita apenas a revisão elegível; outra intenção vira conflito, sem last-write-wins; política de overlap Q-03 |
| TS-07 | API: início/fim declarados válidos, servidor retrocede/troca instância | Duração pelo intervalo declarado não muda; received_at é só metadata; nenhum stop é negado só pelo relógio de recepção |
| TS-08 | Android: wall clock ±, DST, viagem, reboot/perda de âncora | Âncora contínua usa monotônico; perdida marca needs_review; sem negativo/truncagem silenciosa ou reinício da sessão |
| TS-09 | Integrado: comando confirmado, receipt expurgado com piso válido, replay | Reconciliation_required ou recibo preservado, nunca reaplicar; número de sessões/filhos invariável |
| TS-10 | API: epoch desconhecido/revogado ou sequência com lacuna | Não recriar epoch/chave; preservar dependências; piso não avança sobre lacuna sem resolução |
| TS-11 | Restore: snapshot antigo e fila antiga tentam revalidar epoch | Quarentena/reconciliação antes de servir; garantias definitivas dependem Q-04/Q-07; não declarar teste aprovado com política ausente |
| TS-12 | Android/web: start receipt rev1 chega depois de completed rev2 | Cache não regride, timer/aviso não reabrem; resource_current separado de receipt |
| TS-13 | API/cliente: resposta antiga chega após tombstone | Não ressuscita recurso/nota; leitura posterior respeita owner/generation/delete |
| TS-14 | Contrato HTTP: If-Match ausente, fraco, wildcard, malformado e stale | Respectivamente 428, 400, 400, 400, 412 no comando novo autorizado; ETag citado corresponde ao recurso |
| TS-15 | API: mesma chave com JSON igual/diferente; 422 corrigido antes de receipt | Igual replay; fingerprint diferente 409; parse/schema inválido não consome chave; nova intenção após rejeição definitiva usa chave nova |
| TS-16 | API: comando novo contra terminal e base stale | 412 precede invalid_transition; sem mudança, receipt definitivo conforme contrato |
| TS-17 | PostgreSQL: crash antes/depois de commit + requests paralelos com mesma key | Antes: sem confirmação; depois: mesmo receipt/efeito, não outra sessão; chave não burla autorização |
| TS-18 | API com barreira: remoto revoga sid entre validação inicial e escrita | Após commit de revogação não há commit do sid; access assinado é recusado; B não revoga/lista A |
| TS-19 | Android: stop pending, logout offline, login como B/depois A | B não vê/envia fila A; A reautenticada reconcilia conforme Q-05/Q-06; intenção não some silenciosamente |
| TS-20 | Auth: login Google com aud/nonce inválido, mesma e-mail e propósito Fit trocado | Negado sem auto-link por e-mail; propósito Fit não emite login; linking legítimo depende prova/Q-05 |
| TS-21 | Duas conexões PostgreSQL fazem refresh do mesmo parent simultaneamente | No máximo um sucessor; receipt/retry ou erro finito, nunca dois filhos distintos |
| TS-22 | Refresh versus revoke com barreira e ordens invertidas | Se revoke primeiro, nenhum token novo autorizado; se refresh primeiro, sucessor negado após revoke |
| TS-23 | Resposta de refresh perdida, mesma chave e token consumido com outra chave | Mesma chave só mesmo sucessor válido; outra não cria filho; receipt expirado exige fluxo seguro, não retry infinito |
| TS-24 | Provider simulado bloqueia resposta; disconnect acontece antes do commit | Sem raw/token/normalizado novo após barreira; histórico prévio preservado; status de revogação remoto honesto |
| TS-25 | Callback antigo chega após mudança de generation/delete da conta | Não reconstitui token/conexão/usuário; rejeita replay/propósito e escreve apenas auditoria minimizada |
| TS-26 | Fixture cliente v1 lê history com end_date=dia final e array | Exatamente shape/semântica v1, dia final incluído; sem items imposto ou data reinterpretada |
| TS-27 | Cliente v2 pagina snapshot enquanto há correção/exclusão concorrente | Sem duplicação/revisão antiga vazada; filtro e cursor ligados à conta; snapshot expirado explícito |
| TS-28 | Cliente/token antigo incompatível tenta acessar v2/recurso B | Negação finita/upgrade/reautenticação conforme Q-12; nunca bypass por versão |
| TS-29 | Unitário/contrato: quatro combinações de sono/FC | Só ambos válidos calculam; ausência isolada ou conjunta dá unavailable; não preencher missing |
| TS-30 | Payload misto: sono observado, fase legada estimada, calorias desconhecidas, passos zero observado | Rótulos por campo e coverage coerentes; ausente null, zero observado mantido; sem imputação automática |
| TS-31 | Migração: valor legado sem prova de origem e expected_count desconhecido | kind/coverage unknown, sem “medido”/100% inventados; original preservado |
| TS-32 | Saúde: 22h São Paulo, UTC outro dia, sono cruzando data, viagem | v1 baseline preservada e identificada; v2 segue calendar_basis/Q-09; comparação não muda versão silenciosamente |
| TS-33 | Offline: evento/sessão excluída é reenviada em fila/import antigo | Tombstone/generation impede reaparição; intenção conflitante reportada, não confirmada como nova |
| TS-34 | Privacidade: usuário errado pede exclusão/acesso/portabilidade | 404/negação sem dado alheio; processo legítimo possui recibo e entrega protegida, sem export UI inicial |
| TS-35 | Restore de snapshot anterior à exclusão | Ledger/generation reconciliados antes de leitura/escrita/avisos; se não comprovado, quarentena, não ressuscitação |
| TS-36 | Banco íntegro: confirmar sessão/receipt e matar processo | Recupera mesmos IDs/revisões/outbox, sem perda ou reexecução; não depende da memória do servidor |
| TS-37 | Desastre de storage/região com política de backup selecionada | Medir RPO/RTO e efeitos sobre stop/receipt/revogação contra Q-07; sem política aprovada permanece bloqueado |
| TS-38 | Binding Android roda token/reinstala e troca conta A→B | Binding A revogado, sem mensagem de A para B; token protegido e status rastreável |
| TS-39 | Stop/correção/deletion, quiet hours, permissão negada e aviso atrasado | Sem novo intent obsoleto; tocar consulta estado; negar permissão não bloqueia timer; web sem browser push |
| TS-40 | Escolha local/push e gatilhos/silêncio por família Q-11 | Somente mecanismo/casos aprovados; sem lembrete obrigatório por alvo inexistente ou família sync-failure |
| TS-41 | Manifesto editorial: API/inline/histórico/avisos/catalog | Toda superfície tem versão/revisor/evidência; texto legado não é aprovado por cache; sem fase clínica individual |
| TS-42 | Cliente antigo/offline sem conteúdo revisado disponível | UI explica indisponibilidade/versão; não gera alegação por fallback nem bloqueia stop; mínimo editorial Q-12 |
| TS-43 | Matriz cliente/contrato e rollout selecionado | Cada combinação tem suporte/upgrade definido e fixture; sem promessa irrestrita ao mobile/ sem JWT |
| TS-44 | Runtime Android oficial e web: autenticar→perfil→dados→treino→mapa/recuperação | Mesmas capacidades D09, dados próprios, estimativas qualificadas; não basta compilar TypeScript |
| TS-45 | CI/lint/build/regressão e config negativa | Runner evidencia alvo/casos/exit; CORS/seed/segredo/banco falham de modo esperado; nenhum teste toca produção |
| TS-46 | Android: biometria válida, cancelada e token remoto revogado | Só desbloqueia local; cancelamento não autentica; backend ainda nega revogado |
| TS-47 | Reset: inexistente/existente, token reutilizado/expirado e segredo-canário | Resposta anti-enumeração, uso único e segredo ausente dos logs; prazos/efeito em sessões Q-05 |
| TS-48 | Perfil: goal singular migrado, dois objetivos, peso/medidas/metas por revisão | Sem apagar histórico ou inventar metas/unidades; schema/faixas Q-14 antes de aceitar; sem diário alimentar |
| TS-49 | Duas plataformas reordenam widgets/alteram prioridade simultaneamente | Conflito CAS explícito; sem perda/duplicação de widgets ou origem secundária; preferências pertencem à conta |
| TS-50 | Correlação com amostra insuficiente, qualidade faltante e sessão adicionada | Unavailable até critério Q-09; sem causalidade; readiness baseline não muda por sessão de jejum |
| TS-51 | Garmin sem acesso oficial confirmado e Fit simulado | Garmin não aparece available; Fit preservado/testado com sandbox; verificação de condições não supõe credenciais existentes |
| TS-52 | Treino manual/importado e evento duplicado de Fit/Garmin | Preserva originais/source links; canônico não duplica volume nem apaga edição incerta; política de matching Q-10 |
| TS-53 | 7/30/90/custom e comparação individual, sessão corrigida | Bordas/unidades/versões/cobertura claras, sem dupla contagem, PDF, relatório consolidado ou dado de outro usuário; agregados Q-09 |
| TS-54 | Android/web pt-BR em light/dark/system, fonte ampliada e leitores | Foco/labels/contraste/alvos verificados, sem color-only/tick spam; padrão e matriz Q-13 |
| TS-55 | Release interna→beta→produção, falha de gate e rollback | Sem promoção sem evidência/aprovação; parar/histórico/reconciliação permanecem seguros; sem worker que ignora generation |
| TS-56 | Mesmas fixtures de readiness legacy nos limites 40/60/80 e stress ausente | Resultados iguais por versão; mudança nova requer comparação registrada e Q-09, sem backfill silencioso |
| TS-57 | Feedback false/null/ausente e todos os campos do formulário | Round-trip após schema Q-14; sem campo silenciosamente descartado nem aprendizagem não autorizada |
| TS-58 | Canários em nota/token/medida e auditoria de acesso sensível | Logs/analytics sem payload; eventos autorizados mínimos, protegidos e retidos conforme Q-06; auditoria não é compartilhamento |
| TS-59 | Android offline start→nota→stop→corrigir→kill→reconnect; web consulta mesmo histórico | Comandos e revisões convergem ou apresentam conflito sem perda silenciosa; timer não reabre por receipt antigo; paridade D01 |

## 13. D aprovadas → DEC originais → requisitos

Mantém o mapeamento por assunto do registro aprovado. “Atendido documentalmente” não significa DEC inteira fechada; Q indica o que falta. D15 não tem DEC própria e não será artificialmente equiparada a DEC-15.

| D | DEC relacionadas | Requisitos/contratos v0.2 e decisões incorporadas |
|---|---|---|
| D01 | DEC-03/04/16 | FST-01/06/07, FR-12, API-10: jejum API+Android+web inicial, recursos centrais |
| D02 | DEC-04/13 | FST-01/03/04/05/13, API-10: livre contínuo, sem pausa/alvo obrigatório, edição histórica |
| D03 | DEC-04/12/13/15/17 | FST-02/07/09/10/14/15, EDU-01 a EDU-04: timer/timeline/estatística/nota/lembrete |
| D04 | DEC-11/13/19 | FST-08/13/14, DAT-03, API-10: offline Android completo, sync/dedup e conflito sem perda |
| D05 | DEC-06/14/17/19 | FR-14, FST-12, API-16: associação descritiva não causal, sem fator direto no score |
| D06 | DEC-08/10 | INT-02/07, FR-05/20, API-15: Fit e Garmin condicionado, dedup, Health Connect fora |
| D07 | DEC-03/07 | FR-04/20, API-11: widgets ordenáveis por conta sincronizados; tela e widget opcional de jejum |
| D08 | DEC-05/06/19 | FR-07/08/09, DAT-04: evolução comparativa, preservação de históricos e fatores/qualidade |
| D09 | DEC-03/06/08/10/16 | FR-10, INT-08, API-06/07/15: paridade, import/manual, recuperação/mapa e dedup |
| D10 | DEC-08/09/13/15 | SEC-01/05, DAT-05, API-14: privado, excluir individual/conta, preservar histórico desconectado, sem export UI mas com direitos legais |
| D11 | DEC-03/12/15/17 | FR-21, FST-09, API-17: famílias opcionais, quiet hours, Android/web in-app, exclusões preservadas |
| D12 | DEC-02/10/19 | DAT-01/06, INT-03, OPS-02/03: PostgreSQL operacional, BigQuery quando necessário, GCP, SQLite condicionado |
| D13 | DEC-05/08/18 | FR-01/15/16/17, SEC-09, API-13: e-mail/senha/Google, biometria local/reset, Fit separado |
| D14 | DEC-05/06/17 | FR-03/18, DAT-07, API-12: objetivos simultâneos/evolução, histórico corporal/metas/sugestões não médicas |
| D15 | Sem DEC dedicada; restringe DEC-04/14 | FR-18 e seção 2: sem diário alimentar/nutrição por inferência; calorias de atividade existentes preservadas |
| D16 | DEC-03/06/13/19 | FR-13, FST-15, API-16: 7/30/90/custom, comparação/tendências/gráficos individuais, sem PDF |
| D17 | DEC-05/06/08/19 | FR-08/20, DAT-02/04, seção 8: origem, prioridade, quality/coverage, sem imputação |
| D18 | DEC-03/20 | FR-19, NFR-04/05: temas, pt-BR, identidade por plataforma e acessibilidade |
| D19 | DEC-01/02/09/15/18/19 | FR-22, SEC-01 a SEC-10, OPS-05: sessão/dispositivo, crypto/tokens/auditoria e gates |
| D20 | DEC-01/16/19 | OPS-01 a OPS-05, NFR-07, T-01 a T-26: incrementos, interna/beta/produção, CI/PR/evidências sem autorizar código |

| DEC original | Aspecto consolidado | Pendência explícita |
|---|---|---|
| DEC-01 | D19/D20 fixam gates e aprovação por fase | Q-12: responsáveis, aprovação Fase 0/versão e integração |
| DEC-02 | D12/D19 escolhem PostgreSQL/GCP e proteção | Q-06/Q-07: serviços, chaves, topologia, store real/restore |
| DEC-03 | D01/D07/D09/D11/D16/D18 fixam plataformas/paridade/UX | Q-12/Q-13: matriz de suporte/legado e ambientes |
| DEC-04 | D01–D04/D15 fixam produto jejum livre/sem pausa/offline/notas | Q-01/Q-02/Q-03: elegibilidade, tempo/cancel/overlap |
| DEC-05 | D08/D13/D14/D17 ampliam identidade/perfil/qualidade | Q-05/Q-14: linking/reset e schemas/faixas/feedback |
| DEC-06 | D05/D08/D09/D14/D16/D17 fixam evolução/versionamento/qualidade | Q-09/Q-10: método, calendário, validação e matching |
| DEC-07 | D07 fixa ordem/seleção por conta e tela/widget | Q-12/Q-14: migração/defaults, schema de preferências |
| DEC-08 | D06/D09/D10/D13/D17 fixam fontes/privacidade e separar Google login | Q-05/Q-10: acesso oficial/scopes/protocolo provider |
| DEC-09 | D10/D19 fixam dados privados/sem compartilhar | Q-06: acesso operacional mínimo, não produto multiusuário |
| DEC-10 | D06/D09/D12 fixam direção de import/fontes/store | Q-10: sync de saúde síncrono/job, Beam/Dataflow; D04 não decide essa arquitetura |
| DEC-11 | D04 exige offline iniciar/parar/corrigir/anotar e sync automático | Q-02/Q-03/Q-04/Q-05: políticas temporais/fila/retention/logout |
| DEC-12 | D03/D11 fixam famílias/canais/quiet hours e exclusões | Q-11: Android mecanismo, triggers, DST/defer/expiry |
| DEC-13 | D02/D03/D04/D10/D16 fixam edição/notas/sem pausa/exclusão/histórico | Q-02/Q-03/Q-09: cancel/overlap/dias e agregados |
| DEC-14 | D05 autoriza correlações, não efeito direto no readiness | Q-09: método/suficiência/linguagem sem causalidade |
| DEC-15 | D03/D10/D11/D19 fixam privacidade/exclusão/segurança | Q-06/Q-15: bases/prazos/acesso/portabilidade/analytics |
| DEC-16 | D01/D09/D19/D20 fixam plataformas/gates/interna-beta-produção | Q-12: versões, rollout, proteções e compatibilidade |
| DEC-17 | D03/D05/D08/D09/D14/D17 fixam conteúdo não médico/qualidade | Q-01/Q-09: fontes/revisores/contraindicações/suficiência |
| DEC-18 | D13/D19 fixam Google, reset, biometria local, sessões remotas | Q-05: linking/recovery/TTL/grace/reuso e armazenamento web |
| DEC-19 | D04/D08/D12/D16/D17/D19/D20 impõem integridade/validação/gates | Q-04/Q-07/Q-08/Q-09: nenhum valor SLO/RPO/TTL/skew/amostra inventado |
| DEC-20 | D18 fixa pt-BR/temas/acessibilidade | Q-13: padrão mensurável, SO/leitores e evidências |

## 14. Perguntas objetivas ainda abertas ao Product Owner

Parâmetros ausentes são bloqueios de aceite, não defaults “a definir no código”. Responder com escopo/valor, responsável e referência de aprovação; se for investigação técnica, registrar quem valida e qual evidência, sem transformar falta de dado em decisão.

| ID | Pergunta / alternativas que exigem definição | Requisitos e gates dependentes |
|---|---|---|
| Q-01 | Qual público/elegibilidade e revisão clínica/editorial? Quem aprova fontes/contraindicações/textos e eventual faixa educativa? | EDU-01 a EDU-04, FST-10, FR-14/18; sem conteúdo não revisado |
| Q-02 | Quais horários declarados/futuros/retroativos aceitam confirmação automática? Como usuário confirma tempo após reboot/clock inconsistente, e há tolerância aprovada? | FST-02/03/13, GF-02; não usar reconnect como fim |
| Q-03 | Uma ativa por conta e intervalos sem overlap são a política? Qual significado de cancelar e de excluir ativa? Como tratar edições que cruzam intervalos? | FST-04/05, API-10; sem pausa continua decidido |
| Q-04 | Qual máximo de idade offline e política de epochs/receipts/pisos/expurgo/reconciliação? Como vincular esses prazos à privacidade? | FST-08, DAT-03/05, GF-05 |
| Q-05 | Quais TTLs/reuso/revogações de sessão/reset/linking/biometria, armazenamento web e retenção de intenção no logout offline? Reset encerra quais sessões? | FR-02/15/16/17/22, SEC-07/09; revogar remoto efetivamente continua obrigatório |
| Q-06 | Quais finalidade/base/consentimentos, prazos por dados/notas/revisões/logs/backups/tombstones, canal de acesso/portabilidade e prova de identidade? Como ledger de exclusão é protegido? | SEC-03/05/10, DAT-05, GF-15; export UI continua excluído |
| Q-07 | Quais serviços/topologia/custos GCP, garantias por domínio de falha, RPO/RTO, fonte durável do ledger/epochs e procedimento de desastre? | DAT-01/06, NFR-01, OPS-03; GF-16 pendente |
| Q-08 | Quais SLO/capacidade, timeout/rate limit, limites de página/intervalo/notas, cursor e parâmetros operacionais mensuráveis? | SEC-08, NFR-03, OPS-02/04; sem teste de limite com valor inventado |
| Q-09 | Qual dia de sono/readiness, timezone/atribuição histórica, agregados/estatísticas e critérios de suficiência/cobertura/comparação/correlação/sugestão? | FR-07/13/14/18, FST-15, NFR-05, GF-14 |
| Q-10 | Há acesso/condições verificadas Garmin? Quais scopes/métricas/matching manual-importado, fallback de prioridade e arquitetura de sync de saúde/Beam suportada? | FR-05/06/20, INT-02/05/07/08 |
| Q-11 | Android usará local, push ou híbrido? Quais eventos por família, quiet hours com DST/viagem, defer versus descartar, expiração e conteúdo da lockscreen? | FR-21, FST-09, API-17; sem browser push |
| Q-12 | Quais versões/clientes legados suportar, janela de migração/token/conteúdo, coortes/flags/rollback/responsáveis/proteções e testes críticos de aprovação por fase? Qual default/migração de preferências existentes? | FR-12, OPS-01/04/05, GF-01/19 |
| Q-13 | Qual padrão mensurável de acessibilidade e matriz Android/navegadores/leitores? Preferência de tema persiste por conta ou dispositivo? | FR-19, NFR-04/05; pt-BR/temas já aprovados, WCAG específico não presumido |
| Q-14 | Quais campos/enums/faixas/unidades de perfil/metas/medidas/feedback, nullability, política de senha e migração de goal singular/booleans? | FR-01/03/11/18, DAT-07, API-02/08/12 |
| Q-15 | Além dos gráficos/correlações individuais aprovados, haverá analytics de produto? Quais eventos/finalidade/retention/consentimento são permitidos? | NFR-06, SEC-05; nenhuma telemetry de saúde implícita |

## 15. Riscos do inventário → requisitos → testes

| Risco original | Decisões / requisitos v0.2 | Cenários e gate |
|---|---|---|
| S01 | D10/D19; SEC-01/07, FST-11 | TS-18/25/34; owner e barreira por commit obrigatórios |
| S02 | D12/D19; SEC-02/03, OPS-02 | TS-45/58; fail-closed/config/chaves |
| S03 | D10/D19; SEC-03/05/10, DAT-05 | TS-34/35/47/58; Q-06/Q-07 |
| S04 | D06/D13; SEC-04/09, INT-02 | TS-20/24/25/51; purpose/generation/prova provider |
| S05 | D12; DAT-01/06, INT-03, NFR-01, OPS-03 | TS-21/35/36/37; PostgreSQL e recuperação Q-07 |
| S06 | D03/D05/D08/D09/D14/D17; FR-08/09, EDU-01 a EDU-04 | TS-30/31/41/42/50; sem falsa medição/causalidade |
| S07 | D01/D07/D09/D13; FR-01/02, INT-01/06 | TS-18 a TS-23, TS-26/44/59; runtime e compat |
| S08 | D19/D20; SEC-06, API-09, OPS-02 | TS-45; sem seed produção |
| S09 | D19; SEC-06 | TS-45; política de origens explícita |
| S10 | D10/D13/D19; FR-02/22, SEC-07, DAT-05 | TS-18/19/38/46; conta/fila/cache/biometria |
| S11 | D02/D03/D14/D17; SEC-08, INT-01 | TS-14 a TS-17, TS-48/57; Q-08/Q-14 |
| S12 | D04/D06/D07/D09/D12/D17; DAT-02/03/04, INT-04 | TS-04/06/09/17/21/49/52; DAG/CAS/dedup |
| S13 | D19; SEC-03/10, NFR-06, INT-05 | TS-45/58; auditoria não replica payload sensível |
| S14 | D03/D10/D11/D14; SEC-05, DAT-05, EDU-01 a EDU-04 | TS-33 a TS-35, TS-41/42/58; Q-01/Q-06 |
| S15 | D19/D20; OPS-01 a OPS-05, NFR-07 | TS-43 a TS-45, TS-55; CI, versões e gates |

## 16. Resposta Goldfish, resumo de alterações e aprovação

A [matriz completa de resposta](04-elephant-v0.2-goldfish-resolution.md) cobre GF-01–GF-20 com correção, contrato técnico, casos e aceite. Avaliação autoral: **11 resolvidos na especificação, 8 parcialmente resolvidos, 1 pendente**. O documento original de revisão permanece intacto; estados não são fechamento independente nem aprovação automática. Entre os 17 bloqueadores originais, 9 ainda são parciais/pendentes nesta avaliação: GF-01/02/05/08/14/15/16/17/19.

Mudanças v0.1→v0.2:
- Produto D01–D20 incorporado, com novos requisitos para paridade, correções/notas, correlações, Garmin condicionado, identidade/perfil, qualidade, avisos e UX.
- Protocolo offline substitui modos incompatíveis com D04, separa relógios/intenções/receipts/estado e explicita replay/expurgo/recovery.
- Revogação/refresh/conexões têm barreiras/CAS; v1 e v2 têm migração e formas distintas; qualidade por campo, manifesto editorial e cenários com oráculos respondem GF.
- PostgreSQL/GCP e direitos de exclusão/access/portability refletem D12/D10 sem autorizar migração nem fabricar retenção/SLO/RPO.
- Questões Q tornam dependências não aprovadas objetivas e bloqueáveis; não se afirma que a existência desta versão valida fórmula, conteúdo, integração ou testes.

**Gates atuais:** decisões de produto registradas; versão técnica v0.2 pendente de nova Goldfish independente e aprovação explícita do proprietário. Aprovação do inventário, responsáveis/valores Q aplicáveis e critérios críticos precisam registro. Nenhuma implementação, merge, migração, deploy ou publicação de ambiente foi iniciada.

Validação desta entrega é **documental**: referências/IDs/cobertura D/DEC/GF/S, contratos e cenários, diff restrito à spec e à matriz de resposta, preservação das fontes originais. Nenhum teste de produto, build, lint funcional, ensaio de carga, provider real ou operação remota foi executado. A próxima etapa é revisão Goldfish, não implementação.
