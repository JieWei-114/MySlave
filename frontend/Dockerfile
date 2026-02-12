# ---------- deps ----------
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci


# ---------- dev ----------
FROM deps AS dev
WORKDIR /app
COPY . .
EXPOSE 4200
CMD ["npm", "run", "start", "--", "--host", "0.0.0.0"]


# ---------- build-spa ----------
FROM deps AS build-spa
WORKDIR /app
COPY . .
RUN npm run build:spa


# ---------- build-ssr ----------
FROM deps AS build-ssr
WORKDIR /app
COPY . .
RUN npm run build


# ---------- spa runtime ----------
FROM nginx:1.27-alpine AS spa
RUN rm -rf /usr/share/nginx/html/*
COPY --from=build-spa /app/dist/frontend/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 4173


# ---------- ssr runtime ----------
FROM node:20-alpine AS ssr
WORKDIR /app
ENV NODE_ENV=production
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY --from=build-ssr /app/dist ./dist
EXPOSE 4000
CMD ["node", "dist/frontend/server/server.mjs"]
