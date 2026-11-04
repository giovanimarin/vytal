# Vytal — Product Roadmap

## MVP (em implementação)

### Indicadores Core
- [x] Daily Readiness Score (sono 40%, FC 30%, atividade 20%, estresse 10%)
- [x] Contribuições por fator
- [x] Insight text básico
- [ ] **Histórico do Score (7 dias)** — gráfico de evolução
- [ ] **Detalhes de Sono** — duração, fases (deep, REM, light), horário
- [ ] **Passos e Calorias do dia**
- [ ] **Recomendação acionável baseada no score** — o que fazer hoje
- [ ] **Zonas de Frequência Cardíaca** — repouso, leve, moderado, intenso

### Indicadores Avançados
- [ ] **Social Jetlag Score** — diferença entre relógio biológico e social (semana vs fim de semana)
- [ ] **Personal Recovery Curve** — quantos dias você leva para se recuperar de uma noite ruim
- [ ] **Budget Watch Signal Quality** — confiabilidade dos dados do relógio no dia

### Engajamento
- [ ] **Subjective Wellness Feedback** — check-in pós-treino/pós-sono para calibrar indicadores
  - Perguntas: cansado? treino valeu a pena? estava disposto?
  - Objetivo: ajustar pesos dos indicadores ao perfil individual

---

## V2 (pós-MVP)

### Lifestyle Impact Tracker
- Usuário loga eventos (álcool, estresse, pulou treino)
- Sistema correlaciona eventos com variação do score
- Mostra: "Noites com álcool reduzem seu score em X pontos em média"

### Módulo de Notificações / Previsibilidade
- Notifica quando a pessoa ficar muito tempo sem abrir o app
- Recomendação proativa: "Hoje é dia de descanso", "Treino leve recomendado", "Pode treinar forte"
- Baseado no conjunto de indicadores do dia
- Push notifications (Expo Notifications + FCM)

### Personal Recovery Curve (ML)
- Aprende o padrão individual de recuperação ao longo de semanas
- "Você precisa de X noites boas para se recuperar de uma noite ruim"
- Requer mínimo de 30 dias de histórico

### Autenticação Real
- JWT + refresh tokens
- Suporte multi-usuário
- Perfil do usuário (idade, peso, nível de fitness)

### Multi-provider
- Apple HealthKit
- Fitbit
- Samsung Health
- Garmin (premium)

---

## Arquitetura de Features

### Social Jetlag Score
```
Input: histórico de sono 14 dias
Cálculo:
  - midpoint_weekday = média do meio do sono (dias úteis)
  - midpoint_weekend = média do meio do sono (fim de semana)
  - social_jetlag = |midpoint_weekend - midpoint_weekday| em horas
Output: score 0-10 (0 = sem jetlag, >2h = crítico)
```

### Personal Recovery Curve
```
Input: histórico de readiness + sono 30 dias
Cálculo:
  - Identifica "noites ruins" (sono < 6h ou score < 40)
  - Mede quantos dias até readiness voltar à baseline
  - Baseline = média dos 7 dias anteriores à noite ruim
Output: "Você leva em média X dias para se recuperar"
```

### Budget Watch Signal Quality
```
Input: raw health events do dia
Cálculo:
  - Verifica gaps no sinal de FC (>30min sem leitura)
  - Verifica inconsistências de sono (múltiplas sessões fragmentadas)
  - Verifica passos zerados em horas de movimento
Output: score 0-100 + flag (confiável / use com cautela / dados incompletos)
```

### Subjective Wellness Feedback
```
Trigger: após sync de dados (pós-treino ou manhã seguinte)
Perguntas (1-3 por sessão, não todas de uma vez):
  - "Como você se sentiu hoje?" (1-5 estrelas)
  - "O treino valeu a pena?" (sim/não/não treinei)
  - "Você estava disposto para o treino?" (sim/mais ou menos/não)
  - "Como foi sua energia ao longo do dia?" (1-5)
Uso:
  - Correlacionar resposta subjetiva com score previsto
  - Ajustar insight_text se indicadores divergem do real
  - Dados para futuro ajuste de pesos (Personal Recovery Curve)
```

### Recomendação Acionável
```
Score >= 80 (intense):  "Ótimo dia para treino intenso. Seu corpo está recuperado."
Score 60-79 (moderate): "Treino moderado recomendado. Evite ultrapassar 80% da FC máxima."
Score 40-59 (light):    "Prefira atividades leves hoje. Caminhada ou yoga são boas opções."
Score < 40 (rest):      "Seu corpo pede descanso. Priorize sono e hidratação hoje."

Modificadores contextuais:
  - Social jetlag alto → adicionar alerta de ritmo circadiano
  - Signal quality baixa → "dados com qualidade reduzida, use com cautela"
  - 2+ dias consecutivos ruins → "padrão de fadiga identificado, considere consultar um profissional"
```
