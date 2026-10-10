# Our own Grafana (compose profile "observability"), provisioning and dashboards baked in: no bind mount.
FROM grafana/grafana:13.2.3
COPY provisioning /etc/grafana/provisioning
COPY dashboards /var/lib/grafana/dashboards
