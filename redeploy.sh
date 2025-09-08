#!/bin/bash
set -e

CLUSTER=selfheal
IMAGE=selfheal-api:0.1

echo "🔥 Deleting old cluster..."
kind delete cluster --name $CLUSTER || true

echo "🚀 Creating fresh cluster..."
kind create cluster --name $CLUSTER

echo "📦 Loading Docker image into cluster..."
kind load docker-image $IMAGE --name $CLUSTER

echo "📊 Installing monitoring stack (Prometheus + Grafana)..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install obs prometheus-community/kube-prometheus-stack -n monitoring --create-namespace

echo "🗂️ Applying manifests (with namespace ordering)..."
# Apply namespaces first to avoid invalid namespace errors
kubectl apply -f k8s/namespace.yaml

# Then apply other manifests
kubectl apply -f monitoring/ || true
kubectl apply -f monitors/ || true
kubectl apply -f detector/ || true
kubectl apply -f k8s/ || true

echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=180s deployment --all -n selfheal || true
kubectl wait --for=condition=available --timeout=180s deployment --all -n monitoring || true

# Optional: wait for specific pods to be ready
kubectl wait --for=condition=ready pod -l app=selfheal-api -n selfheal --timeout=180s || true
kubectl wait --for=condition=ready pod -l app=prometheus -n monitoring --timeout=180s || true

echo "🔌 Restarting port-forwards..."
# Kill old port-forwards on the relevant ports
pkill -f "kubectl.*port-forward.*3000" || true
pkill -f "kubectl.*port-forward.*9090" || true

# Start new ones in background with logs
nohup kubectl -n selfheal port-forward svc/selfheal-api-svc 3000:3000 > portforward-selfheal.log 2>&1 &
nohup kubectl -n monitoring port-forward svc/obs-kube-prometheus-stack-prometheus 9090:9090 > portforward-prometheus.log 2>&1 &

echo "✅ Redeploy complete!"
kubectl get pods -A

echo "Port-forward logs:"
echo " - Selfheal API: portforward-selfheal.log"
echo " - Prometheus: portforward-prometheus.log"
echo ""
echo "Access Selfheal API at: http://localhost:3000"
echo "Access Prometheus at: http://localhost:9090"
