class OAuthApiUrls:

    def __init__(self, api_data_url: str, api_token_url: str):
        self._data_url = api_data_url
        self._token_url = api_token_url

    @property
    def data_url(self) -> str:
        return self._data_url

    @property
    def token_url(self) -> str:
        return self._token_url
