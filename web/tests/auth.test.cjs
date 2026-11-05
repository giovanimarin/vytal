const { test, beforeEach } = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs'), ts = require('typescript')
require.extensions['.ts'] = (module, filename) => module._compile(ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true },
}).outputText, filename)
const values = new Map()
global.localStorage = { getItem: (k) => values.get(k) ?? null, setItem: (k, v) => values.set(k, v), removeItem: (k) => values.delete(k) }
global.window = { location: { href: '' }, localStorage }
const { AxiosError } = require('axios')
const { api } = require('../lib/api.ts')
const { useAuthStore } = require('../lib/store.ts')
const state = () => useAuthStore.getState()
const seed = (name = 'A') => state().setAuth(`account-${name}`, `${name}@example.invalid`, name, `access-${name}`, `refresh-${name}`)
const ok = (config, data) => ({ status: 200, data, config, statusText: 'OK', headers: {} })
const denied = (config) => { throw new AxiosError('Unauthorized', 'ERR_BAD_REQUEST', config, null, { status: 401, data: {}, headers: {}, config }) }
const flush = () => new Promise(setImmediate)
beforeEach(() => { state().clear(); window.location.href = ''; api.defaults.adapter = async () => { throw new Error('Unexpected request') } })

test('401 clears persisted and in-memory authentication, not just localStorage aliases', async () => {
  seed()
  api.defaults.adapter = async (config) => denied(config)
  await assert.rejects(api.get('/users/me'))
  assert.equal(state().userId, null)
  assert.equal(state().accessToken, null)
  assert.equal(JSON.parse(localStorage.getItem('vytal-auth')).state.accessToken, null)
})

test('concurrent 401s share one refresh and one retry per request', async () => {
  seed()
  let refreshes = 0
  api.defaults.adapter = async (config) => {
    if (config.url === '/auth/refresh') {
      refreshes++; await flush()
      return ok(config, { access_token: 'renewed', refresh_token: 'renewed-refresh' })
    }
    if (config.headers.Authorization === 'Bearer access-A') return denied(config)
    assert.equal(config.headers.Authorization, 'Bearer renewed')
    return ok(config, { user_id: 'account-A' })
  }
  assert.equal((await Promise.all([api.get('/users/me'), api.get('/users/me')])).length, 2)
  assert.equal(refreshes, 1)
  assert.equal(state().accessToken, 'renewed')
})

test('second 401 terminates retry and clears credentials', async () => {
  seed(); let attempts = 0, refreshes = 0
  api.defaults.adapter = async (config) => {
    if (config.url === '/auth/refresh') {
      refreshes++; return ok(config, { access_token: 'renewed', refresh_token: 'renewed-refresh' })
    }
    attempts++; return denied(config)
  }
  await assert.rejects(api.get('/users/me'))
  assert.equal(attempts, 2); assert.equal(refreshes, 1)
  assert.equal(state().userId, null)
})

test('legacy web sessions without refresh require reauthentication on 401', async () => {
  state().setAuth('account-A', 'A@example.invalid', 'A', 'legacy')
  let requests = 0
  api.defaults.adapter = async (config) => { requests++; return denied(config) }
  await assert.rejects(api.get('/users/me'))
  assert.equal(requests, 1); assert.equal(state().userId, null)
})

test('bad password does not refresh or clear an unrelated valid session', async () => {
  seed(); let calls = 0
  api.defaults.adapter = async (config) => {
    calls++; assert.equal(config.url, '/auth/login')
    assert.equal(config.headers.Authorization, undefined)
    return denied(config)
  }
  await assert.rejects(api.post('/auth/login', { email: 'wrong', password: 'wrong' }))
  assert.equal(calls, 1); assert.equal(state().userId, 'account-A')
})

for (const failure of ['network', '500', '401', 'malformed']) {
  test(`refresh ${failure} rejects once, clears the session and never recurses`, async () => {
    seed(); let renewals = 0
    api.defaults.adapter = async (config) => {
      if (config.url !== '/auth/refresh') return denied(config)
      renewals++
      if (failure === 'network') throw new AxiosError('Synthetic network failure', 'ERR_NETWORK', config)
      if (failure === '500') throw new AxiosError('Synthetic failure', 'ERR_BAD_RESPONSE', config, null, { status: 500, data: {}, headers: {}, config })
      if (failure === '401') return denied(config)
      return ok(config, { access_token: '', refresh_token: null })
    }
    const results = await Promise.allSettled([api.get('/users/me'), api.get('/users/me')])
    assert.ok(results.every((result) => result.status === 'rejected'))
    assert.equal(renewals, 1); assert.equal(state().accessToken, null)
  })
}

test('ordinary request network failure preserves a valid session and never refreshes', async () => {
  seed(); let calls = 0
  api.defaults.adapter = async (config) => { calls++; throw new AxiosError('Synthetic network failure', 'ERR_NETWORK', config) }
  await assert.rejects(api.get('/users/me'))
  assert.equal(calls, 1); assert.equal(state().accessToken, 'access-A')
})

for (const account of ['A', 'B']) {
  test(`late response cannot survive logout/login to ${account}`, async () => {
    seed(); let start, release
    const arrived = new Promise((resolve) => { start = resolve })
    const barrier = new Promise((resolve) => { release = resolve })
    api.defaults.adapter = async (config) => { start(); await barrier; return ok(config, { user_id: 'account-A' }) }
    const request = api.get('/users/me')
    const rejected = assert.rejects(request, /sessão mudou/)
    await arrived; state().clear(); seed(account); release()
    await rejected; assert.equal(state().userId, `account-${account}`)
  })
}

test('old refresh cannot overwrite a newer session', async () => {
  seed(); let start, release
  const arrived = new Promise((resolve) => { start = resolve })
  const barrier = new Promise((resolve) => { release = resolve })
  api.defaults.adapter = async (config) => {
    if (config.url !== '/auth/refresh') return denied(config)
    start(); await barrier; return ok(config, { access_token: 'old', refresh_token: 'old' })
  }
  const request = api.get('/users/me')
  const rejected = assert.rejects(request, /sessão mudou/)
  await arrived; state().clear(); seed('B'); release()
  await rejected; assert.equal(state().accessToken, 'access-B')
})

test('account switch drops previous profile preferences', () => {
  seed(); state().setProfile({ gender: 'male', preferredModalities: ['corrida'] })
  seed('B')
  assert.equal(state().gender, null); assert.deepEqual(state().preferredModalities, [])
})

test('late login result cannot revive session after logout', async () => {
  const { login } = require('../lib/auth.ts')
  let start, release
  const arrived = new Promise((resolve) => { start = resolve })
  const barrier = new Promise((resolve) => { release = resolve })
  api.defaults.adapter = async (config) => {
    start(); await barrier
    return ok(config, { user_id: 'account-A', email: 'A@example.invalid', name: 'A', access_token: 'A', refresh_token: 'R' })
  }
  const request = login('A@example.invalid', 'synthetic')
  const rejected = assert.rejects(request, /sessão mudou/)
  await arrived; state().clear(); release(); await rejected
  assert.equal(state().userId, null)
})

test('explicit logout clears local state before remote revocation and tolerates network failure', async () => {
  const { logout } = require('../lib/auth.ts')
  seed(); let raw
  api.defaults.adapter = async (config) => {
    assert.equal(config.url, '/auth/logout'); raw = JSON.parse(config.data).refresh_token
    assert.equal(state().userId, null)
    throw new AxiosError('Synthetic offline', 'ERR_NETWORK', config)
  }
  logout(); await flush()
  assert.equal(raw, 'refresh-A'); assert.equal(state().refreshToken, null)
})

test('web refresh credential stays in memory and is excluded from persisted state', () => {
  seed()
  assert.equal(state().refreshToken, 'refresh-A')
  assert.equal(JSON.parse(localStorage.getItem('vytal-auth')).state.refreshToken, undefined)
})

test('login installs flat v1 credentials and uses them to retrieve the same profile', async () => {
  const { login } = require('../lib/auth.ts')
  api.defaults.adapter = async (config) => {
    if (config.url === '/auth/login') {
      assert.equal(config.headers.Authorization, undefined)
      return ok(config, { user_id: 'account-A', email: 'A@example.invalid', name: 'A', access_token: 'access-A', refresh_token: 'refresh-A' })
    }
    assert.equal(config.url, '/users/me'); assert.equal(config.headers.Authorization, 'Bearer access-A')
    return ok(config, { gender: 'male', preferred_modalities: ['corrida'] })
  }
  await login('A@example.invalid', 'synthetic')
  assert.equal(state().userId, 'account-A'); assert.equal(state().gender, 'male')
  assert.equal(state().refreshToken, 'refresh-A')
})

test('a definitive profile authentication failure cannot be reported as successful login', async () => {
  const { login } = require('../lib/auth.ts')
  let renewals = 0
  api.defaults.adapter = async (config) => {
    if (config.url === '/auth/login') return ok(config,
      { user_id: 'account-A', email: 'A@example.invalid', access_token: 'access-A', refresh_token: 'refresh-A' })
    if (config.url === '/auth/refresh') renewals++
    return denied(config)
  }
  await assert.rejects(login('A@example.invalid', 'synthetic'), /sessão mudou/)
  assert.equal(renewals, 1); assert.equal(state().userId, null)
})

test('queued renewal cannot send an old refresh after logout', async () => {
  const { refreshSession } = require('../lib/api.ts')
  seed(); let sent = 0
  api.defaults.adapter = async (config) => {
    sent++; return ok(config, { access_token: 'old-access', refresh_token: 'old-refresh' })
  }
  const pending = refreshSession()
  const rejected = assert.rejects(pending, /sessão mudou/)
  state().clear()
  await rejected
  assert.equal(sent, 0)
})
