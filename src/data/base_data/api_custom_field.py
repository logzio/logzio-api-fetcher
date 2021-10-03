class ApiCustomField:

    def __init__(self, field_key: str, field_value: str) -> None:
        self._key = field_key
        self._value = field_value

    @property
    def key(self) -> str:
        return self._key

    @property
    def value(self) -> str:
        return self._value
