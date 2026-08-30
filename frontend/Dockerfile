# Sprint 8 (D15) : image de prod pour le frontend Next.js — n'existait pas
# avant ce sprint, le frontend tournait uniquement via `npm run dev` en
# local (spec §8.1 point 1 le liste pourtant dans le docker-compose cible).
# Build multi-stage classique, sortie `output: "standalone"` (next.config.mjs)
# pour un runtime minimal sans réinstaller les dépendances complètes.

FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
CMD ["node", "server.js"]
