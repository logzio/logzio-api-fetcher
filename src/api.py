from abc import ABC, abstractmethod
from typing import Generator


class Api(ABC):

    def __init__(self, api_id: str, api_key: str, start_date: str) -> None:
        self.api_id = api_id
        self.api_key = api_key
        self.start_date = start_date
        self.last_start_date = start_date

    @abstractmethod
    def get_events(self) -> Generator:
        pass

    @abstractmethod
    def update_start_date(self) -> None:
        pass

    @abstractmethod
    def get_last_start_date(self) -> str:
        pass

