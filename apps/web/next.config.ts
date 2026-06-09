import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    const backend = process.env.API_BACKEND_URL ?? "http://localhost:8000";
    return [
      {
        source: "/api/v1/:path*/",
        destination: `${backend}/api/v1/:path*/`,
      },
      {
        source: "/api/v1/:path*",
        destination: `${backend}/api/v1/:path*/`,
      },
      {
        source: "/admin/:path*/",
        destination: `${backend}/admin/:path*/`,
      },
      {
        source: "/admin/:path*",
        destination: `${backend}/admin/:path*/`,
      },
      {
        source: "/static/:path*",
        destination: `${backend}/static/:path*`,
      },
    ];
  },
};

export default nextConfig;
