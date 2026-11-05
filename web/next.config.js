const { resolveBackend } = require('./config/security')
const backend = resolveBackend(process.env)

/** @type {import('next').NextConfig} */
module.exports = {
  distDir: process.env.NODE_ENV === 'development' ? (process.env.VYTAL_NEXT_DIST_DIR || '.next-dev') : '.next',
  async rewrites() {
    return [{ source: '/api/:path*', destination: `${backend}/api/:path*` }]
  },
}
