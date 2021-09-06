class ApiFilter:

    def __init__(self, api_filter_key: str, api_filter_value: str):
        self._key = api_filter_key
        self._value = api_filter_value

    @property
    def key(self) -> str:
        return self._key

    @property
    def value(self) -> str:
        return self._value
