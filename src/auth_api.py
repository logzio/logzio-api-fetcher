from typing import Generator, Optional
from abc import abstractmethod
from .api import Api
from .data.api_credentials import ApiCredentials
from .data.api_filter import ApiFilter
from .data.api_json_paths import ApiJsonPaths


class AuthApi(Api):

    def __init__(self, api_name: str, api_credentials: ApiCredentials, api_filters: list[ApiFilter],
                 api_url: str = None, api_start_date_name: str = None, api_json_paths: ApiJsonPaths = None):
        self._name = api_name
        self.credentials = api_credentials
        self.start_date_name = api_start_date_name
        self.filters = api_filters
        self.url = api_url
        self.json_paths = api_json_paths
        self.last_start_date: Optional[str] = None

    def get_api_name(self):
        return self._name

    @abstractmethod
    def fetch_data(self) -> Generator:
        pass

    @abstractmethod
    def update_start_date_filter(self) -> None:
        pass

    @abstractmethod
    def get_last_start_date(self) -> str:
        pass
