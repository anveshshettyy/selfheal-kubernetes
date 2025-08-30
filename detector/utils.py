import logging, os, sys
from prometheus_client import start_http_server, Counter, Gauge

LOG = logging.getLogger("selfheal")
logging.basicConfig(stream=sys.stdout, level=os.getenv("LOG_LEVEL","INFO"),
                    format="%(asctime)s %(levelname)s %(message)s")

ANOMALIES = Counter('detector_anomalies_total','anomalies detected', ['metric'])
ACTIONS = Counter('detector_actions_sent_total','actions sent', ['type','target'])
VALUES = Gauge('detector_metric_value','last scraped value', ['metric'])
