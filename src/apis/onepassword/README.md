# 1Password API Configuration
By default `1password` API type has built in pagination settings and sets the `response_data_path` to `items` field.

## Configuration
| Parameter Name           | Description                                                                                                  | Required/Optional | Default           |
|--------------------------|--------------------------------------------------------------------------------------------------------------|-------------------|-------------------|
| name                     | Name of the API (custom name)                                                                                | Optional          | the defined `url` |
| onepassword_bearer_token | The 1Password Bearer token                                                                                   | Required          | -                 |
| url                      | The request URL                                                                                              | Required          | -                 |
| method                   | The request method (`GET` or `POST`)                                                                         | Optional          | `GET`             |
| additional_fields        | Additional custom fields to add to the logs before sending to logzio                                         | Optional          | -                 |
| days_back_fetch          | The amount of days to fetch back in the first request. Applies a filter on 1password `start_time` parameter. | Optional          | -                 |
| scrape_interval          | Time interval to wait between runs (unit: `minutes`)                                                         | Optional          | 1 (minute)        |
| onepassword_limit        | 1Password limit for number of events to return in a single request (allowed range: 100 to 1000)              | Optional          | 100               |
| pagination_off           | True if builtin pagination should be off, False otherwise                                                    | Optional          | `False`           |


## Example
```Yaml
apis:
  - name: 1Password example
    type: 1password
    onepassword_bearer_token: <<1PASSWORD_BEARER_TOKEN>>
    url: https://events.1password.com/api/v1/auditevents
    method: POST
    days_back_fetch: 3
    scrape_interval: 5
    additional_fields:
      type: 1password
    onepassword_limit: 200

logzio:
  url: https://listener-eu.logz.io:8071  # for us-east-1 region delete url param (default)
  token: <<SHIPPING_TOKEN>>
```
