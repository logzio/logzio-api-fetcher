from .config_base_data import ConfigBaseData
from .oauth_api_urls import OAuthApiUrls
from .api_json_paths import ApiJsonPaths


class OAuthApiConfigData:

    def __init__(self, base_config: ConfigBaseData,
                 api_urls: OAuthApiUrls = None,
                 api_json_paths: ApiJsonPaths = None) -> None:
        self._config_base_data = base_config
        self._urls = api_urls
        self._json_paths = api_json_paths

    @property
    def urls(self) -> OAuthApiUrls:
        return self._urls

    @property
    def json_paths(self) -> ApiJsonPaths:
        return self._json_paths

    @json_paths.setter
    def json_paths(self, value) -> None:
        self._json_paths = value

    @property
    def config_base_data(self) -> None:
        return self._config_base_data
