# Vytal — revalidação Goldfish do Elephant v0.2

**Base exata:** `docs/egm-elephant-v0-2`, commit `edee1012053022d743e5b88c2de2845a6c4f16f6`.
**Parecer:** não aprovar integralmente a especificação; propor aprovação delimitada dos pacotes fechados em [06-implementation-packages.md](06-implementation-packages.md).
**Fontes preservadas:** [AGENTS.md](../../AGENTS.md), [inventário](00-inventory.md), [Elephant v0.2](01-master-spec.md), [Goldfish original](02-goldfish-review.md), [D01–D20](03-approved-product-decisions.md) e [matriz do autor](04-elephant-v0.2-goldfish-resolution.md).

## 1. Resultado executivo e limites

Reavaliação individual: **9 resolvidos no desenho da especificação, 10 parcialmente resolvidos, 1 pendente**. Divergência da matriz autoral: **GF-03 e GF-07 voltam a parcialmente resolvidos** por lacunas concretas de revisão esperada/fingerprint. Dos 17 bloqueadores originais, **11 continuam parciais/pendentes**: GF-01, GF-02, GF-03, GF-05, GF-07, GF-08, GF-14, GF-15, GF-16, GF-17 e GF-19. Isso não bloqueia automaticamente uma correção v1 independente de jejum/infraestrutura, mas impede aprovar o produto completo.

“Resolvido” nesta revisão significa que o problema contratual específico recebeu resposta suficiente para seu desenho, **não** que existe código, passou teste ou está liberado em produção. Ausência de código novo não é motivo, por si só, para reabrir uma correção documental. Inversamente, um schema escrito não prova durabilidade ou autorização executável.

Foi feita leitura crítica separada da matriz autoral e confronto dirigido com o código. **Limitação de independência:** este mesmo assistente contribuiu para os documentos anteriores; não se declara auditoria externa, revisão humana ou segundo autor que não ocorreu. As duas discordâncias abaixo, referências e contraexemplos tornam o parecer contestável; aprovação continua do proprietário.

**Conclusão prática:** o primeiro PR deve fechar o acesso cruzado nas APIs v1 e incluir testes de regressão. Login Android, interceptor de refresh, validação de defaults de segredo, contratos v1 e sanitização de logs também podem avançar em recortes pequenos. Nenhuma dessas tarefas exige escolher política de jejum, RPO ou fórmula nova. O gate formal de aprovação é separado no backlog e na [classificação Q](07-owner-decisions-and-engineering.md).

## 2. Matriz atualizada GF-01–GF-20

Referências de seção/requisito abaixo apontam ao Elephant no commit da base. Estados são desta revalidação; a matriz 04 e o relatório original não foram editados.

| Achado | Estado do autor | Revalidação | Evidência/requisitos e razão do parecer | Funcionalidades afetadas / condição de fechamento |
|---|---|---|---|---|
| GF-01 | parcialmente resolvido | parcialmente resolvido | §§1–2/13–14, OPS-05: D foram incorporadas, mas aprovação do escopo, responsáveis e políticas Q não existem por decorrência do registro | Governança/release integral; aprovar escopos versionados e resolver Q relevantes. Não exige resolver Q-01–Q-15 para corrigir owner v1 |
| GF-02 | parcialmente resolvido | parcialmente resolvido | §5.3, FST-02/03/13, TS-02/08: declarado/recebido/efetivo separados, sem fim na reconexão; ainda falta regra de aceitação/correção de horário inconsistente | Jejum offline/histórico; Q-02/Q-03 devem fixar rejeição/revisão/aceite sem inventar tolerância |
| GF-03 | resolvido na especificação | parcialmente resolvido | §5.4/§5.5, FST-08, DAT-03: DAG e IDs resolvem ordem/identidade, mas não vinculam `base_revision`/ETag do sucessor ao resultado do predecessor antes de congelar fingerprint. Ver RV-01 | Start→nota→stop e sessões consecutivas offline; fechar binding tardio, identidade de intenção/comando e casos de concorrência |
| GF-04 | resolvido na especificação | resolvido | §5.3, NFR-02, TS-07: hora de recepção não calcula duração; mudança de instância/relógio backend não altera intervalo declarado | Cronômetro/servidor: suficiente para o problema original de wall clock backend. Política de relógio cliente continua GF-02, não resolvida por esta conclusão |
| GF-05 | parcialmente resolvido | parcialmente resolvido | §5.5, DAT-03/05: epoch/piso impedem replay ingênuo, mas expurgo/idade offline/ledger após restore dependem Q-04/Q-06/Q-07 | Fila/idempotência/dados; aprovar retenção e demonstrar piso/epoch não retrocedendo no domínio de falha |
| GF-06 | resolvido na especificação | resolvido | §5.5/§7.3, TS-12/13: receipt não é snapshot atual, revisão monotônica e tombstone não regridem | Cliente/cache/timer/avisos: implementar/testar separação e merge por revisão; não há autorização para habilitar jejum por essa resolução |
| GF-07 | resolvido na especificação | parcialmente resolvido | §7.1/§7.3, SEC-08, TS-14–TS-17: HTTP/ETag melhoraram; falta regra para divergência entre `base_revision` do corpo e If-Match. Ver RV-02 | Mutações v2/edição/notas; eleger autoridade única ou exigir igualdade antes de consumir chave, com caso explícito |
| GF-08 | parcialmente resolvido | parcialmente resolvido | §6.1/§10, SEC-07, FR-02/22: sid/generation e barreira descritos; TTL/reset/linking/logout offline e migração de tokens seguem Q-05/Q-06/Q-12 | Gestão remota/sessões/reset; owner check v1 é separável e não precisa implementar todo esse modelo |
| GF-09 | resolvido na especificação | resolvido | §6.2, DAT-01, TS-21/22/23: CAS, parent único, transação e ordem de locks dão invariante de no máximo um sucessor | Refresh servidor: desenho suficiente para concorrência; código atual ainda faz get→revoke→create separados. Runtime exige persistência/migração, não está pronto por documento |
| GF-10 | resolvido na especificação | resolvido | §6.3, FR-05, INT-02, TS-24/25: revalidar generation no commit contra disconnect/delete cobre resposta externa atrasada | Providers/callback/import: contrato de barreira adequado; tabelas/gerações inexistentes no código atual e integração real continuam a construir/testar |
| GF-11 | resolvido na especificação | resolvido | §§7.1/10, FR-12, TS-26: v1 preserva arrays e data final inclusiva; envelopes/intervalos novos em v2 | Compatibilidade de shape/intervalo: pode receber testes agora; suporte de todos os binários antigos é GF-19, não resolvido |
| GF-12 | resolvido na especificação | resolvido | FR-07/§8.2, TS-29: tabela verdade exige sono E FC válidos; ausência isolada não calcula | Readiness baseline: reforçar testes sem mudar fórmula; não aprova algoritmo clínico ou correlação nova |
| GF-13 | resolvido na especificação | resolvido | §8.1, FR-08, TS-30/31: qualidade por campo distingue observado/estimado/derivado/ausente/desconhecido e cobertura sem denominador inventado | Summary/insights: desenho de qualidade suficiente; matching/fallback de fontes e suficiência seguem Q-09/Q-10 |
| GF-14 | parcialmente resolvido | parcialmente resolvido | §8.2, NFR-05, TS-32: legacy UTC explícito, mas dia civil/atribuição do sono/agrupamento não decididos | Histórico/sono/readiness/correlações; Q-09 bloqueia mudar semântica, não teste de regressão do BETWEEN atual |
| GF-15 | parcialmente resolvido | parcialmente resolvido | §11.1/API-14: barreira/delete/processo descritos; retenção, base/canal legal e ledger de restore ainda dependem Q-03/Q-06/Q-07 | Exclusão/exportação legal/backups: não liberar fluxo completo ou promessa de apagamento integral sem essas definições |
| GF-16 | pendente | pendente | §11, NFR-01, OPS-03, TS-37: separar processo/desastre remove promessa falsa, mas não produz RPO/RTO/topologia/evidência | Produção/migração/restore: pendente Q-07/Q-08. Não impede laboratório PostgreSQL isolado e rollback de teste |
| GF-17 | parcialmente resolvido | parcialmente resolvido | §9/API-17, TS-38–TS-40: preferências/bindings/gerações descritos; transporte Android, gatilhos, defer/expiry não escolhidos | Avisos jejum/recuperação/readiness: Q-11 e conteúdo Q-01 bloqueiam feature completa; não criam browser push |
| GF-18 | resolvido na especificação | resolvido | EDU-01–EDU-04 e manifesto §9 abrangem copy inline/persistida/cache/avisos, não só jejum novo | Conteúdo: checklist corrigido; nenhuma evidência clínica real foi aprovada por esse desenho; Q-01 continua necessário |
| GF-19 | parcialmente resolvido | parcialmente resolvido | §10/FR-12 distingue fonte preservada, capacidade e binário; Q-12 não escolheu versões/janelas. mobile/ não envia JWT | Suporte/rollout de clientes: não reabrir API para o legado; correção owner é necessária mesmo que exponha cliente já incompatível |
| GF-20 | resolvido na especificação | resolvido | §12/NFR-07 contém fixture/ação/camada/oráculo nos 59 TS e grupos T; não apenas IDs. Casos RV-01/RV-02 devem ser adicionados ao corrigir as lacunas | Plano de teste: estrutura suficiente como plano, não evidência de execução. Nesta revisão só baseline e reprodução representativa foram executados |

**Contagem:** resolvidos GF-04/06/09/10/11/12/13/18/20 (**9**); parciais GF-01/02/03/05/07/08/14/15/17/19 (**10**); pendente GF-16 (**1**).

## 3. Lacunas técnicas adicionais que motivam as divergências

### RV-01 — Congelamento de comando versus revisão ainda desconhecida do predecessor

**Gravidade:** alta para sync offline. **Relaciona:** GF-03, FST-08/13/14, DAT-03, TS-04/05/06/59.

Evidência: §5.4 exige `base_revision`, dependências e reenvio do mesmo comando; §5.5 inclui a precondição no fingerprint imutável; §7.3 exige If-Match. Esses mecanismos não definem quando um comando criado offline passa a ter revisão esperada concreta.

Contraexemplo de mesa: c1=start(A), c2=nota(A), c3=stop(A), todos criados sem rede. c2 só pode conhecer o ETag resultante após c1; c3 precisa do resultado de c2. Adivinhar a revisão produz 412; substituí-la após primeiro envio pode mudar fingerprint/chave; ler o ETag mais recente sem distinguir mudança externa pode apagar edição legítima. O DAG sozinho não fecha o protocolo automático.

**Recomendação de engenharia, não aprovação:** separar intenção local imutável de envelope HTTP final; permitir referência local ao resultado de predecessor; concretizar ETag/base apenas depois do recibo daquele predecessor e antes do primeiro envio; congelar depois disso. Se for necessário, receipt deve transportar `resulting_etag` ou uma forma inequívoca de obtê-lo sem assumir que resource_current ainda é a mesma revisão. Não rebasing automático sobre edição de outro dispositivo. Outra solução é aceitável se provar as mesmas propriedades.

**Novos casos de aceite planejados:** start→nota→stop offline sincroniza sem conflito artificial quando não houve concorrência; uma edição externa entre predecessores gera conflito sem rebase silencioso; perder resposta/reiniciar não altera fingerprint de comando já transmitido. Não foram executados: não há implementação de jejum.

### RV-02 — Autoridade duplicada da revisão: corpo e If-Match

**Gravidade:** média, bloqueadora para contrato de mutação. **Relaciona:** GF-07, SEC-08, API-10, TS-14/15/16.

Evidência: §7.3 contém `base_revision` no envelope; §7.1 exige If-Match forte, mas não estabelece igualdade entre os dois ou elimina um deles. Fingerprint inclui a precondição, sem resolver qual informação descreve a base da intenção.

Contraexemplo de mesa: corpo baseado na revisão 1 de uma nota e header apontando para revisão 2. Um servidor que só compara o header pode aceitar intenção velha como atual. Outro pode rejeitar. O resultado precisa ser único, não inferido pelo implementador.

**Recomendação de engenharia, não aprovação:** usar uma autoridade de CAS; se ambos forem mantidos, exigir que tipo/ID/revisão concordem, rejeitando divergência estrutural com 422 antes de consumir chave. Definir quando header ausente/malformado, chave já conhecida e corpo inconsistente têm precedência. Não alterar expectativa em retry para “fazer passar”.

**Casos de aceite planejados:** corpo/header iguais→segue CAS; divergentes→nenhum efeito/receipt aplicado; retry exato mantém resultado; correção consciente após rejeição definitiva usa nova intenção. Esta proposta não escolhe política de sobreposição, prazo ou idade offline.

## 4. Evidência do código e verificações executadas

| Verificação nesta revisão | Método / resultado | Limite |
|---|---|---|
| Baseline backend | Em backend: `GOOGLE_CLIENT_ID=review-offline GOOGLE_CLIENT_SECRET=review-offline ../.venv/bin/pytest --no-cov -p no:cacheprovider -q` → **66 passaram**, exit 0 | Suíte existente majoritariamente unitária/mockada; cobertura não foi reexecutada. Aviso pytest-asyncio sobre escopo de loop não fixado |
| Reprodução representativa do isolamento | TestClient + SQLite/config exclusivos em diretório temporário, duas contas sintéticas, JWT real com chaves efêmeras; A grava feedback de B→**201**, A lê B→**200** | **Defeito reproduzido**, não teste de segurança passado; não é validação de todas as 15 operações vulneráveis |
| Fronteira de efeitos OAuth | Inspeção de `connect.py` e `OAuthService.handle_callback` | Comparar owner só depois de handle_callback é tarde: troca código e grava token antes de retornar |
| Contratos e auth cliente | `login.tsx/register.tsx` esperam data.user; backend retorna identidade plana; interceptor usa a mesma instância para refresh | Inspeção estática; nenhum build/teste nativo novo nesta revisão |
| Persistência | WarehouseProvider expõe insert/query; SQLite abre/commita por operação; refresh faz get/revoke/create separados | Não comprova transação multioperação. PostgreSQL ainda não é provider runtime implementado |

Sem chamadas a Google/Garmin/produção, acesso a saúde real, extração de credenciais, migration, merge ou deploy. Script de reprodução e banco ficaram fora do checkout; tokens não foram impressos. Os testes de segurança novos propostos no backlog **não foram escritos nem executados** nesta tarefa.

Referências concretas: [router v1](../../backend/app/api/v1/router.py), [dependência JWT](../../backend/app/auth/dependencies.py), [feedback](../../backend/app/api/v1/wellness_feedback.py), [connect](../../backend/app/api/v1/connect.py), [OAuthService](../../backend/app/services/oauth_service.py), [auth service](../../backend/app/services/auth_service.py), [refresh repo](../../backend/app/repositories/refresh_token_repo.py), [adapter local](../../backend/app/adapters/cloud/local.py), [interceptor oficial](../../mobile/vytal-app/src/services/api.ts).

## 5. Caminho de desenvolvimento recomendado

1. Aprovar o **recorte versionado PKG-01**, com owner guard e regressões API, sem liberar a spec integral. Registrar como essa aprovação atende ao gate de AGENTS; não inferir exceção automaticamente.
2. Implementar depois, em PR de código próprio, o pacote delimitado no [backlog](06-implementation-packages.md); rever evidências/contratos A/A e A/B. Mínimo de CI pode acompanhar esse PR se PKG-00 ainda não existir.
3. Avançar PKG-02–PKG-07 conforme suas dependências/escopos. Nenhum Q de jejum/produção deve ser usado como motivo para adiar owner guard, login plano ou correção de deadlock no cliente.
4. Resolver RV-01/RV-02 e as Q relevantes antes de jejum/v2/sessões remotas/persistência de produção. Não marcar feature liberada porque seu contrato foi desenhado.

Esta revalidação não aprova a especificação integral nem altera seus documentos de origem ou D01–D20. A lista de [decisões versus engenharia](07-owner-decisions-and-engineering.md) mostra o que é realmente bloqueio de produto e o que pode receber proposta técnica. O resultado é um backlog acionável, não autorização automática para escrever ou publicar código.
