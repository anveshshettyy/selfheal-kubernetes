set -euo pipefail


URL=${1:-"http://localhost:8080/work?ms=500"}
DURATION=${2:-"60s"}
CONC=${3:-"40"}
QPS=${4:-"30"}


echo "Running hey against $URL (duration=$DURATION, conc=$CONC, qps=$QPS)"
hey -z "$DURATION" -c "$CONC" -q "$QPS" "$URL"