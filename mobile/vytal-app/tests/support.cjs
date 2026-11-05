const fs = require('node:fs')
const Module = require('node:module')
const ts = require('typescript')

// Compile the real TypeScript modules; replace only the device's native storage.
require.extensions['.ts'] = (module, filename) => {
  const result = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022,
      esModuleInterop: true }, fileName: filename,
  })
  module._compile(result.outputText, filename)
}
const storage = new Map()
let storageBarrier = null
let failNextWrite = false
const load = Module._load
Module._load = function (name, parent, main) {
  if (name === 'expo-secure-store') return {
    getItemAsync: async (key) => storage.get(key) ?? null,
    setItemAsync: async (key, value) => { if (failNextWrite) { failNextWrite = false; throw new Error('Synthetic storage failure') } if (storageBarrier) await storageBarrier; storage.set(key, value) },
    deleteItemAsync: async (key) => { storage.delete(key) },
  }
  return load.call(this, name, parent, main)
}
global.__DEV__ = false
process.env.EXPO_PUBLIC_API_URL ||= 'https://api.example.invalid/api/v1'
const { AxiosError } = require('axios')
const { useAuthStore } = require('../src/store/authStore.ts')
const { api } = require('../src/services/api.ts')
const { login, register, getHealthAuthUrl } = require('../src/services/auth.ts')
const { sessionFromResponse } = require('../src/types/auth.ts')

const response = (name) => ({ user_id: `account-${name}`, email: `${name}@example.invalid`,
  name, access_token: `access-${name}`, refresh_token: `refresh-${name}`, token_type: 'bearer' })
const state = () => useAuthStore.getState()
const flush = () => new Promise(setImmediate)
const seed = (name) => state().setSession(sessionFromResponse(response(name)))
const ok = (config, data) => ({ status: 200, statusText: 'OK', data, headers: {}, config })
function unauthorized(config) {
  throw new AxiosError('Synthetic unauthorized', 'ERR_BAD_REQUEST', config, null,
    { status: 401, data: { detail: 'Unauthorized' }, headers: {}, config })
}
function deferred() {
  let resolve
  const promise = new Promise((done) => { resolve = done })
  return { promise, resolve }
}


module.exports = { storage, failWriteOnce: () => { failNextWrite = true }, setStorageBarrier: (value) => { storageBarrier = value },
  useAuthStore, api, login, register, getHealthAuthUrl, sessionFromResponse,
  response, state, flush, seed, ok, unauthorized, deferred }
