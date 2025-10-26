-- Add county column to existing BigQuery table
-- Run this in BigQuery console or via bq CLI

ALTER TABLE `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.CrowdSourceData`
ADD COLUMN IF NOT EXISTS county STRING OPTIONS(description="County name (auto-populated from ZIP)");

-- Also update city and state to REQUIRED if they were NULLABLE before
-- Note: This won't work if there are NULL values. Clean data first if needed.
-- ALTER TABLE `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.CrowdSourceData`
-- ALTER COLUMN city SET OPTIONS(description="City name (auto-populated from ZIP)");
