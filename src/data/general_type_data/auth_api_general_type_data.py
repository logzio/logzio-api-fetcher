from .api_general_type_data import ApiGeneralTypeData
from ..api_http_request import ApiHttpRequest


class AuthApiGeneralTypeData:

    def __init__(self, api_general_type_data: ApiGeneralTypeData, api_http_request: ApiHttpRequest) -> None:
        self._general_type_data = api_general_type_data
        self._http_request = api_http_request

    @property
    def general_type_data(self) -> ApiGeneralTypeData:
        return self._general_type_data

    @property
    def http_request(self) -> ApiHttpRequest:
        return self._http_request
