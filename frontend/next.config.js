/** @type {import('next').NextConfig} */
const nextConfig = {
  output: process.env.EXPORT_STATIC === 'true' ? 'export' : undefined,
  transpilePackages: ['@deck.gl/core', '@deck.gl/layers', '@deck.gl/aggregation-layers', '@deck.gl/react'],
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      'mapbox-gl': 'maplibre-gl',
    };
    return config;
  },
};

module.exports = nextConfig;
