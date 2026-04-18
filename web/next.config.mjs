/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    // Include the logo's display widths (1x=81, 2x=162, 3x=242) in the
    // imageSizes pool so Next.js generates sharp srcset entries for it.
    imageSizes: [16, 32, 48, 64, 81, 96, 128, 162, 242, 256, 384],
  },
};

export default nextConfig;
