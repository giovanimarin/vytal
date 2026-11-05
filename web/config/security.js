function resolveBackend(env) {
  for (const name of Object.keys(env)) {
    if (name.startsWith('NEXT_PUBLIC_') && /SECRET|TOKEN|PASSWORD|PRIVATE_KEY|CREDENTIAL/i.test(name)) {
      throw new Error(`Public credential configuration is not allowed: ${name}`)
    }
  }
  if (!['development', 'test', 'production'].includes(env.NODE_ENV)) throw new Error('NODE_ENV must be explicitly configured')
  const development = env.NODE_ENV !== 'production'
  const raw = env.VYTAL_BACKEND_URL === undefined && development ? 'http://localhost:8003' : env.VYTAL_BACKEND_URL
  try {
    if (typeof raw !== 'string' || !raw.trim()) throw new Error()
    const url = new URL(raw)
    const host = url.hostname.toLowerCase().replace(/^\[|\]$/g, '')
    const local = host === 'localhost' || host.endsWith('.localhost') || host.startsWith('127.')
      || ['::1', '::', '0.0.0.0'].includes(host) || host.startsWith('::ffff:7f')
    if (url.username || url.password || url.search || url.hash || !url.hostname || host.includes('*') || url.pathname !== '/') throw new Error()
    if (development ? !['http:', 'https:'].includes(url.protocol) : url.protocol !== 'https:' || local) throw new Error()
    return url.origin
  } catch {
    throw new Error('VYTAL_BACKEND_URL must be explicitly configured with a safe backend origin; production requires non-local HTTPS')
  }
}
module.exports = { resolveBackend }
