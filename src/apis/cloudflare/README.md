# Cloudflare API Configuration
By default `cloudflare` API type has built in pagination settings and sets the `response_data_path` to `result` field.  

## Configuration
| Parameter Name          | Description                                                                                                                                 | Required/Optional | Default           |
|-------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|-------------------|-------------------|
| name                    | Name of the API (custom name)                                                                                                               | Optional          | the defined `url` |
| cloudflare_account_id   | The CloudFlare Account ID                                                                                                                   | Required          | -                 |
| cloudflare_bearer_token | The Cloudflare Bearer token                                                                                                                 | Required          | -                 |
| url                     | The request URL                                                                                                                             | Required          | -                 |
| next_url                | If needed to update the URL in next requests based on the last response. Supports using variables (see [General API](../general/README.md)) | Optional          | -                 |
| additional_fields       | Additional custom fields to add to the logs before sending to logzio                                                                        | Optional          | -                 |
| days_back_fetch         | The amount of days to fetch back in the first request. Applies a filter on `since` parameter.                                               | Optional          | -                 |
| scrape_interval         | Time interval to wait between runs (unit: `minutes`)                                                                                        | Optional          | 1 (minute)        |
| pagination_off          | True if builtin pagination should be off, False otherwise                                                                                   | Optional          | `False`           |

## Example
```Yaml
apis:
  - name: cloudflare test
    type: cloudflare
    cloudflare_account_id: <<CLOUDFLARE_ACCOUNT_ID>>
    cloudflare_bearer_token: <<CLOUDFLARE_BEARER_TOKEN>>
    url: https://api.cloudflare.com/client/v4/accounts/{account_id}/alerting/v3/history
    next_url: https://api.cloudflare.com/client/v4/accounts/{account_id}/alerting/v3/history?since={res.result.[0].sent}
    days_back_fetch: 7
    scrape_interval: 5
    additional_fields:
      type: cloudflare

logzio:
  url: https://listener-eu.logz.io:8071  # for us-east-1 region delete url param (default)
  token: <<SHIPPING_TOKEN>>
```
