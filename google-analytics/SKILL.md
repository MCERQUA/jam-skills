---
name: google-analytics
description: "Query Google Analytics 4 data — real traffic, sessions, users, conversions, page performance, traffic sources, realtime. Use when user asks about website analytics, real traffic numbers, visitor behavior, or conversion data."
metadata:
  version: 1.0.0
  openclaw:
    requires:
      env: ["GOOGLE_APPLICATION_CREDENTIALS"]
---

# Google Analytics 4 — Real Traffic Data

Access real website analytics data from Google Analytics 4. This gives you actual visitor counts, session data, page performance, traffic sources, and conversion metrics — not estimates.

## When to Use

Activate when the user asks about:
- Real website traffic ("how many visitors did we get?")
- Page performance ("which pages get the most views?")
- Traffic sources ("where is our traffic coming from?")
- User behavior ("what's our bounce rate?")
- Conversions or goals
- Realtime visitors ("who's on the site right now?")
- Comparing GA data vs SEO estimated traffic

## API Access

The Google Analytics MCP server provides 6 tools. Use them via the MCP integration.

### Tools Available

| Tool | Purpose | Cost |
|------|---------|------|
| `get_account_summaries` | List all GA4 accounts/properties | Free |
| `get_property_details` | Property config (timezone, currency, industry) | Free |
| `run_report` | Standard report — any dimensions/metrics/dates | Free |
| `run_realtime_report` | Live data from last 30 minutes | Free |
| `get_custom_dimensions_and_metrics` | Custom definitions on the property | Free |
| `list_google_ads_links` | Linked Google Ads accounts | Free |

All GA4 API calls are **free** (no per-query cost). Quota: 10,000 requests/property/day.

### Common Dimensions
`date`, `pagePath`, `pageTitle`, `sessionDefaultChannelGroup`, `sessionSource`, `sessionMedium`, `country`, `city`, `deviceCategory`, `browser`, `eventName`, `landingPage`

### Common Metrics
`sessions`, `totalUsers`, `newUsers`, `screenPageViews`, `averageSessionDuration`, `bounceRate`, `conversions`, `eventCount`, `engagedSessions`, `engagementRate`

## Example Queries

### Monthly traffic summary
```
run_report:
  property: properties/123456789
  dimensions: [date]
  metrics: [sessions, totalUsers, screenPageViews, bounceRate]
  dateRange: 30daysAgo to today
```

### Top 20 pages by views
```
run_report:
  property: properties/123456789
  dimensions: [pagePath, pageTitle]
  metrics: [screenPageViews, averageSessionDuration, bounceRate]
  dateRange: 30daysAgo to today
  orderBy: screenPageViews desc
  limit: 20
```

### Traffic by source/medium
```
run_report:
  property: properties/123456789
  dimensions: [sessionSource, sessionMedium]
  metrics: [sessions, totalUsers, conversions]
  dateRange: 30daysAgo to today
```

### Organic search traffic only
```
run_report:
  property: properties/123456789
  dimensions: [date, landingPage]
  metrics: [sessions, totalUsers]
  dateRange: 30daysAgo to today
  dimensionFilter: sessionDefaultChannelGroup == "Organic Search"
```

## Integration with SEO Platform

GA4 real traffic data complements DataForSEO estimated traffic:
- **DataForSEO** `bulk_traffic_estimation` → estimated organic traffic based on rankings
- **GA4** `run_report` → actual sessions, actual users, actual pageviews

Comparing the two reveals:
- How accurate the SEO traffic estimates are
- Non-organic traffic sources (direct, social, referral, paid)
- Actual conversion rates that SEO estimates can't provide
- Page-level performance vs keyword-level estimates

## Authentication

Requires a Google service account JSON key. Set `GOOGLE_APPLICATION_CREDENTIALS` env var to the key path.

The service account email must be added as **Viewer** on the GA4 property (Admin → Property Access Management).

Setup: `bash ~/scripts/setup-google-analytics-auth.sh`
