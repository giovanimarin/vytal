# Vytal — Fase 2: revisão crítica Goldfish

**Data:** 2026-11-04. **Estado:** revisão concluída; achados abertos, especificação não aprovada.
**Branch de origem:** `docs/egm-phase-1-elephant`.
**Commit revisado:** `2722445bb889160390d79e2932f876bebbd03870`.
**Objeto:** [Elephant 0.1.0](01-master-spec.md), confrontado com [AGENTS.md](../../AGENTS.md), [inventário](00-inventory.md), [prompt Goldfish](prompts/02-goldfish.md) e código nessa base.

## 1. Parecer e critérios

**Não aprovar a versão 0.1.0 como especificação integral para implementação.** Foram registrados **20 problemas: 12 de gravidade alta e 8 média; 17 impedem a aprovação integral e 3 são recomendações não bloqueadoras**. Nenhum foi classificado como vulnerabilidade crítica nova comprovada em produção. A revisão de um rascunho não equivale a constatar exploração ou defeito de uma funcionalidade de jejum já existente: ela ainda não existe no código.

O Elephant acerta ao preservar o Android oficial `mobile/vytal-app/`, manter o legado sem descarte automático, separar atual/proposto/decisão, não inventar faixas metabólicas, vincular S01–S15 a requisitos e manter gates de aprovação. Essas salvaguardas reduzem risco, mas os vínculos de IDs não tornam contratos incompletos implementáveis nem resolvem contradições de recuperação/tempo/compatibilidade.

Independência desta entrega significa papel crítico e artefato separado, sem presumir que a proposta esteja correta e sem editar o texto analisado. **O mesmo assistente participou da elaboração do Elephant; esta entrega não constitui certificação por auditor externo ou revisão por outro autor.** Os contraexemplos e referências permitem contestação por um segundo revisor. Não se declara revisão humana ou por outro agente que não ocorreu.

Classificação:

- **Alta:** indefinição ou conflito capaz de produzir perda/inconsistência de dados, falha de segurança, impossibilidade de transição essencial ou regressão relevante se implementado literalmente.
- **Média:** contrato, semântica ou validação insuficientemente precisos; pode bloquear a aprovação do grupo afetado sem representar exploração confirmada.
- **Bloqueador:** deve ser resolvido na especificação/decisão antes de aprovar implementação do escopo atingido. Um bloqueador exclusivo de jejum não impede, por si, aprovar uma especificação separada de correção de autenticação; exige delimitar essa aprovação, não ignorá-lo.
- **Não bloqueador:** o requisito já contém proteção suficiente para este gate, mas a recomendação deve entrar na preparação de contratos/testes/release. Não é autorização para publicar conteúdo ou pular teste.

Todas as correções abaixo são **recomendadas, não aplicadas**. O proprietário precisa escolher alternativas de produto; o autor deve traduzir a escolha em requisitos consistentes e testes. Não se contam as 20 DEC abertas como 20 defeitos adicionais. GF-01 agrega o gate de decisões; os demais identificam lacunas concretas não resolvidas apenas por selecionar uma opção.

## 2. Índice de achados

| ID | Gravidade | Bloqueia aprovação integral? | Tema / escopo |
|---|---|---|---|
| GF-01 | Alta | Sim | Perfil aprovável e decisões essenciais ainda ausentes; governança |
| GF-02 | Alta | Sim | Horário efetivo de stop/cancel offline; jejum |
| GF-03 | Média | Sim | Dependências da fila entre sessões e aparelhos; jejum |
| GF-04 | Alta | Sim | Relógio do servidor pode impedir encerramento; jejum |
| GF-05 | Alta | Sim | Expurgo de idempotência permite reaplicar comando antigo; jejum/dados |
| GF-06 | Média | Sim | Replay de recibo antigo pode regredir estado do cliente; jejum |
| GF-07 | Média | Sim | Precondições, representação de versão e ordenação de erros incompletas; API de jejum |
| GF-08 | Alta | Sim | Revogação de acesso/conta e stop seguro não têm semântica fechada; segurança |
| GF-09 | Alta | Sim | Rotação de refresh não especifica concorrência atômica no servidor; segurança |
| GF-10 | Alta | Sim | Desconexão/exclusão competindo com sync e callback; integração |
| GF-11 | Alta | Sim | Envelope/paginação e intervalo exclusivos conflitam com v1 atual; regressão |
| GF-12 | Média | Não | Ausência de um versus ambos os sinais obrigatórios; redação/testes |
| GF-13 | Média | Sim | Proveniência por campo sem schema de qualidade; dados/segurança de interpretação |
| GF-14 | Média | Sim | Dia civil dos indicadores não definido de ponta a ponta; produto/dados |
| GF-15 | Alta | Sim | Exclusão/exportação/restore sem fluxo e contrato verificável; privacidade |
| GF-16 | Alta | Sim | Garantia de não perda e recuperação/RPO não reconciliadas; implantação |
| GF-17 | Alta | Sim | Notificações dependem de preferências/bindings/operações ainda sem contrato; jejum |
| GF-18 | Média | Não | Migração editorial das alegações existentes não tem checklist; conteúdo |
| GF-19 | Alta | Sim | Preservação de cliente legado sem política de suporte executável; regressão |
| GF-20 | Média | Não | Cobertura por IDs não demonstra cobertura de cenários; testes |

## 3. Achados detalhados

### GF-01 — Não existe um perfil fechado que possa receber aprovação integral

- **Gravidade:** Alta. **Bloqueador:** Sim — aprovação integral/governança. **Estado:** Aberto.
- **Requisitos afetados:** OPS-05, DAT-01, INT-01, NFR-03, FST-01 a FST-12; DEC-01 a DEC-20.
- **Evidência:** Elephant [L12](01-master-spec.md#L12), [L22](01-master-spec.md#L22), [L385](01-master-spec.md#L385) e tabela final de gates: inventário sem aprovação registrada, todas as DEC abertas e contratos candidatos. Isso é corretamente declarado; não é violação de autorização desta fase documental.
- **Problema/impacto:** “Aprovar a spec” não identifica quais alternativas e escopo são normativos: banco, contrato auth/feedback, suporte a clientes, modo offline, notificações e elegibilidade continuam mutuamente abertos. Aprovar o documento inteiro sem escolher produz implementações incompatíveis, mesmo que cada equipe cite um ID válido. SLO/limites sem números não devem ser inventados pelo implementador.
- **Correção recomendada:** criar um perfil de escopo aprovado com tabela decisão→alternativa→requisitos/contratos finais e exclusões explícitas. Para cada gate, registrar responsável, versão/commit e evidência. Diferenciar decisões que bloqueiam desenho/implementação das que bloqueiam apenas release. Se o proprietário quiser aprovar só correções existentes, emitir versão delimitada, sem presumir jejum ou outra alternativa.
- **Critério de fechamento:** autor e revisor conseguem determinar uma única expectativa para cada caso T aplicável a partir de decisões registradas; nenhuma escolha clínica, contrato ou engine essencial é inferida por silêncio. Pergunta ao proprietário: **qual escopo e quais alternativas desta versão podem ser aprovados?**

### GF-02 — Stop/cancel offline não tem regra de horário efetivo nem protocolo completo de reconciliação

- **Gravidade:** Alta. **Bloqueador:** Sim — jejum. **Estado:** Aberto.
- **Requisitos afetados:** FST-02/03/04/08, DAT-03, NFR-02, T-10/11; DEC-11/13/19.
- **Evidência:** Elephant [L135](01-master-spec.md#L135) usa horário do servidor em comandos online; [L145](01-master-spec.md#L145) permite stop offline mesmo no modo A; [L262](01-master-spec.md#L262) aceita `client_recorded_at` só no perfil aprovado; [L272](01-master-spec.md#L272) diz que o recibo identifica instantes aceitos, mas [L266](01-master-spec.md#L266) não contém esses campos.
- **Contraexemplo de mesa:** sessão confirmada; usuário para às 10h sem rede e reconecta às 14h. Usar recebimento registra quatro horas a mais; aceitar hora civil sem validação conflita com a garantia temporal. Selecionar A ou B não determina qual regra é válida. `needs_review` tampouco possui comando/fluxo de resolução definido.
- **Correção recomendada:** especificar separadamente horário declarado, recebido, efetivo e a qualidade/autoridade de cada um; definir o que o servidor aceita automaticamente e o que exige revisão. Fechar request/response e UX de correção sem alterar silenciosamente o instante; permitir parar localmente sem manter a pessoa “em jejum” por falha de rede. Não escolher tolerância ou regra médica nesta revisão.
- **Critério de fechamento:** T-11 cobre o intervalo 10h→14h, hora adulterada, rejeição e revisão; resposta e histórico informam exatamente qual instante foi usado. O proprietário decide política de retroatividade; a spec define o mecanismo correspondente.

### GF-03 — A fila não define dependências e identificação para sessões consecutivas

- **Gravidade:** Média. **Bloqueador:** Sim — jejum offline/multi-dispositivo. **Estado:** Aberto.
- **Requisitos afetados:** FST-01/05/08, DAT-03, SEC-07, T-09/11; DEC-11/13.
- **Evidência:** Elephant [L148](01-master-spec.md#L148) exige ID de comando, ID provisório, ordenação de dependências e envio de comando dependente de start após aceite; [L260](01-master-spec.md#L260) só declara `client_session_id` no start; não há contrato de dependência entre stop de uma sessão e start da próxima.
- **Contraexemplo de mesa:** A ativa confirmada; offline registra stop(A), start(B), stop(B). Ao reconectar, servidor ainda vê A ativa. Sem grafo/mapeamento, start(B) pode receber 409 permanente antes de stop(A), e stop(B) pode não conhecer ID/versão canônicos. Outro aparelho pode avançar A enquanto a fila estava parada.
- **Correção recomendada:** definir formato e escopo de IDs locais/comandos, mapeamento para ID/versão canônicos, dependências entre sessões e comportamento ao falhar um predecessor. Separar falha transitória, conflito final e comando que aguarda dependência; não usar last-write-wins nem repetir conflito permanente como retry automático.
- **Critério de fechamento:** T-11 especifica resultados para toda a cadeia, inclusive reinício do processo, entrega fora de ordem, troca de conta e avanço por segundo aparelho. A escolha offline permanece do proprietário; a cadeia precisa ser consistente na opção escolhida.

### GF-04 — O relógio do backend também pode retroceder ou divergir entre instâncias

- **Gravidade:** Alta. **Bloqueador:** Sim — semântica temporal de jejum. **Estado:** Aberto.
- **Requisitos afetados:** FST-02/03/06, NFR-01/02, DAT-03, T-09/10; DEC-19.
- **Evidência:** Elephant [L133](01-master-spec.md#L133) exige fim≥início, [L135](01-master-spec.md#L135) escolhe hora do servidor como candidata e [L137](01-master-spec.md#L137) só detalha âncora monotônica da UI. Não há regra de fonte de tempo/coerência do backend.
- **Contraexemplo de mesa:** início aceito por instância com relógio adiantado; stop chega a instância atrasada e produz `ended_at < started_at`. Rejeitar stop deixa sessão ativa; truncar a duração para zero sem aviso reescreve significado. Ser “server_confirmed” não prova precisão nem monotonicidade entre máquinas.
- **Correção recomendada:** definir autoridade temporal, detecção de skew, política de indisponibilidade/revisão e representação de horário solicitado versus confirmado. Uma falha de relógio não pode impedir registro seguro da intenção de encerrar. Não confundir UTC, que é representação, com garantia de relógio correto.
- **Critério de fechamento:** T-10 inclui relógio do servidor retrocedendo, duas instâncias com diferença de tempo e recuperação; transição/qualidade resultantes são determinísticas e não alteram duração silenciosamente. Tolerâncias dependem DEC-19.

### GF-05 — Depois de expurgar a chave, o servidor não distingue retry antigo de comando novo

- **Gravidade:** Alta. **Bloqueador:** Sim — idempotência/dados de jejum. **Estado:** Aberto.
- **Requisitos afetados:** FST-01/05/08, DAT-03/05, SEC-08, T-09/11/15; DEC-15/19.
- **Evidência:** Elephant [L256](01-master-spec.md#L256) exige retenção `R_idempotency` e proíbe reaplicar comandos expirados sem reconciliação; [L296](01-master-spec.md#L296) permite expurgar recibos. Não há limite de idade de comando reconhecível independentemente da existência desse recibo.
- **Contraexemplo de mesa:** start com chave K concluiu; sessão foi encerrada; recibo K expirou e foi removido. Uma fila antiga reapresenta start(K). Sem registro ou prova de idade, K parece nova e cria sessão ativa indevida. Dizer que R cobre a fila não define o máximo offline nem o caso de restore/fila esquecida.
- **Correção recomendada:** especificar retenção e janela de validade conjuntas, fonte verificável de idade/época do comando e estratégia de chaves/tombstones compatível com privacidade. O contrato deve distinguir chave nova, expirada e impossível de reconciliar. Não confiar só no relógio declarado pelo cliente; decidir quando exigir novo comando consciente.
- **Critério de fechamento:** T-09/11 simula replay após expurgo e após restore, sem criar sessão nova; T-17 verifica a minimização dos registros necessários. Não se exige retenção infinita nem se escolhe prazo nesta revisão.

### GF-06 — Um recibo idempotente pode devolver a versão antiga como sessão ativa

- **Gravidade:** Média. **Bloqueador:** Sim — cliente/API de jejum. **Estado:** Aberto.
- **Requisitos afetados:** FST-02/03/08/09, DAT-03, INT-01, T-09/11; DEC-11.
- **Evidência:** Elephant [L124](01-master-spec.md#L124) admite recurso atual em versão posterior; [L256](01-master-spec.md#L256) retorna resultado original; POSTs devolvem `{session,...}`. Não há regra obrigatória de merge por versão ou leitura canônica após replay.
- **Contraexemplo de mesa:** start gerou v1 active; outro aparelho encerrou em v2; retry do start retorna recibo v1. Um cliente que aplica a resposta normalmente pode reabrir visualmente timer e agendar lembrete da sessão encerrada, embora o servidor não tenha reaberto nada.
- **Correção recomendada:** diferenciar snapshot do resultado do comando e recurso atual; indicar replay/versão canônica quando possível e exigir cliente monotônico por versão. Nunca substituir estado v2 por v1; consultar estado atual antes de reativar timer/agendamento em replay/retomada.
- **Critério de fechamento:** T-09/11 entrega respostas fora de ordem e replay após término, sem regressão visual nem notificação nova. O recibo continua útil para confirmar a execução sem ser tratado como estado atual.

### GF-07 — If-Match e rejeições não têm contrato HTTP/schema suficiente

- **Gravidade:** Média. **Bloqueador:** Sim — contrato de mutação de jejum. **Estado:** Aberto.
- **Requisitos afetados:** FST-05, INT-01, SEC-08, DAT-03, T-09; DEC-05/16.
- **Evidência:** Elephant [L228](01-master-spec.md#L228) define 428/412; [L254](01-master-spec.md#L254) expõe inteiro version; [L256](01-master-spec.md#L256) exige If-Match e fingerprint com versão; [L268](01-master-spec.md#L268) persiste rejeições. Não define formato ETag/If-Match, origem do valor, campos obrigatórios/erros de header, nem quais falhas consomem a chave.
- **Problema/impacto:** clientes podem mandar inteiro cru versus ETag opaco/entre aspas, alterar If-Match no retry da mesma chave e receber 409 em vez de 412. Um erro 422 corrigido com a mesma chave pode ficar permanentemente rejeitado ou executar, dependendo da interpretação. Também falta resultado escolhido para comando novo contra estado terminal com versão divergente.
- **Correção recomendada:** especificar headers, parser, ETag e sua presença nas respostas, canonicalização/fingerprint e tabela de precedência de erros. Definir quando uma rejeição é definitiva e exige nova chave após ação explícita. Não alterar automaticamente versão para “fazer passar” um comando conflitante.
- **Critério de fechamento:** OpenAPI/exemplos e T-09 cobrem header ausente/malformado, stale version, terminal+stale, corpo alterado, erro corrigido e replay com recurso já atualizado; cada entrada tem um resultado esperado único.

### GF-08 — Logout, conta revogada e parada segura não têm semântica de acesso completa

- **Gravidade:** Alta. **Bloqueador:** Sim — segurança base e jejum autenticado. **Estado:** Aberto.
- **Requisitos afetados:** FR-02, SEC-01/02/05/07, FST-03/08, OPS-04, T-01/02/11; DEC-18.
- **Evidência:** Elephant [L78](01-master-spec.md#L78) revoga “quando possível”, [L196](01-master-spec.md#L196) exige sessão/cache consistentes e [L129](01-master-spec.md#L129) exige parada local segura. No código, [logout](../../backend/app/services/auth_service.py#L87) revoga somente refresh; [JWT](../../backend/app/auth/jwt_handler.py#L15) e [dependência](../../backend/app/auth/dependencies.py#L9) não verificam estado de conta/sessão após decodificar.
- **Problema/impacto:** não está decidido se access token previamente emitido continua autorizado após logout/exclusão nem como um pedido em voo deve se comportar. “Encerrar é sempre acessível” não pode significar aceitar operação remota sem autorização, mas limpar toda fila offline também pode apagar intenção de parada.
- **Correção recomendada:** definir separadamente logout local, revogação remota de refresh/access, conta desabilitada/excluída, sessão ativa no servidor e retenção protegida da intenção offline. Escolher mecanismo/limites de revogação e reautenticação, mantendo parada local possível sem autorizar escrita anônima. Incluir validação das claims necessárias e da identidade operacional existente.
- **Critério de fechamento:** T-01/02/11 tem resultados explícitos para access antigo após logout/revogação/exclusão, pedido em voo e retorno após reautenticar. Não aceitar token de conta removida nem perder silenciosamente intenção local; prazos são DEC-18.

### GF-09 — Evitar refresh recursivo no cliente não assegura rotação única no servidor

- **Gravidade:** Alta. **Bloqueador:** Sim — autenticação/sessão. **Estado:** Aberto.
- **Requisitos afetados:** FR-02, SEC-07, DAT-01, API-01, T-02; DEC-18.
- **Evidência:** Elephant FR-02 e T-02 citam concorrência/rotação/replay, sem invariante de sucessores. [AuthService.refresh](../../backend/app/services/auth_service.py#L65) faz get→revoke→create; [RefreshTokenRepository](../../backend/app/repositories/refresh_token_repo.py#L33) usa operações independentes; [adapter local](../../backend/app/adapters/cloud/local.py#L249) abre conexão/commit por query. O bloqueio `isRefreshing` no Android só cobre aquele processo.
- **Contraexemplo de mesa:** dois pedidos validam o mesmo refresh antes da revogação; ambos podem emitir um sucessor. Logout concorrente com refresh pode deixar sucessor válido após a revogação percebida. T-02 não declara quantos sucessores são aceitáveis nem a política para retry de resposta perdida.
- **Correção recomendada:** especificar consumo atômico de refresh, família/sessão ou mecanismo equivalente, comportamento de reutilização e corrida logout×refresh. Definir explicitamente se um retry legítimo pode recuperar o mesmo sucessor e como distingui-lo de uso indevido sem inventar tolerância.
- **Critério de fechamento:** teste servidor com duas conexões/instâncias, barreira entre leitura e commit, falha após emissão e logout concorrente. Resultado não depende apenas do interceptor de um aparelho.

### GF-10 — Desconectar uma fonte não tem barreira contra sync/refresh/callback em andamento

- **Gravidade:** Alta. **Bloqueador:** Sim — integração/privacidade. **Estado:** Aberto.
- **Requisitos afetados:** FR-05/06, SEC-04/05, INT-02/04, DAT-05, T-04/05/17; DEC-08/15.
- **Evidência:** Elephant [L81](01-master-spec.md#L81) interrompe novas coletas; DELETE candidato em [L248](01-master-spec.md#L248). [HealthDataService.sync](../../backend/app/services/health_data_service.py#L34) lê token e depois grava raw/normalizados; [callback](../../backend/app/services/oauth_service.py#L31) salva tokens após chamada externa. Não há contrato futuro para essas operações quando disconnect/exclusão ocorre no intervalo.
- **Contraexemplo de mesa:** sync consulta o provider; usuário desconecta ou exclui dados; resposta Google chega e persiste novos dados. Callback antigo ainda válido pode recriar tokens. Status disconnected pode então coexistir com nova coleta/gravação não esperada.
- **Correção recomendada:** definir ponto de linearização, geração de conexão/consentimento e política de aceitar ou descartar resultados em voo; revalidar antes do commit e invalidar transações OAuth anteriores à desconexão. Separar “coleta interrompida” de revogação remota pendente e de exclusão de histórico; política é decisão explícita.
- **Critério de fechamento:** T-04/05/17 usa provider simulado com resposta suspensa e disconnect/delete no meio; verifica tokens, dados, status e ausência de recriação por callback antigo. Não foi reproduzido em produção nesta revisão.

### GF-11 — Regras globais novas de listas e filtros alteram contratos v1 atuais

- **Gravidade:** Alta. **Bloqueador:** Sim — compatibilidade web/Android. **Estado:** Aberto.
- **Requisitos afetados:** FR-07/10/12, INT-01, API-04/05/06, T-05/06/07/16; DEC-16.
- **Evidência:** Elephant [L226](01-master-spec.md#L226) exige migração/versionamento, mas [L230](01-master-spec.md#L230) apresenta listas `items,next_cursor` e fim exclusivo sem delimitar “somente novos contratos”. [ReadinessRepository](../../backend/app/repositories/readiness_repo.py#L19) retorna array e usa `BETWEEN` inclusivo; [hook Android](../../mobile/vytal-app/src/hooks/useReadiness.ts#L19) espera array e envia end_date como dia final.
- **Contraexemplo de mesa:** aplicar envelope no mesmo endpoint rompe componente que lê array. Aplicar fim exclusivo a `end_date=hoje` remove o dia que o cliente espera incluir. São regressões semânticas mesmo que paths e autenticação permaneçam iguais.
- **Correção recomendada:** criar matriz operação×versão×cliente com schema e regra de borda exatos. Restringir regras novas a contratos novos ou estabelecer adaptação/versão explícita, ordem de rollout e fallback. Corrigir autorização não justifica mudar envelope ou intervalo silenciosamente.
- **Critério de fechamento:** fixtures de cliente antigo/novo consultam mesmo intervalo, inclusive dia final e página adicional; ambos têm resultado aprovado e documentado. T-16 exige evidência de coexistência quando suporte simultâneo for prometido.

### GF-12 — “Sem ambos” é menos preciso que a regra atual de dois sinais obrigatórios

- **Gravidade:** Média. **Bloqueador:** Não — precisão editorial/testes; CUR-07 já declara ambos obrigatórios. **Estado:** Aberto.
- **Requisitos afetados:** FR-07, CUR-07, T-06; DEC-06.
- **Evidência:** Elephant [L83](01-master-spec.md#L83) usa “sem ambos mostra indisponível”; [código](../../backend/app/services/readiness_service.py#L45) faz `if not sleep_rows or not hr_rows: return None`.
- **Problema/impacto:** redação pode ser entendida como indisponível apenas quando os dois faltam, embora o restante da especificação dê contexto correto. Um teste só com ambos ausentes não diferencia as interpretações.
- **Correção recomendada:** escrever “se faltar sono **ou** FC” e explicitar os quatro casos de presença/ausência e dados inválidos. Não alterar o cálculo nesta revisão.
- **Critério de fechamento:** T-06 contém tabela verdade: ambos presentes calculam; cada ausência isolada e ambas ausências não calculam. Não se afirma que o código atual viola essa regra.

### GF-13 — Qualidade/proveniência por campo não possui schema que o cliente possa consumir

- **Gravidade:** Média. **Bloqueador:** Sim — contrato de interpretação de dados de saúde. **Estado:** Aberto.
- **Requisitos afetados:** FR-08/09, INT-01/04, DAT-04, EDU-01, API-04/05, T-05/06; DEC-05/06.
- **Evidência:** Elephant FR-08 exige observado/derivado/estimado/ausente; API-04 promete adicionar origem/qualidade, sem campos/enums ou relação com cada medida. [Summary](../../backend/app/services/health_data_service.py#L84) retorna registros sem essa classificação. [Adapter Google](../../backend/app/adapters/connectors/google_fit.py#L323) fabrica estágios; calorias são zero em [L287](../../backend/app/adapters/connectors/google_fit.py#L287).
- **Problema/impacto:** marcar o registro inteiro como observado rotula estágios estimados como medidos; marcar tudo estimado esconde observações reais. Não há representação definida para zero observado versus zero preenchido, erro de fonte, ausência e dado legado de origem desconhecida. Preservar valor original não basta para interpretação segura.
- **Correção recomendada:** fechar schema de qualidade/proveniência por medida ou estrutura equivalente, com enumerações, método/versão, origem, referência temporal e motivo de ausência. Definir regra para valores antigos cuja qualidade não pode ser recuperada; não deduzir medição apenas porque o campo tem número.
- **Critério de fechamento:** um mesmo payload com duração observada, fases estimadas, calorias desconhecidas e passos realmente zero produz rótulos corretos em Android/web, inclusive cliente legado suportado. T-05/06 exercita round-trip e migração da qualidade.

### GF-14 — UTC do instante não resolve o significado do “dia” dos indicadores

- **Gravidade:** Média. **Bloqueador:** Sim — semântica diária/migração. **Estado:** Aberto.
- **Requisitos afetados:** FR-06/07/10, DAT-04/06, NFR-05, API-04/05, T-05/06/10; DEC-06/13/20.
- **Evidência:** Elephant [L139](01-master-spec.md#L139) trata timezone de jejum e NFR-05 exige calendário consistente, mas não define data de sono/atividade/readiness. [Dashboard Android](../../mobile/vytal-app/app/%28dashboard%29/index.tsx#L32) extrai dia UTC via toISOString; [sync HTTP](../../backend/app/api/v1/health_data.py#L24) transforma datas em UTC; métricas usam data do evento e repositórios consultam date textual.
- **Contraexemplo de mesa:** às 22h em São Paulo já é outro dia UTC em parte do ano; a UI pode pedir “hoje” diferente do diário pretendido. Sono atravessando meia-noite, viagem e backfill podem mudar categoria/treino associado. Testar duração de jejum com DST não cobre esse problema.
- **Correção recomendada:** definir timezone canônico por dataset/usuário, regra de atribuição do sono e conversão do intervalo civil para instantes. Versionar qualquer mudança em dias/histórico; se a decisão for manter UTC no legado, documentar o rótulo e a migração em vez de chamá-lo de dia local.
- **Critério de fechamento:** T-05/06 inclui meia-noite UTC/local, sono cruzando data, viagem e reprocessamento da mesma origem. Os resultados por versão/cliente são explícitos; não se escolhe novo dia de referência nesta revisão.

### GF-15 — Privacidade exige export/delete, mas ainda não existe fluxo verificável para cumpri-los

- **Gravidade:** Alta. **Bloqueador:** Sim — privacidade/novas categorias de dados. **Estado:** Aberto.
- **Requisitos afetados:** SEC-05/07, FST-11, DAT-05/06, T-11/15/17; DEC-15/18.
- **Evidência:** Elephant SEC-05/DAT-05 obrigam exportação/exclusão em caches, filas, backups e analítico; [L270](01-master-spec.md#L270) deixa os endpoints fora da aprovação implícita; [L148](01-master-spec.md#L148) e [L286](01-master-spec.md#L286) proíbem ressuscitação. Código atual não oferece exclusão/exportação de conta segundo inventário §6.
- **Problema/impacto:** não está definido se haverá API, processo operacional autenticado ou ambos, nem como provar identidade, acompanhar conclusão/erro, interromper coleta e aplicar tombstone após restore. Restaurar backup anterior à exclusão pode restaurar também credencial/fila/receipt que permite regravar dado removido. Receipts mínimos e exclusão irreversível têm tensão de retenção ainda aberta.
- **Correção recomendada:** escolher fluxo autenticado e política por entidade, incluindo dados derivados/Google, cancelamento de lembretes, revogação, expiração e reconciliação após restore. Definir ledger/geração de exclusão ou mecanismo equivalente que sobreviva ao procedimento de recuperação sem reter saúde desnecessariamente. Prazos e base de tratamento são decisões do proprietário com revisão adequada, não suposições desta auditoria.
- **Critério de fechamento:** T-17 demonstra export/delete com falha parcial e conta errada; T-15/11 restaura snapshot antigo e reconecta fila antiga sem recriar dados/credenciais de conta excluída. Pode ser procedimento operacional, desde que tenha contrato de resultado, prazo e evidência.

### GF-16 — “Sem perder confirmados” não foi conciliado com a política de desastre/RPO

- **Gravidade:** Alta. **Bloqueador:** Sim — durabilidade/implantação. **Estado:** Aberto.
- **Requisitos afetados:** FST-06, NFR-01, DAT-03/06, OPS-03/04, T-15/16; DEC-02/19.
- **Evidência:** Elephant FST-06 garante confirmação após commit durável; OPS-04 pede rollback sem perder sessões confirmadas; [L307](01-master-spec.md#L307) pede backup/restore; DEC-19 deixa RPO/RTO em aberto. O store realmente implantado também é desconhecido (DEC-02; inventário §6.1).
- **Problema/impacto:** commit de banco, rollback de aplicação e restauração de desastre não têm a mesma garantia. Um backup com RPO positivo pode perder stop ou receipt já confirmado e restaurar sessão como ativa. “Restaurar IDs” não garante restaurar a última versão nem impede retry duplicado após recuperação.
- **Correção recomendada:** separar garantias por falha: processo, instância, storage, região e rollback. Aprovar RPO/RTO e fonte de recuperação/replay; definir o que o usuário verá se a garantia permitir perda e como reconciliar recibos, versões, exclusões e reminders. Se a promessa for zero perda de confirmados, escolher infraestrutura/protocolo e ensaio que a sustentem.
- **Critério de fechamento:** T-15 simula confirmação→falha→restore antigo, verifica versão/sessão/receipt/notificações e mede os objetivos aprovados. Nenhuma métrica é inventada aqui; sem esse fechamento não chamar produção pronta.

### GF-17 — Lembretes não têm contrato completo de preferência, instalação e revogação

- **Gravidade:** Alta. **Bloqueador:** Sim — notificações do escopo de jejum, caso aprovadas. **Estado:** Aberto.
- **Requisitos afetados:** FST-09, FR-02, SEC-03/05/07, DAT-03, OPS-04, T-12/17; DEC-04/12/15.
- **Evidência:** Elephant [L152](01-master-spec.md#L152) a [L156](01-master-spec.md#L156) define condições úteis; [L297](01-master-spec.md#L297) e [L298](01-master-spec.md#L298) propõem intents/bindings; [L270](01-master-spec.md#L270) não aprova endpoints de preferências/push. Nenhum módulo de notificação está implementado atualmente (CUR-15).
- **Problema/impacto:** após escolher local/push/híbrido ainda faltam local de verdade das preferências, evento que calcula fire_at, vínculo de instalação/conta, reatribuição do aparelho, rotação/revogação do token e resultado de opt-out durante sessão. Meta é opcional; não existe trigger de lembrete automaticamente definido por start. Permissão do SO não resolve consentimento ou entrega após logout.
- **Correção recomendada:** especificar apenas o mecanismo escolhido, incluindo ciclo de preferência/instalação, operações locais ou API conforme necessário, quais transições agendam e quais invalidam, TTL/retry e falha parcial. Se somente local, não exigir API push desnecessária; se push, autenticar binding e impedir reutilização entre contas. Não escolher marcos/horários ou notificações clínicas por default.
- **Critério de fechamento:** T-12 cobre opt-out ativo, token reinstalado/rotacionado, logout A→B, stop em outro aparelho e entrega obsoleta; nenhum aviso de A aparece como instrução para B. Alternativamente, excluir notificações explicitamente de uma versão aprovada, sem dizer que FST-09 foi atendido.

### GF-18 — A revisão editorial protege conteúdo futuro, mas precisa rastrear os textos já existentes

- **Gravidade:** Média. **Bloqueador:** Não — há gates suficientes em EDU-01/FR-09 para impedir alegação sem revisão; recomendação de migração/release. **Estado:** Aberto.
- **Requisitos afetados:** FR-07/08/09, EDU-01 a EDU-04, DAT-04, T-06/13; DEC-06/17.
- **Evidência:** Elephant [L83](01-master-spec.md#L83) preserva insight, §6 exige evidência e §6.1 dá exemplos candidatos, sem catálogo de migração de copy. Hoje [ReadinessService](../../backend/app/services/readiness_service.py#L22) diz “Seu corpo está recuperado”; [catálogo Android](../../mobile/vytal-app/app/catalog.tsx#L35) promete saber “exatamente” e [L54](../../mobile/vytal-app/app/catalog.tsx#L54) atribui estágios ao Google apesar das estimativas do adapter.
- **Problema/impacto:** uma implementação pode revisar só a biblioteca nova de jejum e deixar mensagens persistidas/cliente antigo intactas. Falta checklist que identifique texto inline, conteúdo persistido e versão revisada; preservar algoritmo não obriga preservar afirmação enganosa.
- **Correção recomendada:** mapear cada superfície existente, fonte/revisor, substituição/qualificação e política para insight salvo no histórico. Deixar claro que exemplos educativos do Elephant não foram validados cientificamente e não substituem aprovação de conteúdo.
- **Critério de fechamento:** T-13 examina dashboard, catálogo, histórico, notificações e conteúdo offline/versão antiga; evidencia ausência de alegação individual não aprovada. Esta recomendação não certifica conteúdo atual como seguro para release.

### GF-19 — Preservar o código legado e prometer cliente legado funcional são compromissos diferentes

- **Gravidade:** Alta. **Bloqueador:** Sim — matriz de suporte/regressão. **Estado:** Aberto.
- **Requisitos afetados:** FR-10/12, SEC-01/06, INT-01/06, OPS-01/04, T-07/16; DEC-03/16.
- **Evidência:** Elephant [L86](01-master-spec.md#L86), [L88](01-master-spec.md#L88) e §2 usam preservação de funcionalidades/plataformas, mas suporte ainda depende DEC. [Cliente `mobile/`](../../mobile/src/services/api.ts#L9) não envia JWT e [router](../../backend/app/api/v1/router.py#L19) protege saúde/treinos. O Android oficial está inequivocamente em `mobile/vytal-app/`.
- **Problema/impacto:** não é possível demonstrar “dados próprios continuam acessíveis” no cliente legado tal como está apenas tornando autorização mais estrita. Equipe pode indevidamente reabrir API para suportá-lo, apagá-lo como inútil ou prometer paridade Android de telas só existentes na web. Publicação de branch de documentação tampouco comprova CI/branch protection corretos.
- **Correção recomendada:** distinguir preservação de fonte, capacidades existentes e suporte binário/runtime por versão. O proprietário escolhe clientes suportados e eventual migração de autenticação, mantendo dados e sem bypass de segurança; definir ordem cliente/backend e política de versões incompatíveis. Fonte legada permanece preservada nesta fase.
- **Critério de fechamento:** matriz versão×plataforma×capacidade×contrato×teste em T-16; T-07 valida somente caminhos realmente suportados. Retirada de suporte precisa aprovação explícita e não autoriza apagar código como parte desta revisão.

### GF-20 — Rastreabilidade por IDs não substitui cenários executáveis e oráculos

- **Gravidade:** Média. **Bloqueador:** Não — aperfeiçoamento do plano de teste; os bloqueadores de semântica estão individualizados acima. **Estado:** Aberto.
- **Requisitos afetados:** NFR-07, INT-01/03, OPS-01, T-01 a T-17.
- **Evidência:** Elephant [L342](01-master-spec.md#L342) inicia 17 grupos amplos; a validação documental final confirma IDs/links, não um teste de comportamento. Inventário §9 registra que 66 testes são principalmente unitários com mocks e não executaram APK/Google/GCP.
- **Problema/impacto:** um caso por grupo pode deixar a maior parte dos requisitos sem validação real. Contagem de IDs ou TypeScript aprovado não prova sessão nativa, duas instâncias, headers HTTP, recuperação e migração entre clientes. Não se encontrou afirmação falsa de testes futuros já passados; a lacuna é de granularidade do plano.
- **Correção recomendada:** após resolver decisões, decompor cada T em cenário com pré-condição, fixture/clock/provider, ação, resultado esperado, camada (unitário/contrato/integrado/E2E), ambiente e evidência exigida. Incluir jornada Android oficial autenticar→perfil→sync/dados e jejum start→kill/restart→stop→histórico, com notificações quando no escopo.
- **Critério de fechamento:** revisor consegue identificar caso e oráculo para cada invariante e falha relevante, inclusive os contraexemplos GF. Não exigir acesso a produção/saúde pessoal para comprovar testes. Cobertura de linhas é complemento, não gate único de segurança.

## 4. Decisões do proprietário e ordem recomendada de resolução

Esta tabela organiza dependências; não resolve DEC por preferência do revisor e não altera a especificação.

| Grupo de decisão | Achados relacionados | Ação necessária antes da aprovação correspondente |
|---|---|---|
| DEC-01/03/16 — escopo, versões e gates | GF-01/11/19 | Registrar aprovação Fase 0 e versão/escopo da spec; definir plataformas suportadas e estratégia de compatibilidade |
| DEC-02/15/18/19 — dados, sessão e operação | GF-05/08/09/10/15/16 | Fechar store e garantias, revogação/concorrência, proteção/retention, exclusão/export/restore e parâmetros testáveis |
| DEC-04/11/13/19 — jejum/tempo/offline | GF-02/03/04/05/06/07 | Escolher modo e regras, depois fechar máquina/requests/recibos/cliente/relógios; somente escolher A/B não basta |
| DEC-05/06/08/20 — contratos/integração/dia | GF-10/11/12/13/14 | Especificar schemas, dia canônico, proveniência, invariantes do provider e efeitos de migração |
| DEC-12/15/17 — notificações e conteúdo | GF-17/18 | Definir canal/ciclo de permissão e dados; revisão científica/editorial antes de disponibilizar conteúdo |
| DEC-07/09/14 e demais dependências de produto | GF-01, requisitos correspondentes do Elephant | Aprovar/excluir explicitamente preferências, compartilhamento e relação jejum/readiness; nenhum default inferido |

Ordem sugerida: delimitar escopo → segurança de identidade e ciclo de dados → garantias do store/tempo/idempotência → contratos e migração de clientes → jejum/offline/notificações/conteúdo → testes detalhados e runbook. Isso não é plano de implementação aprovado, cronograma, autorização de merge ou deploy.

## 5. Resoluções, bloqueios e reavaliação

**Bloqueadores de aprovação integral:** GF-01 a GF-11, GF-13 a GF-17 e GF-19 (**17**).
**Recomendações não bloqueadoras deste gate:** GF-12, GF-18 e GF-20 (**3**).

Por escopo, o agrupamento é:

- Gate/escopo: GF-01.
- Base de segurança, dados, integração e compatibilidade: GF-08/09/10/11/13/14/15/16/19.
- Jejum/tempo/offline/notificações: GF-02/03/04/05/06/07/17; GF-05 também depende do ciclo geral de dados e recuperação.

**Resoluções aplicadas nesta entrega: nenhuma.** Os 20 achados permanecem abertos. Aprovar este relatório documental não significa aprovar o Elephant nem marcar um problema resolvido. Não se solicita implementação para encerrar achado de especificação: primeiro corrigir/decidir a especificação em outra alteração autorizada, depois rever os contratos e critérios de aceitação. Testes de produto serão executados na fase autorizada correspondente.

Para fechar cada GF: registrar decisão do proprietário quando necessária, referência à nova versão/commit da spec, texto/contrato corrigido, resultado da reavaliação e teste futuro atualizado. Semântica removida do escopo pode fechar bloqueio daquele perfil somente mediante exclusão explícita; não rotular requisito ausente como implementado/validado. Depois da resolução dos bloqueadores aplicáveis, a aprovação final continua sendo explícita do proprietário, conforme AGENTS.md.

## 6. Método, validação e limitações desta execução

- Leitura dos quatro arquivos solicitados, confronto estático dos contratos/máquinas/decisões e inspeção dirigida de auth/refresh, OAuth/sync, persistência, métricas, consumidores Android/web/legado e workflows. Caminhos/linhas referem-se ao commit revisado, não ao futuro texto corrigido.
- Contraexemplos são **ensaios de mesa**, não exploração executada de jejum nem prova de incidentes em produção. Eles mostram comportamentos que o contrato ainda não impede ou não determina. Jejum e notificações continuam propostos.
- Nenhum teste funcional, lint de produto, build, APK, migração, acesso Google/GCP ou chamada a produção foi executado nesta Fase 2. Os resultados da Fase 0 não são recontados como validação nova. Não houve tentativa de extrair credenciais, coletar saúde pessoal ou investigar logs remotos.
- Validação documental: unicidade dos GF, contagens por gravidade/bloqueio, validade das referências de requisitos/arquivos/linhas e diff restrito a `docs/egm/02-goldfish-review.md`. Comparar a base confirma que Elephant, inventário, código, configuração e dependências permanecem inalterados.
- A branch própria publica somente esta revisão. Limitação de API GitHub, se ocorrer na tentativa de PR, é limitação de publicação do PR, não evidência de que um achado foi resolvido ou de que houve revisão externa. Estado de execução EGM autônoma, proteções remotas e produção não foi certificado.

**Conclusão de revisão:** o rascunho é base útil para discussão e mantém corretamente a aprovação pendente. Precisa das resoluções acima para tornar um escopo definido implementável e verificável. Esta entrega não altera a especificação, não autoriza implementação, não faz merge e não executa deploy.
