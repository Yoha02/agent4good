# Alert Management System - Complete Implementation Guide

## Overview
This guide covers the complete alert management system with BigQuery storage, allowing health officials to issue, track, and cancel public health alerts with full audit trails.

## Features Implemented

### 1. **BigQuery Alerts Table**
- Persistent storage of all alerts (active, expired, cancelled)
- Full audit trail with issued_by, cancelled_by, timestamps
- Auto-expiration based on duration settings
- Location filtering (city, state, county)

### 2. **Alert Management Dashboard**
- Table view showing all alerts with filtering (All, Active, Expired, Cancelled)
- Status badges (Active, Expired, Cancelled) with color coding
- Level indicators (Critical, Warning, Info)
- Cancel button for each active alert
- Real-time updates after issuing or cancelling alerts

### 3. **Alert Lifecycle**
1. **Issue Alert** → Officials create alert with AI summary assistance
2. **Display** → Alert shows on main page (index.html) and officials dashboard
3. **Track** → Alert appears in management table with full details
4. **Cancel** → Officials can cancel from table with name authentication
5. **Auto-Expire** → Alerts expire automatically based on duration

## Setup Instructions

### Step 1: Create BigQuery Table

Run this command in your terminal:

```powershell
bq query --use_legacy_sql=false @bigquery_alerts_schema.sql
```

Or manually execute the SQL in BigQuery console:

```sql
CREATE TABLE IF NOT EXISTS `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.public_health_alerts` (
  alert_id STRING NOT NULL,
  message STRING NOT NULL,
  level STRING NOT NULL,
  issued_by STRING NOT NULL,
  issued_at TIMESTAMP NOT NULL,
  duration_hours INT64,
  expires_at TIMESTAMP,
  cancelled BOOL DEFAULT FALSE,
  cancelled_by STRING,
  cancelled_at TIMESTAMP,
  location_city STRING,
  location_state STRING,
  location_county STRING,
  active BOOL DEFAULT TRUE
);
```

### Step 2: Verify Environment Variables

Make sure your `.env` file has:
```properties
GOOGLE_CLOUD_PROJECT=qwiklabs-gcp-00-4a7d408c735c
BIGQUERY_DATASET=CrowdsourceData
GEMINI_API_KEY=AIzaSyD-NH9KzOLmSKJmdqszwILplZs3kGL64eA
```

### Step 3: Test the System

1. **Start the Flask server:**
   ```powershell
   python app_local.py
   ```

2. **Navigate to Officials Dashboard:**
   ```
   http://localhost:8080/officials
   ```

3. **Issue an Alert:**
   - Click "Issue Public Alert" button
   - AI summary will generate from recent reports
   - Enter your message
   - Select level (Critical/Warning/Info)
   - Select duration (1hr, 4hr, 8hr, 24hr, 3 days, or Until Cancelled)
   - Click Send Alert

4. **Verify Alert Display:**
   - Check alert banner appears on officials dashboard
   - Navigate to main page (localhost:8080) and verify alert shows
   - Scroll down on officials dashboard to see Alert Management table

5. **Filter Alerts:**
   - Click "Active" to show only active alerts
   - Click "Expired" to show expired alerts
   - Click "Cancelled" to show cancelled alerts
   - Click "All" to show everything

6. **Cancel an Alert:**
   - Click red "Cancel" button in alerts table
   - Enter your name in the modal
   - Confirm cancellation
   - Alert disappears from main page and shows as "Cancelled" in table

## API Endpoints

### 1. `POST /api/officials/generate-alert-summary`
Generates AI summary from recent reports
```json
{
  "filters": {
    "state": "California",
    "city": "San Ramon",
    "county": "Contra Costa County"
  }
}
```

### 2. `POST /api/officials/post-alert`
Creates a new alert
```json
{
  "message": "Air quality alert in effect...",
  "level": "critical",
  "duration_hours": 24,
  "issued_by": "Dr. Sarah Johnson",
  "filters": {
    "state": "California",
    "city": "San Ramon"
  }
}
```

### 3. `GET /api/officials/get-active-alert`
Retrieves current active alert (for public display)
```json
{
  "success": true,
  "alert": {
    "id": "uuid",
    "message": "...",
    "level": "critical",
    "issued_at": "2025-11-08T...",
    "expires_at": "2025-11-09T..."
  }
}
```

### 4. `POST /api/officials/cancel-alert`
Cancels a specific alert
```json
{
  "alert_id": "uuid",
  "cancelled_by": "Dr. Sarah Johnson"
}
```

### 5. `GET /api/officials/list-alerts?status={all|active|expired|cancelled}&limit=50`
Lists all alerts with filtering
```json
{
  "success": true,
  "alerts": [...],
  "count": 15
}
```

## File Changes

### Modified Files:
1. **app_local.py**
   - Replaced JSON file storage with BigQuery
   - Added `list-alerts` endpoint
   - Updated `post-alert`, `get-active-alert`, `cancel-alert` to use BigQuery
   - Added parameterized queries for security

2. **templates/officials_dashboard.html**
   - Added Alert Management table section after Quick Actions
   - Table with columns: Status, Level, Message, Issued By, Issued At, Expires, Actions
   - Filter buttons: All, Active, Expired, Cancelled
   - Empty state message

3. **static/js/officials-dashboard.js**
   - Added `loadAlerts(status)` function
   - Added `displayAlertsTable(alerts)` function
   - Added `filterAlerts(status)` function
   - Added `cancelAlertFromTable(alertId)` function
   - Added `getStatusBadge()` and `getLevelBadge()` helpers
   - Updated `sendAlert()` to reload table after posting
   - Updated `confirmCancelAlert()` to use alert_id and reload table

### New Files:
1. **bigquery_alerts_schema.sql** - BigQuery table creation script

## Troubleshooting

### Alert not appearing on main page
- Check browser console for errors
- Verify alert is "active" in BigQuery table
- Clear sessionStorage: `sessionStorage.removeItem('alertDismissed')`

### Cancel button not working
- Verify alert_id is being passed correctly
- Check BigQuery table for alert with matching ID
- Ensure name input has at least 3 characters

### Alerts table not loading
- Open browser console and check for errors
- Verify BigQuery table exists: `bq ls CrowdsourceData`
- Check network tab for 500 errors on `/api/officials/list-alerts`

### BigQuery errors
- Verify service account has BigQuery permissions
- Check table name matches: `CrowdsourceData.public_health_alerts`
- Ensure project ID is correct in queries

## Next Steps

### Recommended Enhancements:
1. **Authentication** - Replace hardcoded "Dr. Sarah Johnson" with real user session
2. **Email Notifications** - Send emails when alerts are issued/cancelled
3. **SMS Integration** - Integrate Twilio for emergency SMS alerts
4. **Map Integration** - Show alert locations on a map
5. **Alert Templates** - Pre-defined templates for common scenarios
6. **Multi-language** - Translate alerts using existing translation system
7. **Push Notifications** - Browser push notifications for new alerts
8. **Alert History Export** - Export alerts to CSV/PDF for reporting

## Testing Checklist

- [ ] Create BigQuery table successfully
- [ ] Issue a new alert from officials dashboard
- [ ] Verify alert displays on main page (index.html)
- [ ] Verify alert appears in Alert Management table
- [ ] Filter alerts by status (Active, Expired, Cancelled)
- [ ] Cancel an alert from the table
- [ ] Verify cancelled alert no longer shows on main page
- [ ] Verify cancelled alert shows with "Cancelled" badge in table
- [ ] Test auto-expiration (create 1-hour alert, wait/mock time)
- [ ] Test all alert levels (Critical, Warning, Info) display correctly
- [ ] Test dismissing alert on main page (session storage)

## Support

For issues or questions:
1. Check browser console for JavaScript errors
2. Check Flask terminal for Python errors
3. Verify BigQuery table structure matches schema
4. Review this guide's Troubleshooting section
