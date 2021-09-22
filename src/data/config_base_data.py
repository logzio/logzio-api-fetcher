from src.data.api_credentials import ApiCredentials
from src.data.api_filter import ApiFilter


class ConfigBaseData:
    def __init__(self, api_type: str, api_name: str, api_credentials: ApiCredentials, api_filters: list[ApiFilter]
                 , api_start_date_name: str = None, max_bulk_size: int = 2500):
        self._type = api_type
        self._name = api_name
        self._credentials = api_credentials
        self._start_date_name = api_start_date_name
        self._filters = api_filters
        self._max_bulk_size = max_bulk_size

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

    @start_date_name.setter
    def start_date_name(self, name):
        self._start_date_name = name

    @property
    def max_bulk_size(self) -> int:
        return self._max_bulk_size

    @max_bulk_size.setter
    def max_bulk_size(self, value):
        self._max_bulk_size = value
