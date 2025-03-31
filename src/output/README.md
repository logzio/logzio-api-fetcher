# Logzio output
It's possible to configure all APIs data to be exported to a single Logz.io account, or to set up multiple outputs and specify which input API to send to which Logz.io account.

## Single output
```yaml
logzio:
  url: https://listener-eu.logz.io:8071  # for us-east-1 region delete url param (default) 
  token: <<SHIPPING_TOKEN>>
```

## Multiple outputs
```yaml
apis:
  - name: input 1
    ...
  - name: input 2
    ...

logzio:
  - url: https://listener-eu.logz.io:8071  # for us-east-1 region delete url param (default)
   token: <<SHIPPING_TOKEN_ACCOUNT1>>
   inputs: 
     - input 1
     - input 2

  - url: https://listener-eu.logz.io:8071  # for us-east-1 region delete url param (default)
    token: <<SHIPPING_TOKEN_ACCOUNT2>>
    inputs: [ "input 1" ]
```

## Configuration options

| Parameter Name | Description                 | Required/Optional | Default                         |
|----------------|-----------------------------|-------------------|---------------------------------|
| url            | The logzio Listener address | Optional          | `https://listener.logz.io:8071` |
| token          | The logzio shipping token   | Required          | -                               |
