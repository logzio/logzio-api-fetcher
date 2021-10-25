from .base_data.auth_api_base_data import AuthApiBaseData
from .general_type_data.auth_api_general_type_data import AuthApiGeneralTypeData


class AuthApiData:

    def __init__(self, auth_api_base_data: AuthApiBaseData,
                 auth_api_general_type_data: AuthApiGeneralTypeData = None) -> None:
        self._base_data = auth_api_base_data
        self._general_type_data = auth_api_general_type_data

    @property
    def base_data(self) -> AuthApiBaseData:
        return self._base_data

    @property
    def general_type_data(self) -> AuthApiGeneralTypeData:
        return self._general_type_data
