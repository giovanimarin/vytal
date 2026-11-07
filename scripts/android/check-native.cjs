// Check the resolved native dependency graph before compilation.
const assert = require('node:assert/strict')
const { execFileSync } = require('node:child_process')
const path = require('node:path')
const app = path.resolve(__dirname, '../../mobile/vytal-app')
const resolve = name => require.resolve(name, { paths: [app] })
const pkg = require(resolve('./package.json'))
const semver = require(resolve('semver'))
const expected = require(resolve('expo/bundledNativeModules.json'))
for (const [name, range] of Object.entries(expected)) {
  if (pkg.dependencies[name]) assert.ok(semver.satisfies(require(resolve(name + '/package.json')).version, range), `${name} must satisfy SDK 54: ${range}`)
}
assert.ok(semver.satisfies(require(resolve('babel-preset-expo/package.json')).version, require(resolve('expo/package.json')).dependencies['babel-preset-expo']))
const autolink = require.resolve('expo-modules-autolinking/bin/expo-modules-autolinking', { paths: [app] })
const modules = JSON.parse(execFileSync(process.execPath, [autolink, 'resolve', '--platform', 'android', '--json'], { cwd: app, encoding: 'utf8' })).modules
for (const name of ['expo-web-browser', 'expo-linking', 'expo-secure-store', 'expo-dev-client']) {
  assert.ok(modules.some(m => m.packageName === name), `Native autolinking missing ${name}`)
}
const rn = JSON.parse(execFileSync(process.execPath, [autolink, 'react-native-config', '--platform', 'android', '--json'], { cwd: app, encoding: 'utf8' }))
assert.ok(rn.dependencies['react-native-health-connect']?.platforms.android, 'Health Connect Android autolinking missing')
console.log('SDK compatibility, Babel and native autolinking validated')
