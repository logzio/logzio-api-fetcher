import logging
import unittest

from src.utils.MaskInfoFormatter import MaskInfoFormatter


class TestMaskingTokensLogging(unittest.TestCase):
    """
    Test masking tokens in the logging
    """

    def test_masking_tokens_in_logs(self):
        formatter = MaskInfoFormatter()
        mock_log_record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=123,
            msg='https://listener.logz.io:8071/?token=logz-io-super-secret-token-value',
            args=(),
            exc_info=None
        )

        formatted_log = formatter.format(mock_log_record)

        self.assertEqual("https://listener.logz.io:8071/?token=******-value", formatted_log)
