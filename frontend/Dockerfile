# CloudForge AI frontend (Next.js 14) - production image.
# Build arg NEXT_PUBLIC_API_URL is baked in at build time:
#   docker build --build-arg NEXT_PUBLIC_API_URL=https://api.example.com ./frontend

FROM node:20-alpine AS deps
WORKDIR /srv/app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /srv/app
COPY --from=deps /srv/app/node_modules ./node_modules
COPY . .
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /srv/app
ENV NODE_ENV=production
COPY --from=builder /srv/app/package.json ./package.json
COPY --from=builder /srv/app/node_modules ./node_modules
COPY --from=builder /srv/app/.next ./.next
COPY --from=builder /srv/app/public ./public
COPY --from=builder /srv/app/next.config.js ./next.config.js
EXPOSE 3000
CMD ["npm", "run", "start", "--", "-p", "3000"]
