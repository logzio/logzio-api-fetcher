# General API Configuration
For structuring custom API calls use type `general` API with the parameters below.
- [Configuration](#configuration)
- [Pagination Configuration](#pagination-configuration-options)
- [Example](#example)

## Configuration
| Parameter Name     | Description                                                                                                                       | Required/Optional | Default                     |
|--------------------|-----------------------------------------------------------------------------------------------------------------------------------|-------------------|-----------------------------|
| name               | Name of the API (custom name)                                                                                                     | Optional          | the defined `url`           |
| url                | The request URL                                                                                                                   | Required          | -                           |
| headers            | The request Headers                                                                                                               | Optional          | `{}`                        |
| body               | The request body                                                                                                                  | Optional          | -                           |
| method             | The request method (`GET` or `POST`)                                                                                              | Optional          | `GET`                       |
| pagination         | Pagination settings if needed (see [options below](#pagination-configuration-options))                                            | Optional          | -                           |
| next_url           | If needed to update the URL in next requests based on the last response. Supports using variables ([see below](#using-variables)) | Optional          | -                           |
| response_data_path | The path to the data inside the response                                                                                          | Optional          | response root               |
| additional_fields  | Additional custom fields to add to the logs before sending to logzio                                                              | Optional          | Add `type` as `api-fetcher` |
| scrape_interval    | Time interval to wait between runs (unit: `minutes`)                                                                              | Optional          | 1 (minute)                  |

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
Mathematical operations `+` and `-` are supported, to add or reduce a number from the variable value.  

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

## Example
```Yaml
apis:
  - name: fetcher1
    type: general
    url: https://first/request/url
    headers:
      CONTENT-TYPE: application/json
      another-header: XXX
    body: {
            "size": 1000
          }
    method: POST
    additional_fields:
      type: my fetcher
      another_field: 123
    pagination:
      type: url
      url_format: ?page={res.info.page+1}
      update_first_url: True
      stop_indication:
        field: result
        condition: empty
    response_data_path: result

  - name: fetcher2
    type: general
    url: https://first/request/url
    additional_fields:
      type: fetcher2
    next_url: https://url/for/any/request/after/first/?since={res.result.[0].sent}

logzio:
  url: https://listener-eu.logz.io:8071  # for us-east-1 region delete url param (default)
  token: <<SHIPPING_TOKEN>>
```
