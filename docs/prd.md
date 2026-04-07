# PRD — Vytal MVP

**Status**: Aguardando aprovação do Tech Lead  
**Versão**: 0.1  
**Data**: 2026-04-02

---

## Problema

Usuários de smartwatches populares (não Garmin, Polar ou similares premium) coletam dados de saúde nos seus dispositivos, mas não têm acesso a análises, indicadores e recomendações personalizadas. Os apps nativos desses relógios mostram apenas dados brutos sem contexto. Plataformas que oferecem isso cobram preços premium ou exigem hardware específico.

---

## Solução

Vytal é um app mobile que conecta ao Google Fit para coletar dados de saúde do usuário, processa esses dados e apresenta indicadores inteligentes — começando pelo **Daily Readiness Score** — com recomendações personalizadas em linguagem acessível.

---

## Usuário

**Perfil principal**: pessoa física que usa smartwatch acessível (Xiaomi, Amazfit, Samsung entry-level, etc.), sincroniza com o celular via Google Fit, e quer entender melhor sua saúde e performance sem pagar por plataformas premium.

**Dor principal**: "Tenho os dados no celular mas não sei o que fazer com eles."

---

## MVP — Funcionalidades

### 1. Conexão com Google Fit
O usuário autoriza o Vytal a acessar seus dados de saúde via Google Fit (OAuth). O app coleta os seguintes tipos de dados brutos:

| Dado | Descrição |
|------|-----------|
| Sono | duração, fases, qualidade |
| Passos | contagem diária, por hora |
| Atividades | duração, intensidade, tipo, calorias |
| Frequência cardíaca | repouso e ao longo do dia, média |
| Estresse | score quando disponível |

Cada tipo de dado é representado por uma classe que implementa uma interface abstrata (`HealthMetric`), garantindo extensibilidade para novos tipos no futuro.

### 2. Ingestão e Armazenamento dos Dados Brutos
Os dados coletados são armazenados na camada `raw/` sem modificação, com timestamp de ingestão e identificação do usuário. Essa camada é imutável.

### 3. Processamento e Sanitização
Os dados brutos passam por um pipeline de transformação que:
- Remove registros inválidos ou fora de range esperado
- Adapta os dados para uma linguagem de negócio (ex: `duration_minutes`, `heart_rate_bpm`)
- Produz dados normalizados na camada `normalized/`

### 4. Daily Readiness Score
Indicador principal do MVP. Score de 0 a 100 calculado por usuário por dia, baseado nos dados normalizados:

| Score | Recomendação |
|-------|-------------|
| 80–100 | Treino intenso |
| 50–79 | Cardio leve ou Treino de força moderado |
| 30–49 | Cardio leve |
| 0–29 | Descanso |

O score é armazenado em modelagem estrela no warehouse, particionado por usuário e data.

### 5. Insights de Recomendação
A partir do Daily Readiness Score, o sistema gera uma recomendação textual personalizada em linguagem acessível (ex: "Seu sono foi curto e sua frequência cardíaca de repouso está elevada. Hoje é um bom dia para descansar ou fazer uma caminhada leve.").

### 6. Interface Mobile (MVP)
Tela mínima funcional com:
- Tela de conexão com Google Fit
- Tela principal com o Daily Readiness Score do dia (score + recomendação)
- Visualização básica dos dados coletados (sono, passos, FC)

Interface não precisa ser refinada visualmente — foco em funcionalidade.

### 7. Infraestrutura
- **Cloud**: GCP como provider padrão (Cloud Storage, BigQuery, Dataflow/Beam)
- **Local**: suporte a execução local (DirectRunner + banco local) para desenvolvimento e testes
- A troca entre local e cloud é feita por configuração, sem alterar código

---

## Fora do Escopo do MVP

| Item | Motivo |
|------|--------|
| Outros providers (Apple Health, Samsung, etc.) | Será adicionado após validação do padrão com Google Fit |
| Outros indicadores além do Daily Readiness | Foco na validação do fluxo completo primeiro |
| Autenticação e autorização de usuários | Será implementado antes do lançamento público |
| Versão web | Mobile first; web virá em fase posterior |
| Design visual refinado | Validação funcional primeiro |
| Múltiplos usuários em produção | MVP é validação pelo próprio Tech Lead |

> Importante: a arquitetura deve ser projetada para suportar todos esses itens futuros, mesmo que não implementados no MVP. Novos providers, indicadores e autenticação não devem exigir reescrita estrutural.

---

## Métrica de Sucesso do MVP

**Critério único**: o Tech Lead consegue instalar o app no próprio celular, conectar ao Google Fit, e visualizar o Daily Readiness Score com recomendação gerada a partir dos seus dados reais.

---

## Restrições de Negócio

- **LGPD/GDPR**: dados de saúde são sensíveis. Mesmo no MVP, nunca logar valores brutos em produção e sempre associar dados ao usuário.
- **Precisão dos dados**: o app deve funcionar mesmo com dados imprecisos (relógios baratos têm menor precisão). O processamento deve ser resiliente a valores ausentes ou fora do padrão.

---

## Próximos Passos (pós-MVP)

Para orientar decisões de arquitetura desde o início:

1. Autenticação e autorização (JWT + multi-usuário)
2. Novos Health Data Connectors (Apple HealthKit, Samsung Health, Fitbit)
3. Novos indicadores (HRV Score, Sleep Quality Index, Training Load, etc.)
4. Versão web (React ou Next.js)
5. Insights gerados por IA (Claude API)
6. Monetização freemium

---

*Gerado pelo PM Agent — Vytal v0.1*
