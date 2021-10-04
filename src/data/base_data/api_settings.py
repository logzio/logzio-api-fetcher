class ApiSettings:

    def __init__(self, time_interval: int, days_back_to_fetch: int = 14) -> None:
        self._time_interval = time_interval
        self._days_back_to_fetch = days_back_to_fetch

    @property
    def time_interval(self) -> int:
        return self._time_interval

    @property
    def days_back_to_fetch(self) -> int:
        return self._days_back_to_fetch
