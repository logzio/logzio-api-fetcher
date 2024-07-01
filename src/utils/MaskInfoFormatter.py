import logging
import re


class MaskInfoFormatter(logging.Formatter):
    """
    Formatter that masks sensitive information such as tokens from the program logs.
    """
    @staticmethod
    def _filter(org_log):
        return re.sub(r'(token=|grant_type=|client_secret=|Bearer |Authorization[\"|\']: [\"|\']Basic |TOKEN[\"|\']: [\"|\'])[^&\n]{0,26}',
                      r'\g<1>******', org_log)

    def format(self, record):
        original = super().format(record)
        return self._filter(original)
