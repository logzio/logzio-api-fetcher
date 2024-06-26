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
- [General API](./src/apis/general/README.md) Configuration Options
- [General OAuth](./src/apis/oauth/README.md) Configuration Options
- [Azure Graph](./src/apis/azure/README.MD/#azure-graph) Configuration Options
- [Azure Mail Reports](./src/apis/azure/README.MD/#azure-mail-reports) Configuration Options
- [Azure General](./src/apis/azure/README.MD/#azure-general) Configuration Options
- [Cloudflare](./src/apis/cloudflare/README.md) Configuration Options

And your logzio output under `logzio`:

| Parameter Name | Description                 | Required/Optional | Default                         |
|----------------|-----------------------------|-------------------|---------------------------------|
| url            | The logzio Listener address | Optional          | `https://listener.logz.io:8071` |
| token          | The logzio shipping token   | Required          | -                               |

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
