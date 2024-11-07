# DockerHub API Configuration
The `dockerhub` API type is used to fetch audit logs from DockerHub. It supports pagination and allows filtering logs based on a date range.

## Configuration
| Parameter Name     | Description                                                                               | Required/Optional | Default           |
|--------------------|-------------------------------------------------------------------------------------------|-------------------|-------------------|
| name               | Name of the API (custom name)                                                             | Optional          | the defined `url` |
| dockerhub_user     | DockerHub username                                                                        | Required          | -                 |
| dockerhub_token    | DockerHub personal access token or password                                               | Required          | -                 |
| url                | The request URL                                                                           | Required          | -                 |
| next_url           | URL for the next page of results (used for pagination)                                    | Optional          | -                 |
| method             | The request method (`GET` or `POST`)                                                      | Optional          | `GET`             |
| days_back_fetch    | The amount of days to fetch back in the first request. Adds a filter on `from` parameter. | Optional          | 0                 |
| scrape_interval    | Time interval to wait between runs (unit: `minutes`)                                      | Optional          | 1 (minute)        |
| additional_fields  | Additional custom fields to add to the logs before sending to logzio                      | Optional          | -                 |

## Example
You can customize the endpoints to collect data from by adding extra API configurations under `apis`. DockerHub API Docs can be found [here](https://docs.docker.com/docker-hub/api/latest/).

Example configuration:

```yaml
apis:
  - name: Dockerhub audit logs
    type: dockerhub
    dockerhub_token: <<docker_hub_password>>
    dockerhub_user: <<docker_hub_username>>
    url: https://hub.docker.com/v2/auditlogs/<<dockerhub_account>>
    next_url: https://hub.docker.com/v2/auditlogs/logzio?from={res.logs.[0].timestamp}
    method: GET
    days_back_fetch: 7
    scrape_interval: 1
    additional_fields:
      type: dockerhub-audit
      eventType: auditevents

logzio:
  url: https://<<LISTENER-HOST>>:8071
  token: <<LOG-SHIPPING-TOKEN>>
```