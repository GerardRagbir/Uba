# The recipe for the frontend image. Three stages keep the final image small:
# the tools used to build the site are not shipped with it.

# 1. Install dependencies
FROM node:24-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# 2. Build the site
FROM node:24-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# 3. The image that actually runs: just Node and the built output
FROM node:24-alpine AS run
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
RUN addgroup -S uba && adduser -S uba -G uba
COPY --from=build /app/public ./public
COPY --from=build --chown=uba:uba /app/.next/standalone ./
COPY --from=build --chown=uba:uba /app/.next/static ./.next/static
USER uba
EXPOSE 3000
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=5 \
  CMD wget -qO- http://127.0.0.1:3000/healthz || exit 1
CMD ["node", "server.js"]
