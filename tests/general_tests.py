import unittest
import logging
import multiprocessing
import json
import math
import responses
import requests

from requests.sessions import InvalidSchema
from src.cisco_secure_x import CiscoSecureX
from src.logzio_shipper import LogzioShipper
from .tests_utils import TestUtils


logger = logging.getLogger(__name__)


class GeneralTests(unittest.TestCase):

    BASE_CONFIG_FILE = 'tests/config/cisco_secure_x/base_config.yaml'
    CISCO_SECURE_X_BODY_JSON = 'tests/api_body/cisco_secure_x_body.json'
    BAD_LOGZIO_URL = 'https://bad.endpoint:1234'
    BAD_URI = 'https:/bad.uri:1234'
    BAD_CONNECTION_ADAPTER_URL = 'bad://connection.adapter:1234'

    cisco_secure_x_json_body: dict = None

    @classmethod
    def setUpClass(cls) -> None:
        with open(cls.CISCO_SECURE_X_BODY_JSON, 'r') as json_file:
            cls.cisco_secure_x_json_body = json.load(json_file)

    def setUp(self) -> None:
        self.tests_utils = TestUtils(CiscoSecureX.HTTP_METHOD, CiscoSecureX.URL,
                                     GeneralTests.cisco_secure_x_json_body)

        with open(self.tests_utils.LAST_START_DATES_FILE, 'w'):
            pass

    def test_signal(self):
        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               GeneralTests.BASE_CONFIG_FILE,
                                                               self.tests_utils.run_auth_api_process,
                                                               status=200,
                                                               sleep_time=10)

    def test_task_scheduler(self):
        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               GeneralTests.BASE_CONFIG_FILE,
                                                               self.tests_utils.run_auth_api_process,
                                                               status=200,
                                                               sleep_time=70)

        requests_num, _, sent_bytes = queue.get()

        self.assertEqual(math.ceil(sent_bytes / 2 / LogzioShipper.MAX_BULK_SIZE_BYTES) * 2, requests_num)

    def test_write_last_start_date_to_file(self) -> None:
        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               GeneralTests.BASE_CONFIG_FILE,
                                                               self.tests_utils.run_auth_api_process,
                                                               status=200,
                                                               sleep_time=10)

        file_lines = self.tests_utils.get_last_start_dates_file_lines()

        if not file_lines[0] == 'cisco: 2021-10-05T10%3A10%3A11%2B00%3A00\n':
            self.assertEqual(True, False)

        self.assertEqual(1, len(file_lines))

    def test_append_last_start_date_to_file(self) -> None:
        with open(TestUtils.LAST_START_DATES_FILE, 'w') as file:
            file.writelines('cisco test: 2021-10-04T10%3A10%3A10%2B00%3A00\n')

        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               GeneralTests.BASE_CONFIG_FILE,
                                                               self.tests_utils.run_auth_api_process,
                                                               status=200,
                                                               sleep_time=10)

        file_lines = self.tests_utils.get_last_start_dates_file_lines()

        if not file_lines[1] == 'cisco: 2021-10-05T10%3A10%3A11%2B00%3A00\n':
            self.assertEqual(True, False)

        self.assertEqual(2, len(file_lines))

    def test_override_last_start_date(self) -> None:
        with open(TestUtils.LAST_START_DATES_FILE, 'w') as file:
            file.writelines(['cisco test: 2021-10-04T10%3A10%3A10%2B00%3A00\n',
                             'cisco: 2021-10-04T10%3A10%3A10%2B00%3A00\n',
                             'cisco test: 2021-10-04T10%3A10%3A10%2B00%3A00\n'])

        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               GeneralTests.BASE_CONFIG_FILE,
                                                               self.tests_utils.run_auth_api_process,
                                                               status=200,
                                                               sleep_time=10)

        file_lines = self.tests_utils.get_last_start_dates_file_lines()

        if not file_lines[1] == 'cisco: 2021-10-05T10%3A10%3A11%2B00%3A00\n':
            self.assertEqual(True, False)

        self.assertEqual(3, len(file_lines))

    def test_send_retry_status_500(self):
        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               GeneralTests.BASE_CONFIG_FILE,
                                                               self.tests_utils.run_auth_api_process,
                                                               status=500,
                                                               sleep_time=10)

        requests_num, _, _ = queue.get()

        self.assertEqual(LogzioShipper.MAX_RETRIES + 1, requests_num)

    def test_send_retry_status_502(self) -> None:
        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               GeneralTests.BASE_CONFIG_FILE,
                                                               self.tests_utils.run_auth_api_process,
                                                               status=502,
                                                               sleep_time=10)

        requests_num, _, _ = queue.get()

        self.assertEqual(LogzioShipper.MAX_RETRIES + 1, requests_num)

    def test_send_retry_status_503(self) -> None:
        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               GeneralTests.BASE_CONFIG_FILE,
                                                               self.tests_utils.run_auth_api_process,
                                                               status=503,
                                                               sleep_time=10)

        requests_num, _, _ = queue.get()

        self.assertEqual(LogzioShipper.MAX_RETRIES + 1, requests_num)

    def test_send_retry_status_504(self) -> None:
        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               GeneralTests.BASE_CONFIG_FILE,
                                                               self.tests_utils.run_auth_api_process,
                                                               status=504,
                                                               sleep_time=10)

        requests_num, _, _ = queue.get()

        self.assertEqual(LogzioShipper.MAX_RETRIES + 1, requests_num)

    @responses.activate
    def test_send_bad_format(self) -> None:
        responses.add(responses.POST, self.tests_utils.LOGZIO_URL, status=400)

        logzio_shipper = LogzioShipper(self.tests_utils.LOGZIO_URL, self.tests_utils.LOGZIO_TOKEN)

        logzio_shipper.add_log_to_send('{"test": "test"}')

        self.assertRaises(requests.HTTPError, logzio_shipper.send_to_logzio)

    def test_sending_bad_logzio_url(self) -> None:
        logzio_shipper = LogzioShipper(GeneralTests.BAD_LOGZIO_URL, self.tests_utils.LOGZIO_TOKEN)

        logzio_shipper.add_log_to_send('{"test": "test"}')

        self.assertRaises(requests.ConnectionError, logzio_shipper.send_to_logzio)

    @responses.activate
    def test_sending_bad_logzio_token(self) -> None:
        responses.add(responses.POST, self.tests_utils.LOGZIO_URL, status=401)

        logzio_shipper = LogzioShipper(self.tests_utils.LOGZIO_URL, self.tests_utils.LOGZIO_TOKEN)

        logzio_shipper.add_log_to_send('{"test": "test"}')

        self.assertRaises(requests.HTTPError, logzio_shipper.send_to_logzio)

    def test_sending_bad_uri(self) -> None:
        logzio_shipper = LogzioShipper(GeneralTests.BAD_URI, self.tests_utils.LOGZIO_TOKEN)

        logzio_shipper.add_log_to_send('{"test": "test"}')

        self.assertRaises(requests.exceptions.InvalidURL, logzio_shipper.send_to_logzio)

    def test_sending_bad_connection_adapter(self) -> None:
        logzio_shipper = LogzioShipper(GeneralTests.BAD_CONNECTION_ADAPTER_URL, self.tests_utils.LOGZIO_TOKEN)

        logzio_shipper.add_log_to_send('{"test": "test"}')

        self.assertRaises(InvalidSchema, logzio_shipper.send_to_logzio)
