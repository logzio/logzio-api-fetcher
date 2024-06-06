# OAuth API Configuration
For structuring custom OAuth calls use type `oauth` API with the parameters below.

## Configuration
| Parameter Name  | Description                                                                                                                  | Required/Optional | Default           |
|-----------------|------------------------------------------------------------------------------------------------------------------------------|-------------------|-------------------|
| name            | Name of the API (custom name)                                                                                                | Optional          | the defined `url` |
| token_request   | Nest here any detail relevant to the request to get the bearer access token. (Options in [General API](../general/README.md) | Required          | -                 |
| data_request    | Nest here any detail relevant to the data request. (Options in [General API](../general/README.md)                           | Required          | -                 |
| scrape_interval | Time interval to wait between runs (unit: `minutes`)                                                                         | Optional          | 1 (minute)        |

## Example
```Yaml
apis:
  - name: oauth test
    type: oauth
    token_request:
      url: https://the/token/url
      headers:
        my_client_id: my_client_password
    data_request:
      url: https://the/data/url
      method: POST
      additional_fields:
        type: oauth-test
        some_field_to_add_to_logs: 1234
    scrape_interval: 8

logzio:
  url: https://listener-au.logz.io:8071
  token: <<SHIPPING_TOKEN>>
```
