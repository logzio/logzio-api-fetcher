# Cisco XDR API

This module provides integration with Cisco XDR (Extended Detection and Response) APIs using OAuth 2.0 client credentials flow with Basic Authentication.

## Configuration

### Basic Configuration

```yaml
apis:
  - name: cisco_xdr_events
    type: cisco_xdr
    cisco_client_id: ${CISCO_CLIENT_ID}
    client_password: ${CISCO_CLIENT_SECRET}
    scrape_interval: 5    
    data_request:
      url: https://visibility.amp.cisco.com/iroh/iroh-event/event/search
      method: POST
      body:
        query: <xdr_query>
        limit: 1000
      response_data_path: data 
    additional_fields:
      product: cisco_xdr
      source_type: security_event

```

## Parameters

| Parameter Name | Description | Required/Optional | Default |
|----------------|-------------|-------------------|---------|
| name | Name of the API (custom name) | Optional | the defined `url` |
| cisco_client_id | Cisco Client ID | Required | - |
| client_password | Cisco Client password | Required | - |
| data_request.url | The request URL | Required | - |
| data_request.body | The request body | Optional | - |
| data_request.method | The request method (`GET` or `POST`) | Optional | `GET` |
| data_request.pagination | Pagination settings if needed | Optional | - |
| data_request.next_url | If needed to update the URL in next requests based on the last response | Optional | - |
| data_request.response_data_path | The path to the data inside the response | Optional | response root |
| additional_fields | Additional custom fields to add to the logs before sending to logzio | Optional | - |
| scrape_interval | Time interval to wait between runs (unit: `minutes`) | Optional | 1 (minute) |

## Authentication

This module uses OAuth 2.0 client credentials flow with Basic Authentication. The credentials are automatically encoded and sent in the Authorization header to the `/iroh/oauth2/token` endpoint.
