from .api_general_type_data import ApiGeneralTypeData


class OAuthApiGeneralTypeData:

    def __init__(self, api_general_type_data: ApiGeneralTypeData) -> None:
        self._general_type_data = api_general_type_data

    @property
    def general_type_data(self) -> ApiGeneralTypeData:
        return self._general_type_data
