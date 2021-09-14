class ApiUrl:

    def __init__(self, api_url: str, url_headers: dict=None):
        self._api_url = api_url
        self._url_headers = url_headers

    @property
    def api_url(self) -> str:
        return self._api_url

    @property
    def url_headers(self) -> dict:
        return self._url_headers
