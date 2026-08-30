/** @type {import('next').NextConfig} */
const nextConfig = {
  // Sprint 8 (D15) : sortie standalone requise pour l'image Docker de prod
  // (frontend/Dockerfile) — un runtime minimal sans devDependencies/npm
  // install en prod, plutôt que de copier tout node_modules.
  output: "standalone",
};

export default nextConfig;
