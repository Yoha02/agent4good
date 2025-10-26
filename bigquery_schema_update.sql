-- BigQuery Schema Update for Agent4Good
-- Adds columns for AI analysis, attachments, and review workflow
-- Run this script to update the CrowdSourceData table

-- Note: ai_overall_summary and ai_media_summary already exist in the schema
-- This script adds the remaining required columns

-- Add AI-related columns
ALTER TABLE `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.CrowdSourceData`
ADD COLUMN IF NOT EXISTS ai_tags STRING OPTIONS(description='AI-generated tags (JSON array): valid, urgent, moderate, inappropriate, needs_review, contact_required, etc.'),
ADD COLUMN IF NOT EXISTS ai_confidence FLOAT64 OPTIONS(description='AI confidence score (0-1) for the analysis'),
ADD COLUMN IF NOT EXISTS ai_analyzed_at TIMESTAMP OPTIONS(description='Timestamp when AI analysis was performed');

-- Add attachment/media columns
ALTER TABLE `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.CrowdSourceData`
ADD COLUMN IF NOT EXISTS attachment_urls STRING OPTIONS(description='JSON array of GCS URLs for uploaded files (images, PDFs, videos, CSV)');

-- Add review workflow columns
ALTER TABLE `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.CrowdSourceData`
ADD COLUMN IF NOT EXISTS reviewed_by STRING OPTIONS(description='Name of the health official who reviewed this report'),
ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP OPTIONS(description='Timestamp when the report was reviewed'),
ADD COLUMN IF NOT EXISTS exclude_from_analysis BOOL OPTIONS(description='Flag to exclude this report from analysis (spam, duplicate, etc.)'),
ADD COLUMN IF NOT EXISTS exclusion_reason STRING OPTIONS(description='Reason for exclusion: Duplicate Report, Spam/Inappropriate, Test Data, Insufficient Information, Out of Jurisdiction, Other'),
ADD COLUMN IF NOT EXISTS manual_tags STRING OPTIONS(description='JSON array of manually added tags by reviewers');

-- Verify the schema update
SELECT 
  column_name, 
  data_type, 
  description
FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS`
WHERE table_name = 'CrowdSourceData'
  AND column_name IN (
    'ai_tags', 
    'ai_confidence', 
    'ai_analyzed_at',
    'attachment_urls',
    'reviewed_by',
    'reviewed_at',
    'exclude_from_analysis',
    'exclusion_reason',
    'manual_tags',
    'ai_overall_summary',
    'ai_media_summary'
  )
ORDER BY column_name;
