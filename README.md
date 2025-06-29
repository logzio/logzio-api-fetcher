# Fetcher to send API data to Logz.io
The API Fetcher offers way to configure fetching data from APIs every defined scrape interval.

## Setup

### Pull Docker Image
Download the logzio-api-fetcher image:

```shell
docker pull logzio/logzio-api-fetcher
```

### Configuration
Create a local config file `config.yaml`.  
Configure your API inputs under `apis`. For every API, mention the input type under `type` field:
<details>
  <summary>
    <span><a href="./src/apis/general/README.md">General API</a></span>
  </summary>

For structuring custom API calls use type `general` API with the parameters below.

## Configuration Options
| Parameter Name     | Description                                                                                                                           | Required/Optional | Default                     |
|--------------------|---------------------------------------------------------------------------------------------------------------------------------------|-------------------|-----------------------------|
| name               | Name of the API (custom name)                                                                                                         | Optional          | the defined `url`           |
| url                | The request URL                                                                                                                       | Required          | -                           |
| headers            | The request Headers                                                                                                                   | Optional          | `{}`                        |
| body               | The request body                                                                                                                      | Optional          | -                           |
| method             | The request method (`GET` or `POST`)                                                                                                  | Optional          | `GET`                       |
| pagination         | Pagination settings if needed (see [options below](#pagination-configuration-options))                                                | Optional          | -                           |
| next_url           | If needed to update the URL in the next request based on the last response. Supports using variables ([see below](#using-variables))  | Optional          | -                           |
| next_body          | If needed to update the body in the next request based on the last response. Supports using variables ([see below](#using-variables)) | Optional          | -                           |
| response_data_path | The path to the data inside the response                                                                                              | Optional          | response root               |
| additional_fields  | Additional custom fields to add to the logs before sending to logzio                                                                  | Optional          | Add `type` as `api-fetcher` |
| scrape_interval    | Time interval to wait between runs (unit: `minutes`)                                                                                  | Optional          | 1 (minute)                  |

## Pagination Configuration Options
If needed, you can configure pagination.

| Parameter Name   | Description                                                                                                                                      | Required/Optional                                  | Default |
|------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------|---------|
| type             | The pagination type (`url`, `body` or `headers`)                                                                                                 | Required                                           | -       |
| url_format       | If pagination type is `url`, configure the URL format used for the pagination. Supports using variables ([see below](#using-variables)).         | Required if pagination type is `url`               | -       |
| update_first_url | `True` or `False`; If pagination type is `url`, and it's required to append new params to the first request URL and not reset it completely.     | Optional if pagination type is `url`               | False   |
| headers_format   | If pagination type is `headers`, configure the headers format used for the pagination. Supports using variables ([see below](#using-variables)). | Required if pagination type is `headers`           | -       |
| body_format      | If pagination type is `body`, configure the body format used for the pagination. Supports using variables ([see below](#using-variables)).       | Required if pagination type is `body`              | -       |
| stop_indication  | When should the pagination end based on the response. (see [options below](#pagination-stop-indication-configuration)).                          | Optional (if not defined will stop on `max_calls`) | -       |
| max_calls        | Max calls that the pagination can make. (Supports up to 1000)                                                                                    | Optional                                           | 1000    |

## Pagination Stop Indication Configuration
| Parameter Name | Description                                                                             | Required/Optional                               | Default |
|----------------|-----------------------------------------------------------------------------------------|-------------------------------------------------|---------|
| field          | The name of the field in the response body, to search the stop indication at            | Required                                        | -       |
| condition      | The stop condition (`empty`, `equals` or `contains`)                                    | Required                                        | -       |
| value          | If condition is `equals` or `contains`, the value of the `field` that we should stop at | Required if condition is `equals` or `contains` | -       |

## Using Variables
Using variables allows taking values from the response of the first request, to structure the request after it.  
Mathematical operations `+` and `-` are supported, in order to add or reduce a number from the variable value.  

Use case examples for variable usage:
1. Update a date filter at every call
2. Update a page number in pagination

To use variables:
- Wrap the variable name in curly brackets
- Provide the full path to that variable in the response
- Add `res.` prefix to the path.

Example: Say this is my response:
```json
{
  "field": "value",
  "another_field": {
    "nested": 123
  },
  "num_arr": [1, 2, 3],
  "obj_arr": [
    {
      "field2": 345
    },
    {
      "field2": 567
    }
  ]
}
```
Paths to fields values are structured like so:
- `{res.field}` = `"value"`
- `{res.another_field.nested}` = `123`
- `{res.num_arr.[2]}` = `3`
- `{res.obj_arr.[0].field2}` = `345`

Using the fields values in the `next_url` for example like so:
```Yaml
next_url: https://logz.io/{res.field}/{res.obj_arr[0].field2}
```
Would update the URL at every call to have the value of the given fields from the response, in our example the url for the next call would be:
```
https://logz.io/value/345
```
And in the call after it, it would update again according to the response and the `next_url` structure, and so on.


</details>
<details>
  <summary>
    <span><a href="./src/apis/oauth/README.md">OAuth API</a></span>
  </summary>

For structuring custom OAuth calls use type `oauth` API with the parameters below.

## Configuration Options
| Parameter Name    | Description                                                                                                                           | Required/Optional | Default                     |
|-------------------|---------------------------------------------------------------------------------------------------------------------------------------|-------------------|-----------------------------|
| name              | Name of the API (custom name)                                                                                                         | Optional          | the defined `url`           |
| token_request     | Nest here any detail relevant to the request to get the bearer access token. (Options in [General API](./src/apis/general/README.md)) | Required          | -                           |
| data_request      | Nest here any detail relevant to the data request. (Options in [General API](./src/apis/general/README.md))                           | Required          | -                           |
| scrape_interval   | Time interval to wait between runs (unit: `minutes`)                                                                                  | Optional          | 1 (minute)                  |
| additional_fields | Additional custom fields to add to the logs before sending to logzio                                                                  | Optional          | Add `type` as `api-fetcher` |

</details>
<details>
  <summary>
    <span><a href="./src/apis/azure/README.MD/#azure-graph">Azure Graph</a></span>
  </summary>

For Azure Graph, use type `azure_graph` with the below parameters.

## Configuration Options
| Parameter Name        | Description                                                          | Required/Optional | Default           |
|-----------------------|----------------------------------------------------------------------|-------------------|-------------------|
| name                  | Name of the API (custom name)                                        | Optional          | `azure api`       |
| azure_ad_tenant_id    | The Azure AD Tenant id                                               | Required          | -                 |
| azure_ad_client_id    | The Azure AD Client id                                               | Required          | -                 |
| azure_ad_secret_value | The Azure AD Secret value                                            | Required          | -                 |
| date_filter_key       | The name of key to use for the date filter in the request URL params | Optional          | `createdDateTime` |
| data_request.url      | The request URL                                                      | Required          | -                 |
| additional_fields     | Additional custom fields to add to the logs before sending to logzio | Optional          | -                 |
| days_back_fetch       | The amount of days to fetch back in the first request                | Optional          | 1 (day)           |
| scrape_interval       | Time interval to wait between runs (unit: `minutes`)                 | Optional          | 1 (minute)        |

</details>

<details>
  <summary>
    <span><a href="./src/apis/azure/README.MD/#azure-mail-reports">Azure Mail Reports</a></span>
  </summary>

For Azure Mail Reports, use type `azure_mail_reports` with the below parameters.

## Configuration Options
| Parameter Name        | Description                                                                 | Required/Optional | Default     |
|-----------------------|-----------------------------------------------------------------------------|-------------------|-------------|
| name                  | Name of the API (custom name)                                               | Optional          | `azure api` |
| azure_ad_tenant_id    | The Azure AD Tenant id                                                      | Required          | -           |
| azure_ad_client_id    | The Azure AD Client id                                                      | Required          | -           |
| azure_ad_secret_value | The Azure AD Secret value                                                   | Required          | -           |
| start_date_filter_key | The name of key to use for the start date filter in the request URL params. | Optional          | `startDate` |
| end_date_filter_key   | The name of key to use for the end date filter in the request URL params.   | Optional          | `EndDate`   |
| data_request.url      | The request URL                                                             | Required          | -           |
| additional_fields     | Additional custom fields to add to the logs before sending to logzio        | Optional          | -           |
| days_back_fetch       | The amount of days to fetch back in the first request                       | Optional          | 1 (day)     |
| scrape_interval       | Time interval to wait between runs (unit: `minutes`)                        | Optional          | 1 (minute)  |


</details>
<details>
  <summary>
    <span><a href="./src/apis/azure/README.MD/#azure-general">Azure General API</a></span>
  </summary>

For structuring custom general Azure API calls use type `azure_general` API with the parameters below.

## Configuration Options
| Parameter Name        | Description                                                                                                 | Required/Optional | Default     |
|-----------------------|-------------------------------------------------------------------------------------------------------------|-------------------|-------------|
| name                  | Name of the API (custom name)                                                                               | Optional          | `azure api` |
| azure_ad_tenant_id    | The Azure AD Tenant id                                                                                      | Required          | -           |
| azure_ad_client_id    | The Azure AD Client id                                                                                      | Required          | -           |
| azure_ad_secret_value | The Azure AD Secret value                                                                                   | Required          | -           |
| data_request          | Nest here any detail relevant to the data request. (Options in [General API](./src/apis/general/README.md)) | Required          | -           |
| additional_fields     | Additional custom fields to add to the logs before sending to logzio                                        | Optional          | -           |
| days_back_fetch       | The amount of days to fetch back in the first request                                                       | Optional          | 1 (day)     |
| scrape_interval       | Time interval to wait between runs (unit: `minutes`)                                                        | Optional          | 1 (minute)  |

</details>
<details>
  <summary>
    <span><a href="./src/apis/cloudflare/README.md">Cloudflare</a></span>
  </summary>

For Cloudflare API, use type as `cloudflare`.  
By default `cloudflare` API type:

- has built in pagination settings
- sets the `response_data_path` to `result` field.

## Configuration Options
| Parameter Name          | Description                                                                                                                                | Required/Optional | Default           |
|-------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|-------------------|-------------------|
| name                    | Name of the API (custom name)                                                                                                              | Optional          | the defined `url` |
| cloudflare_account_id   | The CloudFlare Account ID                                                                                                                  | Required          | -                 |
| cloudflare_bearer_token | The Cloudflare Bearer token                                                                                                                | Required          | -                 |
| url                     | The request URL                                                                                                                            | Required          | -                 |
| next_url                | If needed to update the URL in next requests based on the last response. Supports using variables (see [General API](./general/README.md)) | Optional          | -                 |
| additional_fields       | Additional custom fields to add to the logs before sending to logzio                                                                       | Optional          | -                 |
| scrape_interval         | Time interval to wait between runs (unit: `minutes`)                                                                                       | Optional          | 1 (minute)        |
| pagination_off          | True if builtin pagination should be off, False otherwise                                                                                  | Optional          | `False`           |

</details>
<details>
  <summary>
    <span><a href="./src/apis/onepassword/README.md">1Password</a></span>
  </summary>

By default `1password` API type has built in pagination settings and sets the `response_data_path` to `items` field.

## Configuration Options
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

</details>

<details>
  <summary>
    <span><a href="./src/apis/dockerhub/README.md">Dockerhub</a></span>
  </summary>

For dockerhub audit logs, use type `dockerhub` with the below parameters.

## Configuration Options
| Parameter Name         | Description                                                                           | Required/Optional | Default           |
|------------------------|---------------------------------------------------------------------------------------|-------------------|-------------------|
| name                   | Name of the API (custom name)                                                         | Optional          | the defined `url` |
| dockerhub_user         | DockerHub username                                                                    | Required          | -                 |
| dockerhub_token        | DockerHub personal access token or password                                           | Required          | -                 |
| url                    | The request URL                                                                       | Required          | -                 |
| next_url               | URL for the next page of results (used for pagination)                                | Optional          | -                 |
| method                 | The request method (`GET` or `POST`)                                                  | Optional          | `GET`             |
| days_back_fetch        | Number of days to fetch back in the first request. Adds a filter on `from` parameter. | Optional          | -1                |
| refresh_token_interval | Interval in minutes to refresh the JWT token                                          | Optional          | 30 (minute)       |
| scrape_interval        | Time interval to wait between runs (unit: `minutes`)                                  | Optional          | 1 (minute)        |
| additional_fields      | Additional custom fields to add to the logs before sending to logzio                  | Optional          | -                 |


</details>
<details>
  <summary>
    <span><a href="./src/apis/google/README.md#google-workspace-activities">Google Workspace Activity</a></span>
  </summary>

For Google Workspace Activity, use type `google_activity` with the below parameters.


## Configuration Options
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


</details>
<details>
  <summary>
    <span><a href="./src/apis/google/README.md#google-workspace-general">Google Workspace General API</a></span>
  </summary>

For structuring custom general Google Workspace API calls use type `google_workspace` API with the parameters below.

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

</details>


And your logzio output under `logzio`:

| Parameter Name | Description                 | Required/Optional | Default                         |
|----------------|-----------------------------|-------------------|---------------------------------|
| url            | The logzio Listener address | Optional          | `https://listener.logz.io:8071` |
| token          | The logzio shipping token   | Required          | -                               |

> [!NOTE]
> To configure multiple outputs, please see [multiple outputs example](./src/output/README.md#multiple-outputs)

#### Example
```Yaml
apis:
  - name: random
    type: general
    additional_fields:
      type: random
    ...
  - name: another api
    type: oauth
    additional_fields:
      type: oauth-api
    ...
logzio:
  url: https://listener-ca.logz.io:8071  # for us-east-1 region delete url param (default)
  token: <<SHIPPING_TOKEN>>
```

### Run The Docker Container
In the path where you saved your `config.yaml`, run:
```shell
docker run --name logzio-api-fetcher \
-v "$(pwd)":/app/src/shared \
logzio/logzio-api-fetcher 
```

#### Change logging level
The default logging level is `INFO`. To change it, add `--level` flag to the command:
```shell
docker run --name logzio-api-fetcher \
-v "$(pwd)":/app/src/shared \
logzio/logzio-api-fetcher \
--level DEBUG
```
Available Options: `INFO`, `WARN`, `ERROR`, `DEBUG`

## Stopping the container
When you stop the container, the code will run until completion of the iteration. To make sure it will finish the iteration on time, 
please give it a grace period of 30 seconds when you run the docker stop command:

```shell
docker stop -t 30 logzio-api-fetcher
```

## Changelog:
- **2.0.1**:
  - Suppoort for cisco xdr
- **2.0.0**:
  - Add Google Workspace Support
  - Add option to configure multiple Logz.io outputs.
  - Bug fix for Cloudflare `next_url` to be optional.
  - **Note:** No breaking changes, major version bump is made to align with semantic versioning in future releases.
- **0.3.1**:
  - Handle internal logger configuration in memory instead of disk
- **0.3.0**:
  - Add support for dockerhub audit logs
- **0.2.2**:
  - Resolve Azure mail reports bug
- **0.2.1**:
  - Add 1Password Support
  - Add `next_body` support to allow more customization in general settings
  - Support integers and boolean as values in pagination 'equals' stop condition
- **0.2.0**:
  - **Breaking changes!!**
    - Deprecate configuration fields:
      - `credentials`, `start_date_name`, `end_date_name`, `json_paths`, `settings.days_back_fetch`
      - `settings.time_interval` >> `scrape_interval`
      - OAuth Changes:
        - `token_http_request` >> `token_request`
        - `data_http_request` >> `data_request`
      - All APIs now nested in the config under `apis` and supported types are:
        - `general`, `oauth`, `azure_general`, `azure_graph`, `azure_mail_reports`, `cloudflare`.
    - Upgrade General API settings to allow more customization 
      - Adding Authorization Header is required, if needed, due to `credentials` field deprecation.
      - Adding `Content-Type` may be required based on the API
    - Deprecate Cisco SecureX 
  - **New Features!!**
    - Add Pagination support
    - Add variables support in `next_url` and pagination settings
      - Supports `+` and `-` mathematical operations on values
      - Supports arrays
    - Upgrade python version `3.9` >> `3.12`
    - Add Cloudflare Support
    - Add option to control logging level with `--level` flag.
- **0.1.3**:
  - Support another date format for `azure_graph`.
- **0.1.2**:
  - Support another date format for `security_alerts`.
- **0.1.1**:
  - Bug fix for `security_alerts` task fails on second cycle.
- **0.1.0**:
  - Added `azure_mail_reports` type.
- **0.0.6**:
  - Improved documentation.
  - Added error log.
- **0.0.5**:
  - Bug fix for `azure_graph` task fails on second cycle.
  - Changed start date filter mechanics for auth_api.
- **0.0.4**:
  - Bug fix for `azure_graph` task fails when trying to get start date from file.
