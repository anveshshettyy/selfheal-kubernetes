set -euo pipefail


# Port-forward dashboards and tail pods
(kubectl -n monitoring port-forward svc/monitoring-grafana 3000:80 >/dev/null 2>&1 &)
(kubectl -n monitoring port-forward svc/monitoring-kube-prometheus-prometheus 9090:9090 >/dev/null 2>&1 &)


# App service forward
(kubectl -n selfheal port-forward svc/app-svc 8080:80 >/dev/null 2>&1 &)


echo "Prometheus: http://localhost:9090"
echo "Grafana: http://localhost:3000"
echo "App: http://localhost:8080"


echo "Tailing selfheal-api logs. Ctrl+C to stop."
kubectl -n selfheal logs -f deploy/selfheal-api