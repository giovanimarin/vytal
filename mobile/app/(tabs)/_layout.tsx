import { Tabs } from 'expo-router'

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: '#0f172a',
          borderTopColor: '#1e293b',
        },
        tabBarActiveTintColor: '#3b82f6',
        tabBarInactiveTintColor: '#475569',
      }}
    >
      <Tabs.Screen
        name="index"
        options={{ title: 'Hoje', tabBarLabel: 'Hoje' }}
      />
      <Tabs.Screen
        name="modalities"
        options={{ title: 'Modalidades', tabBarLabel: 'Modalidades' }}
      />
      <Tabs.Screen
        name="workout-log"
        options={{ title: 'Treino', tabBarLabel: 'Treino' }}
      />
      <Tabs.Screen
        name="data"
        options={{ title: 'Dados', tabBarLabel: 'Dados' }}
      />
    </Tabs>
  )
}
