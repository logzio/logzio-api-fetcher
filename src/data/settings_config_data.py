class SettingsConfigData:

    def __init__(self, time_interval: int, max_bulk_size: int = 2500) -> None:
        self._time_interval = time_interval
        self._max_bulk_size = max_bulk_size

    @property
    def time_interval(self) -> int:
        return self._time_interval

    @property
    def max_bulk_size(self) -> int:
        return self._max_bulk_size
