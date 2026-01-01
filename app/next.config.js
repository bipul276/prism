/** @type {import('next').NextConfig} */
const nextConfig = {
    async rewrites() {
        return [
            {
                source: '/api/:path*',
                // Prioritize environment variable, fallback to Docker service name (api), then localhost
                destination: (process.env.INTERNAL_API_URL || 'http://api:8000') + '/api/:path*',
            },
        ]
    },
}

module.exports = nextConfig
