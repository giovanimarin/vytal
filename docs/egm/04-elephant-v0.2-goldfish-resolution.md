# Elephant v0.2 — matriz de resposta à revisão Goldfish

**Data:** 2026-11-04. **Estado:** resposta documental do autor, para nova revisão independente; não aprovação da especificação, código ou release.
**Especificação:** [Elephant v0.2](01-master-spec.md).
**Revisão preservada:** [Goldfish](02-goldfish-review.md), commit `a8a85b578c08c47f73b8cc5035a83aed0c9342a6`, sobre [Elephant 0.1.0](https://github.com/giovanimarin/vytal/blob/2722445bb889160390d79e2932f876bebbd03870/docs/egm/01-master-spec.md).
**Decisões:** [registro D01–D20](03-approved-product-decisions.md) no commit exigido `3d00ffa3e1d5aeb5259cdd06a926f33df460bf38`; IDs D e DEC não são equiparados.

## 1. Interpretação dos estados

- **resolvido na especificação:** a lacuna descrita tem correção técnica/contratual e cenário/oráculo explícitos na v0.2, sem implementar ou executar o teste. É conclusão autoral a ser contestada pela próxima Goldfish.
- **parcialmente resolvido:** há correção/desenho e testes propostos, mas falta política/parâmetro/decisão Q indispensável para fechar o grupo.
- **pendente:** a garantia essencial ainda depende de resposta/evidência externa ao registro; os controles propostos não a substituem.

Não alterar o relatório Goldfish original para marcá-lo resolvido retroativamente. Seus links/linhas referem-se ao commit Elephant 0.1.0; esta matriz referencia seções/IDs atuais. Perguntas Q estão na seção 14 da spec, casos TS e grupos T na seção 12. **Nenhum cenário TS foi executado nesta tarefa.**

## 2. Correção, contrato, cenário e aceite por achado

| GF / gravidade original | Estado autoral na v0.2 | Correção e contrato técnico | Cenários e aceite objetivo para reavaliação | Pendências / origem aprovada |
|---|---|---|---|---|
| GF-01 / Alta | parcialmente resolvido | §§1–2/13–14: perfil produto incorpora todas D, mantém DEC/Q e gates; OPS-05 não confunde decisão com aprovação técnica | TS-01/43/55: todas D rastreadas e nenhum requisito dependente de Q aparece liberado sem resposta/versão/responsável | D01–D20 incorporadas; Q-01–Q-15, aprovação Fase 0/versionada e responsáveis ainda necessários |
| GF-02 / Alta | parcialmente resolvido | §5.3/API-10: separar declarado/recebido/efetivo e time_quality; recebimento não vira fim; correção com revisão | TS-02/03/08: stop 10h offline/reconnect 14h não confirma fim 14h automaticamente; resposta mostra aceito ou conflito, preservando pedido | D02/D04 aprovam edição/offline; Q-02/Q-03 fecham validação/intervalos e revisão sem política inventada |
| GF-03 / Média | resolvido na especificação | §5.4/DAT-03: IDs de sessão estáveis, command/epoch/seq e depends_on; cadeia start/stop entre sessões; rejection bloqueia descendentes sem apagá-los | TS-04/05/06/59: entrega fora de ordem/kill não confirma B antes do predecessor exigido; mapa de IDs não perde stop/nota/correção | D04 incorporada; Q-03 define política de simultaneidade, sem substituir protocolo de dependências |
| GF-04 / Alta | resolvido na especificação | §5.3/NFR-02: instantes de evento não usam wall clock da recepção para duração; relógio backend é metadata; perda de âncora cliente explícita | TS-07/08: servidores com relógios divergentes não fazem fim<início por recepção nem truncam duração; reinício/clock cliente não perde intenção | D02/D04; validação de datas futuras/client clock continua em GF-02/Q-02, não se declara medição precisa |
| GF-05 / Alta | parcialmente resolvido | §5.5: epochs emitidos/ativos, geração, piso contíguo e receipts transacionais; expurgo não transforma seq antiga em nova | TS-09/10/11/35: replay após receipt expurgado nunca cria outra sessão; epoch desconhecido/revogado não é recriado; restore sem prova fica em quarentena | Q-04/Q-06/Q-07: janelas de retenção/idade offline e recuperação de ledger não fornecidas |
| GF-06 / Média | resolvido na especificação | §5.5/§7.3: receipt sem snapshot autoritativo; resource_current separado, ETag atual; cache por revisão monotônica/tombstone | TS-12/13: receipt start rev1 após completed rev2 não reabre timer/lembrete; resposta antiga não ressuscita excluído | D01/D04; não exige valor numérico de política para definir merge correto |
| GF-07 / Média | resolvido na especificação | §7.1: formato ETag/If-Match, validação, prioridade 428/400/412/409, parse 422 sem consumir key e rejeição definitiva com nova intenção | TS-14/15/16/17: cada combinação de header, terminal+stale, fingerprint alterado e replay tem resultado único, sem reaplicar CAS | D04/D19; campos de negócio ainda abertos Q-14 não são confundidos com protocolo HTTP |
| GF-08 / Alta | parcialmente resolvido | §6.1/§10: sid/generation, autorização no commit contra revoke; offline blocked_auth e migração de token não rastreável | TS-18/19/20/46/47: revogado nega novo commit, biometria não emite JWT, conta B não adota fila; logout offline não finge ACK remoto | Q-05/Q-06/Q-12: reset/reuso/lifetimes, retenção de intenção e suporte de token/cliente v1 |
| GF-09 / Alta | resolvido na especificação | §6.2/DAT-01: consumo CAS e parent único, transação token/sid/receipt e ordem comum de locks com revogação | TS-21/22/23: duas conexões criam no máximo um filho; retry não cria sucessor distinto; revoke bloqueia filho emitido antes | D13/D19; ação adicional ao reuso e TTL Q-05 não enfraquecem invariante de sucessor único |
| GF-10 / Alta | resolvido na especificação | §6.3: connection/account generation revalidadas no commit; disconnect invalida callback/job/intents anteriores; histórico prévio permanece | TS-24/25: provider suspenso, disconnect/delete e resposta tardia não repersistem raw/token/normalizado; status de revogação remota é honesto | D10 preserva importado, não autoriza nova gravação depois da barreira; D06/D13 separam propósitos |
| GF-11 / Alta | resolvido na especificação | §§7.1/7.2/10: v1 arrays/end_date inclusivo intocados; novos envelopes/calendários sob v2; adapters/versionamento explícitos | TS-26/27/28: cliente v1 mantém dia final e array, v2 cursor por snapshot; sem bypass de segurança por versão | D01/D09/D20; versão mínima/janela de suporte é GF-19/Q-12, não autorização para mudar v1 silenciosamente |
| GF-12 / Média | resolvido na especificação | FR-07/§8.2: corrigir “sem ambos” para “se faltar sono ou FC”; tabela verdade explícita | TS-29/56: quatro combinações de sinais e limiares legacy; nenhum dado ausente é preenchido para calcular | D08/D17 preservados; fórmula nova continua exigindo validação |
| GF-13 / Média | resolvido na especificação | FR-08/§8.1: quality por campo com value/unit/kind/source_records/method/calendar/missing/coverage; unknown/absent/zero distintos | TS-30/31: payload misto rotula fases legadas estimadas, duração observada, calorias desconhecidas e zero real; denominador desconhecido não dá 100% | D17 sem imputação; critérios quantitativos de suficiência são Q-09, separados da definição do schema |
| GF-14 / Média | parcialmente resolvido | §§7.1/8.2: calendar_basis/version e legado UTC explícitos, filtros absolutos/civis separados e sem conversão silenciosa | TS-26/32/53: dia final v1 preservado; novo dia local/sono/viagem só validados contra regra aprovada, não string UTC chamada “hoje” | Q-09: regra de atribuição sono/dia/estatísticas e migração semântica não escolhida nas D |
| GF-15 / Alta | parcialmente resolvido | §11.1/API-14: delete próprio com recibo/tombstone, geração contra fila, processo autenticado de acesso/portabilidade sem export UI; restore em quarentena | TS-33/34/35/58: conta errada negada, fila/import antigo não recriam registro e restore não serve dados excluídos antes da reconciliação | D10/D19; Q-03/Q-06/Q-07: ativo, prazos/base/canal legal, ledger/backups/chaves/restore |
| GF-16 / Alta | pendente | §11: separar crash com banco preservado, rollback de software e desastre; retirar promessa indistinta de perda zero; DAT-06/OPS-03 exigem runbook e restore | TS-36 pode verificar processo/commit; TS-37 depende de RPO/RTO/domínio de falha aprovados e evidence de recuperação — não pode ser marcado passado sem Q | D12 fixa PostgreSQL/GCP, não topologia/custo/RPO. Q-07/Q-08/Q-12 indispensáveis; produção permanece bloqueada |
| GF-17 / Alta | parcialmente resolvido | §9/API-17: famílias/prefs/quiet hours, vínculo owner/sid/generation e outbox versionado; caixa web/ACK sem browser push | TS-38/39/40: A→B, token rotacionado, stop em outro aparelho, quiet hours e aviso tardio não vazam/reabrem; gatilhos não inferidos da meta | D11 define famílias/canais, não Android local/push/híbrido nem triggers/defer/DST/expiry; Q-11 e revisão Q-01 |
| GF-18 / Média | resolvido na especificação | EDU-01–EDU-04/§9: manifesto editorial cobre insight persistido, catálogo, advanced, avisos, cache e versões legadas | TS-41/42: cada superfície tem texto→evidência→revisor→versão; ausência de revisão não vira fallback clínico; histórico não vira afirmação medida | D03/D05/D08/D09/D14/D17; revisão científica/conteúdo real ainda Q-01, checklist não é certificação clínica |
| GF-19 / Alta | parcialmente resolvido | FR-12/§10: distinguir fonte preservada, capacidade de produto e binário suportado; v2 exige autenticação rastreável, sem acesso anônimo ao legado | TS-28/43/44: combinações versão/plataforma/contrato recebem suporte/upgrade/negação definido e testes; Android oficial não confundido com mobile/ | D01/D09 ampliam paridade; Q-12 ainda define versões mínimas, janela/retirada/rollout e aprovação correspondente |
| GF-20 / Média | resolvido na especificação | §12: preservar T-01–T-17, ampliar T-18–T-26 e decompor em 59 casos TS com fixture/ação/camada/oráculo | TS-01/45/55/59: cada GF tem caso; runner/target/resultados distinguem passou/falhou/bloqueado; jornadas Android/web reais planejadas | D20; validação documental não é execução dos testes. Q pendente fica bloqueio, não skip/pass |

## 3. Contagem e efeito sobre os gates

| Estado autoral | Quantidade | IDs |
|---|---|---|
| resolvido na especificação | 11 | GF-03, GF-04, GF-06, GF-07, GF-09, GF-10, GF-11, GF-12, GF-13, GF-18, GF-20 |
| parcialmente resolvido | 8 | GF-01, GF-02, GF-05, GF-08, GF-14, GF-15, GF-17, GF-19 |
| pendente | 1 | GF-16 |

Dos 17 bloqueadores originais, **9 continuam parciais/pendentes** nesta avaliação: GF-01, GF-02, GF-05, GF-08, GF-14, GF-15, GF-16, GF-17, GF-19. Os outros 8 bloqueadores têm resposta contratual para nova contestação independente, não implementação validada. As três recomendações GF-12/18/20 receberam resposta documental.

Não aprovar integralmente a spec para implementação com base na contagem. Política/calendário/cancelamento/retention/recuperação/segurança e compatibilidade pendentes precisam respostas Q e revisão. A nova Goldfish pode reabrir qualquer resolução ou encontrar achados do escopo ampliado pelas D.

## 4. Verificação documental e próxima etapa

Revisão de consistência deve conferir:
- D01–D20 do registro exigido estão incorporadas, sem supor Dnn=DEC-nn.
- Todos os 20 GF têm correção, contrato, cenário/oráculo e estado honesto.
- Riscos S01–S15 e IDs estáveis anteriores permanecem rastreáveis; novos requisitos têm testes futuros.
- Não há alvo médico, prazo/limite/SLO/grace/RPO inventado, export UI/PDF/browser push ou autorização funcional implícita.
- Goldfish original, decisões aprovadas, inventário, AGENTS e código permanecem inalterados; diff é somente spec v0.2 e esta matriz.

Esta tarefa não executa teste funcional, build, migração ou deploy, não aprova formulação clínica, não verifica Garmin remoto e não muda configurações do ambiente. O commit/PR draft é documentação para revisão. Próximo passo: nova Goldfish independente e decisões Q, não implementação.
