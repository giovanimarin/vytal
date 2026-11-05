const { resolveApiUrl, rejectPublicSecrets } = require('./config/security')

module.exports = ({ config }) => {
  rejectPublicSecrets(process.env)
  const development = ['development', 'test'].includes(process.env.NODE_ENV)
  const apiUrl = resolveApiUrl(process.env.EXPO_PUBLIC_API_URL, development)
  return { ...config, plugins: [...(config.plugins || []), 'react-native-health-connect',
    ['expo-build-properties', { android: { minSdkVersion: 26, compileSdkVersion: 36, targetSdkVersion: 36 } }],
    './plugins/withHealthConnectLocal'], extra: { ...config.extra, apiUrl } }
}
