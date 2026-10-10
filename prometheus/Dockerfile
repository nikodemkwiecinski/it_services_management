# Our own Prometheus (compose profile "observability"), its configuration baked in: no bind mount.
FROM prom/prometheus:v3.15.0
COPY prometheus.yml alerts.yml /etc/prometheus/
