import type { NextConfig } from "next";

const isDev = process.env.NODE_ENV !== "production";

const contentSecurityPolicy = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""}`,
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  "img-src 'self' data: blob:",
  "font-src 'self' https://fonts.gstatic.com",
  "connect-src 'self'",
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join("; ");

const securityHeaders = [
  { key: "Content-Security-Policy", value: contentSecurityPolicy },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
];

const nextConfig: NextConfig = {
  output: "standalone",
  async headers() {
    return [
      {
        source: "/:path*",
        headers: securityHeaders,
      },
    ];
  },
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
