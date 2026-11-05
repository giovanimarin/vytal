# Vytal — Q-01–Q-15: produto, engenharia e bloqueios reais

**Base:** Elephant v0.2, commit `edee1012053022d743e5b88c2de2845a6c4f16f6`. **Referências:** [spec](01-master-spec.md), [D01–D20](03-approved-product-decisions.md), [revalidação](05-goldfish-v0.2-revalidation.md) e [pacotes](06-implementation-packages.md).

## 1. Conclusão operacional

As Q do Elephant agrupam decisões de produto, parâmetros técnicos e evidência operacional. **Nenhuma Q isoladamente exige paralisar toda implementação.** Ela bloqueia a função/garantia que depende da resposta. Não usar uma política de jejum pendente para adiar owner guard v1 nem RPO de produção para adiar teste de contrato local.

Há, porém, um **gate formal comum G-A**: AGENTS exige aprovação explícita de especificação versionada antes de código funcional. O pedido atual autoriza revisão/backlog/documentação, não código. O PO pode aprovar um recorte versionado de correção, registrando como atende a esse gate; o revisor não aprova sozinho a versão inteira nem cria uma exceção implícita. Se for necessário ajustar o processo para aprovações parciais, isso deve ser explícito do proprietário antes da implementação.

As recomendações de engenharia abaixo **não foram aprovadas ou implementadas**. Segurança obrigatória e direitos legais não são alternativas que possam ser dispensadas por conveniência. Quando uma decisão depende de privacidade/jurídico ou revisão clínica/editorial, o PO deve designar responsável competente e evidência, não presumir que uma preferência valide uma alegação médica.

## 2. Classificação das 15 questões

| Q | Decisão que realmente cabe ao PO / responsável de negócio | Definição que engenharia pode propor, com fundamento | Bloqueio específico; efeito nos primeiros pacotes |
|---|---|---|---|
| Q-01 | Público/elegibilidade e responsável clínico/editorial; aceitar conteúdo e revisão de fontes/contraindicações | Manifesto versionado texto→fonte→revisor→versão, conteúdo indisponível sem revisão; separação timer/explicação evita falsa medição | Bloqueia conteúdo educativo/insights clínicos e release de jejum elegível; **não** bloqueia PKG-01–PKG-07 |
| Q-02 | Qual experiência para corrigir/confirmar horários históricos/futuros e inconsistentes; expectativas de uso após reboot | Instantes declarados/recebidos/efetivos separados; monotônico quando válido; needs_review explícito; não inferir fim na reconexão nem escolher tolerância sem medição/aprovação | Bloqueia aceite final do tempo/edição de jejum; não a autorização por owner ou regressão v1 |
| Q-03 | Uma ativa por conta, permitir/proibir overlap, significado de cancelar e excluir sessão ativa; efeitos desejados da correção | Máquina de estados/constraints/CAS conforme escolha. Propor uma ativa e conflito explícito como alternativa, **não** como decisão já aprovada. RV-01/RV-02 são refinamento técnico separado | Bloqueia regras de jejum e exclusão de ativa; não tests/hardening atuais |
| Q-04 | Expectativa de duração máxima offline e equilíbrio retenção/conveniência/privacidade, junto ao responsável de dados | Política de epoch/piso/recibo e recuperação; RV-01 propõe bind tardio de ETag só antes do primeiro envio, preservando fingerprint depois; testar expurgo/replay com ledger | Bloqueia protocolo offline final/retenção; não login plano, refresh cliente ou testes existentes. Não inventar prazo |
| Q-05 | UX/efeitos de reset, linking/unlinking e logout offline; quais sessões encerrar; tolerância de conveniência versus segurança | Revisar TTL/grace/rotação/armazenamento conforme threat model; parent único/transação, sid/generation e revogação efetiva já têm direção obrigatória D19. Propor linking com prova de posse e cliente sem refresh recursivo | Bloqueia sessão v2/recovery/linking completos (PKG-09), não remoção do deadlock (PKG-04) ou leitura do contrato v1 (PKG-03) |
| Q-06 | Finalidade/base de tratamento, consentimentos, política/prazos de retenção, canal de acesso/portabilidade e responsáveis; obrigações legais com revisão adequada | Mapear dados/derivados/backups, ledger/tombstones mínimos e geração de exclusão, chaves e fluxo autenticado. Propor quarentena pós-restore até reconciliar; sanitizar logs agora sem esperar prazo novo | Bloqueia exclusão integral/garantias de privacidade novas, não parar de imprimir payload/token (PKG-06) nem guard (PKG-01) |
| Q-07 | RPO/RTO e domínios de falha aceitáveis, orçamento e aprovação de produção | Propor arquitetura gerenciada PostgreSQL em GCP e analisar custo/HA/backup/ledger com ensaios; escolha concreta de serviço/topologia não aprovada. Garantia de crash com banco íntegro separada de desastre | Bloqueia migração/produção/restore; não PostgreSQL efêmero de CI/UoW (PKG-07), pois D12 escolheu o engine |
| Q-08 | Expectativas de disponibilidade/latência, capacidade-alvo e limites que afetam experiência, custo e retenção | Medir baseline/carga e propor rate limits, payload/página/timeout; riscos e valores sob revisão, sem número arbitrário. Primeiro fix não muda o timeout existente ou cria mínimo de segredo novo | Bloqueia aceite de performance/limites do serviço novo; não testes de contratos vigentes/hardening. Gate de produção, não veto global |
| Q-09 | Dia civil de sono/readiness, agrupamentos/estatísticas, significado e apresentação de comparação/sugestão, com revisão de suficiência/saúde | Propor calendar_basis por versão e IANA no novo contrato, mantendo v1 UTC/inclusivo; método/cobertura/amostra fundamentados antes de insight. Não usar correlação como causalidade nem adicionar jejum à fórmula | Bloqueia fórmula/insights/calendário/estatísticas novos; não preservar o BETWEEN atual ou testar ausência de sono/FC (PKG-05) |
| Q-10 | Aceitar eventual indisponibilidade/custo/condições da Garmin e decidir experiência quando prioridade não tem dado ou fontes divergem | Verificar API oficial/acesso/scopes; propor IDs de origem/source links, matching e revisão de duplicatas; escolher sync síncrono/job e runners com evidência de carga. Não inferir scraping ou provider disponível | Bloqueia Garmin/dedup/imports novos e arquitetura de ingestão final; não correção owner em Fit atual nem sanitização de log |
| Q-11 | Quais eventos gerarão lembretes, quando adiar/descartar, UX de quiet hours/viagem e privacidade do conteúdo | Comparar local/push/híbrido Android segundo confiabilidade/bateria/custo; outbox/binding por conta, invalidação e dedup são propostas técnicas. Web segue in-app, sem browser push aprovado | Bloqueia notificações completas; não testes/regressões de auth/persistência isolada |
| Q-12 | Aprovação do recorte e responsáveis; versões/janelas de suporte, retirada de legado, coortes/critérios de interna/beta/produção | Propor matriz por cliente/contrato e rollback compatível; adicionar job de regressão em PR e manter falha lint visível. Proteções/required checks requerem permissões administrativas; isso é gate de merge, não de escrever o teste | A **parte formal de aprovação** afeta qualquer pacote funcional. Outras partes bloqueiam release/compatibilidade nova, não exigem escolher toda política antes de PKG-01 |
| Q-13 | Nível de acessibilidade aceito e se tema acompanha conta ou dispositivo; alcance de plataformas suportadas | Recomendar WCAG 2.2 AA para web mais verificação TalkBack/escala/foco Android, com matriz e evidências; é proposta, não aprovação automática. pt-BR/light/dark/system já decididos D18 | Bloqueia aceite UX/acessibilidade nova; não auth backend. Testes existentes não dependem de aprovar idioma adicional |
| Q-14 | Perguntas/semântica de feedback, unidades/taxonomia/metas/nullability e expectativas de perfil | Propor schemas/versionamento e adapter preservando significado; alinhar senha Android aos 8 **já exigidos no v1** não é decidir nova política. Não inventar onde salvar trained_today nem descartar pergunta | Bloqueia PKG-08 completo/perfil novo; não PKG-03 no contrato plano e regra v1 existentes |
| Q-15 | Se haverá analytics de produto além das análises individuais aprovadas; finalidade/consentimento e acesso | Propor inventário mínimo de eventos/proteção/redaction com privacidade, sem tracker novo por inferência. Auditoria de segurança D19 é distinta de marketing/telemetry de saúde | Bloqueia nova coleta/telemetria; não retirar logs sensíveis existentes ou executar testes sintéticos |

**Questões que bloqueiam qualquer implementação funcional nesta rodada:** nenhuma escolha de domínio específica isoladamente; o que é comum é **G-A**, a aprovação explícita do recorte versionado, tratada na parte de governança de Q-12/AGENTS. Esta frase não autoriza código sem aprovação e não reduz os bloqueios de produção a uma formalidade.

## 3. Recomendações técnicas que não precisam virar novas decisões de produto

Podem ser propostas e revisadas pela engenharia dentro de um pacote aprovado; não exigem que o PO desenhe um algoritmo ou escolha cada biblioteca:

1. **Owner guard v1:** usar o sub validado e comparar com path/query/corpo/state antes de efeitos; resposta genérica de negação recomendada 404, mantendo contratos válidos. D10/D19 já proíbem acesso entre contas. Revisar/testar o código é necessário; não perguntar ao PO se deve existir bypass.
2. **Interceptors e identidade:** consumir a identidade plana real, transição de sessão coerente e excluir refresh/login/cadastro de renovação recursiva. Não esperar schema v2 ou novos métodos de autenticação para reparar o fluxo atual.
3. **CAS e fila:** para RV-01, definir intenção versus comando transmitido e bind tardio de revisão do predecessor antes de congelar fingerprint; para RV-02, eliminar duplicidade ou exigir igualdade de body/header com erro estrutural. Isso é protocolo técnico a corrigir/rever, não escolha de duração de jejum.
4. **PostgreSQL:** driver/UoW/fixtures/isolamento e teste real de concorrência são desenho de engenharia sob D12. Propor laboratório PKG-07 antes de alterar fábrica/app/schema; não pedir definição de RPO para criar teste efêmero nem alegar que teste resolve produção.
5. **Testes/CI:** selecionar harness mínimo compatível com stacks existentes, fixar versões e usar fixtures/providers sintéticos; fazer o job rodar nas bases reais. Não confundir lint legado falhando com autorização para desativar checks.
6. **Logs:** remover tokens/raw payload antes de discutir duração de retenção futura. Não criar evento sensível novo para substituir outro sem inventário de finalidade/acesso.

São recomendações fundamentadas nos defeitos observados e nas invariantes já aprovadas; implementação e decisões técnicas concretas ainda passam pelo PR autorizado e revisão. Nenhum prazo, limite, número de coorte ou tolerância foi escolhido nesta revisão.

## 4. Lista objetiva para aprovação, por prioridade

### Agora — para destravar o primeiro PR

**Aprovar ou rejeitar o recorte PKG-01**, identificado no backlog e neste commit documental: owner guard nas 15 operações pessoais v1, proteção do usuário do state antes do exchange, regressões e mínimo de CI; nenhuma nova feature, API v2, migração ou deploy. Confirmar como a aprovação desse escopo versionado atende ao gate de AGENTS. Não é necessário responder todas as Q antes desse recorte.

As recomendações 404 no mismatch e método de fixture podem ser revistas na aprovação técnica do pacote; o requisito de não acessar B com token A não é opcional. Se o proprietário exigir aprovação integral da master spec antes de qualquer correção funcional, isso deve ficar explícito: o backlog permanece pronto, mas o revisor não declara a exceção sozinho.

### Antes das funcionalidades específicas

| Frente | Perguntas objetivas a responder / responsável a designar |
|---|---|
| Jejum | Q-01/Q-02/Q-03/Q-04: público/revisor, aceitar ou revisar horários, uma ativa/overlap/cancelamento/exclusão ativa, idade offline/retention. Engenharia fecha RV-01/RV-02; não delegar essas escolhas de produto ao algoritmo |
| Sessões/login novo | Q-05/Q-06/Q-12: efeito de reset e linking/logout, lifetimes/reuso propostos pelo time de segurança, dados retidos e transição de clientes/tokens |
| Direitos de dados e produção | Q-06/Q-07/Q-08/Q-12: canal/base/prazos com privacidade/jurídico, garantias/custos/objetivos de recuperação e critérios críticos de promoção/rollback |
| Análises/integrações | Q-09/Q-10/Q-14: dia/estatísticas/suficiência e medidas/perguntas; viabilidade Garmin e comportamento de prioridade/duplicata. Engenharia apresenta alternativas e evidências |
| Notificações/UX | Q-11/Q-13: eventos/defer/silêncio/lockscreen e padrão/matriz acessível; engenharia recomenda mecanismo conforme plataforma aprovada |
| Analytics de produto | Q-15: existe finalidade e aprovação para coleta adicional? Sem resposta, não adicionar tracker; isso não impede gráficos pessoais nem sanitização |

## 5. O que a aprovação deste relatório não faz

Não modifica D01–D20, não resolve automaticamente os 11 bloqueadores originais ainda parciais/pendentes na revalidação, não aprova a especificação inteira, não realiza migração, não conecta provider e não aciona release. O próximo passo útil é aprovar um recorte concreto e abrir seu PR de código separado, não produzir mais uma especificação integral antes de corrigir um acesso cruzado já reproduzido.
