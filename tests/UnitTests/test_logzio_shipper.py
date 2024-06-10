import responses
import requests
import unittest

from src.output.LogzioShipper import LogzioShipper


class TestLogzioShipper(unittest.TestCase):
    """
    Test logzio shipper
    """

    def test_add_log_to_send(self):
        s = LogzioShipper(token="myShippingToken")

        # Text log
        s.add_log_to_send("random text log", {"type": "someType"})
        self.assertIn('{"message": "random text log", "type": "someType"}', s.curr_logs)

        # Json log
        s.add_log_to_send('{"message": "json log", "field": 123}',
                          {"type": "api-fetcher", "field2": "value"})
        self.assertIn('{"message": "json log", "field": 123, "type": "api-fetcher", "field2": "value"}',
                      s.curr_logs)

    @responses.activate
    def test_send_to_logzio(self):
        s = LogzioShipper(token="myShippingToken")

        responses.add(responses.POST, "https://listener.logz.io:8071/?token=myShippingToken",
                      status=200)

        s.add_log_to_send("random text log", {"type": "someType"})
        with self.assertLogs("src.output.LogzioShipper", level='INFO') as log:
            s.send_to_logzio()
        self.assertIn("INFO:src.output.LogzioShipper:Successfully sent bulk of 50 bytes to Logz.io.", log.output)

    @responses.activate
    def test_invalid_token(self):
        s = LogzioShipper(token="notGoodShippingToken")

        responses.add(responses.POST, "https://listener.logz.io:8071/?token=notGoodShippingToken",
                      status=401)

        s.add_log_to_send("random text log", {"type": "someType"})
        with self.assertLogs("src.output.LogzioShipper", level='INFO') as log:
            with self.assertRaises(requests.exceptions.HTTPError):
                s.send_to_logzio()
        self.assertIn("ERROR:src.output.LogzioShipper:Logzio Shipping Token is missing or invalid. Make sure you’re using the right account token.", log.output)
