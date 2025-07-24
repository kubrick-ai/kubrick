import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: false,
  // async rewrites() {
  //   return [
  //     {
  //       source: "/api/proxy/:path*",
  //       destination: "http://localhost:5003/:path*",
  //     },
  //   ];
  // },
};

export default nextConfig;
