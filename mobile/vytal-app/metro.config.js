const { getDefaultConfig } = require('expo/metro-config')

const config = getDefaultConfig(__dirname)

// Usa o bundle correto para web (evita import.meta de pacotes como zustand)
config.resolver.unstable_enablePackageExports = true
config.resolver.unstable_conditionNames = ['browser', 'require', 'default']

module.exports = config
