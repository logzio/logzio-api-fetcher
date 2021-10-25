# Ship Auth/OAuth Api's data to Logz.io

Every time interval, fetches data of each api in the configuration and sends it to Logz.io.
Every api has set of settings that define it.


## Getting Started

### Pull Docker Image

Download the logzio-api-fetcher image:

```shell
docker pull logzio/logzio-api-fetcher
```

### Mount a Host Directory as a Data Volume

Create a local directory and move into it:

```shell
mkdir logzio-api-fetcher
cd logzio-api-fetcher
```

### Configuration

Create and edit the configuration file and name it `config.yaml`. There are 3 sections of the configuration:

#### logzio

| Parameter Name | Description | Required/Optional | Default |
| --- | --- | ---| ---|
| url | The Logz.io Listener URL for your region with port 8071. For example: https://listener.logz.io:8071 | Required | - |
| token | Your Logz.io log shipping token securely directs the data to your Logz.io account. | Required | - |

#### auth_apis

Supported types:

- cisco_secure_x
- general

The following parameters are for every type:

| Parameter Name | Description | Required/Optional | Default |
| --- | --- | ---| ---|
| type | The type of the auth api. Currently we support the following types: cisco_secure_x, general. | Required | - |
| name | The name of the auth api. Please make names unique. | Required | - |
| credentials.id | The auth api credentials id. | Required | - |
| credentials.key | The auth api credentials key. | Required | - |
| settings.time_interval | The auth api time interval between runs. | Required | - |
| settings.days_back_fetch | The max days back to fetch from the auth api. | Optional | 14 (days) |
| filters | Pairs of key and value of parameters that can be added to the auth api url. Make sure the keys and values are valid for the auth api. | Optional | - |
| custom_fields | Pairs of key and value that will be added to each data and be sent to Logz.io. | Optional | - |

The following parameters are for general type only:

| Parameter Name | Description | Required/Optional | Default |
| --- | --- | ---| ---|
| start_date_name| The start date parameter name of the auth api url. | Required | - |
| http_request.method | The HTTP method. Can be GET or POST. | Required | - |
| http_request.url | The auth api url. Make sure the url is without `?` at the end. | Required | - |
| http_request.headers | Pairs of key and value the represents the headers of the HTTP request. | Optional | - |
| http_request.body | The body of the HTTP request. Will be added to HTTP POST requests only. | Optional | - |
| json_paths.next_url | The json path to the next url value inside the response of the auth api. | Required | - |
| json_paths.data | The json path to the data value inside the response of the auth api. | Required | - |
| json_paths.data_date | The json path to the data's date value inside the response of the auth api. | Required | - |

#### oauth_apis
The following configuration uses OAuth 2.0 flow.

Supported types:

- azure_graph
- general

The following parameters are for every type:

| Parameter Name | Description | Required/Optional | Default |
| --- | --- | ---| ---|
| type | The type of the auth api. Currently we support the following types: cisco_secure_x, general. | Required | - |
| name | The name of the auth api. Please make names unique. | Required | - |
| credentials.id | The auth api credentials id. | Required | - |
| credentials.key | The auth api credentials key. | Required | - |
| http_request.method | The HTTP method. Can be GET or POST. | Required | - |
| http_request.url | The oauth api url. Make sure the url is without `?` at the end. | Required | - |
| http_request.headers | Pairs of key and value the represents the headers of the HTTP request. | Optional | - |
| http_request.body | The body of the HTTP request. Will be added to HTTP POST requests only. | Optional | - |
| token_http_request.method | The HTTP method. Can be GET or POST. | Required | - |
| token_http_request.url | The oauth api token request  url. Make sure the url is without `?` at the end. | Required | - |
| token_http_request.headers | Pairs of key and value the represents the headers of the HTTP request. | Optional | - |
| token_http_request.body | The body of the HTTP request. Will be added to HTTP POST requests only. | Optional | - |
| json_paths.next_url | The json path to the next url value inside the response of the auth api. | Required/Optional for Azure | - |
| json_paths.data | The json path to the data value inside the response of the auth api. | Required/Optional for Azure | - |
| json_paths.data_date | The json path to the data's date value inside the response of the auth api. | Required | - |
| settings.time_interval | The auth api time interval between runs. | Required | - |
| settings.days_back_fetch | The max days back to fetch from the auth api. | Optional | 14 (days) |
| filters | Pairs of key and value of parameters that can be added to the auth api url. Make sure the keys and values are valid for the auth api. | Optional | - |
| custom_fields | Pairs of key and value that will be added to each data and be sent to Logz.io. | Optional | - |
| start_date_name| The start date parameter name of the oauth api url. (Same as json_paths.data_date in most cases)| Required | - |

### Example

Auth apis and Oauth apis can be combined in the same config file. Separated for readability.

#### Auth api config:

```yaml
logzio:
  url: https://listener.logz.io:8071
  token: 123456789a

auth_apis:
  - type: cisco_secure_x
    name: cisco
    credentials:
      id: <<API_CREDENTIALS_ID>>
      key: <<API_CREDENTIALS_KEY>>
    settings:
      time_interval: 5
      days_back_fetch: 7
    filters:
      event_type%5B%5D: '1090519054'
      start_date: 2021-10-05T10%3A10%3A10%2B00%3A00
    custom_fields:
      type: cisco
      level: high
  - type: general
    name: cisco general
    credentials:
      id: <<API_CREDENTIALS_ID>>
      key: <<API_CREDENTIALS_KEY>>
    settings:
      time_interval: 2
      days_back_fetch: 5
    start_date_name: start_date
    http_request:
      method: GET
      url: https://api.amp.cisco.com/v1/events
    json_paths:
      next_url: metadata.links.next
      data: data
      data_date: date
    filters:
      event_type%5B%5D: '1090519054'
```

#### OAuth Api config:

```yaml
logzio:
  url: https://listener.logz.io:8071
  token: 123456789a

oauth_apis:
  - type: azure_graph
    name: azure_test
    credentials:
      id: <<AZURE_AD_SECRET_ID>>
      key: <<AZURE_AD_SECRET_VALUE>>
    token_http_request:
      url: https://login.microsoftonline.com/<<AZURE_AD_TENANT_ID>>/oauth2/v2.0/token
      body: client_id=<<AZURE_AD_CLIENT_ID>>
        &scope=https://graph.microsoft.com/.default
        &client_secret=<<AZURE_AD_SECRET_VALUE>>
        &grant_type=client_credentials
      headers:
      method: POST
    data_http_request:
      url: https://graph.microsoft.com/v1.0/auditLogs/signIns
      headers:
    json_paths:
      data_date: createdDateTime
      next_url:
      data:
    settings:
      time_interval: 1
      days_back_fetch: 30
  - type: general
    name: general_test
    credentials:
      id: aaaa-bbbb-cccc
      key: abcabcabc
    token_http_request:
      url: https://login.microsoftonline.com/abcd-efgh-abcd-efgh/oauth2/v2.0/token
      body: client_id=aaaa-bbbb-cccc
            &scope=https://graph.microsoft.com/.default
            &client_secret=abcabcabc
            &grant_type=client_credentials
      headers:
      method: POST
    data_http_request:
      url: https://graph.microsoft.com/v1.0/auditLogs/directoryAudits
      headers:
    json_paths:
      data_date: activityDateTime
      data: value
      next_url: '@odata.nextLink'
    settings:
      time_interval: 1
    start_date_name: activityDateTime

```

### Create Last Start Dates Text File

Create an empty text file named last_start_dates.txt in the same directory as the config file:

```shell
$ touch last_start_dates.txt
```

### Run The Docker Container

```shell
docker run --name logzio-api-fetcher \
-v "$(pwd)":/app/src/shared \
logzio/logzio-api-fetcher
```

## Stop Docker Container

When you stop the container, the code will run until completion of the iteration. To make sure it will finish the iteration on time, 
please give it a grace period of 30 seconds when you run the docker stop command:

```shell
docker stop -t 30 logzio-api-fetcher
```

## Last Start Dates Text File

After every successful iteration of each api, the last start date of the next iteration will be written to a file named `last_start_dates.txt`.
Each line starts with the api name and ends with the last start date.

You can find the file inside your mounted host directory that you created.

If you stopped the container, you can continue from the exact place you stopped, by adding the date to the api filters in the configuration.






