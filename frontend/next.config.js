/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // The build must never call the real backend; pages that need live data
  // fetch it client-side at runtime instead.
  experimental: {
    missingSuspenseWithCSRBailout: false,
  },
  // Production same-origin proxy: the browser calls /api/* on the frontend
  // origin (relative URLs), and Next.js forwards those requests to the backend
  // server-side. This keeps session cookies first-party and avoids baking a
  // backend origin into the build. BACKEND_INTERNAL_URL is set in production
  // (e.g. Render); it defaults to local development.
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${
          process.env.BACKEND_INTERNAL_URL || "http://localhost:8000"
        }/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
