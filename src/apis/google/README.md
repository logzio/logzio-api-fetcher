# Google Workspace API Configuration
Currently, the below API types are supported:
- [Google Workspace General](#google-workspace-general) (`google_workspace`)
- [Google Workspace Activities](#google-workspace-activities) (`google_activity`)


## Google Workspace General
By default `google_workspace` API type has built in pagination settings and sets the `response_data_path` to `items` field.

| Parameter Name              | Description                                                                                                                                                                | Required/Optional | Default                                                            |
|-----------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------|--------------------------------------------------------------------|
| name                        | Name of the API (custom name)                                                                                                                                              | Optional          | `Google Workspace`                                                 |
| google_ws_sa_file_name      | The name of the service account credentials file. **Required unless** `google_ws_sa_file_path` is set.                                                                     | Required*         | `""`                                                               |
| google_ws_sa_file_path      | The path to the service account credentials file. **Required unless** `google_ws_sa_file_name` is set. Use this if mounting the file to a different path than the default. | Optional*         | `./src/shared/<google_ws_sa_file_name>`                            |
| google_ws_delegated_account | The email of the user for which the application is requesting delegated access                                                                                             | Required          | -                                                                  |
| scopes                      | The OAuth 2.0 scopes that you might need to request to access Google APIs                                                                                                  | Optional          | `["https://www.googleapis.com/auth/admin.reports.audit.readonly"]` |
| data_request                | Nest here any detail relevant to the data request. (Options in [General API](../general/README.md))                                                                        | Required          | -                                                                  |
| additional_fields           | Additional custom fields to add to the logs before sending to logzio                                                                                                       | Optional          | -                                                                  |
| days_back_fetch             | The amount of days to fetch back in the first request                                                                                                                      | Optional          | 1 (day)                                                            |
| scrape_interval             | Time interval to wait between runs (unit: `minutes`)                                                                                                                       | Optional          | 1 (minute)                                                         |

## Google Workspace Activities
You can configure the Google Workspace activities endpoint using the `google_workspace` API.  
However, for easier setup, we provide a dedicated `google_activity` API type.

| Parameter Name              | Description                                                                                                                                                                                                                                         | Required/Optional | Default                                 |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------|-----------------------------------------|
| name                        | Name of the API (custom name)                                                                                                                                                                                                                       | Optional          | `Google Workspace`                      |
| google_ws_sa_file_name      | The name of the service account credentials file. **Required unless** `google_ws_sa_file_path` is set.                                                                                                                                              | Required*         | `""`                                    |
| google_ws_sa_file_path      | The path to the service account credentials file. **Required unless** `google_ws_sa_file_name` is set. Use this if mounting the file to a different path than the default.                                                                          | Optional*         | `./src/shared/<google_ws_sa_file_name>` |
| google_ws_delegated_account | The email of the user for which the application is requesting delegated access                                                                                                                                                                      | Required          | -                                       |
| application_name            | Specifies the [Google Workspace application](https://developers.google.com/workspace/admin/reports/reference/rest/v1/activities/list#applicationname) to fetch activity data from (e.g., `saml`, `user_accounts`, `login`, `admin`, `groups`, etc). | Required          | -                                       |
| user_key                    | The unique ID of the user to fetch activity data for                                                                                                                                                                                                | Optional          | `all`                                   |
| additional_fields           | Additional custom fields to add to the logs before sending to logzio                                                                                                                                                                                | Optional          | -                                       |
| days_back_fetch             | The amount of days to fetch back in the first request                                                                                                                                                                                               | Optional          | 1 (day)                                 |
| scrape_interval             | Time interval to wait between runs (unit: `minutes`)                                                                                                                                                                                                | Optional          | 1 (minute)                              |

## Example

> [!IMPORTANT]
> Save your Google service account credentials file in the path where you store your API fetcher config.
> If you prefer to mount it from a different path, use an additional `-v` flag in the docker run command.

```yaml
apis:
  - name: google workspace general example
    type: google_workspace
    google_ws_sa_file_name: credentials_file.json
    google_ws_delegated_account: user@example.com
    scopes:
      - https://www.googleapis.com/some/scope.readonly
    data_request:
      url: https://admin.googleapis.com/admin/endpoint/url
      next_url: https://admin.googleapis.com/admin/endpoint/url?startTime={res.items.[0].id.time}
    additional_fields:
      type: google_workspace
    days_back_fetch: 7
    scrape_interval: 5

  - name: google saml
    type: google_activity
    google_ws_sa_file_name: credentials_file.json
    google_ws_delegated_account: user@example.com
    application_name: saml
    additional_fields:
      type: google_activity
    days_back_fetch: 7
    scrape_interval: 5

  - name: google user accounts
    type: google_activity
    google_ws_sa_file_name: credentials_file.json
    google_ws_delegated_account: user@example.com
    application_name: user_accounts
    additional_fields:
      type: google_activity
    days_back_fetch: 7
    scrape_interval: 5

  - name: google login
    type: google_activity
    google_ws_sa_file_name: credentials_file.json
    google_ws_delegated_account: user@example.com
    application_name: login
    additional_fields:
      type: google_activity
    days_back_fetch: 7
    scrape_interval: 5

logzio:
  url: https://listener-<<LOGZIO_REGION_CODE>>.logz.io:8071  # for us-east-1 region delete url param (default) 
  token: <<SHIPPING_TOKEN>>
```
