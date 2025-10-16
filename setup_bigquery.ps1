# BigQuery Setup Script
# This script helps you set up BigQuery dataset and load air quality data

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "BigQuery Setup for Air Quality Data" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get project ID
$PROJECT_ID = Read-Host "Enter your Google Cloud Project ID"
if ([string]::IsNullOrWhiteSpace($PROJECT_ID)) {
    Write-Host "Error: Project ID is required" -ForegroundColor Red
    exit 1
}

# Set project
Write-Host ""
Write-Host "Setting project to $PROJECT_ID..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID

# Create dataset
Write-Host ""
Write-Host "Creating BigQuery dataset..." -ForegroundColor Yellow
bq mk --dataset --location=US $PROJECT_ID`:air_quality_dataset

Write-Host "✓ Dataset created" -ForegroundColor Green

# Create table
Write-Host ""
Write-Host "Creating table..." -ForegroundColor Yellow
bq mk --table $PROJECT_ID`:air_quality_dataset.air_quality_data `
  date:DATE,state_name:STRING,county_name:STRING,aqi:INTEGER,parameter_name:STRING,site_name:STRING

Write-Host "✓ Table created" -ForegroundColor Green

# Load data
$CSV_FILE = "..\daily_88101_2025\daily_88101_2025.csv"

if (Test-Path $CSV_FILE) {
    Write-Host ""
    Write-Host "Loading data from CSV file..." -ForegroundColor Yellow
    bq load --source_format=CSV --skip_leading_rows=1 `
      $PROJECT_ID`:air_quality_dataset.air_quality_data `
      $CSV_FILE `
      date:DATE,state_name:STRING,county_name:STRING,aqi:INTEGER,parameter_name:STRING,site_name:STRING
    
    Write-Host "✓ Data loaded successfully" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Warning: CSV file not found at $CSV_FILE" -ForegroundColor Yellow
    Write-Host "Please load your data manually using:" -ForegroundColor Yellow
    Write-Host "  bq load --source_format=CSV --skip_leading_rows=1 air_quality_dataset.air_quality_data your_file.csv date:DATE,state_name:STRING,county_name:STRING,aqi:INTEGER,parameter_name:STRING,site_name:STRING" -ForegroundColor White
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ BigQuery setup completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
