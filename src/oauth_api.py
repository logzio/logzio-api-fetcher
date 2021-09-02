from abc import abstractmethod
from .api import Api


class OAuthApi(Api):

    def __init__(self, api_id: str, api_key: str, api_filter: list[str], token_url: str = None,
                 data_url: str = None, next_url_json_path: str = None, data_json_path: str = None):
        self.api_id = api_id
        self.api_key = api_key
        self.api_filter = api_filter
        self.token_url = token_url
        self.data_url = data_url
        self.next_url_json_path = next_url_json_path
        self.data_json_path = data_json_path

    @abstractmethod
    def fetch_data(self):
        pass
