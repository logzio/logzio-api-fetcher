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
You can customize the endpoints to collect data from by adding extra API configurations under `apis`. 1Password API Docs can be found [here](https://developer.1password.com/docs/connect/connect-api-reference/).

Example configuration:

```yaml
apis:
  - name: 1Password Audit Events
    type: 1password
    onepassword_bearer_token: <<1PASSWORD_BEARER_TOKEN>>
    url: https://events.1password.com/api/v1/auditevents
    method: POST
    days_back_fetch: 7
    scrape_interval: 5    
    additional_fields:
      type: 1password
      eventType: auditevents

  - name: 1Password Item Usages
    type: 1password
    onepassword_bearer_token: <<1PASSWORD_BEARER_TOKEN>>
    url: https://events.1password.com/api/v1/itemusages
    method: POST
    days_back_fetch: 7
    scrape_interval: 5
    additional_fields:
      type: 1password
      eventType: itemusages

  - name: 1Password Sign In Attempts
    type: 1password
    onepassword_bearer_token: <<1PASSWORD_BEARER_TOKEN>>
    url: https://events.1password.com/api/v1/signinattempts
    method: POST
    days_back_fetch: 7
    scrape_interval: 5
    additional_fields:
      type: 1password
      eventType: signinattempts

logzio:
  url: https://<<LISTENER-HOST>>:8071
  token: <<LOG-SHIPPING-TOKEN>>
```