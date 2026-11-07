// Real Metro manifest/bundle, no device or network outside loopback.
const { test } = require('node:test')
const assert = require('node:assert/strict')
const { spawn, execFileSync } = require('node:child_process')
const { once } = require('node:events')
const net = require('node:net')
const path = require('node:path')

test('CI development APK can load a new LAN API URL from Metro without native rebuild', { timeout: 240000 }, async () => {
  const probe = net.createServer()
  probe.listen(0, '127.0.0.1')
  await once(probe, 'listening')
  const port = probe.address().port
  await new Promise(resolve => probe.close(resolve))
  const advertised = `http://192.168.77.42:${port}`
  const api = 'http://192.168.77.42:8000/api/v1'
  const worker = spawn(process.execPath, [path.resolve(__dirname, '../node_modules/expo/bin/cli'), 'start', '--dev-client', '--localhost', '--port', String(port), '--clear'], {
    cwd: path.resolve(__dirname, '..'), detached: process.platform !== 'win32',
    env: { ...process.env, NODE_ENV: 'development', EXPO_PUBLIC_API_URL: api,
      EXPO_PACKAGER_PROXY_URL: advertised, REACT_NATIVE_PACKAGER_HOSTNAME: '192.168.77.42',
      EXPO_OFFLINE: '1', EXPO_NO_TELEMETRY: '1', CI: '1' },
    stdio: ['ignore', 'pipe', 'pipe'],
  })
  let logs = ''
  worker.stdout.on('data', data => { logs = (logs + data).slice(-6000) })
  worker.stderr.on('data', data => { logs = (logs + data).slice(-6000) })
  try {
    let ready = false
    for (let attempt = 0; attempt < 120; attempt++) {
      if (worker.exitCode !== null) throw new Error(`Metro terminated: ${logs}`)
      try {
        ready = (await (await fetch(`http://127.0.0.1:${port}/status`, { signal: AbortSignal.timeout(2000) })).text()).includes('packager-status:running')
      } catch { /* Startup only; no external service. */ }
      if (ready) break
      await new Promise(resolve => setTimeout(resolve, 500))
    }
    assert.ok(ready, `Metro startup: ${logs}`)
    const response = await fetch(`http://127.0.0.1:${port}/`, { headers: { accept: 'application/expo+json', 'expo-platform': 'android', 'expo-protocol-version': '1' }, signal: AbortSignal.timeout(90000) })
    const manifestBody = await response.text()
    assert.equal(response.status, 200, `Metro manifest failed: ${manifestBody} ${logs}`)
    const manifest = JSON.parse(manifestBody)
    assert.equal(manifest.extra.expoClient.extra.apiUrl, api)
    assert.equal(new URL(manifest.launchAsset.url).host, new URL(advertised).host)
    const bundleUrl = new URL(manifest.launchAsset.url)
    // Fetch only through loopback; advertised LAN address is synthetic.
    bundleUrl.hostname = '127.0.0.1'
    bundleUrl.searchParams.set('lazy', 'false')
    const bundled = await fetch(bundleUrl, { signal: AbortSignal.timeout(120000) })
    assert.equal(bundled.status, 200)
    const source = await bundled.text()
    // SDK 54's Babel preset inlines EXPO_PUBLIC_* references into the client.
    // Assert the selected LAN API is in the served JS; avoid coupling to Babel's
    // variable names or the removed SDK 53 process.env polyfill format.
    assert.ok(source.includes(JSON.stringify(api)), 'Served Android JS must contain the selected LAN API URL')

  } finally {
    if (worker.exitCode === null) {
      if (process.platform === 'win32') execFileSync('taskkill', ['/PID', String(worker.pid), '/T', '/F'], { stdio: 'ignore' })
      else process.kill(-worker.pid, 'SIGTERM')
      await Promise.race([once(worker, 'exit'), new Promise(resolve => setTimeout(resolve, 3000))])
    }
  }
})
