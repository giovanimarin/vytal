const { test, beforeEach } = require('node:test')
const assert = require('node:assert/strict')
const { storage, setStorageBarrier, failWriteOnce, useAuthStore, api, login, register,
  getHealthAuthUrl, sessionFromResponse, response, state, flush, seed, ok,
  unauthorized, deferred } = require('./support.cjs')

beforeEach(async () => {
  setStorageBarrier(null)
  state().logout()
  await flush()
  storage.clear()
  api.defaults.adapter = async () => { throw new Error('Unexpected HTTP request') }
})

test('login consumes flat v1 identity and publishes credentials/profile atomically', async () => {
  await seed('A')
  const observations = []
  const stop = useAuthStore.subscribe((s) => observations.push([s.userId, s.accessToken]))
  api.defaults.adapter = async (config) => {
    assert.equal(config.url, '/auth/login')
    assert.deepEqual(JSON.parse(config.data), { email: 'B@example.invalid', password: 'synthetic' })
    assert.equal(config.headers.Authorization, undefined)
    return ok(config, response('B'))
  }
  await login(' B@example.invalid ', 'synthetic')
  stop()
  assert.deepEqual(observations, [['account-B', 'access-B']])
  assert.equal(state().userProfile.name, 'B')
  assert.equal(state().isAuthenticated, true)
  assert.equal(JSON.parse(storage.get('vytal_session')).userProfile.user_id, 'account-B')
})

test('registration consumes the same flat contract and replaces the prior profile', async () => {
  await seed('A')
  api.defaults.adapter = async (config) => {
    assert.equal(config.url, '/auth/register')
    assert.deepEqual(JSON.parse(config.data), { name: 'B', email: 'B@example.invalid', password: 'synthetic' })
    return ok(config, response('B'))
  }
  await register(' B ', ' B@example.invalid ', 'synthetic')
  assert.equal(state().userId, 'account-B')
  assert.equal(state().userProfile.birth_date, null)
  assert.equal(state().accessToken, 'access-B')
})

test('invalid login response cannot install tokens without an identity', async () => {
  await seed('A')
  api.defaults.adapter = async (config) => ok(config, { access_token: 'new', refresh_token: 'new' })
  await assert.rejects(login('B@example.invalid', 'synthetic'))
  assert.equal(state().userId, 'account-A')
  assert.equal(state().accessToken, 'access-A')
})

test('incorrect password rejects promptly without refreshing or exposing an old Bearer', async () => {
  await seed('A')
  let calls = 0
  api.defaults.adapter = async (config) => {
    calls++
    assert.equal(config.url, '/auth/login')
    assert.equal(config.headers.Authorization, undefined)
    return unauthorized(config)
  }
  await assert.rejects(login('B@example.invalid', 'incorrect'))
  assert.equal(calls, 1)
})

for (const name of ['A', 'B']) {
  test(`authenticated connection uses ${name}'s real identity and Bearer`, async () => {
    await seed(name)
    api.defaults.adapter = async (config) => {
      assert.equal(config.url, '/connect/google_fit/auth-url')
      assert.equal(config.params.user_id, `account-${name}`)
      assert.equal(config.headers.Authorization, `Bearer access-${name}`)
      return ok(config, { auth_url: 'https://provider.invalid', state: 'signed-state' })
    }
    assert.equal((await getHealthAuthUrl('google_fit')).state, 'signed-state')
  })
}

test('a signed-out connection does not send a fixed identity or any request', async () => {
  await assert.rejects(getHealthAuthUrl('google_fit'))
  assert.equal(state().isAuthenticated, false)
})

test('restoration ignores stale local profile and confirms identity with backend /me', async () => {
  storage.set('vytal_session', JSON.stringify({ accessToken: 'access-A', refreshToken: 'refresh-A',
    userProfile: sessionFromResponse(response('B')).userProfile }))
  api.defaults.adapter = async (config) => {
    assert.equal(config.url, '/users/me')
    assert.equal(config.headers.Authorization, 'Bearer access-A')
    assert.equal(state().isAuthenticated, false)
    return ok(config, response('A'))
  }
  await state().initFromStorage()
  assert.equal(state().userId, 'account-A')
})

test('legacy tokens migrate after /me; the persisted legacy profile cannot select account B', async () => {
  storage.set('vytal_access_token', 'access-A')
  storage.set('vytal_refresh_token', 'refresh-A')
  storage.set('vytal_user_profile', JSON.stringify(response('B')))
  api.defaults.adapter = async (config) => ok(config, response('A'))
  await state().initFromStorage()
  assert.equal(state().userId, 'account-A')
  assert.equal(storage.has('vytal_user_profile'), false)
  assert.equal(storage.has('vytal_session'), true)
})

test('corrupt persisted session fails closed without setting authenticated state', async () => {
  storage.set('vytal_session', '{invalid')
  await state().initFromStorage()
  await flush()
  assert.equal(state().isAuthenticated, false)
  assert.equal(storage.has('vytal_session'), false)
})

test('profile updates cannot switch account', async () => {
  await seed('A')
  assert.throws(() => state().setProfile(sessionFromResponse(response('B')).userProfile))
  assert.equal(state().userId, 'account-A')
})

test('concurrent 401s share one refresh and retry with the same account', { timeout: 3000 }, async () => {
  await seed('A')
  let refreshes = 0
  api.defaults.adapter = async (config) => {
    if (config.url === '/auth/refresh') {
      refreshes++
      await flush()
      return ok(config, { access_token: 'renewed-A', refresh_token: 'renewed-refresh-A' })
    }
    if (config.headers.Authorization === 'Bearer access-A') return unauthorized(config)
    assert.equal(config.headers.Authorization, 'Bearer renewed-A')
    return ok(config, { user_id: 'account-A' })
  }
  const responses = await Promise.all([api.get('/users/me'), api.get('/users/me')])
  assert.equal(refreshes, 1)
  assert.equal(responses.length, 2)
  assert.equal(state().userId, 'account-A')
})

test('rejected refresh terminates all requests and signs out instead of recursive refresh', { timeout: 3000 }, async () => {
  await seed('A')
  let refreshes = 0
  api.defaults.adapter = async (config) => {
    if (config.url === '/auth/refresh') refreshes++
    return unauthorized(config)
  }
  const results = await Promise.allSettled([api.get('/users/me'), api.get('/users/me')])
  assert.ok(results.every((r) => r.status === 'rejected'))
  assert.equal(refreshes, 1)
  assert.equal(state().isAuthenticated, false)
})

test('expired session restores through bounded refresh before becoming authenticated', async () => {
  storage.set('vytal_session', JSON.stringify(sessionFromResponse(response('A'))))
  api.defaults.adapter = async (config) => {
    if (config.url === '/auth/refresh') return ok(config, { access_token: 'renewed-A', refresh_token: 'renewed-refresh-A' })
    if (config.headers.Authorization === 'Bearer access-A') return unauthorized(config)
    return ok(config, response('A'))
  }
  await state().initFromStorage()
  assert.equal(state().userId, 'account-A')
  assert.equal(state().accessToken, 'renewed-A')
  assert.equal(state().isAuthenticated, true)
})

test('late response from account A cannot be delivered after switching to B', async () => {
  await seed('A')
  const arrived = deferred(), release = deferred()
  api.defaults.adapter = async (config) => {
    arrived.resolve()
    await release.promise
    return ok(config, response('A'))
  }
  const request = api.get('/users/me')
  const rejected = assert.rejects(request, /sessão mudou/)
  await arrived.promise
  await seed('B')
  release.resolve()
  await rejected
  assert.equal(state().userId, 'account-B')
})

test('an in-flight A refresh cannot overwrite account B or log it out', async () => {
  await seed('A')
  const arrived = deferred(), release = deferred()
  api.defaults.adapter = async (config) => {
    if (config.url !== '/auth/refresh') return unauthorized(config)
    arrived.resolve()
    await release.promise
    return ok(config, { access_token: 'renewed-A', refresh_token: 'renewed-refresh-A' })
  }
  const request = api.get('/users/me')
  const rejected = assert.rejects(request, /sessão mudou/)
  await arrived.promise
  await seed('B')
  release.resolve()
  await rejected
  assert.equal(state().userId, 'account-B')
  assert.equal(state().accessToken, 'access-B')
})

test('logout during a storage write cannot resurrect a session', async () => {
  const barrier = deferred()
  setStorageBarrier(barrier.promise)
  const pending = seed('A')
  const rejected = assert.rejects(pending, /sessão mudou/)
  await flush()
  state().logout()
  setStorageBarrier(null)
  barrier.resolve()
  await rejected
  await flush()
  assert.equal(state().isAuthenticated, false)
  assert.equal(storage.has('vytal_session'), false)
})

test('late login cannot restore a session after explicit logout', async () => {
  const arrived = deferred(), release = deferred()
  api.defaults.adapter = async (config) => {
    arrived.resolve()
    await release.promise
    return ok(config, response('A'))
  }
  const pending = login('A@example.invalid', 'synthetic')
  const rejected = assert.rejects(pending, /sessão mudou/)
  await arrived.promise
  state().logout()
  release.resolve()
  await rejected
  assert.equal(state().isAuthenticated, false)
})

test('account switch and logout evict cached health/profile data', async () => {
  const { queryClient } = require('../src/services/queryClient.ts')
  await seed('A')
  queryClient.setQueryData(['user-profile', 'account-A'], response('A'))
  queryClient.setQueryData(['readiness', 'account-A'], { score: 75 })
  await seed('B')
  assert.equal(queryClient.getQueryCache().getAll().length, 0)
  queryClient.setQueryData(['user-profile', 'account-B'], response('B'))
  state().logout()
  assert.equal(queryClient.getQueryCache().getAll().length, 0)
})

test('invalid registration response cannot retain new tokens with an old profile', async () => {
  await seed('A')
  api.defaults.adapter = async (config) => ok(config, { ...response('B'), user_id: '' })
  await assert.rejects(register('B', 'B@example.invalid', 'synthetic'))
  assert.equal(state().accessToken, 'access-A')
  assert.equal(state().userProfile.user_id, 'account-A')
})


test('failed secure storage cannot publish a new identity with old credentials', async () => {
  await seed('A')
  failWriteOnce()
  await assert.rejects(seed('B'), /storage failure/)
  await flush()
  assert.equal(state().userId, null)
  assert.equal(state().accessToken, null)
  assert.equal(storage.has('vytal_session'), false)
})

test('an empty display name permitted by v1 does not prevent legitimate login', async () => {
  api.defaults.adapter = async (config) => ok(config, { ...response('A'), name: '' })
  await login('A@example.invalid', 'synthetic')
  assert.equal(state().userId, 'account-A')
  assert.equal(state().userProfile.name, '')
})

test('a second 401 after one refresh clears the session', async () => {
  await seed('A')
  let renewals = 0
  api.defaults.adapter = async (config) => {
    if (config.url === '/auth/refresh') {
      renewals++
      return ok(config, { access_token: 'renewed-A', refresh_token: 'renewed-refresh-A' })
    }
    return unauthorized(config)
  }
  await assert.rejects(api.get('/users/me'))
  assert.equal(renewals, 1)
  assert.equal(state().isAuthenticated, false)
})

test('401 without refresh credentials clears an unusable session', async () => {
  await seed('A')
  useAuthStore.setState({ refreshToken: null })
  api.defaults.adapter = async (config) => unauthorized(config)
  await assert.rejects(api.get('/users/me'))
  assert.equal(state().isAuthenticated, false)
})

test('logout and login of the same account must still reject an old response', async () => {
  await seed('A')
  const arrived = deferred(), release = deferred()
  api.defaults.adapter = async (config) => {
    arrived.resolve(); await release.promise
    return ok(config, { user_id: 'account-A' })
  }
  const pending = api.get('/users/me')
  await arrived.promise
  state().logout()
  await seed('A')
  release.resolve()
  await assert.rejects(pending, /sessão mudou/)
})

for (const failure of ['network', '500', 'malformed']) {
  test(`refresh ${failure} rejects concurrent requests once and clears credentials`, async () => {
    const { AxiosError } = require('axios')
    await seed('A'); let renewals = 0
    api.defaults.adapter = async (config) => {
      if (config.url !== '/auth/refresh') return unauthorized(config)
      renewals++
      if (failure === 'network') throw new AxiosError('Synthetic network failure', 'ERR_NETWORK', config)
      if (failure === '500') throw new AxiosError('Synthetic failure', 'ERR_BAD_RESPONSE', config, null,
        { status: 500, data: {}, headers: {}, config })
      return ok(config, { access_token: '', refresh_token: null })
    }
    const results = await Promise.allSettled([api.get('/users/me'), api.get('/users/me')])
    assert.ok(results.every((result) => result.status === 'rejected'))
    assert.equal(renewals, 1); assert.equal(state().isAuthenticated, false)
  })
}

test('ordinary request network failure preserves session and never refreshes', async () => {
  await seed('A'); let calls = 0
  api.defaults.adapter = async () => { calls++; throw new Error('Synthetic network failure') }
  await assert.rejects(api.get('/users/me'))
  assert.equal(calls, 1); assert.equal(state().userId, 'account-A')
})

test('explicit logout drops identity before revocation and tolerates offline transport', async () => {
  const { logout } = require('../src/services/auth.ts')
  await seed('A'); let raw
  api.defaults.adapter = async (config) => {
    assert.equal(config.url, '/auth/logout'); raw = JSON.parse(config.data).refresh_token
    assert.equal(state().userId, null)
    throw new Error('Synthetic network failure')
  }
  logout(); await flush()
  assert.equal(raw, 'refresh-A'); assert.equal(state().refreshToken, null)
})

test('session refresh coordinator shares failure and permits a later independent attempt', async () => {
  const { createSessionRefresh } = require('../src/services/sessionRefresh.ts')
  const renew = createSessionRefresh()
  let count = 0
  const action = async () => { count++; throw new Error('Synthetic renewal failure') }
  const first = renew('session-A', action), second = renew('session-A', action)
  assert.equal(first, second)
  await Promise.all([assert.rejects(first), assert.rejects(second)])
  assert.equal(count, 1)
  await assert.rejects(renew('session-B', action))
  assert.equal(count, 2)
})

test('queued renewal cannot send an old refresh after logout', async () => {
  const { refreshSession } = require('../src/services/api.ts')
  await seed('A'); let sent = 0
  api.defaults.adapter = async (config) => {
    sent++; return ok(config, { access_token: 'old-access', refresh_token: 'old-refresh' })
  }
  const pending = refreshSession()
  const rejected = assert.rejects(pending, /sessão mudou/)
  state().logout()
  await rejected
  assert.equal(sent, 0)
})
