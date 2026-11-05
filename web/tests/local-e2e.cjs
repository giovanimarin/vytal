// Real browser + real local servers + isolated SQLite. No mocked API responses.
const assert = require('node:assert/strict')
const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')
const { spawn, spawnSync } = require('node:child_process')
const { randomBytes } = require('node:crypto')
const { chromium } = require(process.env.VYTAL_PLAYWRIGHT_MODULE || 'playwright')

const root = path.resolve(__dirname, '../..')
const work = fs.mkdtempSync(path.join(os.tmpdir(), 'vytal-local-e2e-'))
const artifacts = path.resolve(process.env.VYTAL_E2E_ARTIFACTS || path.join(root, '.local-vytal/evidence'))
fs.mkdirSync(artifacts, { recursive: true })
const python = process.env.VYTAL_PYTHON || path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python')
const env = { ...process.env, ENVIRONMENT: 'test', CONFIG_PATH: path.join(work, 'config.json'),
  GOOGLE_CLIENT_ID: 'synthetic', GOOGLE_CLIENT_SECRET: 'synthetic',
  SECRET_KEY: randomBytes(32).toString('hex'), JWT_SECRET_KEY: randomBytes(32).toString('hex'),
  ALLOW_DEV_SEED: 'false', CORS_ORIGINS: '[]' }
fs.writeFileSync(env.CONFIG_PATH, JSON.stringify({ cloud: { provider: 'local' }, local: { data_dir: work, db_path: path.join(work, 'e2e.db') } }))
const web = 'http://127.0.0.1:3100'
const children = []
const checks = []
let browser
let activePage
function start(command, args, cwd, environment, log) {
  const stream = fs.openSync(path.join(work, log), 'w')
  const child = spawn(command, args, { cwd, env: environment, stdio: ['ignore', stream, stream] })
  children.push(child)
  return child
}
async function ready(url) {
  for (let attempt = 0; attempt < 120; attempt++) {
    try { if ((await fetch(url)).ok) return } catch {}
    await new Promise(r => setTimeout(r, 500))
  }
  throw new Error('Local server failed to become ready')
}
async function api(page, method, route, body) {
  return page.evaluate(async ({ method, route, body }) => {
    const token = localStorage.getItem('access_token')
    const response = await fetch('/api/v1' + route, { method, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: 'Bearer ' + token } : {}) }, body: body ? JSON.stringify(body) : undefined })
    return { status: response.status, body: await response.json() }
  }, { method, route, body })
}
async function text(page, value) {
  await page.getByText(value, { exact: false }).first().waitFor({ timeout: 30000 })
}
async function register(page, name, email, password) {
  await page.goto(web + '/login')
  await page.getByRole('button', { name: 'Criar conta', exact: true }).click()
  await page.getByRole('textbox', { name: 'Nome', exact: true }).fill(name)
  await page.getByRole('textbox', { name: 'Email', exact: true }).fill(email)
  await page.getByLabel('Senha', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Cadastrar', exact: true }).click()
  await page.waitForURL('**/dashboard', { timeout: 45000 })
  await page.getByRole('heading', { name: 'Daily Readiness', exact: true }).waitFor()
}
async function main() {
  start(python, ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8100'], path.join(root, 'backend'), env, 'backend.log')
  await ready('http://127.0.0.1:8100/health')
  start(process.execPath, ['node_modules/next/dist/bin/next', 'dev', '--hostname', '127.0.0.1', '--port', '3100'], path.join(root, 'web'),
    { ...env, NODE_ENV: 'development', VYTAL_BACKEND_URL: 'http://127.0.0.1:8100', VYTAL_NEXT_DIST_DIR: '.next-e2e', NEXT_TELEMETRY_DISABLED: '1' }, 'web.log')
  await ready(web + '/login')
  browser = await chromium.launch({ headless: true, executablePath: process.env.VYTAL_CHROMIUM_PATH || undefined, args: ['--no-sandbox'] })
  const context = await browser.newContext({ viewport: { width: 1440, height: 1100 }, timezoneId: 'UTC' })
  await context.route('**/*', route => new URL(route.request().url()).hostname === '127.0.0.1' ? route.continue() : route.abort())
  const page = await context.newPage()
  activePage = page
  page.setDefaultTimeout(30000)
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  const password = randomBytes(18).toString('hex')
  await register(page, 'Local E2E A', 'local-a@example.invalid', password)
  checks.push('web-registration')
  await page.reload()
  await page.getByRole('heading', { name: 'Daily Readiness' }).waitFor()
  const me = await api(page, 'GET', '/users/me')
  assert.equal(me.status, 200)
  const account = me.body.user_id
  checks.push('web-session-persistence-profile-read')
  await page.goto(web + '/settings')
  await page.getByRole('button', { name: /Feminino/ }).click()
  await page.getByRole('button', { name: /Corrida/ }).click()
  await page.getByRole('button', { name: 'Salvar', exact: true }).click()
  await text(page, 'Perfil atualizado com sucesso!')
  assert.equal((await api(page, 'GET', '/users/me')).body.gender, 'female')
  checks.push('web-profile-update')
  const seed = spawnSync(python, ['scripts/seed_local_account.py', '--email', 'local-a@example.invalid'], { cwd: path.join(root, 'backend'), env, encoding: 'utf8' })
  assert.equal(seed.status, 0, 'Local synthetic health generation failed')
  checks.push('local-health-simulation-real-normalization-persistence')
  const day = new Date().toISOString().split('T')[0]
  const health = await api(page, 'GET', `/health-data/${account}/summary?date=${day}`)
  assert.equal(health.status, 200)
  assert.ok(health.body.sleep.duration_minutes > 0 && health.body.steps.total_steps > 0)
  await page.goto(web + '/dashboard')
  await text(page, 'Contribuições')
  const readiness = await api(page, 'GET', `/readiness/${account}?date=${day}`)
  assert.equal(readiness.status, 200)
  assert.ok(readiness.body.insight_text && readiness.body.readiness_score > 0)
  assert.equal((await api(page, 'GET', `/readiness/${account}/history?start_date=${new Date(Date.now() - 13 * 86400000).toISOString().split('T')[0]}&end_date=${day}`)).body.length, 14)
  await page.getByLabel('Bem-estar', { exact: true }).selectOption('4')
  await page.getByLabel('Anotação do feedback').fill('Dados sintéticos de validação local')
  await page.getByRole('button', { name: 'Salvar feedback', exact: true }).click()
  await text(page, 'Feedback registrado: 4/5')
  checks.push('web-readiness-insights-history-feedback')
  await page.screenshot({ path: path.join(artifacts, 'web-dashboard.png'), fullPage: true })
  await page.goto(web + '/data')
  await page.getByRole('heading', { name: 'Dados de Saúde', exact: true }).waitFor()
  await text(page, 'Readiness Score — 14 dias')
  await page.screenshot({ path: path.join(artifacts, 'web-metrics.png'), fullPage: true })
  checks.push('web-metrics-page')
  await page.goto(web + '/workouts')
  await page.locator('input[type=number]').fill('45')
  await page.getByPlaceholder('Como foi o treino?').fill('Treino E2E sintético')
  await page.getByRole('button', { name: 'Registrar Treino', exact: true }).click()
  await text(page, 'Treino registrado!')
  await page.getByRole('button', { name: 'Histórico', exact: true }).click()
  await text(page, 'Treino E2E sintético')
  checks.push('web-workout-create-history')
  await page.screenshot({ path: path.join(artifacts, 'web-workouts.png'), fullPage: true })
  const nullDate = await api(page, 'POST', '/workouts', { user_id: account, modality: 'corrida', intensity: 'leve', duration_min: 20, date: null })
  assert.equal(nullDate.status, 201)
  assert.equal(nullDate.body.date, day)
  checks.push('workout-null-date-regression')
  await page.goto(web + '/body-map')
  const recovery = await api(page, 'GET', `/muscles/${account}/recovery?date=${day}`)
  assert.equal(recovery.status, 200)
  assert.ok(recovery.body.muscles.length > 0)
  await text(page, 'Todos os grupos musculares')
  await page.screenshot({ path: path.join(artifacts, 'web-recovery.png'), fullPage: true })
  checks.push('web-recovery-page-and-api')
  await page.getByTitle('Sair').click()
  await page.waitForURL('**/login')
  await page.getByRole('textbox', { name: 'Email', exact: true }).fill('local-a@example.invalid')
  await page.getByLabel('Senha', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Entrar', exact: true }).click()
  await page.waitForURL('**/dashboard')
  assert.equal((await api(page, 'GET', '/users/me')).body.user_id, account)
  checks.push('web-logout-and-login')
  const other = await browser.newContext({ timezoneId: 'UTC' })
  await other.route('**/*', route => new URL(route.request().url()).hostname === '127.0.0.1' ? route.continue() : route.abort())
  const b = await other.newPage()
  await register(b, 'Local E2E B', 'local-b@example.invalid', password)
  const bId = (await api(b, 'GET', '/users/me')).body.user_id
  assert.equal((await api(b, 'GET', `/readiness/${account}?date=${day}`)).status, 404)
  assert.equal((await api(page, 'GET', `/readiness/${bId}?date=${day}`)).status, 404)
  assert.equal((await api(b, 'GET', `/workouts/${bId}?start_date=${day}&end_date=${day}`)).body.length, 0)
  assert.equal((await api(b, 'POST', '/wellness-feedback', { user_id: account, date: day, feeling_score: 1 })).status, 404)
  checks.push('two-browser-contexts-account-isolation')
  assert.deepEqual(errors, [], 'Unexpected browser runtime error')
  fs.writeFileSync(path.join(artifacts, 'result.json'), JSON.stringify({ status: 'passed', checks, cloud_calls: 0,
    android_ui_validated: false, web_validation: 'automated real Chromium UI, not human manual', screenshots: 4 }, null, 2))
  console.log(`Passed ${checks.length} local E2E checkpoints; Chromium UI + FastAPI + SQLite; cloud calls 0.`)
}
main().catch(async error => {
    if (activePage && !activePage.isClosed()) {
      console.error('Failure page:', new URL(activePage.url()).pathname)
      await activePage.screenshot({ path: path.join(artifacts, 'failure.png'), fullPage: true }).catch(() => {})
    }
    console.error('Local E2E failed:', error.message); process.exitCode = 1
  })
  .finally(async () => {
    if (browser) await browser.close()
    for (const child of children) child.kill('SIGTERM')
    for (const child of children) await new Promise(resolve => { if (child.exitCode !== null) resolve(); else child.once('exit', resolve) })
    fs.rmSync(work, { recursive: true, force: true })
  })
