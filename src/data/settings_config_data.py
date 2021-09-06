class SettingsConfigData:

    def __init__(self, time_interval: int):
        self._time_interval = time_interval

    @property
    def time_interval(self) -> int:
        return self._time_interval
