const { test } = require('node:test')
const assert = require('node:assert/strict')
const { spawn } = require('node:child_process')
const { once } = require('node:events')
const { mkdtempSync, writeFileSync, rmSync } = require('node:fs')
const { tmpdir } = require('node:os')
const path = require('node:path')
const { randomBytes } = require('node:crypto')
const { createInterface } = require('node:readline')
const { AxiosError } = require('axios')
const { api, login, register, getHealthAuthUrl, state } = require('./support.cjs')

test('real Android auth client + FastAPI/JWT/SQLite: login, registration and A/B isolation', { timeout: 20000 }, async () => {
  const backend = path.resolve(__dirname, '../../../backend')
  const dir = mkdtempSync(path.join(tmpdir(), 'vytal-client-api-'))
  const configPath = path.join(dir, 'config.yaml')
  writeFileSync(configPath, `cloud:\n  provider: local\nlocal:\n  data_dir: ${dir}\n  db_path: ${dir}/api.db\n`)
  const worker = spawn(process.env.VYTAL_PYTHON || 'python3', [path.join(backend, 'tests/api/worker.py')], {
    cwd: backend, stdio: ['pipe', 'pipe', 'inherit'], env: { ...process.env,
      PYTHONPATH: backend, CONFIG_PATH: configPath, ENVIRONMENT: 'local',
      GOOGLE_CLIENT_ID: 'synthetic', GOOGLE_CLIENT_SECRET: 'synthetic',
      SECRET_KEY: randomBytes(32).toString('hex'), JWT_SECRET_KEY: randomBytes(32).toString('hex') },
  })
  const lines = createInterface({ input: worker.stdout })[Symbol.asyncIterator]()
  const next = async () => {
    const message = await lines.next()
    assert.equal(message.done, false, 'Backend worker terminated unexpectedly')
    return JSON.parse(message.value)
  }
  try {
    const actors = await next()
    // Only the transport is adapted: run the real client interceptors/services/store,
    // actual backend registration/login/JWT validation and actual SQLite repositories.
    api.defaults.adapter = async (config) => {
      const query = config.params ? '?' + new URLSearchParams(config.params).toString() : ''
      worker.stdin.write(JSON.stringify({ method: config.method, url: '/api/v1' + config.url + query,
        headers: config.headers.toJSON(), json: config.data ? JSON.parse(config.data) : null }) + '\n')
      const result = await next()
      const response = { status: result.status, statusText: '', data: result.body, headers: {}, config }
      if (result.status >= 400) throw new AxiosError('Synthetic API rejection', 'ERR_BAD_REQUEST', config, null, response)
      return response
    }
    await login('A@example.invalid', 'synthetic-password-123')
    assert.equal(state().userId, actors.A.user_id)
    await api.post('/wellness-feedback', { user_id: state().userId, date: '2026-02-01', notes: 'A' })
    assert.equal((await api.get(`/wellness-feedback/${actors.A.user_id}?date=2026-02-01`)).status, 200)
    await login('B@example.invalid', 'synthetic-password-123')
    assert.equal(state().userId, actors.B.user_id)
    assert.ok((await getHealthAuthUrl('google_fit')).state.startsWith(actors.B.user_id + ':'))
    await assert.rejects(api.get(`/wellness-feedback/${actors.A.user_id}?date=2026-02-01`), (e) => e.response.status === 404)
    await assert.rejects(api.post('/wellness-feedback', { user_id: actors.A.user_id, date: '2026-02-01', notes: 'tampered' }),
      (e) => e.response.status === 404)
    await register('C', 'C@example.invalid', 'synthetic-password-123')
    const me = (await api.get('/users/me')).data
    assert.equal(me.user_id, state().userId)
    assert.equal(me.email, 'C@example.invalid')
    assert.notEqual(me.user_id, actors.A.user_id)
    await assert.rejects(api.get(`/wellness-feedback/${actors.A.user_id}?date=2026-02-01`), (e) => e.response.status === 404)
  } finally {
    state().logout()
    worker.stdin.end()
    const timer = setTimeout(() => worker.kill(), 3000)
    await once(worker, 'close')
    clearTimeout(timer)
    rmSync(dir, { recursive: true, force: true })
  }
})
