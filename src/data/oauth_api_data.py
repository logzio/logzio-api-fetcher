from .base_data.oauth_api_base_data import OAuthApiBaseData
from .general_type_data.oauth_api_general_type_data import OAuthApiGeneralTypeData


class OAuthApiData:

    def __init__(self, oauth_api_base_data: OAuthApiBaseData,
                 oauth_api_general_type_data: OAuthApiGeneralTypeData = None) -> None:
        self._base_data = oauth_api_base_data
        self._general_type_data = oauth_api_general_type_data

    @property
    def base_data(self) -> OAuthApiBaseData:
        return self._base_data

    @property
    def general_type_data(self) -> OAuthApiGeneralTypeData:
        return self._general_type_data
