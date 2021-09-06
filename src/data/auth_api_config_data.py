from .api_credentials import ApiCredentials
from .api_filter import ApiFilter
from .api_json_paths import ApiJsonPaths


class AuthApiConfigData:

    def __init__(self, api_type: str, api_name: str, api_credentials: ApiCredentials, api_filters: list[ApiFilter],
                 api_url: str = None, api_start_date_name: str = None, api_json_paths: ApiJsonPaths = None) -> None:
        self._type = api_type
        self._name = api_name
        self._credentials = api_credentials
        self._start_date_name = api_start_date_name
        self._filters = api_filters
        self._url = api_url
        self._json_paths = api_json_paths

    @property
    def type(self) -> str:
        return self._type

    @property
    def name(self) -> str:
        return self._name

    @property
    def credentials(self) -> ApiCredentials:
        return self._credentials

    @property
    def start_date_name(self) -> str:
        return self._start_date_name

    @property
    def filters(self) -> list[ApiFilter]:
        return self._filters

    @property
    def url(self) -> str:
        return self._url

    @property
    def json_paths(self) -> ApiJsonPaths:
        return self._json_paths
