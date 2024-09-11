# Azure API Configuration
Currently, the below API types are supported:
- [Azure General](#azure-general) (`azure_general`)
- [Azure Graph](#azure-graph) (`azure_graph`)
- [Azure Mail Reports](#azure-mail-reports) (`azure_mail_reports`)

Configuration [example here](#example).


## Azure General
Below fields are relevant for **all Azure API types**

| Parameter Name        | Description                                                                                         | Required/Optional | Default                                                  |
|-----------------------|-----------------------------------------------------------------------------------------------------|-------------------|----------------------------------------------------------|
| name                  | Name of the API (custom name)                                                                       | Optional          | `azure api`                                              |
| azure_ad_tenant_id    | The Azure AD Tenant id                                                                              | Required          | -                                                        |
| azure_ad_client_id    | The Azure AD Client id                                                                              | Required          | -                                                        |
| azure_ad_secret_value | The Azure AD Secret value                                                                           | Required          | -                                                        |
| data_request          | Nest here any detail relevant to the data request. (Options in [General API](../general/README.md)) | Required          | -                                                        |
| scope                 | The specific permissions an application is requesting during a token request.                       | Optional          | Azure graph scope `https://graph.microsoft.com/.default` |
| days_back_fetch       | The amount of days to fetch back in the first request                                               | Optional          | 1 (day)                                                  |
| scrape_interval       | Time interval to wait between runs (unit: `minutes`)                                                | Optional          | 1 (minute)                                               |

## Azure Graph
By default `azure_graph` API type has built in pagination settings and sets the `response_data_path` to `value` field.  
The below fields are relevant **in addition** to the required ones listed under Azure General.

| Parameter Name                 | Description                                                          | Required/Optional | Default           |
|--------------------------------|----------------------------------------------------------------------|-------------------|-------------------|
| date_filter_key                | The name of key to use for the date filter in the request URL params | Optional          | `createdDateTime` |
| data_request.url               | The request URL                                                      | Required          | -                 |
| data_request.additional_fields | Additional custom fields to add to the logs before sending to logzio | Optional          | -                 |

## Azure Mail Reports
By default `azure_mail_reports` API type has built in pagination settings and sets the `response_data_path` to `d.results` field.  
The below fields are relevant **in addition** to the required ones listed under Azure General.

| Parameter Name                 | Description                                                                 | Required/Optional | Default     |
|--------------------------------|-----------------------------------------------------------------------------|-------------------|-------------|
| start_date_filter_key          | The name of key to use for the start date filter in the request URL params. | Optional          | `startDate` |
| end_date_filter_key            | The name of key to use for the end date filter in the request URL params.   | Optional          | `EndDate`   |
| data_request.url               | The request URL                                                             | Required          | -           |
| data_request.additional_fields | Additional custom fields to add to the logs before sending to logzio        | Optional          | -           |

## Example

```Yaml
apis:
  - name: azure graph example
    type: azure_graph
    azure_ad_tenant_id: <<AZURE_AD_TENANT_ID>>
    azure_ad_client_id: <<AZURE_AD_CLIENT_ID>>
    azure_ad_secret_value: <<AZURE_AD_SECRET_VALUE>>
    data_request:
      url: https://graph.microsoft.com/v1.0/auditLogs/signIns
      additional_fields:
        type: azure_graph
        field_to_add_to_my_logs: 123
    scrape_interval: 1
    days_back_fetch: 30

  - name: mail reports example
    type: azure_mail_reports
    azure_ad_tenant_id: <<AZURE_AD_TENANT_ID>>
    azure_ad_client_id: <<AZURE_AD_CLIENT_ID>>
    azure_ad_secret_value: <<AZURE_AD_SECRET_VALUE>>
    data_request:
      url: https://reports.office365.com/ecp/reportingwebservice/reporting.svc/MessageTrace
      additional_fields:
        type: azure_mail_reports
    scrape_interval: 60  # for mail reports we suggest no less than 60 minutes
    days_back_fetch: 8  # for mail reports we suggest up to 8 days

  - name: azure general example
    type: azure_general
    azure_ad_tenant_id: <<AZURE_AD_TENANT_ID>>
    azure_ad_client_id: <<AZURE_AD_CLIENT_ID>>
    azure_ad_secret_value: <<AZURE_AD_SECRET_VALUE>>
    data_request:
      url: ...
    scrape_interval: 30
    days_back_fetch: 30

logzio:
  url: https://listener-eu.logz.io:8071  # for us-east-1 region delete url param (default) 
  token: <<SHIPPING_TOKEN>>
```
