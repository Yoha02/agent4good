-- BigQuery Database Schema for Multi-Source Health & Environmental Data
-- Dataset: health_environmental_data

-- ============================================
-- TABLE 1: data_sources
-- Stores metadata about all data feed sources
-- ============================================
CREATE TABLE `health_environmental_data.data_sources` (
  source_id INT64 NOT NULL,
  source_name STRING NOT NULL,
  source_type STRING NOT NULL,  -- rss, atom, xml, geojson, arcgis
  url STRING NOT NULL,
  data_format STRING NOT NULL,  -- xml, json, geojson
  category STRING NOT NULL,     -- wildfire, earthquake, severe_weather, health, air_quality
  refresh_minutes INT64 NOT NULL DEFAULT 60,
  active BOOL NOT NULL DEFAULT TRUE,
  geocoded BOOL NOT NULL DEFAULT FALSE,
  state_filter STRING,          -- 2-letter state code or NULL for national
  description STRING,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP
);

-- ============================================
-- TABLE 2: data_items
-- Main table storing all fetched data items
-- ============================================
CREATE TABLE `health_environmental_data.data_items` (
  item_id STRING NOT NULL,      -- GUID or source-specific ID
  source_id INT64 NOT NULL,
  
  -- Basic info
  title STRING,
  description STRING,
  link STRING,
  published_date TIMESTAMP,
  
  -- Categorization
  category STRING,              -- alert, warning, info, forecast
  severity STRING,              -- critical, high, moderate, low, info
  event_type STRING,            -- wildfire, earthquake, storm, covid, respiratory, drug_shortage
  
  -- Location data
  location_name STRING,
  state_code STRING,
  latitude FLOAT64,
  longitude FLOAT64,
  geometry GEOGRAPHY,           -- BigQuery GIS support
  affected_area_polygon STRING, -- GeoJSON string
  
  -- Event-specific metrics
  magnitude FLOAT64,            -- For earthquakes, storm intensity, etc.
  alert_level STRING,           -- red, orange, yellow, green
  
  -- Air quality specific
  pollutant_type STRING,        -- PM2.5, Ozone, etc.
  aqi_value INT64,
  
  -- Health data specific
  health_metric STRING,         -- Test positivity, case count, etc.
  health_value FLOAT64,
  health_unit STRING,           -- %, count, rate, etc.
  
  -- Drug availability specific
  drug_name STRING,
  availability_status STRING,   -- available, limited, unavailable
  facility_name STRING,
  
  -- Lifecycle
  expires_at TIMESTAMP,
  is_active BOOL DEFAULT TRUE,
  is_archived BOOL DEFAULT FALSE,
  
  -- Metadata
  metadata_json STRING,         -- Additional data as JSON
  
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP
)
PARTITION BY DATE(published_date)
CLUSTER BY source_id, state_code, event_type;

-- ============================================
-- TABLE 3: map_markers
-- Map visualization data
-- ============================================
CREATE TABLE `health_environmental_data.map_markers` (
  marker_id STRING NOT NULL,
  item_id STRING NOT NULL,      -- FK to data_items
  
  marker_type STRING NOT NULL,  -- wildfire, earthquake, storm, health, drug, air_quality
  latitude FLOAT64 NOT NULL,
  longitude FLOAT64 NOT NULL,
  
  -- Visualization
  marker_color STRING,          -- Hex color
  marker_icon STRING,           -- Icon identifier
  marker_size STRING,           -- small, medium, large
  z_index INT64,                -- Display priority
  
  -- Popup content
  popup_title STRING,
  popup_content STRING,         -- HTML content
  
  -- Display rules
  show_by_default BOOL DEFAULT TRUE,
  zoom_level INT64,             -- Minimum zoom to show
  animation STRING,             -- pulse, bounce, drop, none
  cluster_group STRING,         -- For marker clustering
  visibility_rules STRING,      -- JSON rules
  
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY marker_type, latitude, longitude;

-- ============================================
-- TABLE 4: health_metrics_timeseries
-- Time-series health data (COVID, respiratory, etc.)
-- ============================================
CREATE TABLE `health_environmental_data.health_metrics_timeseries` (
  metric_id STRING NOT NULL,
  source_id INT64 NOT NULL,
  
  -- Location
  state_code STRING,
  county_name STRING,
  facility_name STRING,
  
  -- Metric details
  metric_name STRING NOT NULL,  -- covid_positivity, flu_cases, rsv_cases, etc.
  metric_value FLOAT64,
  metric_unit STRING,
  
  -- Demographics (if available)
  age_group STRING,
  demographic_category STRING,
  
  -- Time
  date_recorded DATE NOT NULL,
  week_number INT64,
  
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date_recorded
CLUSTER BY state_code, metric_name;

-- ============================================
-- TABLE 5: drug_availability
-- Drug/medication availability data
-- ============================================
CREATE TABLE `health_environmental_data.drug_availability` (
  availability_id STRING NOT NULL,
  
  -- Drug info
  drug_name STRING NOT NULL,
  drug_ndc STRING,              -- National Drug Code
  drug_category STRING,         -- antibiotic, vaccine, etc.
  
  -- Location
  facility_name STRING,
  facility_type STRING,         -- pharmacy, hospital, clinic
  address STRING,
  city STRING,
  state_code STRING,
  zip_code STRING,
  latitude FLOAT64,
  longitude FLOAT64,
  
  -- Availability
  availability_status STRING NOT NULL,  -- available, limited, unavailable
  quantity_available INT64,
  last_restocked DATE,
  next_shipment_date DATE,
  
  -- Time
  date_recorded DATE NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date_recorded
CLUSTER BY state_code, drug_name, availability_status;

-- ============================================
-- INDEXES for performance
-- ============================================
-- BigQuery doesn't use traditional indexes, but we use CLUSTERING above

-- ============================================
-- VIEWS for common queries
-- ============================================

-- Active alerts by type
CREATE VIEW `health_environmental_data.active_alerts` AS
SELECT 
  item_id,
  source_id,
  title,
  event_type,
  severity,
  location_name,
  state_code,
  latitude,
  longitude,
  published_date,
  expires_at
FROM `health_environmental_data.data_items`
WHERE is_active = TRUE
  AND is_archived = FALSE
  AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP())
  AND severity IN ('critical', 'high')
ORDER BY published_date DESC;

-- Recent health metrics
CREATE VIEW `health_environmental_data.recent_health_metrics` AS
SELECT 
  state_code,
  metric_name,
  AVG(metric_value) as avg_value,
  MAX(metric_value) as max_value,
  COUNT(*) as reading_count,
  MAX(date_recorded) as latest_date
FROM `health_environmental_data.health_metrics_timeseries`
WHERE date_recorded >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY state_code, metric_name;

-- Drug shortages by state
CREATE VIEW `health_environmental_data.drug_shortages` AS
SELECT 
  state_code,
  drug_name,
  COUNT(*) as total_facilities,
  SUM(CASE WHEN availability_status = 'unavailable' THEN 1 ELSE 0 END) as unavailable_count,
  SUM(CASE WHEN availability_status = 'limited' THEN 1 ELSE 0 END) as limited_count,
  MAX(date_recorded) as latest_update
FROM `health_environmental_data.drug_availability`
WHERE date_recorded >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY state_code, drug_name
HAVING unavailable_count > 0 OR limited_count > 0;

-- ============================================
-- TABLE 6: community_reports
-- Community-submitted incident reports
-- ============================================
CREATE TABLE `health_environmental_data.community_reports` (
  report_id STRING NOT NULL,
  
  -- Submission metadata
  timestamp TIMESTAMP NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP,
  
  -- Report classification
  report_type STRING NOT NULL,     -- health, environmental, weather, emergency
  severity STRING NOT NULL,        -- low, moderate, high, critical
  specific_type STRING,            -- respiratory, air_pollution, flooding, etc.
  
  -- Description
  title STRING GENERATED ALWAYS AS (
    CONCAT(
      UPPER(SUBSTR(report_type, 1, 1)), 
      LOWER(SUBSTR(report_type, 2)), 
      ' Report - ', 
      UPPER(SUBSTR(specific_type, 1, 1)), 
      LOWER(SUBSTR(specific_type, 2))
    )
  ) STORED,
  description STRING NOT NULL,
  
  -- Location information
  address STRING,
  zip_code STRING,
  city STRING NOT NULL,
  state STRING NOT NULL,
  latitude FLOAT64,
  longitude FLOAT64,
  location_point GEOGRAPHY GENERATED ALWAYS AS (
    CASE 
      WHEN latitude IS NOT NULL AND longitude IS NOT NULL 
      THEN ST_GEOGPOINT(longitude, latitude)
      ELSE NULL 
    END
  ) STORED,
  
  -- Impact assessment
  people_affected STRING,          -- 1, 2-5, 6-10, 11-25, 26-50, 50+
  timeframe STRING NOT NULL,       -- now, 1hour, today, yesterday, week, ongoing
  
  -- Contact information (optional)
  contact_name STRING,
  contact_email STRING,
  contact_phone STRING,
  anonymous BOOL NOT NULL DEFAULT FALSE,
  
  -- Media attachments
  photos_count INT64 DEFAULT 0,
  photo_urls ARRAY<STRING>,        -- Cloud storage URLs for uploaded photos
  
  -- Status tracking
  status STRING NOT NULL DEFAULT 'submitted',  -- submitted, reviewing, investigating, resolved, closed
  priority_score INT64 GENERATED ALWAYS AS (
    CASE severity
      WHEN 'critical' THEN 4
      WHEN 'high' THEN 3
      WHEN 'moderate' THEN 2
      WHEN 'low' THEN 1
      ELSE 0
    END +
    CASE report_type
      WHEN 'emergency' THEN 3
      WHEN 'health' THEN 2
      WHEN 'environmental' THEN 1
      WHEN 'weather' THEN 1
      ELSE 0
    END
  ) STORED,
  
  -- Response tracking
  assigned_to STRING,              -- Authority/department assigned to handle
  response_notes STRING,           -- Internal notes and updates
  resolution_date TIMESTAMP,
  public_response STRING           -- Public-facing response/resolution
)
PARTITION BY DATE(timestamp)
CLUSTER BY state, report_type, severity
OPTIONS(
  description="Community-submitted health and environmental incident reports with automated priority scoring and geographic indexing"
);

-- ============================================
-- VIEW: recent_community_reports
-- Active community reports from the last 30 days
-- ============================================
CREATE VIEW `health_environmental_data.recent_community_reports` AS
SELECT 
  report_id,
  timestamp,
  report_type,
  severity,
  specific_type,
  title,
  description,
  city,
  state,
  zip_code,
  people_affected,
  timeframe,
  status,
  priority_score,
  photos_count,
  ST_X(location_point) as longitude,
  ST_Y(location_point) as latitude,
  DATE(timestamp) as report_date,
  CASE 
    WHEN anonymous THEN 'Anonymous'
    ELSE contact_name
  END as reporter_name
FROM `health_environmental_data.community_reports`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  AND status IN ('submitted', 'reviewing', 'investigating')
ORDER BY priority_score DESC, timestamp DESC;

-- ============================================
-- VIEW: community_report_stats
-- Summary statistics for community reports
-- ============================================
CREATE VIEW `health_environmental_data.community_report_stats` AS
SELECT 
  state,
  report_type,
  COUNT(*) as total_reports,
  SUM(CASE WHEN severity IN ('critical', 'high') THEN 1 ELSE 0 END) as high_priority_reports,
  AVG(priority_score) as avg_priority,
  COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_count,
  COUNT(CASE WHEN photos_count > 0 THEN 1 END) as reports_with_photos,
  MIN(timestamp) as first_report_date,
  MAX(timestamp) as latest_report_date,
  COUNT(DISTINCT zip_code) as unique_zip_codes
FROM `health_environmental_data.community_reports`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
GROUP BY state, report_type
ORDER BY total_reports DESC;
