from abc import ABC, abstractmethod
from typing import Generator


class Api(ABC):

    class ApiError(Exception):
        pass

    @abstractmethod
    def fetch_data(self) -> Generator:
        pass

    @abstractmethod
    def update_start_date_filter(self) -> None:
        pass

    @abstractmethod
    def get_last_start_date(self) -> str:
        pass

    @abstractmethod
    def get_api_name(self) -> str:
        pass
