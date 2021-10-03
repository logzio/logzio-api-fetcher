class ApiSettings:

    def __init__(self, time_interval: int, max_fetch_data: int = 2500) -> None:
        self._time_interval = time_interval
        self._max_fetch_data = max_fetch_data

    @property
    def time_interval(self) -> int:
        return self._time_interval

    @property
    def max_fetch_data(self) -> int:
        return self._max_fetch_data
