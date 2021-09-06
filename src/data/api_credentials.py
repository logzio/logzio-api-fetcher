class ApiCredentials:

    def __init__(self, api_credentials_id: str, api_credentials_key: str):
        self._id = api_credentials_id
        self._key = api_credentials_key

    @property
    def id(self) -> str:
        return self._id

    @property
    def key(self) -> str:
        return self._key
