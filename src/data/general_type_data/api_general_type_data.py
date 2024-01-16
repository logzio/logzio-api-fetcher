from .api_json_paths import ApiJsonPaths


class ApiGeneralTypeData:

    def __init__(self, api_start_date_name: str, api_end_date_name: str,
                 api_json_paths: ApiJsonPaths) -> None:
        self._start_date_name = api_start_date_name
        self._end_date_name = api_end_date_name
        self._json_paths = api_json_paths

    @property
    def end_date_name(self) -> str:
        return self._end_date_name

    @property
    def start_date_name(self) -> str:
        return self._start_date_name

    @property
    def json_paths(self) -> ApiJsonPaths:
        return self._json_paths
