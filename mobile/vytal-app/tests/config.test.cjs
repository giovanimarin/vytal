const { test } = require('node:test')
const assert = require('node:assert/strict')
const { resolveApiUrl, rejectPublicSecrets } = require('../config/security')

test('development fallback is local and never selects a production service', () => {
  assert.equal(resolveApiUrl(undefined, true), 'http://localhost:8000/api/v1')
  assert.equal(resolveApiUrl('http://10.0.2.2:8000/api/v1', true), 'http://10.0.2.2:8000/api/v1')
})
for (const url of [undefined, '', ' ', 'http://api.example.invalid/api/v1', 'https://localhost/api/v1',
  'https://127.0.0.1/api/v1', 'https://[::1]/api/v1', 'https://[::ffff:127.0.0.1]/api/v1',
  'https://user:SYNTHETIC_SECRET_MARKER@api.example.invalid/api/v1', 'https://api.example.invalid/api/v1?token=SYNTHETIC_SECRET_MARKER',
  'https://api.example.invalid/api/v1#SYNTHETIC_SECRET_MARKER', 'https://api.example.invalid']) {
  test('production rejects insecure or missing API configuration without exposing its value', () => {
    assert.throws(() => resolveApiUrl(url, false), (error) => {
      assert.ok(error.message.includes('EXPO_PUBLIC_API_URL'))
      assert.ok(!error.message.includes('SYNTHETIC_SECRET_MARKER'))
      return true
    })
  })
}
test('an explicit production HTTPS API v1 endpoint is accepted', () => {
  assert.equal(resolveApiUrl('https://api.example.invalid/api/v1', false), 'https://api.example.invalid/api/v1')
})
for (const name of ['EXPO_PUBLIC_CLIENT_SECRET', 'EXPO_PUBLIC_TOKEN', 'EXPO_PUBLIC_PASSWORD', 'EXPO_PUBLIC_PRIVATE_KEY']) {
  test('public credential settings fail without revealing values', () => {
    assert.throws(() => rejectPublicSecrets({ [name]: 'SYNTHETIC_SECRET_MARKER' }),
      (error) => !error.message.includes('SYNTHETIC_SECRET_MARKER') && error.message.includes(name))
  })
}
test('private build variables and non-secret public settings are not serialized', () => {
  assert.equal(rejectPublicSecrets({ GOOGLE_CLIENT_SECRET: 'SYNTHETIC_SECRET_MARKER', EXPO_PUBLIC_API_URL: 'https://api.example.invalid/api/v1' }), undefined)
})

test('Expo production config validates endpoint and exposes only public endpoint', () => {
  const configure = require('../app.config')
  const previousMode = process.env.NODE_ENV
  const previousUrl = process.env.EXPO_PUBLIC_API_URL
  try {
    process.env.NODE_ENV = 'production'
    delete process.env.EXPO_PUBLIC_API_URL
    assert.throws(() => configure({ config: { name: 'synthetic' } }), /EXPO_PUBLIC_API_URL/)
    process.env.EXPO_PUBLIC_API_URL = 'https://api.example.invalid/api/v1'
    const result = configure({ config: { name: 'synthetic', extra: { feature: true } } })
    assert.deepEqual(result.extra, { feature: true, apiUrl: process.env.EXPO_PUBLIC_API_URL })
  } finally {
    if (previousMode === undefined) delete process.env.NODE_ENV
    else process.env.NODE_ENV = previousMode
    if (previousUrl === undefined) delete process.env.EXPO_PUBLIC_API_URL
    else process.env.EXPO_PUBLIC_API_URL = previousUrl
  }
})
