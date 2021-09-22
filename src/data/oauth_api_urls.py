from src.data.api_url import ApiUrl


class OAuthApiUrls:

    def __init__(self, api_data_url: ApiUrl, api_token_url: ApiUrl):
        self._data_url = api_data_url
        self._token_url = api_token_url

    @property
    def data_url(self) -> ApiUrl:
        return self._data_url

    @property
    def token_url(self) -> ApiUrl:
        return self._token_url