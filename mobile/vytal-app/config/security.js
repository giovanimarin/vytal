// Used by Expo's build configuration and by the runtime transport.
function rejectPublicSecrets(env) {
  for (const name of Object.keys(env)) {
    if (name.startsWith('EXPO_PUBLIC_') && /SECRET|TOKEN|PASSWORD|PRIVATE_KEY|CREDENTIAL/i.test(name)) {
      throw new Error(`Public credential configuration is not allowed: ${name}`)
    }
  }
}
function resolveApiUrl(value, development) {
  const raw = value === undefined && development ? 'http://localhost:8000/api/v1' : value
  try {
    if (typeof raw !== 'string' || !raw.trim()) throw new Error()
    const url = new URL(raw)
    const host = url.hostname.toLowerCase().replace(/^\[|\]$/g, '')
    const local = host === 'localhost' || host.endsWith('.localhost') || host.startsWith('127.')
      || ['::1', '::', '0.0.0.0'].includes(host) || host.startsWith('::ffff:7f')
    if (url.username || url.password || url.search || url.hash || !url.hostname || host.includes('*')) throw new Error()
    if (development ? !['http:', 'https:'].includes(url.protocol) : url.protocol !== 'https:' || local) throw new Error()
    if (!url.pathname.replace(/\/$/, '').endsWith('/api/v1')) throw new Error()
    return url.toString().replace(/\/$/, '')
  } catch {
    throw new Error('EXPO_PUBLIC_API_URL must be explicitly configured with a safe API v1 URL; production requires non-local HTTPS')
  }
}
module.exports = { resolveApiUrl, rejectPublicSecrets }
