set -euo pipefail


# Requires 'ab' (apache2-utils). Example: sudo apt install apache2-utils
URL=${1:-"http://localhost:8080/work?ms=500"}
TOTAL=${2:-"10000"}
CONC=${3:-"100"}


echo "Running ab against $URL (total=$TOTAL, conc=$CONC)"
ab -n "$TOTAL" -c "$CONC" "$URL"