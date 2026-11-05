import tseslint from 'typescript-eslint'

export default [{
  files: ['tests/**/*.cjs', 'eslint.config.mjs', 'config/**/*.js', 'plugins/**/*.js', 'app.config.js'],
  rules: { 'no-unreachable': 'error', 'no-constant-condition': 'error' },
}, {
  files: ['**/*.ts', '**/*.tsx'],
  ignores: ['node_modules/**', 'dist/**', '.expo/**'],
  languageOptions: { parser: tseslint.parser, parserOptions: { ecmaVersion: 'latest', sourceType: 'module', ecmaFeatures: { jsx: true } } },
  plugins: { '@typescript-eslint': tseslint.plugin },
  rules: {
    'no-unreachable': 'error', 'no-constant-condition': 'error',
    '@typescript-eslint/no-duplicate-enum-values': 'error',
    '@typescript-eslint/no-explicit-any': 'error',
  },
}]
