# Vytal — Documento de Produto

## O que é o Vytal

Vytal é um aplicativo de análise de saúde para usuários de smartwatches acessíveis. Ele coleta dados brutos de sono, frequência cardíaca, atividade física e estresse via Google Fit, e transforma esses dados em indicadores personalizados com recomendações acionáveis.

**Problema que resolve:** Smartwatches baratos coletam dados, mas os apps nativos (Xiaomi, Amazfit, Honor, etc.) não oferecem análise profunda. O usuário vê passos e horas de sono, mas não entende o que aquilo significa para sua saúde e desempenho. Soluções premium como Garmin ou Whoop custam caro e exigem hardware específico.

**Para quem é:** Pessoas com smartwatches populares que querem insights de saúde sem pagar por plataformas premium.

---

## Plataforma e Acesso

### Web
Acesse pelo browser em qualquer dispositivo:
```
https://vytal-backend-production-368456539470.us-central1.run.app
```

### Mobile (Android)
APK disponível para instalação direta (não publicado na Play Store ainda).  
Build gerado via EAS (Expo Application Services).

### Como começar

1. Abra o app e toque em **"Conectar com Google Fit"**
2. Autorize o Vytal a ler seus dados de saúde no Google
3. Toque em **"Sincronizar Agora"** para importar os últimos 7 dias
4. Veja seu Daily Readiness Score e os indicadores do dia

> **Modo de teste:** Toque em "Modo de teste (dados simulados)" para explorar o app com dados fictícios sem precisar conectar o Google Fit.

---

## Funcionalidades

### 1. Daily Readiness Score

**O que é:**  
Um score de 0 a 100 calculado diariamente que representa o quão preparado seu corpo está para o dia — seja para treinar, trabalhar ou descansar.

**Como funciona:**  
O score é uma média ponderada de quatro indicadores de saúde coletados nas últimas 24 horas:

| Indicador | Peso | O que mede |
|-----------|------|------------|
| Sono | 40% | Duração e qualidade do sono |
| Frequência cardíaca | 30% | FC de repouso (proxy de recuperação cardiovascular) |
| Carga de atividade | 20% | Intensidade das atividades do dia anterior |
| Estresse | 10% | Nível de estresse fisiológico (quando disponível) |

> O peso do estresse é redistribuído automaticamente quando o relógio não fornece esse dado — o que acontece na maioria dos smartwatches baratos.

**Categorias e recomendações:**

| Score | Categoria | O que fazer |
|-------|-----------|-------------|
| 80–100 | Intenso | Ótimo dia para treino intenso. Seu corpo está recuperado. |
| 60–79 | Moderado | Treino moderado recomendado. Evite ultrapassar 80% da FC máxima. |
| 40–59 | Leve | Prefira atividades leves hoje. Caminhada ou yoga são boas opções. |
| 0–39 | Descanso | Seu corpo pede descanso. Priorize sono e hidratação hoje. |

**Benefícios:**
- Saber se hoje é dia de treinar forte ou descansar sem depender de achismo
- Evitar overtraining (treinar quando o corpo não está recuperado)
- Identificar padrões de recuperação ao longo da semana

**Cenários de uso:**
- Acordou e quer saber se deve fazer aquela corrida pesada ou substituir por yoga
- Está se sentindo bem mas o score está baixo — sinal de que o corpo ainda está se recuperando mesmo sem sintomas
- Score alto por 3 dias seguidos — bom momento para um treino de alta intensidade

---

### 2. Histórico do Score (7 dias)

**O que é:**  
Gráfico de barras mostrando a evolução do Daily Readiness Score nos últimos 7 dias, colorido por categoria (azul = intenso, verde = moderado, amarelo = leve, vermelho = descanso).

**Como funciona:**  
Recupera os scores calculados dos últimos 7 dias e exibe em ordem cronológica. Cada barra tem altura proporcional ao score e mostra o valor numérico.

**Benefícios:**
- Ver tendências: estou melhorando ou piorando ao longo da semana?
- Identificar dias ruins consecutivos (sinal de fadiga acumulada)
- Correlacionar visualmente com a sensação subjetiva

**Cenários de uso:**
- "Minha semana foi pesada de treinos, vejo que o score foi caindo progressivamente"
- "Dormi mal 3 dias seguidos e o histórico confirma que meu corpo está em déficit"

---

### 3. Detalhes de Sono

**O que é:**  
Breakdown completo do sono do dia: duração total e distribuição das fases (sono profundo, REM, leve e tempo acordado).

**Como funciona:**  
O Google Fit registra as sessões de sono e classifica automaticamente as fases com base nos movimentos detectados pelo acelerômetro do relógio. O Vytal exibe isso como uma barra segmentada colorida.

| Fase | Cor | O que representa |
|------|-----|-----------------|
| Profundo | Azul escuro | Recuperação física e consolidação de memória |
| REM | Roxo | Sonhos, processamento emocional |
| Leve | Azul | Transição entre fases |
| Acordado | Cinza | Interrupções durante a noite |

**Benefícios:**
- Entender a qualidade do sono além da duração
- Sono de 8h com pouco profundo = menos recuperador que 7h bem distribuídas
- Identificar noites com muitas interrupções

**Cenários de uso:**
- "Dormi 8 horas mas acordo cansado" — verificar se o sono profundo está baixo
- Avaliar se a rotina de ir dormir mais cedo está melhorando as fases do sono

---

### 4. Passos e Calorias

**O que é:**  
Total de passos do dia com barra de progresso em direção à meta de 10.000 passos, e calorias queimadas em atividades registradas.

**Como funciona:**  
Passos são coletados continuamente pelo acelerômetro do relógio via Google Fit. Calorias são calculadas pelo Google Fit com base no tipo e intensidade das atividades registradas.

**Benefícios:**
- Referência rápida de movimentação diária
- A meta de 10.000 passos é um benchmark amplamente validado para saúde cardiovascular
- Calorias ajudam a contextualizr a carga de atividade do dia

**Cenários de uso:**
- Verificar se dias de trabalho sedentário estão abaixo do mínimo recomendado
- Correlacionar calorias com o indicador de atividade no Readiness Score

---

### 5. Zonas de Frequência Cardíaca

**O que é:**  
Distribuição estimada do tempo em cada zona de FC com base nos dados de FC mínima, média e máxima do dia.

**Como funciona:**  
Calcula as zonas a partir da FC máxima registrada pelo relógio:

| Zona | Intensidade | Faixa |
|------|-------------|-------|
| Repouso | — | ≤ FC de repouso |
| Leve | Recuperação ativa | Repouso a 65% da FC máx |
| Moderado | Cardio | 65–80% da FC máx |
| Intenso | Alta performance | > 80% da FC máx |

**Benefícios:**
- Entender a intensidade real do treino além da percepção subjetiva
- Confirmar se a sessão de cardio ficou na zona-alvo
- FC de repouso alta = sinal de fadiga ou sobrecarga

**Cenários de uso:**
- "Achei que treinei leve mas a FC máxima registrada foi alta" — o relógio capturou um pico
- Monitorar se a FC de repouso está caindo ao longo de semanas de treino consistente (sinal de melhora cardiovascular)

---

### 6. Social Jetlag Score

**O que é:**  
Indicador que mede a diferença entre seu relógio biológico (ritmo circadiano) e seu relógio social (horários da semana vs. fim de semana). Um jetlag social alto é associado a fadiga crônica, problemas metabólicos e pior desempenho cognitivo.

**Como funciona:**  
Analisa os últimos 14 dias de dados de sono e calcula o ponto médio do sono (horário de adormecer + duração/2) separando dias de semana e fins de semana. A diferença entre as médias em horas é o Social Jetlag.

| Valor | Interpretação |
|-------|--------------|
| < 0.5h | Mínimo — ritmo circadiano estável |
| 0.5–1h | Leve — tolerável para a maioria |
| 1–2h | Moderado — pode afetar energia na segunda-feira |
| > 2h | Alto — risco elevado de fadiga crônica e problemas metabólicos |

> Disponível após 14 dias de uso com dados de semana e fim de semana.

**Benefícios:**
- Identificar se a "ressaca de segunda-feira" tem causa fisiológica real
- Motivação para manter horários de sono mais consistentes
- Nenhum app de relógio barato calcula esse indicador

**Cenários de uso:**
- "Durmo às 23h na semana mas às 2h no fim de semana" → Social Jetlag de ~1.5h → segunda é sempre difícil porque é equivalente a viajar um fuso horário
- Profissional que trabalha em turnos monitorando o impacto na saúde

---

### 7. Personal Recovery Curve

**O que é:**  
Aprende quanto tempo *você especificamente* leva para se recuperar de uma noite ruim de sono, com base no seu histórico real. Em vez de usar médias populacionais, o Vytal descobre seu padrão individual.

**Como funciona:**  
Analisa os últimos 30 dias, identifica "noites ruins" (readiness score < 45) e mede quantos dias o score levou para voltar ao nível normal (≥ 60). A média dessas janelas é a sua curva de recuperação pessoal.

**Benefícios:**
- Planejamento real: se você sabe que leva 2 dias para se recuperar, pode ajustar seus treinos pesados
- Mais preciso que qualquer app genérico — é baseado no seu corpo
- Mostra progresso: a curva pode encurtar com hábitos melhores

**Cenários de uso:**
- "Dormi mal quinta à noite. Minha curva diz que levo 2 dias para me recuperar. Logo, não devo treinar pesado até sábado"
- Atleta amador calibrando a periodização de treinos com base em dados reais de recuperação

> Disponível após 30 dias de uso com pelo menos 3 noites ruins identificadas.

---

### 8. Budget Watch Signal Quality

**O que é:**  
Indicador exclusivo do Vytal que avalia a confiabilidade dos dados coletados pelo seu relógio no dia. Relógios baratos têm sensores menos precisos e frequentemente enviam dados fragmentados ou inconsistentes.

**Como funciona:**  
Verifica automaticamente quatro critérios de qualidade:

| Critério | O que verifica |
|----------|---------------|
| Cobertura | Se há dados de todos os tipos esperados (sono, FC, passos, atividade) |
| Fases do sono | Se o relógio detectou as fases ou apenas a duração total |
| Variação de FC | Se a diferença entre FC mínima e máxima é fisiologicamente plausível |
| Consistência atividade | Se passos altos sem atividade registrada indica dado incompleto |

| Score | Flag | Significado |
|-------|------|-------------|
| 80–100 | Confiável | Use os indicadores com confiança |
| 50–79 | Use com cautela | Dados parciais podem afetar a precisão |
| < 50 | Incompleto | Indicadores podem não refletir a realidade |

**Benefícios:**
- Transparência: o app avisa quando os dados não são confiáveis em vez de esconder o problema
- Contexto para decisões: score baixo com dados ruins = não confie cegamente na recomendação
- Incentivo para calibrar o relógio corretamente (posição no pulso, ajuste da pulseira)

**Cenários de uso:**
- "Meu Readiness Score está ótimo mas me sinto péssimo" → Signal Quality baixa → o relógio não capturou os dados corretamente
- "Esqueci de usar o relógio para dormir" → Signal Quality incompleto → dados de sono ausentes

---

### 9. Subjective Wellness Feedback

**O que é:**  
Check-in subjetivo pós-treino ou pós-dia para calibrar os indicadores do Vytal com a sua percepção real. O objetivo é cruzar o que os sensores medem com o que você de fato sentiu.

**Como funciona:**  
Após sincronizar dados, o app exibe um card rápido com 3 perguntas opcionais:

1. **Como foi sua energia hoje?** (1–5: de exausto a cheio de energia)
2. **Treinou hoje?** → Se sim: **Valeu a pena o treino?** (sim/não)
3. **Estava disposto para treinar?** (sim / mais ou menos / não)

Os dados são armazenados e cruzados com os indicadores para identificar divergências sistemáticas.

**Benefícios:**
- Valida se os indicadores estão acertando: score alto + você se sentiu péssimo = algo está errado
- Base para ajuste futuro de pesos dos indicadores por perfil individual
- Histórico de bem-estar subjetivo para o usuário refletir sobre padrões

**Cenários de uso:**
- Score previu treino intenso, você foi e se sentiu mal → feedback negativo ajuda a refinar o modelo
- Score baixo, você descansou e se sentiu ótimo → confirma que a recomendação de descanso foi acertada
- Ferramenta de accountability: o simples ato de responder cria consciência sobre os próprios padrões

---

## Roadmap (próximas versões)

### Lifestyle Impact Tracker *(V2)*
Usuário registra eventos do dia (bebeu álcool, dia muito estressante, pulou treino) e o Vytal calcula as correlações com o Readiness Score ao longo do tempo. Exemplo: *"Noites com álcool reduzem seu score em 18 pontos em média"*.

### Módulo de Notificações *(V2)*
Recomendações proativas baseadas nos indicadores:
- "Seu score está baixo há 3 dias — considere um dia de descanso completo"
- "Boa condição física detectada — bom momento para um treino de alta intensidade"
- Notificação se o app não receber dados por mais de 2 dias

### Autenticação Real *(V2)*
JWT + suporte multi-usuário. Atualmente o MVP usa um `user_id` fixo.

### Multi-provider *(V3)*
- Apple HealthKit (iOS)
- Fitbit
- Samsung Health
- Garmin

---

## Indicadores: Resumo Comparativo

| Indicador | Dados usados | Dias necessários | Disponível no MVP |
|-----------|-------------|-----------------|:-----------------:|
| Daily Readiness Score | Sono, FC, atividade, estresse | 1 | ✅ |
| Histórico 7 dias | Readiness histórico | 7 | ✅ |
| Detalhes de Sono | Fases do sono | 1 | ✅ |
| Passos e Calorias | Steps, atividades | 1 | ✅ |
| Zonas de FC | FC mínima, média, máxima | 1 | ✅ |
| Social Jetlag Score | Sono (semana + fim de semana) | 14 | ✅ |
| Personal Recovery Curve | Readiness histórico | 30 | ✅ |
| Budget Watch Signal Quality | Raw events | 1 | ✅ |
| Subjective Wellness Feedback | Input do usuário | — | ✅ |
| Lifestyle Impact Tracker | Eventos + histórico | 30+ | 🔜 V2 |
| Notificações | Indicadores + comportamento | — | 🔜 V2 |
