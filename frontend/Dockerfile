FROM node:20-alpine AS deps

WORKDIR /app

COPY package*.json ./
RUN npm install

FROM deps AS dev

WORKDIR /app
COPY . .

EXPOSE 4200
CMD ["npm", "run", "start", "--", "--host", "0.0.0.0", "--port", "4200"]

FROM deps AS build

WORKDIR /app
COPY . .
RUN npm run build

FROM node:20-alpine AS ssr

WORKDIR /app
ENV NODE_ENV=production

COPY --from=build /app/dist ./dist
COPY --from=build /app/package.json ./package.json
RUN npm install --omit=dev

EXPOSE 4000
CMD ["node", "dist/frontend/server/server.mjs"]

FROM nginx:1.27-alpine AS spa

RUN rm -rf /usr/share/nginx/html/*
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 4173