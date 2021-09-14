
from .api_json_paths import ApiJsonPaths
from .api_url import ApiUrl
from .config_base_data import ConfigBaseData


class AuthApiConfigData:

    def __init__(self, base_config: ConfigBaseData,
                 api_url: ApiUrl = None, api_json_paths: ApiJsonPaths = None) -> None:
        self._base_config = base_config
        self._api_url = api_url
        self._json_paths = api_json_paths

    @property
    def api_url(self) -> ApiUrl:
        return self._api_url

    @property
    def json_paths(self) -> ApiJsonPaths:
        return self._json_paths

    @property
    def base_config(self) -> ConfigBaseData:
        return self._base_config
