from .api_base_data import ApiBaseData
from ..api_http_request import ApiHttpRequest


class OAuthApiBaseData:

    def __init__(self, api_base_data: ApiBaseData, api_token_http_request: ApiHttpRequest,
                 api_data_http_request: ApiHttpRequest) -> None:
        self._base_data = api_base_data
        self._token_http_request = api_token_http_request
        self._data_http_request = api_data_http_request

    @property
    def base_data(self) -> ApiBaseData:
        return self._base_data

    @property
    def token_http_request(self) -> ApiHttpRequest:
        return self._token_http_request

    @property
    def data_http_request(self) -> ApiHttpRequest:
        return self._data_http_request
