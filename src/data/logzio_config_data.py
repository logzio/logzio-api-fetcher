class LogzioConfigData:

    def __init__(self, logzio_url: str, logzio_token: str):
        self._url = logzio_url
        self._token = logzio_token

    @property
    def url(self) -> str:
        return self._url

    @property
    def token(self) -> str:
        return self._token
