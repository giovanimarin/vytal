import React, { useState } from 'react'
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Animated, LayoutAnimation, Platform, UIManager,
} from 'react-native'
import { useRouter } from 'expo-router'
import { useDashboardStore, type WidgetId } from '../src/store/dashboardStore'

if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true)
}

interface IndicatorDef {
  id: WidgetId
  name: string
  icon: string
  tagline: string
  description: string
  howItWorks: string
  dataNeeded: string[]
  daysNeeded: number | null
  benefit: string
}

const INDICATORS: IndicatorDef[] = [
  {
    id: 'readiness_score',
    name: 'Daily Readiness Score',
    icon: '⚡',
    tagline: 'O quão preparado seu corpo está hoje',
    description: 'Um score de 0 a 100 calculado diariamente que representa o nível de recuperação e prontidão do seu corpo — se está pronto para treinar forte, moderar ou descansar.',
    howItWorks: 'É uma média ponderada de quatro fatores: sono (40%), frequência cardíaca de repouso (30%), carga de atividade (20%) e estresse (10%). O peso do estresse é redistribuído automaticamente quando o relógio não fornece esse dado.',
    dataNeeded: ['Sono', 'Frequência cardíaca', 'Atividade física'],
    daysNeeded: 1,
    benefit: 'Saber exatamente se hoje é dia de treinar forte ou descansar, sem depender de achismo.',
  },
  {
    id: 'score_history',
    name: 'Histórico 7 dias',
    icon: '📈',
    tagline: 'Evolução do seu score na semana',
    description: 'Gráfico de barras com o Daily Readiness Score dos últimos 7 dias, colorido por categoria. Permite ver tendências e identificar padrões de fadiga ou recuperação.',
    howItWorks: 'Recupera os scores calculados dos últimos 7 dias e exibe em ordem cronológica. Cada barra é colorida: azul (intenso), verde (moderado), amarelo (leve), vermelho (descanso).',
    dataNeeded: ['Daily Readiness Score (7 dias)'],
    daysNeeded: 7,
    benefit: 'Ver se você está melhorando ou acumulando fadiga ao longo da semana.',
  },
  {
    id: 'sleep_details',
    name: 'Detalhes do Sono',
    icon: '🌙',
    tagline: 'Qualidade e fases do seu sono',
    description: 'Mostra a duração total do sono e a distribuição por fases: sono profundo, REM, leve e tempo acordado. Vai além da simples contagem de horas.',
    howItWorks: 'O Google Fit registra as sessões de sono e classifica as fases com base nos movimentos do acelerômetro. O Vytal exibe isso como uma barra segmentada colorida com legenda.',
    dataNeeded: ['Dados de sono do Google Fit'],
    daysNeeded: 1,
    benefit: 'Entender por que você acorda cansado mesmo dormindo 8 horas — a qualidade importa tanto quanto a quantidade.',
  },
  {
    id: 'steps_calories',
    name: 'Passos e Calorias',
    icon: '👟',
    tagline: 'Movimentação e gasto calórico do dia',
    description: 'Total de passos do dia com barra de progresso em direção à meta de 10.000 passos, e calorias queimadas nas atividades registradas.',
    howItWorks: 'Passos são coletados continuamente pelo acelerômetro do relógio. Calorias são calculadas pelo Google Fit com base no tipo e intensidade das atividades registradas.',
    dataNeeded: ['Passos', 'Atividades físicas'],
    daysNeeded: 1,
    benefit: 'Acompanhar o mínimo de movimentação diária recomendada para saúde cardiovascular.',
  },
  {
    id: 'hr_zones',
    name: 'Zonas de Frequência Cardíaca',
    icon: '❤️',
    tagline: 'Intensidade real do seu treino',
    description: 'Distribuição estimada do tempo em cada zona de FC: repouso, leve, moderado e intenso. Mostra a intensidade real do dia além da percepção subjetiva.',
    howItWorks: 'Calcula as zonas a partir da FC máxima registrada pelo relógio. Zona leve: até 65% da FC máx. Moderado: 65–80%. Intenso: acima de 80%.',
    dataNeeded: ['Frequência cardíaca (mínima, média e máxima)'],
    daysNeeded: 1,
    benefit: 'Confirmar se o treino ficou na zona-alvo e se a FC de repouso está melhorando com o tempo.',
  },
  {
    id: 'social_jetlag',
    name: 'Social Jetlag Score',
    icon: '🕐',
    tagline: 'Diferença entre seu relógio biológico e social',
    description: 'Mede a diferença entre o horário de sono durante a semana e no fim de semana. Um jetlag social alto é associado a fadiga crônica, problemas metabólicos e pior desempenho cognitivo.',
    howItWorks: 'Analisa os últimos 14 dias de sono e calcula o ponto médio do sono separando dias úteis e fins de semana. A diferença entre as médias em horas é o Social Jetlag. Abaixo de 0,5h = mínimo. Acima de 2h = alto.',
    dataNeeded: ['Sono (últimos 14 dias, incluindo fins de semana)'],
    daysNeeded: 14,
    benefit: 'Entender por que a segunda-feira é sempre difícil — e ter dados para mudar isso.',
  },
  {
    id: 'recovery_curve',
    name: 'Curva de Recuperação',
    icon: '🔄',
    tagline: 'Quantos dias você leva para se recuperar',
    description: 'Aprende quanto tempo você especificamente leva para se recuperar de uma noite ruim de sono, com base no seu histórico real. Em vez de médias populacionais, usa seus próprios dados.',
    howItWorks: 'Analisa os últimos 30 dias, identifica noites ruins (readiness score < 45) e mede quantos dias o score levou para voltar ao normal (≥ 60). A média dessas janelas é sua curva pessoal.',
    dataNeeded: ['Daily Readiness Score (últimos 30 dias com pelo menos 3 noites ruins)'],
    daysNeeded: 30,
    benefit: 'Planejar treinos com precisão: se você leva 2 dias para se recuperar, evite treinos pesados nesse intervalo.',
  },
  {
    id: 'signal_quality',
    name: 'Qualidade do Sinal',
    icon: '📡',
    tagline: 'Confiabilidade dos dados do seu relógio',
    description: 'Avalia a qualidade dos dados coletados pelo seu relógio no dia. Relógios baratos têm sensores menos precisos e frequentemente enviam dados fragmentados ou inconsistentes.',
    howItWorks: 'Verifica quatro critérios: cobertura dos dados esperados, detecção de fases do sono, variação fisiológica da FC e consistência entre passos e atividades registradas. Score de 0 a 100.',
    dataNeeded: ['Todos os tipos de dados do dia'],
    daysNeeded: 1,
    benefit: 'Saber quando confiar nos indicadores e quando os dados do relógio podem estar comprometidos.',
  },
  {
    id: 'wellness_feedback',
    name: 'Check-in de Bem-estar',
    icon: '✅',
    tagline: 'Como você realmente se sentiu hoje',
    description: 'Check-in subjetivo rápido para registrar sua energia, disposição e resultado do treino. Cruza sua percepção com o que os sensores mediram.',
    howItWorks: 'Três perguntas opcionais: nível de energia (1–5), treinou hoje e se valeu a pena. Os dados são armazenados e futuramente cruzados com os indicadores para calibragem personalizada.',
    dataNeeded: ['Resposta do usuário'],
    daysNeeded: null,
    benefit: 'Verificar se os indicadores estão acertando — e contribuir para a calibragem do seu perfil.',
  },
]

export default function CatalogScreen() {
  const router = useRouter()
  const { activeWidgets, addWidget, removeWidget, hasWidget } = useDashboardStore()
  const [expanded, setExpanded] = useState<WidgetId | null>(null)

  function toggle(id: WidgetId) {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut)
    setExpanded((prev) => (prev === id ? null : id))
  }

  function handleToggleWidget(id: WidgetId) {
    if (hasWidget(id)) {
      removeWidget(id)
    } else {
      addWidget(id)
      router.back()
    }
  }

  return (
    <View style={styles.screen}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
          <Text style={styles.backText}>← Voltar</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Indicadores</Text>
        <View style={{ width: 70 }} />
      </View>

      <ScrollView contentContainerStyle={styles.list}>
        <Text style={styles.subtitle}>
          Escolha os indicadores que quer acompanhar no seu dashboard.
        </Text>

        {INDICATORS.map((ind) => {
          const isOpen = expanded === ind.id
          const isActive = hasWidget(ind.id)

          return (
            <View key={ind.id} style={styles.card}>
              {/* Row header */}
              <TouchableOpacity
                style={styles.row}
                onPress={() => toggle(ind.id)}
                activeOpacity={0.7}
              >
                <Text style={styles.rowIcon}>{ind.icon}</Text>
                <View style={styles.rowText}>
                  <View style={styles.rowTitleRow}>
                    <Text style={styles.rowName}>{ind.name}</Text>
                    {isActive && (
                      <View style={styles.activeBadge}>
                        <Text style={styles.activeBadgeText}>No dashboard</Text>
                      </View>
                    )}
                  </View>
                  <Text style={styles.rowTagline}>{ind.tagline}</Text>
                </View>
                <Text style={styles.chevron}>{isOpen ? '▲' : '▼'}</Text>
              </TouchableOpacity>

              {/* Expanded content */}
              {isOpen && (
                <View style={styles.detail}>
                  <Text style={styles.detailDesc}>{ind.description}</Text>

                  <View style={styles.section}>
                    <Text style={styles.sectionLabel}>Como funciona</Text>
                    <Text style={styles.sectionText}>{ind.howItWorks}</Text>
                  </View>

                  <View style={styles.section}>
                    <Text style={styles.sectionLabel}>Dados necessários</Text>
                    {ind.dataNeeded.map((d) => (
                      <Text key={d} style={styles.bullet}>• {d}</Text>
                    ))}
                    {ind.daysNeeded && (
                      <Text style={styles.daysNote}>
                        ⏱ Requer pelo menos {ind.daysNeeded} {ind.daysNeeded === 1 ? 'dia' : 'dias'} de dados
                      </Text>
                    )}
                  </View>

                  <View style={styles.section}>
                    <Text style={styles.sectionLabel}>Benefício</Text>
                    <Text style={styles.sectionText}>{ind.benefit}</Text>
                  </View>

                  <TouchableOpacity
                    style={[styles.addBtn, isActive && styles.addBtnRemove]}
                    onPress={() => handleToggleWidget(ind.id)}
                  >
                    <Text style={styles.addBtnText}>
                      {isActive ? '✕ Remover do dashboard' : '+ Adicionar ao dashboard'}
                    </Text>
                  </TouchableOpacity>
                </View>
              )}
            </View>
          )
        })}
      </ScrollView>
    </View>
  )
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#0f172a' },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 56,
    paddingBottom: 12,
    backgroundColor: '#0f172a',
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
  },
  backBtn: { width: 70 },
  backText: { color: '#3b82f6', fontSize: 15 },
  headerTitle: { fontSize: 18, fontWeight: '700', color: '#f8fafc' },
  list: { padding: 16, gap: 10, paddingBottom: 48 },
  subtitle: { color: '#64748b', fontSize: 14, lineHeight: 20, marginBottom: 4 },
  card: {
    backgroundColor: '#1e293b',
    borderRadius: 16,
    overflow: 'hidden',
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    gap: 12,
  },
  rowIcon: { fontSize: 24, width: 32, textAlign: 'center' },
  rowText: { flex: 1 },
  rowTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 8, flexWrap: 'wrap' },
  rowName: { fontSize: 15, fontWeight: '700', color: '#f8fafc' },
  rowTagline: { fontSize: 13, color: '#64748b', marginTop: 2 },
  chevron: { color: '#475569', fontSize: 12 },
  activeBadge: {
    backgroundColor: '#1d4ed8',
    borderRadius: 6,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  activeBadgeText: { color: '#bfdbfe', fontSize: 11, fontWeight: '600' },
  detail: {
    paddingHorizontal: 16,
    paddingBottom: 16,
    borderTopWidth: 1,
    borderTopColor: '#0f172a',
    gap: 14,
  },
  detailDesc: { color: '#cbd5e1', fontSize: 14, lineHeight: 22, paddingTop: 12 },
  section: { gap: 6 },
  sectionLabel: { color: '#3b82f6', fontSize: 12, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.5 },
  sectionText: { color: '#94a3b8', fontSize: 13, lineHeight: 20 },
  bullet: { color: '#94a3b8', fontSize: 13 },
  daysNote: { color: '#475569', fontSize: 12, marginTop: 4 },
  addBtn: {
    backgroundColor: '#3b82f6',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 4,
  },
  addBtnRemove: { backgroundColor: '#1e293b', borderWidth: 1, borderColor: '#ef4444' },
  addBtnText: { color: '#fff', fontWeight: '700', fontSize: 14 },
})
