FROM node:20-alpine as base

WORKDIR /app

COPY package.json package-lock.json* ./

RUN npm ci || npm i --no-audit --no-fund

COPY . .

EXPOSE 3000

CMD ["npm", "start"]