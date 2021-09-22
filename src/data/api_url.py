class ApiUrl:

    def __init__(self, api_url: str, url_headers: dict = None, url_body: str = None):
        self._api_url = api_url
        self._url_headers = url_headers
        self._body = url_body

    @property
    def api_url(self) -> str:
        return self._api_url

    @property
    def url_headers(self) -> dict:
        return self._url_headers

    @api_url.setter
    def api_url(self, url):
        self._api_url = url

    @property
    def body(self):
        return self._body
