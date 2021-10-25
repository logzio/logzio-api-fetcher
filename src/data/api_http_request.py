class ApiHttpRequest:

    GET_METHOD = 'GET'
    POST_METHOD = 'POST'
    HTTP_METHODS = [GET_METHOD, POST_METHOD]

    def __init__(self, api_http_request_method: str, api_url: str, api_http_request_headers: dict = None,
                 api_http_request_body: str = None) -> None:
        self._method = api_http_request_method
        self._url = api_url
        self._headers = api_http_request_headers
        self._body = api_http_request_body

    @property
    def method(self) -> str:
        return self._method

    @property
    def url(self) -> str:
        return self._url

    @url.setter
    def url(self, url) -> None:
        self._url = url

    @property
    def headers(self) -> dict:
        return self._headers

    @property
    def body(self) -> None:
        return self._body
