# Use Node.js LTS slim
FROM node:22-slim

RUN apt-get update && \
    apt-get install -y curl && \
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
    rm kubectl && apt-get clean

WORKDIR /app

COPY package*.json ./
RUN npm install --production

COPY . .

ENV KUBECONFIG=/var/run/secrets/kubernetes.io/serviceaccount/token

EXPOSE 8080

CMD ["node", "server.js"]
