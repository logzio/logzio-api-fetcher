from typing import Generator
from abc import ABC, abstractmethod


class AuthApi(ABC):

    def __init__(self, api_id: str, api_key: str, api_filters: list[dict], url: str = None,
                 next_url_json_path: str = None, data_json_path: str = None):
        self.api_id = api_id
        self.api_key = api_key
        self.api_filters = api_filters
        self.url = url
        self.next_url_json_path = next_url_json_path
        self.data_json_path = data_json_path
        self.last_start_date = None

    @abstractmethod
    def fetch_data(self) -> Generator:
        pass

    @abstractmethod
    def update_start_date_filter(self) -> None:
        pass

    @abstractmethod
    def get_last_start_date(self) -> str:
        pass
