class ApiJsonPaths:

    def __init__(self, api_next_url_json_path: str, api_data_json_path: str, api_data_date_json_path: str):
        self._next_url = api_next_url_json_path
        self._data = api_data_json_path
        self._data_date = api_data_date_json_path

    @property
    def next_url(self) -> str:
        return self._next_url

    @property
    def data(self) -> str:
        return self._data

    @property
    def data_date(self) -> str:
        return self._data_date
