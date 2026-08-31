import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/tasks",
        destination: "http://127.0.0.1:8000/tasks",
      },
      {
        source: "/api/runs",
        destination: "http://127.0.0.1:8000/runs",
      },
      {
        source: "/api/runs/:path*",
        destination: "http://127.0.0.1:8000/runs/:path*",
      },
      {
        source: "/api/metrics",
        destination: "http://127.0.0.1:8000/metrics",
      },
      {
        source: "/api/health",
        destination: "http://127.0.0.1:8000/health",
      },
    ];
  },
};

export default nextConfig;
