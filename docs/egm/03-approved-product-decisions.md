# Vytal — registro aprovado de produto e matriz de correspondência

**Data de registro:** 2026-11-04. **Origem:** mensagem integral fornecida pelo Product Owner nesta conversa.
**Estado:** escolhas D01–D20 aprovadas como entrada de produto/arquitetura; consolidação e nova validação da especificação ainda pendentes.
**Base documental:** `docs/egm-phase-2-goldfish`, commit `a8a85b578c08c47f73b8cc5035a83aed0c9342a6`.
**Referências:** [AGENTS.md](../../AGENTS.md), [inventário](00-inventory.md), [Elephant 0.1.0](01-master-spec.md), [Goldfish](02-goldfish-review.md) e [instruções Elephant](prompts/01-elephant.md).

## 1. Autoridade, escopo e leitura deste documento

A seção 2 transcreve integralmente o registro recebido, inclusive ressalvas e instruções de execução. As seções seguintes são **análise de correspondência**, não novas decisões do proprietário nem alteração dos documentos anteriores.

D01–D20 identificam decisões da conversa. DEC-01–DEC-20 identificam perguntas agrupadas do Elephant; GF-01–GF-20 identificam achados da revisão. A relação é **muitos para muitos**, por assunto, nunca por coincidência numérica. Uma D pode responder apenas parte de uma DEC ou introduzir uma capacidade que a DEC não descrevia.

As escolhas de produto/arquitetura estão aprovadas nos termos literais registrados. Isso **não** aprova automaticamente a especificação Elephant 0.1.0, não resolve os 17 bloqueadores Goldfish, não certifica integração disponível e não autoriza implementação, merge, deploy, migração ou mudança de infraestrutura. A futura correção Elephant v0.2 deve incorporar essas escolhas, fechar detalhes técnicos e passar por nova revisão.

O Android oficial continua sendo `mobile/vytal-app/`. Nenhuma exclusão do candidato legado `mobile/`, retirada de suporte ou alteração funcional foi autorizada nesta entrega. O índice EGM existente não foi atualizado: este arquivo é o **registro de decisões**, não o plano de implementação anteriormente previsto com prefixo 03.

## 2. Registro integral recebido

<!-- BEGIN PRODUCT OWNER REGISTER -->
Vytal — Registro das 20 decisões aprovadas pelo Product Owner

Status: decisões de produto aprovadas em conversa com o Product Owner.

Objetivo: registrar as escolhas aprovadas como fonte de entrada para a consolidação da especificação Elephant.

Atenção: a numeração D01–D20 abaixo representa a ordem das decisões tomadas na conversa. Ela NÃO corresponde necessariamente aos identificadores DEC-01 a DEC-20 existentes no Elephant. É obrigatório realizar o mapeamento sem presumir equivalência.

D01 — Plataformas do controlador de jejum

O controlador de jejum deverá funcionar no backend, no aplicativo Android e na aplicação web desde a entrega inicial da funcionalidade.

A API centralizará as regras de negócio, com sessões e histórico sincronizados entre plataformas.

D02 — Funcionamento do jejum

- Jejum livre, sem duração-alvo obrigatória.
- Não haverá funcionalidade de pausa.
- O usuário poderá corrigir horários de início e término, inclusive de sessões anteriores.
- Cada sessão representa um intervalo contínuo.

D03 — Interface e acompanhamento do jejum

- Cronômetro de jejum em andamento.
- Linha do tempo educativa.
- Histórico e estatísticas.
- Lembretes opcionais.
- Anotações por sessão.

A linha do tempo deverá apresentar informações fisiológicas como estimativas educativas gerais, não como medições individuais ou afirmações clínicas.

D04 — Funcionamento offline

O aplicativo Android deverá permitir iniciar, acompanhar, encerrar, corrigir e anotar sessões de jejum sem conexão.

Quando a conexão retornar, haverá sincronização automática com deduplicação.

Conflitos deverão ser tratados sem perda silenciosa de dados. O protocolo exato de resolução permanece sujeito à especificação técnica.

D05 — Correlações com indicadores de saúde

Relacionar sessões de jejum a sono, frequência cardíaca, atividade e readiness.

Gerar insights descritivos personalizados quando houver dados suficientes.

O jejum não deverá modificar diretamente a fórmula de readiness.

Não apresentar correlação como causalidade.

D06 — Fontes de dados de saúde

- Manter integração com Google Fit.
- Adicionar integração com Garmin Connect.
- Health Connect não integra o escopo atual.
- Deduplicar dados provenientes de fontes diferentes.

A viabilidade e as condições de acesso à API oficial da Garmin deverão ser verificadas antes de assumir a integração como tecnicamente disponível.

D07 — Dashboard personalizável

O usuário poderá adicionar, remover e reordenar widgets.

As preferências serão vinculadas à conta e sincronizadas entre Android e web.

O cronômetro de jejum poderá ser exibido como widget opcional, além de existir uma tela dedicada.

D08 — Evolução do readiness

A fórmula poderá evoluir, mas toda alteração exigirá validação comparativa com a implementação atual.

Resultados históricos deverão ser preservados ou versionados de maneira que não sejam reinterpretados silenciosamente.

Exibir fatores contribuintes e qualidade dos dados.

Nenhuma fórmula nova será publicada sem validação.

D09 — Treinamentos e recuperação muscular

- Paridade funcional entre Android e web.
- Importação automática de treinos das fontes conectadas.
- Registro manual de treinos.
- Preservação das estimativas de recuperação muscular.
- Preservação do mapa corporal interativo.
- Deduplicação de treinos manuais e importados.

Estimativas de recuperação não devem ser apresentadas como diagnósticos médicos.

D10 — Privacidade e exclusão de dados

A funcionalidade de exportação de dados pela interface fica fora da versão inicial, sem afastar obrigações legais aplicáveis de acesso e portabilidade.

O usuário poderá excluir registros individuais ou toda a conta.

Ao desconectar uma fonte de saúde, o histórico já importado será preservado, salvo solicitação de exclusão.

Os dados serão privados, sem compartilhamento entre usuários.

D11 — Notificações

Haverá notificações opcionais para:

- Jejum.
- Recuperação muscular.
- Resumo diário de readiness.

Não haverá notificações específicas de falhas de sincronização nesta etapa.

O horário silencioso será configurável pelo usuário.

Os canais serão notificações Android e avisos dentro da aplicação web. Push do navegador não está incluído.

D12 — Persistência e infraestrutura

- PostgreSQL para persistência operacional e transacional.
- BigQuery para processamento analítico quando necessário.
- Google Cloud Platform como infraestrutura de produção.

SQLite poderá permanecer como ferramenta de desenvolvimento e testes, desde que a compatibilidade das regras de persistência seja garantida.

A escolha não autoriza migração imediata nem define automaticamente serviços, custos ou topologia de implantação.

D13 — Autenticação

- E-mail e senha.
- Login com Google.
- Biometria Android para desbloqueio local de sessão autenticada.
- Recuperação de senha por e-mail.

Autenticação por Google e autorização para acessar dados do Google Fit são processos independentes.

D14 — Perfil e objetivos pessoais

- Permitir múltiplos objetivos simultâneos.
- Histórico de peso e medidas corporais.
- Metas de frequência e volume de treinos.
- Evolução dos objetivos ao longo do tempo.
- Sugestões personalizadas não médicas, baseadas em tendências observadas.

D15 — Alimentação

Diário alimentar e controle de calorias estão fora do escopo desta etapa.

Não incluir funcionalidades nutricionais por inferência.

D16 — Histórico e análises

- Períodos de 7, 30 e 90 dias.
- Seleção de períodos personalizados.
- Comparação de períodos e indicadores.
- Insights de tendências, respeitando a disponibilidade e a qualidade dos dados.
- Somente gráficos individuais.

Relatórios consolidados e geração de PDF não fazem parte desta etapa.

D17 — Qualidade e origem dos dados

- Exibir a origem dos dados: Google Fit, Garmin Connect ou registro manual.
- Não preencher automaticamente dados ausentes.
- Permitir configurar a fonte prioritária por indicador.
- Exibir qualidade e cobertura dos dados utilizados em cálculos e insights.

A deduplicação deverá preservar rastreabilidade. Valores observados, estimados, derivados, ausentes e desconhecidos deverão ser distinguíveis quando aplicável.

D18 — Experiência visual e acessibilidade

- Temas claro e escuro, com opção de seguir o sistema.
- Português brasileiro inicialmente.
- Identidade visual consistente entre Android e web, respeitando características de cada plataforma.
- Acessibilidade, incluindo contraste, fontes ajustáveis, leitores de tela e controles acessíveis.

D19 — Segurança

A segurança será implementada incrementalmente, mas a publicação em produção permanecerá bloqueada até a aprovação dos testes críticos.

- Visualização de dispositivos e sessões conectadas.
- Encerramento remoto de sessões.
- Criptografia em trânsito e repouso.
- Armazenamento seguro de credenciais e tokens.
- Auditoria de eventos de segurança e acessos sensíveis.

O isolamento de dados entre contas e a autorização efetiva no backend são requisitos obrigatórios.

D20 — Desenvolvimento, testes e lançamento

- Desenvolvimento em entregas pequenas e incrementais.
- Disponibilização primeiro interna, depois beta e finalmente produção.
- Testes unitários, integração, API, Android/web e regressão automatizados no CI.
- Aprovação por fase, mediante Pull Request e evidências.

Nenhum merge, deploy ou alteração funcional está autorizado por este registro.

---

Instruções de execução

1. Criar "docs/egm/03-approved-product-decisions.md" contendo integralmente este registro.
2. Preservar as decisões D01–D20 e suas ressalvas.
3. Não equiparar automaticamente D01–D20 aos identificadores DEC-01–DEC-20 do Elephant.
4. Criar uma matriz de correspondência entre decisões aprovadas, decisões originais do Elephant e achados Goldfish.
5. Distinguir decisões de produto já aprovadas de detalhes técnicos ainda indefinidos.
6. Não declarar os 17 bloqueadores Goldfish resolvidos apenas com este registro.
7. Nesta tarefa, alterar somente o documento de decisões e, se necessário, um índice documental. Não alterar o Elephant, o Goldfish ou o código funcional.
8. Criar branch própria, commit e PR em modo draft, se as permissões permitirem.
9. Caso a criação do PR falhe, informar branch, commit e erro, sem considerar a operação inteira fracassada.
10. Não executar merge ou deploy.

Resultado esperado: registro integral das 20 decisões disponível e versionado no repositório, pronto para servir de entrada à correção Elephant v0.2.

<!-- END PRODUCT OWNER REGISTER -->

## 3. Matriz D → DEC originais → Goldfish

Os vínculos indicam onde revisar e testar na próxima especificação; **não significam fechamento de DEC ou GF**. “Aprovado” se refere ao conteúdo da D, não à implementação ou ao contrato candidato antigo.

| Decisão da conversa | Conteúdo aprovado / mudança que deve entrar no Elephant v0.2 | Perguntas DEC relacionadas por assunto | Achados GF relacionados | Detalhes ainda indefinidos / ressalvas preservadas |
|---|---|---|---|---|
| D01 | Jejum na API, Android e web desde a entrega inicial; regras centralizadas e sessões/histórico sincronizados | DEC-03, DEC-04, DEC-16 | GF-01, GF-11, GF-19, GF-20 | Contratos, compatibilidade/versões e sequência interna de entrega; não equivale a autorizar release |
| D02 | Jejum livre, sem alvo obrigatório, sem pausa; intervalo contínuo; correção de início/fim inclusive históricos | DEC-04, DEC-13 | GF-02, GF-03, GF-04, GF-07 | Cancelamento, sobreposição, validação/limites de correção, concorrência, timezone e trilha de revisões; não escolher protocolos ou durações clínicas |
| D03 | Cronômetro, linha do tempo educativa, histórico/estatísticas, lembretes opcionais e anotações por sessão | DEC-04, DEC-12, DEC-13, DEC-15, DEC-17 | GF-06, GF-13, GF-17, GF-18, GF-20 | Tipos/limites/proteção das notas, métricas das estatísticas, fontes e revisão educativa; notas agora têm aprovação de produto, embora o candidato antigo não as incluísse |
| D04 | Android inicia, acompanha, encerra, corrige e anota offline; sincronização automática, deduplicação, conflitos sem perda silenciosa | DEC-11, DEC-13, DEC-19 | GF-02, GF-03, GF-04, GF-05, GF-06, GF-07, GF-08, GF-15 | Exige protocolo além do candidato antigo: fila, versões, relógios, conflitos, retries, idempotência/expurgo e logout. O modo A que proíbe start offline não atende D04; não basta renomear a alternativa B como protocolo aprovado |
| D05 | Correlacionar jejum e saúde; insights descritivos personalizados quando houver dados suficientes; sem causalidade ou mudança direta de readiness pelo jejum | DEC-06, DEC-14, DEC-17, DEC-19 | GF-01, GF-13, GF-14, GF-18, GF-20 | Método, suficiência/cobertura, janelas, vieses e linguagem de incerteza; correlação não autoriza inferência clínica nem novo coeficiente de jejum no score |
| D06 | Manter Google Fit; adicionar Garmin Connect condicionado à viabilidade da API oficial; deduplicação entre fontes; Health Connect fora | DEC-08, DEC-10 | GF-10, GF-13, GF-14, GF-20 | Verificar acesso/condições Garmin, scopes/contratos, identidade de eventos e tratamento de dados conflitantes; não afirmar integração tecnicamente disponível nem escolher arquitetura de sync |
| D07 | Widgets adicionar/remover/reordenar; preferências por conta sincronizadas Android/web; tela dedicada e widget opcional de jejum | DEC-03, DEC-07 | GF-01, GF-11, GF-19, GF-20 | Estado inicial, migração de preferências, schema/API e conflito de reordenação; nenhum default novo de seleção é inferido |
| D08 | Readiness pode evoluir mediante comparação com atual; preservar/versionar histórico; fatores e qualidade visíveis; sem fórmula nova publicada sem validação | DEC-05, DEC-06, DEC-19 | GF-11, GF-12, GF-13, GF-14, GF-18, GF-20 | Nova fórmula, critérios quantitativos de validação, versionamento/backfill e decisão temporal; não mudar cálculo nesta entrega |
| D09 | Paridade Android/web de treinos/recuperação/mapa; importação automática e registro manual; deduplicação manual/importado; estimativas não médicas | DEC-03, DEC-06, DEC-08, DEC-10, DEC-16 | GF-10, GF-11, GF-13, GF-14, GF-18, GF-19, GF-20 | Expandir explicitamente o Android oficial, contratos de importação, matching/revisão de duplicatas e garantias do cálculo; não supor que as telas já existam nele |
| D10 | Excluir registros/conta; privado e sem compartilhamento; desconectar mantém histórico salvo exclusão; exportação na interface fora da versão inicial, obrigações legais preservadas | DEC-08, DEC-09, DEC-13, DEC-15 | GF-08, GF-10, GF-15 | Fluxo de exclusão e acesso/portabilidade aplicáveis, prazos/base jurídica, efeito em sessões ativas, derivados, filas/backups e restore; não interpretar ausência de export UI como dispensa legal |
| D11 | Notificações opcionais de jejum, recuperação e resumo readiness; horário silencioso configurável; Android e avisos in-app web; sem browser push ou notificações específicas de falha sync | DEC-03, DEC-12, DEC-15, DEC-17 | GF-08, GF-17, GF-18, GF-20 | Android local/push/híbrido, agendamento/revogação, quiet hours/timezone, bindings e privacidade; não remover estados de erro/retry da UI por excluir notificação de falha |
| D12 | PostgreSQL operacional/transacional; BigQuery analítico quando necessário; produção GCP; SQLite dev/teste condicionado à compatibilidade | DEC-02, DEC-10, DEC-19 | GF-05, GF-09, GF-15, GF-16, GF-20 | Serviços, custos, topologia, migração, transações/constraints/dialetos, backup/RPO/RTO; a escolha não é aprovação para migrar nem para executar análise remota |
| D13 | E-mail/senha, login Google, biometria Android como desbloqueio local e recuperação por e-mail; login Google independente de consentimento Fit | DEC-05, DEC-08, DEC-18 | GF-08, GF-09, GF-19, GF-20 | Vinculação de identidades/contas, reset e enumeração, provas de identidade, revogação/rotação/TTL, mecanismo web e proteção biométrica; biometria não substitui autenticação/autorização backend |
| D14 | Múltiplos objetivos, histórico de peso/medidas, metas de treino, evolução e sugestões personalizadas não médicas baseadas em tendências | DEC-05, DEC-06, DEC-17 | GF-01, GF-11, GF-13, GF-14, GF-18, GF-20 | Schema e migração do perfil atual, medidas/unidades, regras de metas/versões, suficiência das tendências e privacidade; sem diário alimentar por inferência |
| D15 | Diário alimentar/controle de calorias fora da etapa; sem função nutricional inferida | Sem DEC dedicada; restringe o escopo de DEC-04 e DEC-14 | GF-01, GF-19 | Não determina remoção do indicador existente de calorias de atividade; não criar alimentos/ingestão ou recomendação nutricional a partir de notas/metas de jejum |
| D16 | 7/30/90 dias, período personalizado, comparação de períodos/indicadores, tendências com qualidade e gráficos individuais; sem relatórios consolidados/PDF | DEC-03, DEC-06, DEC-13, DEC-19 | GF-11, GF-13, GF-14, GF-20 | Schemas, bordas, timezone, paginação e cálculos comparativos; não equivale a autorizar analytics entre usuários, export UI ou PDF |
| D17 | Origem Fit/Garmin/manual, prioridade por indicador, sem preencher automaticamente ausentes; qualidade/cobertura e distinção observado/estimado/derivado/ausente/desconhecido com rastreabilidade | DEC-05, DEC-06, DEC-08, DEC-19 | GF-10, GF-11, GF-13, GF-14, GF-20 | Schema por medida, precedência quando prioridade não tem dado, deduplicação/revisão entre fontes e migração de legado; distinguir imputação de medidas e regras de cálculo explicitamente versionadas |
| D18 | Claro/escuro/sistema; pt-BR inicial; consistência visual respeitando plataformas; contraste/fontes/leitores/controles acessíveis | DEC-03, DEC-20 | GF-01, GF-19, GF-20 | Padrão mensurável de acessibilidade, matriz de SO/dispositivos/navegadores, testes e persistência da preferência de tema; não inferir idiomas adicionais ou certificação WCAG específica |
| D19 | Isolamento/autorização obrigatórios, segurança incremental com produção bloqueada até testes críticos; dispositivos/sessões e encerramento remoto; criptografia/tokens seguros/auditoria | DEC-01, DEC-02, DEC-09, DEC-15, DEC-18, DEC-19 | GF-01, GF-08, GF-09, GF-10, GF-15, GF-16, GF-19, GF-20 | Testes críticos/oráculos, revogação access/refresh, atomicidade, chaves/rotação/auditoria e acesso mínimo; incremental não cria exceção para vazamento entre contas |
| D20 | Entregas pequenas; interna→beta→produção; CI unitário/integração/API/Android/web/regressão; aprovação por fase via PR/evidências; sem autorização funcional/merge/deploy | DEC-01, DEC-16, DEC-19 | GF-01, GF-11, GF-16, GF-19, GF-20 | Coortes, critérios de avanço/rollback, responsáveis/proteções de branch e evidências; não autoriza publicar ambiente ou alterar workflows nesta tarefa |

## 4. Leitura inversa das DEC originais

A tabela distingue **aspectos agora decididos** de **perguntas remanescentes**. Não altera o status escrito no Elephant 0.1.0; esse texto histórico continua intacto até a correção autorizada. Não equiparar “parte respondida” a “DEC inteira encerrada”.

| DEC original | D relacionadas | Aspectos respondidos pelo registro | Perguntas ainda a especificar ou decidir |
|---|---|---|---|
| DEC-01 | D19, D20 | Trabalho incremental, PR/evidências por fase e produção condicionada aos testes críticos | Aprovação formal Fase 0/versão da spec, responsáveis, branch de integração, proteções e autorizações de merge/release |
| DEC-02 | D12, D19 | PostgreSQL operacional, BigQuery analítico quando necessário, GCP e proteção de dados | Ambiente efetivamente implantado, serviços/topologia/custos, transações, backups/restore/chaves e plano de migração autorizado |
| DEC-03 | D01, D07, D09, D11, D16, D18 | Jejum API/Android/web inicial, preferências sincronizadas, paridade de treinos/recuperação/mapa, canais e pt-BR | Suporte por versão, destino de mobile/ e tabs antigas, estratégia de coexistência/migração e critérios de aceite por plataforma |
| DEC-04 | D01, D02, D03, D04, D15 | Funcionalidade de jejum no escopo de produto: livre, sem pausa, editável, notas, educação/estatísticas/lembretes e offline Android | Elegibilidade/contraindicações, significado de cancelamento e limites técnicos/temporais; registro não é autorização para implementar ou lançar |
| DEC-05 | D08, D13, D14, D17 | Métodos de autenticação, ampliação de perfil e qualidade dos dados no escopo | Formato auth plano/envelope, perguntas de feedback, senha/faixas/unidades/enums/nullability, schemas e compatibilidade dos modelos |
| DEC-06 | D05, D08, D09, D14, D16, D17 | Fórmula evolutiva somente validada, histórico preservado/versionado, fatores/qualidade e correlações não causais | Fórmula candidata, comparação/oráculos, calendário, proveniência por campo e backfill sem reinterpretação silenciosa |
| DEC-07 | D07 | Adicionar/remover/reordenar, por conta e sincronizado Android/web; widget jejum opcional e tela dedicada | Estado inicial, schema e migração, conflito de ordem, offline de preferências e compatibilidade |
| DEC-08 | D06, D09, D10, D13, D17 | Fit mantido, intenção Garmin oficial condicionada, Health Connect fora, importação/dedup e histórico preservado ao desconectar; login Google separado de Fit | Verificação de acesso Garmin, condições atuais do provider, scopes/redirects/protocolo OAuth, disponibilidade real e corridas de revogação |
| DEC-09 | D10, D19 | Privacidade e ausência de compartilhamento entre usuários; isolamento/autorização obrigatórios | Modelo de acesso operacional mínimo e funções técnicas, sem presumir produto de compartilhamento ou painel de administração aprovado |
| DEC-10 | D06, D09, D12 | Direção de fontes/importação e fronteira operacional/analítica | D não escolhe sync de saúde síncrono versus job, runner Beam/Dataflow ou Pub/Sub. O sync automático de D04 é de jejum offline, não escolha automática da arquitetura de ingestão de saúde |
| DEC-11 | D04 | Offline Android obrigatório para iniciar/acompanhar/encerrar/corrigir/anotar, com sync automática/dedup e conflitos sem perda silenciosa | Protocolo/estados/clock/fila/dependências/idempotência, múltiplos aparelhos e comportamento ao trocar de conta |
| DEC-12 | D03, D11 | Famílias de notificação, opcionalidade, quiet hours e canais Android/web in-app; exclusões explícitas | Local/push/híbrido Android, momento da permissão, schedule/TTL/retry, silêncio por timezone e ciclo de binding |
| DEC-13 | D02, D03, D04, D10, D16 | Intervalos contínuos sem pausa, correção histórica, notas, histórico, exclusão individual e períodos comparativos | Estados de cancelamento/exclusão/edição, sobreposição, conflitos, auditoria, instantes efetivos e bordas/agrupamento do histórico |
| DEC-14 | D05 | Correlações e insights descritivos com dados suficientes; jejum sem modificar diretamente fórmula de readiness; sem causalidade | Método/janelas/suficiência e linguagem validados. A futura spec deve permitir correlação sem reduzir a decisão a independência total nem adicionar coeficiente de jejum |
| DEC-15 | D03, D10, D11, D19 | Notas/sessões privadas, exclusão individual/conta, preservar histórico desconectado, export UI fora sem dispensa de obrigações legais, tokens seguros/auditoria | Bases/finalidades, consentimentos, acesso/portabilidade aplicáveis, prazos de retenção por entidade/cache/log/fila/backup/receipt e restore sem ressuscitação |
| DEC-16 | D01, D09, D19, D20 | Plataformas/paridade iniciais, segurança, estágios interna/beta/produção e CI/PR por fase | Versões suportadas, API/migrações, legado/demo, flags/coortes, rollback e revisão de dependências; nenhum workflow alterado aqui |
| DEC-17 | D03, D05, D08, D09, D14, D17 | Conteúdo educativo geral, estimativas/qualidade, correlações e sugestões não médicas; nenhuma alegação individual por timer | Fontes, revisores/responsáveis, público, contraindicações, suficiência e faixas educativas eventualmente propostas; não há validação clínica automática |
| DEC-18 | D13, D19 | E-mail/senha/Google, biometria local, recuperação e dispositivos/sessões com encerramento remoto | Vinculação/recuperação, TTL, revogação e família/rotação de tokens, concorrência/replay, logout offline e armazenamento web |
| DEC-19 | D04, D08, D12, D16, D17, D19, D20 | Restrições de integridade, validação comparativa/qualidade e lançamento com testes | Nenhum valor numérico de SLO, RPO/RTO, skew, janelas de idempotência, rate limits, páginas/intervalos ou critérios quantitativos foi fornecido; permanecem abertos |
| DEC-20 | D18 | pt-BR inicial, três opções de tema e acessibilidade/consistência por plataforma | Padrão mensurável, matriz de versões/tecnologias assistivas, critérios e evidências; WCAG 2.2 AA não foi automaticamente aprovado por essa D |

## 5. Consequências para a próxima correção Elephant, sem aplicá-las agora

A futura v0.2 precisará ampliar requisitos/modelos/contratos/testes para capacidades novas, além de escolher alternativas antigas. Este registro não cria IDs de implementação nem critérios quantitativos que o proprietário não forneceu.

1. **Jejum e clientes:** trocar alternativas de plataforma por API+Android+web desde a entrega inicial; incorporar tela e widget opcional, estatísticas e notas. Modelar correção histórica e offline de edição/notas, não apenas start/stop. Sem pausa; sem alvo obrigatório. Cancelar, excluir e corrigir continuam conceitos a distinguir tecnicamente.
2. **Saúde e treinos:** adicionar correlações descritivas sem causalidade, importação/deduplicação entre fontes e manual/importado, prioridade por indicador e qualidade/cobertura. D08 permite evolução de fórmula validada; D05 proíbe introduzir efeito direto do jejum no score. Nenhum cálculo muda nesta tarefa.
3. **Arquitetura:** registrar PostgreSQL como operacional/transacional e a condição de compatibilidade de SQLite dev/teste. BigQuery não vira store de sessão por conveniência. GCP aprovado não escolhe serviços, quotas, topologia ou custos e não autoriza migrar.
4. **Identidade e perfil:** incluir login Google separado de Fit, desbloqueio biométrico local, recuperação de senha, gestão/encerramento remoto de sessões e histórico/metas/objetivos múltiplos. Vinculação de conta, reset, schemas, revogação e migração continuam a especificar.
5. **Privacidade e UX:** diferenciar exclusão individual/conta, desconexão com histórico preservado, exportação fora da UI inicial e obrigações legais aplicáveis. Definir canais de avisos e quiet hours; sem browser push. Manter erros e feedback de sync na interface, sem criar a família de notificações excluída.
6. **Conteúdo e limites de escopo:** não tratar notas/objetivos como autorização nutricional, calorias de atividade como diário alimentar ou gráfico individual como PDF/relatório consolidado. Não confundir gráfico individual com ausência de comparação de períodos da mesma pessoa, que D16 aprova.
7. **Gates:** atualizar texto normativo, contratos e casos de teste em futura tarefa, e só então submeter à nova Goldfish. Aprovação de escolhas D não é aprovação da v0.2 ainda inexistente nem comprovação de critérios de aceite.

### 5.1 Dependências e indefinições preservadas

| Área | Escolha aprovada de entrada | Dependência ainda necessária antes de considerar o desenho fechado |
|---|---|---|
| Garmin | Adicionar integração oficial, condicionada | Verificar viabilidade, acesso/condições e cobertura dos dados; sem promessa de implementação disponível |
| Offline e edição | Operações D04 no Android são obrigatórias | Instantes declarados/recebidos/efetivos, versões, sobreposição, notas, filas e conflitos sem perda silenciosa |
| Deduplicação | Entre fontes de saúde e entre treino manual/importado | Identidade de evento, prioridade/ausência, revisões e preservação de origem; não apagar divergências por last-write-wins |
| Correlações/readiness | Insights descritivos, versionamento/validação e sem efeito direto do jejum na fórmula | Método, suficiência/cobertura, temporalidade, linguagem, comparação e preservação de resultados |
| Infraestrutura | PostgreSQL/BigQuery condicional/GCP | Store atual, esquema/migração, custo/topologia, transações e recuperação; nenhum número RPO/RTO aprovado |
| Autenticação/sessões | D13 e D19 no escopo | Claims, vinculação/recuperação, segredo/proteção, biometria local, expiração/revogação e corridas no servidor |
| Privacidade | Privado, exclusão e retenção ao desconectar salvo exclusão; sem export UI inicial | Fluxo legal/operacional de acesso/portabilidade, retenção, backups/tombstones e restauro |
| Avisos | D11 define canais e famílias | Android local/push/híbrido, preferências/quiet hours, token de instalação e entrega obsoleta; não inferir push web |
| Conteúdo/acessibilidade | Educação não médica, pt-BR, temas e acesso inclusivo | Evidências/revisores/contraindicações, padrões mensuráveis e matriz de dispositivos/leitores |
| Lançamento | Interna→beta→produção com CI e PR/evidências; testes críticos aprovados | Conjunto crítico, critérios de avanço/rollback, coortes/proteções/responsáveis e autorizações por fase |

## 6. Rastreabilidade dos 15 riscos do inventário

Nenhum risco do inventário é declarado corrigido por uma decisão ou por esta transcrição. A matriz mantém sua visibilidade para a futura especificação/testes.

| Risco | Decisões de entrada relacionadas | Obrigações a especificar/verificar posteriormente |
|---|---|---|
| S01 — autorização por owner | D10, D19 | Isolamento backend, recursos por conta e testes A/B em APIs, comandos, notas e histórico |
| S02 — defaults de segredos | D12, D19 | Fail-closed, proteção/provisão/rotação e configuração explícita; valores não foram definidos no registro |
| S03 — tokens/persistência sensível | D10, D12, D19 | Criptografia/armazenamento seguro, privilégios, revogação, backups e auditoria minimizada |
| S04 — OAuth/state/callback | D06, D13, D19 | Separar login Google de Fit; state/redirect/PKCE conforme protocolo validado; concorrência/revogação |
| S05 — paridade/persistência GCP | D12, D19, D20 | PostgreSQL transacional, compatibilidade de regras e fronteira analítica; migração/restore ainda não autorizados |
| S06 — estimativas como medições | D03, D05, D08, D09, D14, D17 | Origem/qualidade/cobertura, rótulos e validação; sem diagnóstico, imputação oculta ou causalidade |
| S07 — integração/ambiente/refresh Android | D01, D07, D09, D13, D18, D20 | Contratos e teste de jornada do Android oficial/web, ambiente isolado e renovação consistente |
| S08 — endpoint demo | D19, D20 | Política de demo/produção e testes negativos continuam necessários; aprovação do registro não libera seed |
| S09 — CORS | D19, D20 | Política de origens e testes por ambiente permanecem a especificar |
| S10 — logout/cache/armazenamento | D10, D13, D19 | Encerramento remoto, biometria apenas local, revogação e limpeza de dados/filas por conta |
| S11 — validação/contratos | D02, D03, D14, D16, D17, D20 | Tipos/faixas/unidades/nullability, correção/anotações/períodos e testes de contrato; não inventar limites |
| S12 — duplicação/concorrência/derivados | D01, D04, D06, D07, D09, D12, D17 | Idempotência, transações/versões, dedup, sync de preferências e qualidade/rastreabilidade dos derivados |
| S13 — logs com dados sensíveis | D10, D19, D20 | Auditoria de segurança/acessos não autoriza cópia de payloads de saúde ou tokens; definir acesso/retenção/minimização |
| S14 — privacidade e textos | D03, D10, D11, D14, D19 | Exclusão/obrigações legais, proteção de notas/metas, histórico preservado ao desconectar e conteúdo/avisos coerentes |
| S15 — CI/dependências/artefatos | D12, D19, D20 | Testes automatizados e gates incrementais; configuração/compatibilidade/versões e proteções ainda precisam evidências |

## 7. Estado Goldfish e limites de aprovação

**Nenhum GF é encerrado nesta tarefa.** Os 20 achados permanecem com o estado registrado no [Goldfish](02-goldfish-review.md); os **17 bloqueadores** continuam GF-01 a GF-11, GF-13 a GF-17 e GF-19. GF-12, GF-18 e GF-20 continuam recomendações não bloqueadoras daquele gate, não itens resolvidos.

O registro responde escolhas de produto relevantes a GF-01, mas faltam consolidação normativa, contratos, critérios técnicos, revisão e aprovação da versão resultante. PostgreSQL não prova atomicidade/restore; offline aprovado não resolve relógios/fila; canais de avisos não resolvem revogação/bindings; decisões de segurança não comprovam testes críticos passados.

D02/D03/D04 ampliam o desenho e requerem reavaliar estados, edições, notas e conflitos. D05/D06/D09/D13/D14 ampliam integrações e dados sensíveis. Isso pode gerar novos achados na próxima Goldfish; o conjunto antigo não é automaticamente uma lista exaustiva do escopo ampliado.

**Próximo passo documental, não executado aqui:** tarefa autorizada de correção Elephant v0.2 usando D01–D20, as duas matrizes e os contraexemplos GF; preservar IDs existentes e criar novos IDs quando necessário, com critérios e dependências explícitos; nova validação Goldfish e aprovação versionada. A aprovação de decisões de produto não substitui essas etapas.

## 8. Escopo e validação desta entrega

- Entrega versionada restrita a `docs/egm/03-approved-product-decisions.md`; índice, Elephant, inventário, Goldfish, instruções, código, dependências e configuração preservados.
- Validação documental executada: integridade da transcrição, presença única das 20 decisões na fonte, cobertura das 20 D/20 DEC/20 GF/15 riscos nas matrizes e referências locais, além de diff/hashes dos documentos de base.
- Não reexecutar testes funcionais, builds, migrações ou deploy para validar uma transcrição documental. Nenhum teste crítico de produto é declarado aprovado aqui.
- Publicação será em branch própria e PR **draft**, se a API/permissões permitirem; falha do PR não desfaz commit/push do registro nem aprova a especificação.

