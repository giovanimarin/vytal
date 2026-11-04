# Vytal — especificação mestre Elephant

**Versão documental:** 0.1.0 — rascunho para revisão. **Data:** 2026-11-04.
**Estado:** PENDENTE DE APROVAÇÃO. Nenhuma implementação ou release autorizada por este documento.
**Base:** `docs/egm-phase-0-inventory`, commit `5af4d029a3924b9c1d841233ed7333cb8661d884`.
**Fontes:** [AGENTS.md](../../AGENTS.md), [inventário Fase 0](00-inventory.md), [prompt Elephant](prompts/01-elephant.md).

## 1. Autoridade, classificação e rastreabilidade

O proprietário solicitou esta especificação, preservação das funcionalidades existentes e tratamento de `mobile/vytal-app/` como Android oficial. Autorizou somente documentação/publicação em branch própria e tentativa de PR. Não autorizou produto de jejum, escolhas ainda abertas, alterações funcionais, merge ou deploy.

O prompt Elephant tem como pré-requisitos inventário aprovado e decisões do proprietário. A solicitação atual permite **redigir o rascunho**; não comprova aprovação formal do inventário nem resolve suas perguntas. Esses gates permanecem explícitos. O [README EGM](README.md) pode continuar com status anterior; esta entrega não altera esse arquivo nem afirma que exista execução autônoma EGM.

Três classes são usadas sem equivalência entre elas:

1. **ATUAL — comprovado na base:** fatos do código ou validações registradas na Fase 0; não garantem funcionamento em produção/dispositivo.
2. **PROPOSTO — futuro sujeito a revisão:** todos os requisitos, contratos, modelos e planos a partir da seção 4. A palavra “deve” expressa condição de aceitação **se o requisito e suas decisões forem aprovados**, nunca uma decisão já tomada.
3. **DECISÃO DO PROPRIETÁRIO — aberta:** entradas DEC-01 a DEC-20. Alternativas não foram escolhidas. Uma recomendação técnica candidata é identificada como tal. Ausência de resposta não aprova alternativa.

Identificadores estáveis: CUR = fato atual; FR = funcionalidade preservada/evoluída; FST = jejum proposto; SEC = segurança; INT = integração; DAT = dados; NFR = qualidade; OPS = operação; EDU = conteúdo; T = teste futuro; DEC = decisão. Não reutilizar IDs removidos: marcar como substituídos e indicar sucessor. S01–S15 referenciam os riscos do inventário, não novos IDs de requisitos. Critérios de aceitação estão nas tabelas e cenários; testes T são **planejados**, não executados nesta fase.

**Regra de completude:** nenhum TBD relevante vira default silencioso. Antes de implementar um grupo, resolver suas DEC, atualizar contratos/exemplos e obter aprovação da versão. Antes de release, resolver todos os bloqueadores aplicáveis, executar Goldfish e testes, e obter autorização de implantação separada.

## 2. Produto, usuários e fronteiras

### 2.1 Objetivo e escopo

ATUAL: Vytal organiza dados de smartwatches via Google Fit e mostra indicadores heurísticos de sono, FC, atividade, stress e prontidão. Backend FastAPI, Android Expo oficial, web Next.js, outro app mobile candidato legado, scripts Beam e infraestrutura GCP estão presentes.

PROPOSTO: preservar acesso às capacidades existentes, corrigir contratos/isolamento/persistência e tornar origem, ausência e incerteza dos dados visíveis. Acrescentar, **se aprovado**, um controlador de jejum para registrar intervalos escolhidos pelo usuário, acompanhá-los, consultar histórico e receber lembretes opcionais com conteúdo educativo revisado. Não diagnosticar metabolismo, prescrever jejum ou prometer efeitos individuais.

Não são compromissos desta versão: equivalência completa web/Android, descarte do app legado, nova integração Health Connect, algoritmos clínicos, treinamento de ML, dieta personalizada, gamificação/streaks, pagamentos, compartilhamento com terceiros, painel profissional, loja Android ou monitoramento clínico. São escolhas adicionais, não implícitas no controlador.

### 2.2 Perfis e jornadas candidatos

Perfis abaixo são hipóteses funcionais para revisão, não pesquisa de usuários nem definição de elegibilidade clínica/comercial (DEC-03/04/17).

| Perfil / jornada | Comportamento atual | Jornada futura proposta / critério de sucesso |
|---|---|---|
| Pessoa que consulta dados próprios | Login, perfil, fontes e indicadores existem, com lacunas | Autenticar → validar identidade → conectar fonte → sincronizar → ver dado observado/estimado/ausente e histórico; nunca acessar outra pessoa |
| Pessoa que configura painel | Android inicia painel vazio e seleciona widgets em memória | Adicionar/remover indicadores sem duplicação; retomar configuração conforme política aprovada; erro de um widget não impede demais |
| Pessoa que registra atividade | Web/candidato legado têm treino/modalidades/músculos | Preservar cadastro de treino e histórico nesses clientes; não prometer essas telas no Android oficial sem DEC-03 |
| Pessoa que usa jejum voluntariamente | Não existe funcionalidade | Ler limites/elegibilidade → iniciar sessão → acompanhar → encerrar ou cancelar → conferir histórico; negar notificação não impede operações básicas |
| Pessoa sem conectividade / com troca de aparelho | Não há fila de comandos de saúde offline demonstrada | Mostrar dado local como desatualizado; operações offline somente segundo DEC-11; reconciliar sem duplicar nem ocultar conflito |
| Responsável por conteúdo/operação | Não há painel/editor nem processo EGM autônomo verificado | Revisar conteúdos versionados, evidências, migrações e release por processo definido; nenhuma permissão administrativa implícita |

## 3. ATUAL — base de preservação e limites comprovados

Fonte detalhada: inventário §§3–9, com caminhos de código e matriz das 24 operações. Este resumo não substitui a evidência nem promove heurísticas a fatos clínicos.

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

Preservar funcionalidades não significa perpetuar vulnerabilidade, dados inventados, contratos quebrados ou exposição em produção. Correções propostas devem ter migração e testes de compatibilidade; mudanças de significado/cálculo ou retirada de tela exigem revisão explícita (DEC-03/06/16).

## 4. PROPOSTO — requisitos funcionais do produto existente

Cada linha tem critério verificável. Todos permanecem pendentes de aprovação. “Mesma fixture” significa mesmos dados sintéticos e versão de algoritmo, não validação fisiológica.

| ID / origem | Requisito proposto | Aceitação / dependências |
|---|---|---|
| FR-01 / CUR-02, S07 | Cadastro/login devem concluir com tokens e identidade consistente no cliente; perfil opcional não pode impedir autenticação válida | Ao cadastrar/entrar, userId corresponde ao sub e `/users/me`; senha cliente/servidor coincidem; falha não deixa flag autenticada sem sessão. Contrato candidato §8; DEC-05 |
| FR-02 / CUR-02, S10 | Renovar sessão sem recursão e encerrar limpando credenciais, perfil, cache e notificações da conta | Refresh inválido termina fila com erro finito, não repete refresh de refresh; logout chama revogação quando possível; acesso de outra conta não reutiliza dados/cache. Logout offline e política de revogação: DEC-18 |
| FR-03 / CUR-02/03 | Manter onboarding e edição do perfil, com validação e política de limpeza de campos | PATCH sem campo mantém valor; null deve ter semântica documentada antes de mudar cliente; dados inválidos são rejeitados com erro por campo, hash nunca retorna. Faixas, enumerações/obrigatoriedade: DEC-05 |
| FR-04 / CUR-03/04 | Manter painel e catálogo dos nove indicadores existentes; evitar duplicação de blocos advanced e falha total do painel | Cada widget tem loading/vazio/erro/dado; ID selecionado aparece uma vez; adicionar/remover não apaga outros; reset e persistência/order dependem DEC-07 |
| FR-05 / CUR-05 | Conectar, consultar estado e desconectar fonte com estado verdadeiro e revogação documentada | UI distingue disconnected/authorizing/connected/expired/error; erro de status não aparece como conexão comprovada; desconexão interrompe novas coletas. Falha externa de revogação é visível; política de dados já coletados: DEC-08/09 |
| FR-06 / CUR-06 | Sincronizar com idempotência, progresso/resultado honesto e proveniência; preservar leitura sem bloquear todo painel | Retry do mesmo intervalo/evento não duplica normalizados; falha de fonte não vira sucesso vazio; sync anterior fica consultável com data de atualização. Síncrono ou job: DEC-10 |
| FR-07 / CUR-07 | Preservar readiness, contribuições, insight e histórico; versão de algoritmo e insuficiência de dados explícitas | Fixture com sono/FC calcula score/categoria de acordo com versão; sem ambos mostra indisponível, não zero; stress ausente redistribui; fronteiras 40/60/80 testadas. Alterar dia da atividade, pesos ou cortes requer DEC-06 e estratégia de backfill |
| FR-08 / CUR-04/05/08, S06 | Exibir sono/FC/passos/calorias/stress distinguindo observado, derivado, estimado e ausente | Estágio sintetizado nunca é rotulado medido; zero observado difere de ausência; múltiplas atividades não somem; origem/método e data são acessíveis na UI. Conector futuro: DEC-08 |
| FR-09 / CUR-08 | Preservar advanced e sua explicação; alinhar rótulos às entradas disponíveis | Duração isolada não afirma mudança de horário do sono; métricas indisponíveis têm motivo; versão/método e janela constam na resposta; revisão clínica/editorial antes de alegação nova. DEC-06/17 |
| FR-10 / CUR-08/10/11 | Preservar treinos, catálogo, modalidades, recuperação/sugestões nas plataformas atuais | Treino+exercícios gravam atomicamente; data omitida tem regra explícita; indicadores derivados são invalidados; fixtures históricas não usam now para período errado. Android equivalente depende DEC-03; versão algorítmica DEC-06 |
| FR-11 / CUR-09 | Manter feedback diário sem descartar silenciosamente respostas do formulário | Contrato inclui cada pergunta aprovada e timestamps consistentes; POST/GET round-trip; sem dados≠erro fatal; nenhum peso de readiness muda por feedback nesta versão. Nomes/mapeamento/cardinalidade DEC-05 |
| FR-12 / CUR-10/11/13 | Preservar web e evidência dos caminhos legados durante compatibilização | Navegação e dados próprios continuam acessíveis nos clientes suportados; matriz de versões compatíveis registrada; não apagar mobile/ nem tabs oficiais sem DEC-03; modo demo nunca habilita acesso real sem JWT. DEC-16 para suporte/retirada |

## 5. PROPOSTO — controlador de jejum

### 5.1 Escopo candidato e requisitos

O desenho a seguir permite avaliar uma proposta coerente, sem escolher público, protocolos, durações máximas/mínimas, metas, benefícios ou frequência de uso. Não há protocolo 16:8/18:6, limite médico, meta automática ou recomendação de prolongar aprovada. Todos esses parâmetros dependem de DEC-04/17; release de jejum fica bloqueada até resolução.

| ID / origem | Requisito proposto | Critério de aceitação / decisão |
|---|---|---|
| FST-01 / CUR-15 | Iniciar sessão voluntária associada exclusivamente ao usuário autenticado, com confirmação do registro e estado de sincronização | Toque simples/retry com mesma chave resulta em um ID; falha não exibe “salvo”; não exige fonte Google, wearable ou dados de readiness. Escopo de tela/elegibilidade DEC-03/04 |
| FST-02 / inventário §10 | Cronômetro mede tempo desde início registrado, não número de ticks da UI | Fechar/reabrir, suspender e reiniciar aparelho não reiniciam sessão; offline/relógio alterado mostram qualidade temporal e estimativa, sem tempo negativo. Modelo temporal §5.3 |
| FST-03 / inventário §10 | Encerrar com horário final e duração consistente, sem exigir atingir meta ou revelar motivo de saúde | Encerrar sessão ativa é sempre acessível; meta, se existir, não bloqueia parada; encerramento confirmado fica no histórico e cancela lembretes associados. Meta e mensagem DEC-04/12/17 |
| FST-04 / inventário §10 | Cancelar é operação distinta de encerrar e de excluir dados | Sessão cancelada não é contada como concluída; retry não cria evento novo; UI explica efeito. Retenção/apresentação/remoção de canceladas DEC-13/15; não inferir consentimento para guardar indefinidamente |
| FST-05 / S12 | Impedir conflitos e sobreposição segundo política aprovada, com controle de concorrência no servidor | Proposta candidata: no máximo uma ativa por owner, intervalo de outra sessão não pode sobrepor; dois starts simultâneos não passam ambos. Sem sobrescrever silenciosamente. Sobreposição histórica/pausa DEC-11/13 |
| FST-06 / S05 | Persistir início/fim/estado/versão e recuperar sessão ativa independentemente do processo do app | API confirma apenas após commit durável; falha parcial não cria sessão sem comando correspondente; restauro mantém IDs e owner. Banco e retenção DEC-02/15 |
| FST-07 / inventário §10 | Histórico com lista/detalhe, intervalos, duração, estado e origem temporal | Ordenação estável e paginação sem duplicar itens; vazio/erro/offline diferenciados; filtro de período com timezone explícito; canceladas distintas. Agrupamento e edição DEC-13 |
| FST-08 / S07/S12 | Modelar ações offline como pendentes, sem aparentar confirmação do servidor | Resultado depende do modo A/B de §5.4; conexão restabelecida reconcilia por comando, conflito exige resolução explícita e não mescla sessões. DEC-11 bloqueia implementação offline |
| FST-09 / inventário §10 | Lembretes opcionais com opt-in, cancelamento e estado de entrega honesto | Permissão negada não bloqueia timer/histórico; stop/cancel/edição invalidam agendamento; entrega duplicada não dispara ação; não garantir exatidão Android. Mecanismo/frequência/conteúdo DEC-12 |
| FST-10 / AGENTS, S06 | Explicar fases somente como conteúdo educativo versionado, com fontes/limites, sem diagnóstico pelo contador | Tela não afirma cetose/autofagia/“queima” individual após X horas; texto explicita que tempo não mede estado fisiológico; conteúdo sem revisão aprovada não é publicado. EDU-01 a EDU-04, DEC-17 |
| FST-11 / S01/S14 | Consultar/alterar somente sessões próprias e incluir controles de privacidade/exportação/exclusão | Conta A não lista/lê/altera sessão B por ID; cancelar não significa excluir; exclusão/retention respeitam política aprovada e dados não reaparecem de fila offline antiga. SEC-01/05, DAT-05 |
| FST-12 / preservação | Jejum não modifica automaticamente prontidão, treino, sono ou perfil clínico | Ativar/desativar a proposta mantém resultados das mesmas fixtures de readiness; nenhum score de adesão clínica ou ranking por duração é criado. Integração futura com indicadores depende DEC-14 |

### 5.2 Máquina de estados candidata

DEC-13 deve aprovar se este conjunto é suficiente. **Não há implementação atual.** Proposta mínima: persistidos `active`, `completed`, `cancelled`; ausência de sessão é representada por null, não por linha `idle`. `completed` significa apenas “registro encerrado”, não atingir objetivo, benefício ou sucesso médico. Pausa, planejamento e reabertura não são presumidos; se aprovados, esta máquina, schema, notificações e testes devem ser revisados.

Estados locais de sincronização, separados do domínio: `confirmed`, `pending`, `conflict`, `failed`; carregamento/sem rede não altera automaticamente um registro confirmado. Um estado `completed + pending` é apenas intenção local até o servidor aceitar o comando.

| Estado inicial | Comando | Estado final candidato | Resposta / efeito |
|---|---|---|---|
| Nenhuma ativa | start | active | Commit de sessão; novo ID/version; recibo idempotente |
| active | start, chave diferente | Sem transição | 409 active_session_exists; cliente apresenta sessão canônica |
| active | stop | completed | Registra ended_at e duração; cancela intenção de lembretes |
| active | cancel | cancelled | Registra cancelled_at; invalida lembretes; não confunde com exclusão |
| completed/cancelled | Novo start sem sobreposição | Nova active | Não altera a sessão antiga |
| Qualquer estado | Mesmo comando com mesma chave/corpo | Nenhuma transição adicional | Retorna recibo do comando, sujeito à autorização; recurso atual pode ter versão posterior |
| completed/cancelled | Novo stop/cancel/retomada | Sem transição | 409 invalid_transition; edição futura somente via contrato aprovado |
| Qualquer estado | Versão esperada divergente | Sem transição | 412 version_mismatch; atualizar estado e pedir resolução, não repetir mudando versão automaticamente |
| ID de outro owner/inexistente | Ler ou comandar | Sem transição | 404 em contrato candidato, sem revelar existência |

Se stop/cancel concorrentes usam a mesma versão, somente um vence; o perdedor consulta estado atual e não converte o resultado. Cancelar e excluir são ações separadas, com confirmação adequada. Interrupção segura não pode depender de conexão: quando offline, a UI permite registrar intenção de parada local, explica pendência e jamais orienta manter o jejum até o servidor responder (FST-03/08, EDU-03).

### 5.3 Tempo, calendário e mudança de relógio

PROPOSTA: armazenar instantes absolutos UTC com precisão de milissegundo, além do timezone IANA do contexto e horários de recebimento do comando. Serialização RFC 3339 com offset explícito; datas sem offset não são timestamps válidos. Duração de concluída = `ended_at - started_at`, não diferença entre relógios de parede locais. Duração não pode ser negativa; `ended_at >= started_at`. Intervalos usam `[início,fim)`; intervalos adjacentes não se sobrepõem. Cancelada usa intervalo até cancelled_at para a regra candidata de sobreposição, mas não recebe duração “concluída”.

Em start/stop online, proposta candidata usa horário do servidor como efetivo. Correção retroativa/horário do cliente só se DEC-13 aprovar; não aceitar silenciosamente timestamp arbitrário como comprovado. A resposta inclui `server_time` e `time_quality` (`server_confirmed`, `client_estimated`, `needs_review`) para distinguir confirmação de precisão fisiológica, que nunca é alegada.

No mesmo processo, UI projeta duração a partir da última âncora confirmada e do tempo monotônico disponível; alteração do relógio do SO não deve alterar o tempo decorrido já medido. Após kill/reboot ou offline sem âncora monotônica contínua, a hora civil pode estar errada: exibir estimativa/necessidade de reconciliação. Não prometer monotonicidade entre reinícios ou correção de início real sem dados. Ao recuperar rede, reconciliar com servidor e informar correção relevante, sem reescrever histórico silenciosamente.

Troca de timezone muda apresentação, não duração. Guardar timezone original permite explicar o contexto; histórico usa o timezone de filtro/presentação explicitamente selecionado (DEC-13). Transições DST, meia-noite, viagem e diferenças UTC/local têm fixtures. Qualquer tolerância de skew e limiar de aviso será parâmetro a decidir em DEC-19, sem número inventado.

### 5.4 Offline e múltiplos dispositivos: alternativas abertas

| Alternativa DEC-11 | Comportamento candidato | Trade-off e teste obrigatório |
|---|---|---|
| A — servidor confirma início | Offline permite consultar cache/acompanhar sessão confirmada; novo start aguarda rede. Stop/cancel offline registra intenção local pendente e aviso | Menos conflitos; início offline indisponível. Testar parada segura com reconnect após start em segundo aparelho |
| B — registro offline provisório | Início/fim/cancelamento locais geram comandos identificados e horários estimados; servidor decide ao reconectar | Mais continuidade, mas relógio/conflito precisam revisão. Testar dois starts offline em aparelhos diferentes e conflito com histórico já aceito |

Para ambos, fila é particionada por conta, não contém tokens em payload de comando e tem persistência protegida; um comando dependente de start só é enviado após start aceito. Usar ID de comando e ID provisório mapeado para ID canônico; ordenar dependências, não confiar só na ordem de chegada. Retry de timeout consulta recibo com mesma chave. Não aceitar “última gravação vence” para fundir sessões. Em conflito, mostrar estado canônico e intenção local; alternativas descartar/revisar/recriar dependem de autorização e regras aprovadas, nunca gerar sessão sobreposta automaticamente. Logout/troca de conta bloqueia envio da fila antiga; exclusão/tombstone impede ressuscitação.

### 5.5 Notificações candidatas

Separar estado de sessão de `disabled`, `permission_required`, `scheduled`, `delivery_unknown`, `failed`, `cancelled` do lembrete. Permissão do SO não é consentimento automático para push remoto nem conteúdo sensível na lockscreen. O momento de pedir permissão, marcos/meta, horário silencioso, expiração e escolha local/push dependem DEC-12/15/17.

Opção local usa agendamento do SO e reconcilia após reboot/retomada/alteração. Opção push exige token de dispositivo por conta, worker/entrega, expiração e tratamento de token inválido; infraestrutura não existe hoje. Solução híbrida exige deduplicação por `(session_id, reminder_type, schedule_version, device_id)` e política para vários aparelhos, ainda aberta. Não introduzir serviço de foreground/alarme exato ou permissões especiais sem justificar necessidade e aprovação de UX/compatibilidade.

No commit de stop/cancel, invalidar a intenção de envio no servidor; tentativa de entrega em andamento pode escapar ao cancelamento. UI e texto precisam lidar com aviso atrasado: tocar consulta estado atual e não reativa sessão. Atualizar/cancelar lembretes locais ao sincronizar. Não afirmar garantia de entrega “no segundo exato”; medir atraso/ausência com dados mínimos e explicitar limitações Android Doze, economia de bateria e permissão negada.

## 6. PROPOSTO — conteúdo educativo e segurança de uso

Nenhuma janela temporal ou alegação metabólica nova é validada por esta especificação. Não foram consultadas fontes clínicas externas nesta fase; portanto, não existe biblioteca de fases pronta para publicação. Aprovação de conteúdo exige evidências e responsável em DEC-17.

| ID / origem | Requisito proposto | Critério de aceitação |
|---|---|---|
| EDU-01 / AGENTS, S06 | Conteúdo distingue explicação geral, medida observada e inferência; mantém fonte, população, limitações, versão e revisor | Cada afirmação publicada liga-se a evidência revisada, data/versão e contexto; alegação sem fonte/aprovação permanece indisponível, não gerada por fallback |
| EDU-02 / FST-10 | “Fases” são organização educativa aproximada, não estado calculado do corpo | Cronômetro e conteúdo têm rótulos separados; nunca “você entrou em autofagia/cetose às X horas”. Se faixas temporais forem aprovadas, apresentar incerteza e variação individual, sem converter sensor/horas em diagnóstico |
| EDU-03 / FST-03 | Orientações não incentivam prolongar, compensar alimentação ou competir por duração; encerramento permanece visível | Negar permissão, falhar sync ou não atingir meta não produz cobrança, ranking, culpa ou bloqueio de encerrar; conteúdo explica limites e procura de orientação adequada sem aconselhamento individual |
| EDU-04 / S14 | Revisar elegibilidade, contraindicações e sinais de interrupção sem coletar perfil clínico excessivo | Revisão explícita para menores, gestação/lactação, transtornos alimentares, diabetes/medicações e condições relevantes; decidir restrições/textos/processo em DEC-04/17. Não emitir liberação clínica com checkbox nem inventar limites terapêuticos |

### 6.1 Roteiro candidato para explicações das fases

As categorias abaixo organizam conteúdo, **não são estados fisiológicos detectados** nem intervalos clínicos escolhidos. Não são uma sequência obrigatória de protocolos. São exemplos de abordagem editorial para avaliação em DEC-17; cada texto e eventual faixa temporal precisará de fonte/revisão antes de entrar no produto.

| Tema educativo candidato | Exemplo de explicação geral, pendente de revisão | Limite que deve acompanhar |
|---|---|---|
| Período após a última refeição | “Digestão e absorção não terminam em um horário universal depois de comer. Uma contagem de horas não mede esses processos.” | O início do registro é uma declaração do usuário; não identifica o fim da digestão ou um estado metabólico |
| Intervalo sem nova ingestão registrado | “O uso de fontes de energia pode variar durante períodos sem alimentação e entre pessoas. O cronômetro registra tempo, não mede essas variações.” | Não afirmar depleção de glicogênio, oxidação de gordura ou benefício individual a partir da duração |
| Discussão de adaptações em períodos mais prolongados | “Mais tempo registrado não confirma uma mudança metabólica específica nem garante mais benefício. Explicações sobre cetonas e processos celulares exigem contexto e evidência.” | Não estabelecer hora de entrada em cetose/autofagia nem recomendar prolongamento; evidência ausente impede publicar a alegação |
| Encerramento do registro e retomada da alimentação | “Encerrar termina este registro de tempo. Isso não comprova um resultado clínico nem determina, por si só, como cada pessoa deve se alimentar.” | Não prescrever quantidade/refeição ou protocolo de realimentação; situações de risco requerem orientação adequada, não uma instrução derivada do timer |

A UI pode apresentar temas sem faixas horárias ou faixas aproximadas se explicitamente aprovadas. Não selecionar automaticamente uma “fase atual do seu corpo”. Se houver destaque por tempo, ele é navegação do conteúdo educativo, deve dizer isso e nunca substituir `time_quality` ou o estado da sessão.

Exemplo **apenas de linguagem candidata**, sujeito à revisão editorial: “O tempo registrado não indica em que estado metabólico você está. Respostas ao jejum variam. Estas explicações são gerais e não substituem orientação profissional.” Esse texto não substitui revisão de contraindicações, política de público ou fundamentação das explicações. O app deve permitir consultar limites antes de iniciar e durante a sessão; não exigir relato de sintomas como condição para parar.

## 7. PROPOSTO — segurança, integração e requisitos não funcionais

### 7.1 Segurança e privacidade

| ID / riscos | Requisito proposto | Aceitação testável / decisões |
|---|---|---|
| SEC-01 / S01 | Derivar owner de sub e autorizar cada leitura/escrita antes de acessar recurso; consulta filtra owner no servidor | Matriz A/B de todas as rotas pessoais falha sem side effect; IDs v1 divergentes são rejeitados, não ignorados; novas rotas não aceitam user_id no corpo. Compartilhamento/admin exige contrato próprio DEC-09 |
| SEC-02 / S02 | Produção falha fechada sem segredos fortes/configuração de provider obrigatória; rotação verificável | Instância com segredo default/ausente não fica pronta; logs não o exibem; rotação invalida/renova conforme política de sessão DEC-18; não confiar em ENVIRONMENT como seletor de banco |
| SEC-03 / S03/S13 | Proteger tokens Google, refresh, filas e backups; mínimo privilégio e segredo fora de código, URL, analytics/logs | Inspeção de logs sintéticos não encontra tokens/corpos de saúde; acesso a token store é separado/restrito; processo de rotação/revogação e restore documentado. Mecanismo de proteção/gestão de chaves DEC-02/15/18 |
| SEC-04 / S04 | OAuth com transação temporária vinculada a owner/provider, state de uso único/expiração, redirect aprovado e fluxo nativo/web explícito | Replay, state expirado/trocado e redirect não permitido são negados; callback browser pode funcionar sem Bearer somente por transação segura; não expõe tokens em deep link. TTL/PKCE/provider e retorno DEC-08/18 |
| SEC-05 / S14 | Política de finalidade/consentimento, retenção, acesso/exportação/exclusão e revogação antes de novas categorias | Usuário vê fluxo real de armazenamento; export/delete tem autenticação e isolamento; revogar fonte interrompe coleta; exclusão cobre cache/fila/derivados e backups conforme política. Prazos/base jurídica/processo DEC-15 |
| SEC-06 / S08/S09 | Separar demo/desenvolvimento/produção; CORS com origens explícitas e endpoints de dev indisponíveis em release | Seed em configuração de produção é negado antes de alteração; cliente dev não chama produção por heurística window; origens não permitidas falham preflight; demo só usa dados sintéticos. DEC-01/16 |
| SEC-07 / S10 | Tokens/caches por usuário; revogar sessão e limpar dados locais de forma consistente | Troca A→B não mostra dados/fila/lembrete de A; reidratação de token expirado não libera telas com dados obsoletos; refresh concorrente termina sem deadlock. Cookie versus armazenamento web e sessão offline DEC-18 |
| SEC-08 / S11/S12 | Validar tipos, tamanho, enumerações, intervalo/data/timezone, entradas extras e volume; limitar abuso sem impedir parada local | JSON inesperado não é descartado silenciosamente em novos contratos; limites explícitos testados em bordas; sem SQL interpolado por entrada; rate limits por endpoint/configuração aprovados em DEC-19; erro não divulga recurso alheio |

### 7.2 Integração

| ID / riscos | Requisito proposto | Aceitação / dependências |
|---|---|---|
| INT-01 / S07/S11 | Fonte única versionada dos contratos e modelos de resposta tipados, com testes dos consumidores oficiais | Auth/perfil/feedback/histórico fazem round-trip em Android e web; OpenAPI gerado documenta segurança/status/nullability; modelo não promete campos que API não retorna. DEC-05/16 |
| INT-02 / S04/S07 | Resolver conexão Google ponta a ponta, status/desconexão e tratamento de refresh/erro | Callback nativo/web, revogação e reautorização têm smoke isolado; token renovado é persistido atomicamente; erro externo não vira sucesso. Confirmar serviço/scopes atuais DEC-08 |
| INT-03 / S05 | Adapter de persistência implementa parâmetros, transações e schema de cada store suportado, sem fingir equivalência SQLite/BigQuery | Mesmas fixtures e constraints funcionam no store transacional escolhido; BigQuery só é anunciado compatível após testes próprios. Escolha de banco e fronteira analítica DEC-02 |
| INT-04 / S12 | Deduplicar ingestão e versionar derivação; invalidar/recalcular apenas resultados afetados | Repetição de sync não aumenta contagem por evento natural; correção de origem atualiza derivados com versão rastreável; falha no meio permite retry consistente. Backfill de algoritmo DEC-06 |
| INT-05 / CUR-13 | Pipelines documentam import/empacotamento, execução e dead letters seguras; não anunciar fila inexistente | CLI instalada no diretório documentado completa fixture sem dado pessoal; falhas estão em status e sink controlado, não payload aberto em logs; DirectRunner e runner remoto testados separadamente se suportados. DEC-10/16 |
| INT-06 / CUR-03/05 | Configurar URL/ambiente explicitamente em clientes, sem decidir por presença de window ou IP fixo | Build dev/teste só acessa destinos de teste; inspeção Android confirma resolução correta; nenhuma chamada de teste para produção. Matriz de plataformas/versões DEC-01/03/16 |

### 7.3 Qualidade e acessibilidade

| ID | Requisito proposto | Aceitação / parâmetros ainda abertos |
|---|---|---|
| NFR-01 | Durabilidade e atomicidade das operações confirmadas | Confirmação só após commit; crash/retry não duplica sessão/treino; store não é filesystem efêmero sem garantia. SLO, RPO/RTO e backend DEC-02/19 |
| NFR-02 | Tempo e sincronização observáveis e honestos | Fixtures de relógio/DST não geram duração negativa; UI marca pendência/desatualização e não promete entrega exata; latência e desvio medidos com perfis de rede aprovados DEC-19 |
| NFR-03 | Desempenho/capacidade sem inventar metas | Antes de release, definir latência p95, capacidade, disponibilidade, timeout, limite de página, skew e expiração em DEC-19 e executar carga correspondente; sem números aprovados, readiness de produção permanece bloqueada |
| NFR-04 | Acessibilidade Android e web | TalkBack/leitor web percorre start/stop/cancel/histórico; labels descrevem estado sem depender só de cor; foco/restauro, escala de fonte, contraste e alvos táteis são verificados; cronômetro não anuncia cada segundo nem impede leitura. Critério candidato web WCAG 2.2 AA e matriz Android dependem DEC-20 |
| NFR-05 | Internacionalização e calendário consistentes | Formatos usam locale e timezone explícitos; nenhum split UTC é tratado automaticamente como dia local; mensagens não concatenam unidades incorretamente. Idiomas e locale inicial DEC-20 |
| NFR-06 | Observabilidade minimizada e depuração segura | Métricas operacionais têm código de resultado/versão, não tokens/notas/horários identificáveis de saúde; correlação técnica com acesso/retention definidos; teste de sanitização. Analytics de produto separado em §11, DEC-15 |
| NFR-07 | Reprodutibilidade e testabilidade | Locks preservados/instalação determinística, ferramentas fixadas, fixtures/clock fake e seams de provider; nenhum teste depende de saúde pessoal/Google real para passar; checagens próprias do contrato e concorrência, não só cobertura percentual |

## 8. PROPOSTO — contratos API e compatibilidade

### 8.1 Regras comuns candidatas

Esses contratos são design para revisão, não endpoints disponíveis. Prefixo candidato `/api/v1`; manter endpoints existentes via adaptação compatível enquanto DEC-16 define suporte. Adição de campos opcionais pode ser compatível; trocar formato, significado, status ou obrigatoriedade exige versão negociada/migração. Não enviar erro novo para cliente antigo sem teste de fallback. Rota pessoal nova usa owner implícito; caminhos antigos com user_id devem rejeitar divergência antes de consultar.

Bearer ausente/inválido → 401 no contrato futuro, com teste para mudança do 403 atual de HTTPBearer. Não confundir com autorização por owner: recurso alheio/inexistente → 404 candidato; papel permitido não concedido → 403 se política aprovada. Validação → 422; conflito de domínio/idempotência → 409; versão divergente → 412; precondição de versão obrigatória ausente → 428; indisponibilidade transitória → 503/timeout com orientação de retry. Detalhes definitivos de erros/versão em DEC-05/16; não altera implementação atual.

Envelope de erro candidato: `{code, message, field_errors?, request_id, retryable}`; mensagens localizadas não são códigos de controle. Nunca ecoar token, dados de outro usuário ou corpo Google. Listas com cursor opaco e `items,next_cursor`; default/máximo aprovados em DEC-19. Intervalo de filtro usa início inclusivo/fim exclusivo e timezone explícito para datas civis. Autorização se repete ao ler recibo, cursor ou idempotency key.

### 8.2 Todas as capacidades atuais: migração de contrato

Cada grupo corresponde às operações reais do inventário. Não remover capacidade porque seu cliente está quebrado; corrigir contrato e validar plataforma suportada. Pontos abaixo são candidatos sujeitos a DEC-05/08/10/16.

| ID de contrato / operações atuais | Contrato futuro candidato e preservação | Requisitos / testes |
|---|---|---|
| API-01: register/login/refresh/logout | Manter resposta plana de auth e buscar `/users/me` após sessão é alternativa compatível; alternativa envelope `{user,tokens}` exige adaptação/versão. Chave canônica e regra senha não escolhidas | FR-01/02, SEC-07, INT-01; T-02/03 |
| API-02: GET/PATCH users/me | Identidade implícita; campos pessoais tipados; PATCH ausência mantém, null limpa somente campos explicitamente anuláveis; retornar perfil saneado | FR-03, SEC-08; T-03 |
| API-03: auth-url, callbacks GET/POST | URL emitida após auth; callback público restrito à transação state/owner, não Bearer do navegador; não retornar expires_at como connected_at. Novos status/disconnect são adições propostas abaixo | FR-05, SEC-04, INT-02; T-04 |
| API-04: sync e summary | Status honesto; summary inclui origem/qualidade sem substituir campos antigos; resultado síncrono com 200 ou job 202+status são alternativas abertas, não fingir assíncrono atual | FR-06/08, INT-04; T-05/06 |
| API-05: readiness atual/history/advanced/modalities | Saída diária e série histórica com schemas distintos; versão/qualidade; error de ausência consistente; mesmos resultados da versão antiga ou migração aprovada | FR-07/09, DAT-04; T-06 |
| API-06: workouts POST/history/exercises catalog | owner implícito futuro, v1 rejeita IDs alheios; data omitida definida por timezone/política; atomicidade e validação de exercícios; catálogo preservado | FR-10, SEC-01; T-07 |
| API-07: muscles recovery/suggestion | Preservar campos e grupos; marcar estimativa, versão, data de referência; invalidar após treino sem rotular 90 como 100 | FR-10, EDU-01; T-06/07 |
| API-08: wellness-feedback POST/GET | Dicionário de perguntas/booleans e round-trip tipado; não mapear worthwhile/trained silenciosamente; regra diário único e null explícitos após decisão | FR-11, INT-01; T-08 |
| API-09: dev/seed e health | Health mínimo sem dados; readiness de infraestrutura separado se necessário; seed negado em release antes de mutação, demo isolada | SEC-02/06, OPS-02; T-01/16 |

**Status/desconexão propostos:** GET `/connect/{provider}/status` → `{provider,status,connected_at?,last_sync_at?,reauthorization_required}` sem token; DELETE `/connect/{provider}` → 204 quando desconectado, idempotente e sem apagar histórico implicitamente. Se revogação remota for assíncrona, usar 202 e recurso de operação, não 204 falso; opção DEC-08. Sem `user_id` novo; cliente antigo que o envia só é atendido se coincide com sub. Status não expõe credenciais. Provider ausente é resposta tipada, não erro ignorado.

### 8.3 Jejum: contratos candidatos detalhados

DEC-04/11/13/16 precisam aprovar escopo e versão. Proposta usa rotas próprias para não sobrecarregar readiness/health-data. Chaves e timestamps abaixo não são valores de produto aprovados.

**FastingSession candidato:** `id` UUID, `status` enum de §5.2, `started_at` UTC, `ended_at` nullable, `cancelled_at` nullable, `timezone_at_start` IANA, `time_quality`, `version` inteiro positivo, `created_at`, `updated_at`. `duration_seconds` calculado apenas para completed; para active, UI calcula elapsed com `server_time` do envelope. `target_duration_seconds?` só existe se meta for aprovada, deve ser positivo dentro da política aprovada em DEC-04 e não é parâmetro médico. `owner_id` interno vem de sub, não é editável nem necessário na resposta. Não incluir notas livres ou motivo clínico por conveniência.

Todas as mutações candidatas exigem `Idempotency-Key` e, salvo start, `If-Match` com versão. Escopo da chave é `(owner, key)`; fingerprint contém método, recurso, corpo canônico e versão esperada quando aplicável. Mesma chave/corpo retorna o resultado original, não reaplica; chave com fingerprint diferente →409. Após falha transitória sem commit, retry pode executar; após commit com resposta perdida, retorna recibo. Guardar recibo e mutação em transação; retenção `R_idempotency` depende DEC-19 e deve cobrir retries/fila. Comandos expirados não são reaplicados sem reconciliação explícita. Reautorizar antes de retornar resultado para não vazar recurso após revogação/exclusão. Ordem candidata de processamento: autenticar/autorizar → verificar recibo idempotente → validar precondição de versão → validar transição/intervalo → commit. Assim, replay legítimo não falha só porque a versão já avançou, nem reabre sessão usando um recibo antigo.

| Operação candidata | Entrada | Resultado / erros de domínio | Efeito persistido |
|---|---|---|---|
| POST `/fasting-sessions` | `{timezone_at_start}`; `client_session_id?,client_recorded_at?` apenas no modo offline aprovado; meta opcional condicionada | 201 `{session,server_time,command_id}`; 409 active_session_exists/overlap/idempotency_conflict; 422 timezone/horário inválido | Nova active, receipt e intenção de notificação opcional atômicos |
| GET `/fasting-sessions/active` | Sem user_id | 200 `{session: Session ou null,server_time}`; erros auth/transiente distinguíveis | Somente leitura, sem iniciar automaticamente |
| POST `/fasting-sessions/{id}/stop` | `{}` online; `client_recorded_at` só se perfil offline/retroatividade aprovado | 200 `{session,server_time,command_id}` completed; 409 invalid_transition; 412 versão; 404 owner | ended_at/versão/receipt; invalida lembretes |
| POST `/fasting-sessions/{id}/cancel` | `{}` online; `client_recorded_at` somente na reconciliação aprovada; nenhum motivo clínico obrigatório | 200 `{session,server_time,command_id}` cancelled; mesmos erros de stop | cancelled_at/versão/receipt; invalida lembretes |
| GET `/fasting-sessions` | `from?,to?,timezone?,status?,cursor?,limit?`; instantes ou datas civis em contrato único, sem mistura | 200 `{items,next_cursor,server_time}`; ordem candidata started_at DESC,id DESC; filtros inclusivo/exclusivo definidos | Sem mutação; cursor vinculado à conta/filtro. Proposta de período filtra started_at, não promete interseção completa sem DEC-13 |
| GET `/fasting-sessions/{id}` | ID | 200 `{session,server_time}` ou 404 | Sem mutação |
| GET `/fasting-commands/{command_id}` | ID opaco pertencente ao owner | 200 `{command_id,status,session_id?,error_code?,resulting_version?}`; 404 alheio | Recuperar recibo de comando conhecido; retry de chave segue operação original |

Recibo de comando, no desenho síncrono de jejum acima, tem `status` candidato `committed` ou `rejected`, `session_id/resulting_version` apenas quando houve commit e erro tipado quando rejeitado; execução transitória sem recibo é resolvida pelo retry idempotente. O estado local `pending` não é uma sessão confirmada nem um job servidor presumido. Persistir rejeições também exige não guardar payload sensível e respeitar retenção. Se DEC-11 exigir processamento assíncrono, expandir estados, consulta/timeout e transições antes de aprovar o contrato.

Não são implicitamente aprovados endpoints de edição/remoção/pausa, preferências, exportação ou push. Se DEC-12/13/15 aprová-los, especificar métodos, autenticação, idempotência, versionamento e retenção antes de implementação. Exclusão de conta/dados exige contrato transversal próprio; o gate SEC-05 não é satisfeito apenas por desenhar cancel.

Para timestamps offline, o recibo identifica quais instantes foram aceitos ou precisam revisão; não promover `client_recorded_at` automaticamente a `started_at`. Se não for possível validar período sem escolher regra de produto, comando fica conflito/erro tipado e a UI orienta revisão, preservando a intenção local conforme retenção aprovada. Um POST rejeitado não vira sessão aceita só por estar na fila.

## 9. PROPOSTO — modelo de dados, integridade e migração

### 9.1 Domínio existente e evolução aditiva

As 16 tabelas atuais estão no inventário §6: users, dim_user, refresh_tokens, oauth_tokens, raw_health_events, normalized_sleep/steps/activity/heart_rate/stress, fact_daily_readiness, wellness_feedback, fact_readiness_by_modality, workout_history, workout_exercises, muscle_recovery. Elas representam capacidades a preservar, não schema automaticamente adequado para produção.

| ID | Requisito de dados proposto | Aceitação / dependência |
|---|---|---|
| DAT-01 | Store operacional deve suportar owner, unicidade/concorrência, transações e migrações; analytics é fronteira separada até prova de paridade | Invariantes FST e auth exercitadas no banco escolhido; não usar INSERT streaming BigQuery como upsert transacional. SQL/dialeto/schema mapeados; DEC-02 |
| DAT-02 | Unicidade natural/deduplicação de origem e integridade referencial explícitas, sem supor cascades | Retry não duplica fato; órfãos/quarentena reportados; constraints/FKs efetivamente ligadas e testadas; regra de identidade provider/evento definida antes da migração |
| DAT-03 | Sessões/comandos/reminders consistentes e idempotentes | Crash após commit antes da resposta recupera mesmo resultado; conflito concorrente deixa uma ativa; histórico não reescreve silenciosamente instantes. FST-05/06 e §9.2 |
| DAT-04 | Proveniência e versão de algoritmo/schema/conteúdo distinguem original de derivado | Fixture antiga é reproduzível; backfill gera versão identificável e comparação, não troca score histórico sem aprovação. Preservar valores originais quando estimativa é retirada; DEC-06 |
| DAT-05 | Exportação/exclusão/retention cobrem dados locais, operacionais, analíticos, filas, lembretes e backups | Operação autenticada tem resultado verificável e prazos aprovados; dados excluídos não reaparecem de offline/restore. Política de tombstones mínimos vs direito de remoção DEC-15 |
| DAT-06 | Migrações versionadas têm pré-condições, dry-run, contagens e plano de recuperação | Banco antigo com colunas faltantes não é tratado como novo; migração interrompida pode retomar/recuperar; pré e pós-contagens/invariantes conferidos sem expor saúde pessoal. DEC-02/19 |

### 9.2 Entidades candidatas para jejum e suporte

Modelo lógico, sem escolher engine ou criar migration. Owner é referência operacional para users, não ID livre ou apenas dim_user. IDs opacos não substituem autorização.

| Entidade candidata | Campos mínimos / índices | Invariantes e condição de aprovação |
|---|---|---|
| `fasting_sessions` | id PK, owner_id FK, status, started_at, ended_at?, cancelled_at?, timezone_at_start, time_quality, version, created_at, updated_at; índice owner/started_at/id e unicidade ativa por owner | active: ambos términos null; completed: ended_at não null e cancelled_at null; cancelled: cancelled_at não null e ended_at null. Fim ≥ início. Regra de sobreposição exige transação/constraint adequada, não só verificação cliente; DEC-13 |
| `fasting_commands` | command_id PK, owner, idempotency_key, fingerprint, operation, session_id?, resulting_version?, outcome, erro tipado?, received_at, expires_at | Chave única por owner; não guardar token; receipt não é fonte separada que pode divergir da sessão; preservar/expurgar conforme R_idempotency. DEC-11/15/19 |
| `reminder_intents` / outbox candidata | id, owner, session_id, reminder_type, schedule_version, fire_at, expires_at, status; chave de deduplicação | Só se notificações aprovadas; commit da transição invalida intents antigos; worker revalida owner/status/versão antes do envio; não guarda conteúdo clínico desnecessário. DEC-12 |
| `device_delivery_bindings` | owner, device_id opaco, canal/token protegido, permission_state, last_seen, revoked_at | Só se push aprovado; segregação de conta, revogação/logout e expiração; token não aparece no analytics. DEC-12/15 |
| `dashboard_preferences` | owner, widget_ids/order, schema_version, updated_at | Somente se persistência for aprovada; valida IDs únicos/suportados, sem remover item antigo por desconhecer versão. DEC-07 |
| `educational_content` / artefato versionado | content_id, versão, locale, tema, texto, evidências, limitações, responsável/reviewed_at, status aprovação | Pode ser arquivo revisado em vez de tabela; não requer CMS. Janelas temporais opcionais só após revisão específica; não armazenar “fase clínica atual do usuário”. DEC-17/20 |

### 9.3 Estratégia de migração candidata

1. Levantar store/configuração realmente implantados e backup/restore; acesso autorizado separado, sem copiar dados pessoais ao repositório. Medir versões de clientes ativas e política de suporte (DEC-01/02/16/19).
2. Inventariar schema em uso, duplicatas naturais, órfãos, IDs e timestamps ambíguos. Não “corrigir” timezone antigo assumindo UTC/local sem evidência; marcar legado e pedir regra de reconciliação (DEC-06/13).
3. Criar migrations **aditivas** após aprovação: tabelas novas, campos nullable/proveniência e constraints validadas em cópia segura. Nenhum descarte de mobile/ ou renome de tabela BigQuery como substituto da adaptação completa.
4. Backfill controlado, contagens/checksums lógicos e amostras autorizadas; duplicatas/quarentena com relatório sem payload sensível; preservar possibilidade de reprocessar sem alterar origem. A migração de tokens exige proteção de segredo e rotação apropriadas, não export em texto.
5. Adaptar contratos/clientes com versão e fixtures, testar coexistência antigo/novo e modo de falha. Mudança de algoritmo/horário/score é release semântica distinta, com DEC-06.
6. Habilitar nova capacidade somente depois dos gates de §12. Rollback de serviço prefere schema expandido compatível; migration destrutiva só em etapa posterior autorizada, depois de janela de suporte/restore aprovada. Desabilitar jejum não apaga sessões nem remove acesso a encerrar sessão ativa sem alternativa segura.

## 10. PROPOSTO — UI e estados de experiência

Esta seção define critérios, não telas implementadas. Local de navegação Android/web e se haverá widget/tela próprios dependem DEC-03/04. Preservar idiomas e visual atuais enquanto se decide expansão; não impor novo onboarding obrigatório sem revisão.

| Área | Estados necessários | Regras observáveis |
|---|---|---|
| Sessão de acesso | Inicializando, anônima, autenticando, válida, renovando, expirada, erro | Não piscar dados de conta anterior; expiração leva a autenticação sem descartar intenção offline silenciosamente; não anunciar autenticado por flag demo |
| Dashboard/fontes | Loading, vazio, parcial, atualizado, desatualizado, autorização pendente, desconectado, erro/retry | Mostrar data/origem; bloquear somente ação dependente; fontes “em breve” não simulam conexão; sem métricas como zero por erro |
| Jejum sem sessão | Loading, nenhuma ativa, indisponível por gate, offline conforme modo | Explicar disponibilidade e limites; ação start conforme política aprovada; não iniciar ao abrir tela ou conceder notificação |
| Jejum em andamento | Active confirmada, active estimada/pending, relógio needs_review, conflito | Timer com qualidade, start visível e encerrar/cancelar acessíveis; meta opcional sem diagnóstico de fase; não esconder falha de sync |
| Encerramento/cancelamento | Confirmando, salvo, pendente, conflito, falhou | Evitar toque duplo; mensagem distingue registro local de servidor; autorização expirada não orienta continuar jejum; conflito mostra versão/ação local sem dados alheios |
| Histórico/detalhe | Vazio, lista, paginando, erro, cache/offline, item cancelado/concluído, excluído | Duração/timezone/qualidade e período consistentes; preservar foco ao voltar; não exibir resultado cancelado como meta atingida |
| Notificações | Sem opt-in, solicitar, negada, habilitada, limitada pelo SO, erro, desabilitada | Benefício do lembrete explicado sem coerção; acesso às configurações; nenhuma permissão exige jejum; entrega atrasada consulta sessão atual |
| Conteúdo | Disponível/revisado, sem evidência aprovada, versão indisponível/offline | Nenhuma geração automática para preencher alegação faltante; rótulo educativo e limites acessíveis; “sem conteúdo aprovado” não impede encerrar |

## 11. PROPOSTO — analytics e observabilidade

Não há autorização nesta fase para coletar telemetria. Separar métricas de confiabilidade de analytics de produto; ambas passam por minimização/retenção/acesso de DEC-15/19. Não registrar payload de saúde, texto livre, duração individual, datas/horários de sessões, identificadores de wearable, tokens OAuth/JWT, email, nascimento ou nomes de usuário em logs/eventos de produto. Identificadores de correlação, mesmo pseudônimos, exigem justificativa e proteção.

Métricas operacionais candidatas: erro por código/versão do contrato, falhas de refresh, conflitos/idempotency retries, latência agregada, lag de reconciliação, falhas de migration/restore e cancelamento de notificações. Dimensões de baixa cardinalidade, sem cruzar evento clínico com pessoa. Alertas devem identificar falha técnica, não monitorar adesão ao jejum.

Eventos de produto **opcionais** para decisão: abertura de recurso, interação com controle, permissão solicitada/negada, conteúdo indisponível. Só adicionar se houver pergunta de produto/finalidade/base válida e política de opt-out. Não presumir que consentimento para armazenar sessão permite analytics. Contagem de stop/cancel pode revelar rotina de saúde e exige avaliação antes de coleta, mesmo sem ID explícito.

Critério NFR-06/SEC-03: testes com valores-canário sintéticos devem demonstrar ausência em logs/telemetria e respeito à retenção/controle de acesso. Auditoria de mudança de estado, quando necessária, registra ator técnico/ação/versão com minimização, sem replicar histórico de saúde indefinidamente.

## 12. PROPOSTO — testes, implantação, rollout e rollback

### 12.1 Catálogo de validação futura

Nenhum teste desta tabela foi executado nesta Fase 1. Os 66 testes e resultados de lint/TypeScript citados em CUR-14 pertencem à Fase 0. Testes que dependem de decisão aberta só têm aceitação final após resolução; expectativa de negativa de segurança não depende de saber dado real de produção.

| ID | Requisitos cobertos | Cenários / evidência exigida |
|---|---|---|
| T-01 | SEC-01/02/06/08, API-09 | Matriz completa das operações pessoais: sem token, A/A, A/B, token inválido/expirado; checar ausência de escrita B; seed e segredo default negados em produção; CORS permitido/negado |
| T-02 | FR-01/02, API-01, SEC-07 | Login/cadastro Android/web→perfil correto; refresh concorrente/expirado/timeout falha finita; logout/rotação/replay; troca de conta limpa dados e fila; limites senha alinhados |
| T-03 | FR-03/04, API-02, DEC-07 | PATCH omissão/null/tipos/faixas, painel empty/add/remove/restart/multi-conta; ordem/persistência escolhidas, sem duplicar AdvancedMetrics |
| T-04 | FR-05, SEC-04, INT-02, API-03 | Provider simulado: state replay/expirado/trocado, redirect inválido, browser sem JWT mas transação legítima, callback nativo, status/disconnect/revogação e erro refresh; smoke real só em conta de teste autorizada |
| T-05 | FR-06/08, INT-04, API-04 | Sync parcial/erro/sem dado/zero observado; repetir intervalo, paginação e múltiplas atividades; proveniência de sono/calorias; transação abortada e retry; contrato job ou síncrono escolhido |
| T-06 | FR-07/09/10, DAT-04, EDU-01, API-05/07 | Fixtures de limiares 40/60/80, sono/FC ausentes, stress ausente, mesmos resultados históricos por versão; horário/duração/jetlag não confundidos; qualidade sem raw; timestamp histórico sem now |
| T-07 | FR-10, DAT-01/02, API-06 | Treino com/sem data, exercícios/texto, rollback parcial, usuário alheio, catálogo, modalidade e recovery invalidados; preservação da navegação web/candidato suportado |
| T-08 | FR-11, INT-01, API-08 | Todas as respostas de feedback persistem round-trip; null/false/ausente diferentes; timestamp consistente; sem ajuste oculto de readiness; teste de compatibilidade de clientes antigos |
| T-09 | FST-01/03/04/05/06, DAT-03 | Todos os pares estado/comando, start simultâneo, stop×cancel, replay mesmo corpo/chave e corpo diferente; falha antes/depois de commit; usuário alheio; overlap e intervalos adjacentes |
| T-10 | FST-02/07, NFR-02/05 | Clock fake com relógio para frente/trás, DST, viagem, meia-noite e reabertura/reboot; duração não negativa; filtro/ordem/cursor, estimativa e histórico em timezone correto |
| T-11 | FST-08/11, SEC-05/07 | Offline start conforme modo escolhido, stop seguro, dependência start→stop, dois dispositivos, timeout/retry, tombstone/conta excluída, logout/troca de conta, conflito sem last-write-wins |
| T-12 | FST-09, DEC-12 | Android real/emulador compatível: permissão negada, reboot, doze, atraso, dedupe, stop/cancel antes de entrega, toque em aviso obsoleto e logout; push só se aprovado e em sandbox |
| T-13 | EDU-01/02/03/04, FST-10/12 | Revisão editorial/evidência/contraindicações; snapshot de linguagem não individualizante; conteúdo indisponível; parar sem meta; nenhuma dependência clínica entre timer/readiness; sem alegações não aprovadas |
| T-14 | NFR-04/05, §10 | TalkBack/leitor web, foco, cor, contraste, escala, navegação, estados vazios/erro/offline e timer sem anúncios contínuos; idiomas/formatos aprovados |
| T-15 | DAT-01 a DAT-06, INT-03, NFR-01, OPS-03/04 | Banco antigo/novo, FKs/constraints/dialetos, concorrência em store escolhido, migração interrompida, contagens/dedup, backup/restore, tokens protegidos, rollback com cliente antigo e sessões ativas |
| T-16 | FR-12, OPS-01/02/05, INT-05/06, NFR-03/07 | CI em PRs/branch correta; locks/toolchain, lint baseline tratado, TypeScript/builds, CLI Beam, porta/health/config; matriz de cliente/ambiente sem produção; carga/SLO e audit de dependências |
| T-17 | SEC-03/05, DAT-05, NFR-06, §11 | Canários sintéticos em logs/analytics, export/delete/retention, isolamento de backups/outbox/cache, minimização de IDs/tokens; nenhum dado ressuscita no restore/reconnect |

### 12.2 Requisitos operacionais e gates

| ID / riscos | Requisito proposto | Aceitação / decisão |
|---|---|---|
| OPS-01 / S15 | CI deve proteger master e branches de revisão, sem acoplar documentação a deploy | PRs executam verificações apropriadas, baseline lint resolvido/decidido e ferramentas fixadas; proteção/checks obrigatórios comprovados. Branch/revisores DEC-01/16; não alterar workflows nesta entrega |
| OPS-02 / S02/S05/S08 | Configuração de ambiente validada na inicialização: URL, porta, provider, banco, secrets e health/readiness | Docker/Compose/Cloud Run com contrato de porta coerente; falta de banco/config não recai silenciosamente em SQLite local em produção; testes não acessam produção |
| OPS-03 / S05/S12 | Expandir schema antes de ativar recurso, com backup e restore testado | Migração em sandbox e restore cumprem RPO/RTO aprovados; contagens/constraints e compatibilidade verificadas. DEC-02/19 |
| OPS-04 / FST-06/09 | Rollout reversível e rollback de aplicação/worker sem perder sessões confirmadas | Flag/configuração de ativação só após aprovação; desabilitar novo start mantém caminho seguro de encerrar/exportar histórico já criado; workers antigos não reenviam reminder invalidado. Mecanismo/coortes DEC-04/12/16 |
| OPS-05 / AGENTS | Separar aprovação de spec, implementação, merge e release | Registro de aprovação versionada e revisão Goldfish, PRs revisados por pessoa/política, autorização separada de deploy; nenhuma execução autônoma declarada sem trigger/permissões/observação reais. DEC-01 |

Sequência candidata por dependência, sem estimativa de esforço ou cronograma inventado:

1. Revisão do inventário + resolução das DEC de segurança/dados/escopo; definir ambiente e suporte. Redigir contratos finais e políticas de privacidade/conteúdo.
2. Goldfish independente ([prompt](prompts/02-goldfish.md)) confronta riscos e IDs; achados bloqueadores resolvidos ou requisito reescrito; proprietário aprova versão/hashes e decisões. Publicar um PR de spec não satisfaz esse gate.
3. Só então planejar implementação: primeiro isolamento/segredos/configuração, contratos e persistência, depois recuperação/compatibilidade das capacidades existentes. Cada alteração com testes T relevantes e migration.
4. Jejum depende desses fundamentos, de elegibilidade/conteúdo/notificação e de contratos finais; implementação e smoke em sandbox, sem Google/saúde pessoal como fixture. Não ligar por simples presença de tabela nova.
5. Preparar runbook, backup/restore, métricas/alertas e rollback; autorizar release separadamente. Coortes, gatilhos e critérios numéricos de progressão/recuo devem ser aprovados em DEC-16/19 antes de liberar a qualquer usuário.
6. Em incidente, parar novos starts/entregas conforme runbook, preservar comandos confirmados e acesso seguro a parar/histórico, restaurar versão compatível e investigar com logs minimizados. Rollback de feature não deve exigir apagar banco nem permitir fluxo de autorização antigo vulnerável; se versão anterior é insegura, usar correção/compatibilidade segura em vez de downgrade cego.

Sem valores aprovados para SLO/retention/janelas/coortes e sem validação correspondente, não declarar release pronta. Não há deploy ou rollback executado nesta fase; o plano descreve evidências futuras necessárias.

## 13. DECISÕES DO PROPRIETÁRIO — registro aberto

Todos os estados são **ABERTO**, sem alternativa escolhida. Recomendações técnicas deste documento podem ser aceitas, substituídas ou recusadas com justificativa registrada. Decisões clínicas/editoriais requerem responsável qualificado; o proprietário define quem revisa, não substitui evidência por preferência. Aprovação deve citar versão do documento e atualizar esta tabela com resolução/data/responsável e IDs afetados.

| ID | Questão e alternativas a avaliar | Bloqueia / IDs afetados |
|---|---|---|
| DEC-01 | Confirmar aprovação/revisão Fase 0, responsáveis EGM, branch de integração/PR e política de aprovação/produção. Bootstrap/inventário primeiro ou integração por outro PR? | Gate de implementação/release; OPS-01/05 |
| DEC-02 | Qual store/configuração está implantado? Store transacional durável para identidade/tokens/sessões; BigQuery analítico separado ou adapter com outro desenho? Motor/hosting/backup/chaves não escolhidos | DAT-01/06, INT-03, SEC-02/03, OPS-02/03 |
| DEC-03 | Quais telas e plataformas são suportadas? Android oficial confirmado; web/legado preservados, mas paridade de treino/body-map e novo jejum web são expansão ou fora do primeiro escopo? | FR-04/10/12, FST-01/07, UI/T-14/16 |
| DEC-04 | Jejum será autorizado? Público/elegibilidade, objetivos, meta opcional, superfície/tela/widget, parâmetros de duração e ausência de protocolo médico. Sem eleição automática de 16:8 ou máximo | Todos FST, EDU-04, OPS-04 |
| DEC-05 | Contratos canônicos de auth/perfil/feedback; manter auth plano+GET me ou envelope versionado? Quais perguntas, faixas, enums, nullability e regra de senha? | FR-01/03/11, INT-01, API-01/02/08 |
| DEC-06 | Preservar fórmulas atuais versionadas ou corrigir significado/dia de atividade/proxies e backfill? Como apresentar histórico antes/depois e dados estimados? | FR-07/08/09/10, DAT-04, EDU-01 |
| DEC-07 | Configuração do dashboard será local ou por conta no servidor? Persistir ordem e seleção? Qual estado inicial sem apagar preferências existentes? | FR-04, entidade dashboard_preferences, T-03 |
| DEC-08 | Google Fit continua viável/intencionado? Scopes/redirects/PKCE/retorno de navegador, status e revogação; Health Connect é avaliação separada, não integração pressuposta | FR-05, INT-02, SEC-04, API-03 |
| DEC-09 | Somente dados próprios ou haverá compartilhamento/roles/admin? Nenhum papel privilegiado está aprovado; dados retidos após desconexão não são automaticamente apagados | SEC-01, FR-05, SEC-05 |
| DEC-10 | Sync de saúde permanece síncrono com status correto ou vira job com consulta/cancelamento/retry? Beam/Dataflow faz parte do runtime suportado? | FR-06, API-04, INT-05, T-05/16 |
| DEC-11 | Modo offline A ou B (§5.4), ações permitidas e resolução de conflito entre aparelhos; o que fazer com comandos não confirmados ao sair da conta? | FST-05/08, fila/commands, T-09/11 |
| DEC-12 | Lembrete local, push ou híbrido? Opcionais por quais eventos/metas, momento de permissão, horários silenciosos, dedupe entre aparelhos e privacidade da lockscreen? | FST-09, reminder/device entities, T-12 |
| DEC-13 | Aprovar máquina mínima active/completed/cancelled e bloqueio de sobreposição? Pausa/planejamento, edição retroativa/remoção, histórico cancelado, timezone de apresentação e filtro por início/interseção? | FST-02/04/05/07, API jejum, DAT-03, T-09/10 |
| DEC-14 | Jejum fica independente de readiness/treino? Não há evidência para ajuste automático; qualquer integração futura precisa novo requisito/evidência | FST-12, FR-07/10, T-13 |
| DEC-15 | Finalidades/base de tratamento, consentimentos, export/delete, retenção por entidade/cache/log/backup/fila/receipt, processo e analytics permitidos? | SEC-03/05/07, DAT-05, §11, T-17 |
| DEC-16 | Clientes/versões suportados, versionamento API, retirada de demo/legado, rollout/flag/coortes e revisão de dependências/CI. Não presumir descontinuação ou migração invisível | FR-12, INT-01/06, OPS-01/04, §8/12 |
| DEC-17 | Quem aprova fontes, linguagem, fases, contraindicações e público? Haverá faixas educativas temporais ou conteúdo temático sem faixas? Não há fontes clínicas validadas nesta entrega | Todos EDU, FST-10, T-13 |
| DEC-18 | Duração/revogação/rotação de sessões e OAuth, TTL state, política refresh/replay e logout offline; estratégia web token/cookie | FR-02, SEC-02/04/07, API-01, T-02/04 |
| DEC-19 | Aprovar SLO p95/disponibilidade/capacidade, RPO/RTO, skew, limites de requests/páginas/intervalos, timeout e retenção de idempotência; requisitos devem virar valores testáveis | NFR-01/02/03, SEC-08, DAT-03/06, OPS-03/04, T-15/16 |
| DEC-20 | Idiomas/locales, cobertura Android/versões, padrão de acessibilidade e evidências de aceitação; proposta WCAG 2.2 AA web a revisar | NFR-04/05, conteúdo versionado, T-14/16 |

Se a decisão não é necessária ao escopo aprovado, registrar explicitamente “fora desta versão” com razão e impacto; não remover o bloqueio por silêncio. Decisões sobre proteção básica de dados não podem aprovar acesso cruzado, vazamento de segredo ou alegação clínica falsa como requisito de produto.

## 14. Matriz dos riscos do inventário → requisitos → evidência futura

| Risco Fase 0 | Requisitos de tratamento propostos | Testes/gates de verificação |
|---|---|---|
| S01 — owner ausente | SEC-01, FST-11, API-01 a API-08, DAT-03 | T-01/09/11; bloqueador antes de novas escritas/jejum |
| S02 — defaults de segredos | SEC-02/03, OPS-02/05 | T-01/16/17; readiness fail-closed |
| S03 — tokens plaintext/acesso | SEC-03/05, DAT-01/05/06 | T-04/15/17; chaves/restore e acesso mínimo revisados |
| S04 — OAuth/state/callback | SEC-04, FR-05, INT-02, API-03 | T-04; transação e redirect nativo/web revisados |
| S05 — persistência GCP/Cloud Run | DAT-01/02/06, INT-03, NFR-01, OPS-02/03/04 | T-15/16; store durável e restore antes de release |
| S06 — estimativa apresentada como medição | FR-08/09, EDU-01 a EDU-04, FST-10/12, DAT-04 | T-05/06/13; aprovação de conteúdo e incerteza |
| S07 — contrato Android/ambiente/refresh | FR-01/02, INT-01/02/06, SEC-07 | T-02/03/04/16; smoke sem produção |
| S08 — endpoint demo | SEC-06, FR-12, API-09, OPS-02 | T-01/16; negar seed em produção antes de escrita |
| S09 — CORS aberto | SEC-06, OPS-02 | T-01/16; origens explícitas e preflight |
| S10 — armazenamento/logout/cache | FR-02, SEC-03/05/07, DAT-05 | T-02/11/17; troca de conta e sessão offline |
| S11 — validação/contratos | FR-03/10/11, SEC-08, INT-01, API-01 a API-08 | T-02/03/07/08/09; nulidade/tipos/limites com decisões finais |
| S12 — duplicação/concorrência/derivados | FR-06/10, INT-04, DAT-02/03/04, FST-05/08 | T-05/07/09/10/11/15; crash/retry/concorrência |
| S13 — logs/health payload | SEC-03, NFR-06, INT-05, §11 | T-16/17; canários e acesso/retention de logs |
| S14 — privacidade/textos inconsistentes | SEC-05, DAT-05, EDU-03/04, FST-11 | T-13/17; consentimento, export/delete e linguagem revisados |
| S15 — CI/dependências/artefatos | OPS-01/02/05, NFR-07, INT-06 | T-16; branch correta, baseline/locks/compatibilidade; sem atualização funcional nesta fase |

## 15. Registro de aprovação e próximos gates

| Gate | Estado desta versão | Evidência necessária |
|---|---|---|
| Inventário base recebido | Disponível em `5af4d029a3924b9c1d841233ed7333cb8661d884` | Aprovação do proprietário ainda não registrada; DEC-01 |
| Elephant | **Rascunho 0.1.0, pendente** | Revisão deste documento e resolução das DEC aplicáveis |
| Goldfish | **Não executado nesta entrega** | `02-goldfish-review.md` por revisão independente, achados ligados a IDs e resoluções |
| Especificação aprovada | **Não** | Responsável, data, versão/commit, decisões/limites de escopo aprovados explicitamente |
| Implementação | **Não autorizada por esta entrega** | Spec aprovada + plano de tarefas rastreável por requisito e teste |
| Merge / produção | **Não executados; exigem gates próprios** | Revisão de PR, validação, runbook e autorização separada de release |

Validação desta entrega documental: leitura dos três documentos solicitados e de fontes de contrato; checagem de referências locais, definição dos IDs, cobertura dos 15 riscos, coerência dos contratos e diff antes do commit. Não foram reexecutados testes funcionais, builds ou lint de produto, pois a alteração é somente documental. Não apresentar aceitação futura como teste passado. Não alterar `00-inventory.md` para fingir aprovação ou resultados novos. Publicação da branch/PR de documentação é somente revisão da especificação; não aprova o produto nem publica o ambiente.
