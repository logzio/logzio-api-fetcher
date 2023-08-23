from typing import Generator
from .api_credentials import ApiCredentials
from .api_settings import ApiSettings
from .api_filter import ApiFilter
from .api_custom_field import ApiCustomField


class ApiBaseData:

    def __init__(self, api_type: str, api_name: str, api_credentials: ApiCredentials, api_settings: ApiSettings,
                 api_filters: list[ApiFilter],
                 api_custom_fields: list[ApiCustomField], date_filter: str = None) -> None:
        self._type = api_type
        self._name = api_name
        self._credentials = api_credentials
        self._settings = api_settings
        self._filters = api_filters
        self._date_filter_value = date_filter
        self._custom_fields = api_custom_fields

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
    def settings(self) -> ApiSettings:
        return self._settings

    @property
    def filters(self) -> Generator[ApiFilter, None, None]:
        for filter in self._filters:
            yield filter

    @property
    def custom_fields(self) -> Generator[ApiCustomField, None, None]:
        for custom_field in self._custom_fields:
            yield custom_field

    def get_filter_index(self, key: str) -> int:
        index = 0

        for filter in self._filters:
            if filter.key == key:
                return index

            index += 1

        return -1

    def get_filters_size(self) -> int:
        return len(self._filters)

    def update_filter_value(self, index: int, value: str) -> None:
        self._filters[index].value = value

    def append_filters(self, filter: ApiFilter) -> None:
        self._filters.append(filter)
