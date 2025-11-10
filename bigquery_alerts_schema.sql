-- BigQuery Schema for Public Health Alerts Table
-- Table: CrowdsourceData.public_health_alerts

CREATE TABLE IF NOT EXISTS `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.public_health_alerts` (
  alert_id STRING NOT NULL,
  message STRING NOT NULL,
  level STRING NOT NULL, -- 'info', 'warning', 'critical'
  issued_by STRING NOT NULL, -- Name of official who issued the alert
  issued_at TIMESTAMP NOT NULL,
  duration_hours INT64, -- NULL means "until cancelled"
  expires_at TIMESTAMP, -- NULL means "until cancelled"
  cancelled BOOL DEFAULT FALSE,
  cancelled_by STRING,
  cancelled_at TIMESTAMP,
  location_city STRING,
  location_state STRING,
  location_county STRING,
  active BOOL DEFAULT TRUE -- Computed field: not cancelled AND (expires_at is NULL OR expires_at > CURRENT_TIMESTAMP())
);

-- To create this table, run this SQL in BigQuery console or use the bq command-line tool:
-- bq query --use_legacy_sql=false < bigquery_alerts_schema.sql
