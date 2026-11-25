/** @type {import('next').NextConfig} */
const isVercel = process.env.VERCEL === '1';

const nextConfig = {
  async rewrites() {
    // In Vercel, top-level vercel.json routes /api/* to the backend service.
    // In local development, proxy to localhost:8000.
    if (isVercel) {
      return [];
    }
    return [
      {
        source: '/api/:path*',
        destination: process.env.BACKEND_URL || 'http://127.0.0.1:8000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
