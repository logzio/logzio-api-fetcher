from .api_base_data import ApiBaseData


class AuthApiBaseData:

    def __init__(self, api_base_data: ApiBaseData) -> None:
        self._base_data = api_base_data

    @property
    def base_data(self) -> ApiBaseData:
        return self._base_data
