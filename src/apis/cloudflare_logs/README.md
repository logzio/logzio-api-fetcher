# Cloudflare Logs Received API Configuration
The `cloudflare_logs` API type supports the Cloudflare [Logs Received](https://developers.cloudflare.com/api/resources/logs/subresources/received/methods/get/) endpoint (`/zones/{zone_id}/logs/received`).

Unlike the standard `cloudflare` type (designed for audit log endpoints with `since`-based filtering and page-based pagination), this type:

- Dynamically manages `start` and `end` time window parameters required by the `logs/received` endpoint.
- Handles NDJSON (newline-delimited JSON) response format.
- Automatically splits requests into 1-hour windows (Cloudflare API maximum).
- On first run, fetches logs going back `days_back_fetch` days. On subsequent runs, continues from where the last fetch ended.

## Configuration
| Parameter Name          | Description                                                          | Required/Optional | Default           |
|-------------------------|----------------------------------------------------------------------|-------------------|-------------------|
| name                    | Name of the API (custom name)                                        | Optional          | the defined `url` |
| cloudflare_account_id   | The Cloudflare Account ID                                            | Required          | -                 |
| cloudflare_bearer_token | The Cloudflare Bearer token                                          | Required          | -                 |
| url                     | The request URL (do not include `start`/`end` params, they are managed automatically) | Required          | -                 |
| days_back_fetch         | The amount of days to fetch back in the first request (max: 7)       | Optional          | 1 (day)           |
| additional_fields       | Additional custom fields to add to the logs before sending to logzio | Optional          | -                 |
| scrape_interval         | Time interval to wait between runs (unit: `minutes`)                 | Optional          | 1 (minute)        |

## Example
```yaml
apis:
  - name: cloudflare zone logs
    type: cloudflare_logs
    cloudflare_account_id: <<CLOUDFLARE_ACCOUNT_ID>>
    cloudflare_bearer_token: <<CLOUDFLARE_BEARER_TOKEN>>
    url: https://api.cloudflare.com/client/v4/zones/<<ZONE_ID>>/logs/received
    days_back_fetch: 7
    scrape_interval: 5
    additional_fields:
      type: cloudflare

logzio:
  url: https://listener-eu.logz.io:8071  # for us-east-1 region delete url param (default)
  token: <<SHIPPING_TOKEN>>
```

## Notes
- The Cloudflare API requires `end` to be at least 5 minutes before the current time.
- The maximum time span per request is 1 hour. If `days_back_fetch` exceeds 1 hour, the fetcher will automatically make multiple requests in 1-hour windows.
- `start` cannot exceed 7 days in the past.
- **First-run volume:** Higher `days_back_fetch` values result in many API calls on the first run (e.g., `days_back_fetch: 7` triggers ~168 sequential 1-hour window requests). Consider starting with a lower value to avoid rate limiting. After the first run, only the time since the last fetch is queried.
- Your Cloudflare API token must have `Logs Read` or `Logs Write` permission.
