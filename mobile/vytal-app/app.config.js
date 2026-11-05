const { resolveApiUrl, rejectPublicSecrets } = require('./config/security')

module.exports = ({ config }) => {
  rejectPublicSecrets(process.env)
  const development = ['development', 'test'].includes(process.env.NODE_ENV)
  const apiUrl = resolveApiUrl(process.env.EXPO_PUBLIC_API_URL, development)
  return { ...config, extra: { ...config.extra, apiUrl } }
}
