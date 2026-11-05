const { test } = require('node:test')
const assert = require('node:assert/strict')
const { resolveBackend } = require('../config/security')

test('documented development/test proxy remains available', () => {
  assert.equal(resolveBackend({ NODE_ENV: 'development' }), 'http://localhost:8003')
  assert.equal(resolveBackend({ NODE_ENV: 'test' }), 'http://localhost:8003')
})
for (const mode of [undefined, '', 'prodution', 'local']) {
  test('unknown runtime environment never silently selects development', () => {
    assert.throws(() => resolveBackend({ NODE_ENV: mode }), /NODE_ENV/)
  })
}
for (const url of [undefined, '', ' ', 'http://backend.example.invalid', 'https://localhost', 'https://127.0.0.1',
  'https://[::1]', 'https://[::ffff:127.0.0.1]', 'https://user:SYNTHETIC_SECRET_MARKER@backend.example.invalid',
  'https://backend.example.invalid/?secret=SYNTHETIC_SECRET_MARKER', 'https://backend.example.invalid/api/v1']) {
  test('production rejects unsafe upstream configuration without exposing values', () => {
    assert.throws(() => resolveBackend({ NODE_ENV: 'production', VYTAL_BACKEND_URL: url }), (error) => {
      assert.ok(error.message.includes('VYTAL_BACKEND_URL'))
      assert.ok(!error.message.includes('SYNTHETIC_SECRET_MARKER'))
      return true
    })
  })
}
test('explicit HTTPS upstream preserves the API v1 proxy mapping', () => {
  assert.equal(resolveBackend({ NODE_ENV: 'production', VYTAL_BACKEND_URL: 'https://backend.example.invalid' }), 'https://backend.example.invalid')
})
for (const name of ['NEXT_PUBLIC_CLIENT_SECRET', 'NEXT_PUBLIC_TOKEN', 'NEXT_PUBLIC_PASSWORD', 'NEXT_PUBLIC_PRIVATE_KEY']) {
  test('public credentials are rejected without printing their value', () => {
    assert.throws(() => resolveBackend({ NODE_ENV: 'production', VYTAL_BACKEND_URL: 'https://backend.example.invalid',
      [name]: 'SYNTHETIC_SECRET_MARKER' }), (error) => !error.message.includes('SYNTHETIC_SECRET_MARKER') && error.message.includes(name))
  })
}
