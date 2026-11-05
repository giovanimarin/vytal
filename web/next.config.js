const { resolveBackend } = require('./config/security')
const backend = resolveBackend(process.env)

/** @type {import('next').NextConfig} */
module.exports = {
  async rewrites() {
    return [{ source: '/api/:path*', destination: `${backend}/api/:path*` }]
  },
}
