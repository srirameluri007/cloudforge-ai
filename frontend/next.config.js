/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // The build must never call the real backend; pages that need live data
  // fetch it client-side at runtime instead.
  experimental: {
    missingSuspenseWithCSRBailout: false,
  },
};

module.exports = nextConfig;
