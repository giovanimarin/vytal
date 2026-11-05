const fs = require('fs')
const path = require('path')
const { withAndroidManifest, withDangerousMod } = require('@expo/config-plugins')
const READS = ['EXERCISE', 'STEPS', 'DISTANCE', 'ACTIVE_CALORIES_BURNED', 'TOTAL_CALORIES_BURNED',
  'HEART_RATE', 'RESTING_HEART_RATE', 'SLEEP', 'WEIGHT', 'SPEED', 'ELEVATION_GAINED']
module.exports = config => {
  config = withDangerousMod(config, ['android', async config => {
    const pkg = config.android.package
    const folder = path.join(config.modRequest.platformProjectRoot, 'app/src/main/java', ...pkg.split('.'))
    fs.mkdirSync(folder, { recursive: true })
    fs.writeFileSync(path.join(folder, 'HealthPermissionsActivity.kt'), `package ${pkg}
import android.app.Activity
import android.os.Bundle
import android.widget.ScrollView
import android.widget.TextView
class HealthPermissionsActivity : Activity() {
  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    val text = TextView(this)
    text.text = "Vytal — Conexão Saúde\nLeitura opcional de exercícios, passos, distância, calorias, frequência cardíaca, sono, peso, velocidade e elevação. Os dados são enviados somente ao backend local SQLite da sua conta via rede Wi-Fi. Não solicitamos senha Garmin. Não enviamos dados a serviços de nuvem. Revogue acesso na Conexão Saúde. O histórico importado permanece no backend local até sua exclusão. Estimativas de readiness não são diagnóstico médico."
    text.textSize = 18f
    text.setPadding(32, 48, 32, 48)
    val scroll = ScrollView(this)
    scroll.addView(text)
    setContentView(scroll)
  }
}
`)
    return config
  }])
  return withAndroidManifest(config, config => {
  const manifest = config.modResults.manifest
  manifest['uses-permission'] ||= []
  for (const type of READS) {
    const name = `android.permission.health.READ_${type}`
    if (!manifest['uses-permission'].some(p => p.$['android:name'] === name)) manifest['uses-permission'].push({ $: { 'android:name': name } })
  }
  manifest.queries ||= []
  if (!manifest.queries.some(q => q.package?.some(p => p.$['android:name'] === 'com.google.android.apps.healthdata'))) {
    manifest.queries.push({ package: [{ $: { 'android:name': 'com.google.android.apps.healthdata' } }] })
  }
  const app = manifest.application[0]
  const main = app.activity.find(a => a.$['android:name'] === '.MainActivity')
  if (main) main['intent-filter'] = (main['intent-filter'] || []).filter(f => !f.action?.some(a => a.$['android:name'] === 'androidx.health.ACTION_SHOW_PERMISSIONS_RATIONALE'))
  app.activity = (app.activity || []).filter(a => a.$['android:name'] !== '.HealthPermissionsActivity')
  app.activity.push({ $: { 'android:name': '.HealthPermissionsActivity', 'android:exported': 'true' },
    'intent-filter': [{ action: [{ $: { 'android:name': 'androidx.health.ACTION_SHOW_PERMISSIONS_RATIONALE' } }] }] })
  for (const alias of app['activity-alias'] || []) {
    if (alias.$['android:name'] === 'ViewPermissionUsageActivity') alias.$['android:targetActivity'] = '.HealthPermissionsActivity'
  }
  manifest.application[0].$['android:usesCleartextTraffic'] = String(process.env.NODE_ENV === 'development')
  return config
  })
}
module.exports.READS = READS
