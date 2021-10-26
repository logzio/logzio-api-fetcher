import unittest
import logging
import multiprocessing
import json
import math

import httpretty

from src.cisco_secure_x import CiscoSecureX
from src.logzio_shipper import LogzioShipper
from .tests_utils import TestUtils


logger = logging.getLogger(__name__)


class CiscoSecureXApiTests(unittest.TestCase):

    BASE_CONFIG_FILE = 'tests/config/cisco_secure_x/base_config.yaml'
    DAYS_BACK_FETCH_CONFIG_FILE = 'tests/config/cisco_secure_x/days_back_fetch_config.yaml'
    FILTERS_CONFIG_FILE = 'tests/config/cisco_secure_x/filters_config.yaml'
    CUSTOM_FIELDS_CONFIG_FILE = 'tests/config/cisco_secure_x/custom_fields_config.yaml'
    MULTIPLE_CONFIG_FILE = 'tests/config/cisco_secure_x/multiple_config.yaml'
    TIME_INTERVAL_CONFIG_FILE = 'tests/config/cisco_secure_x/time_interval_config.yaml'
    BAD_CONFIG_FILE = 'tests/config/cisco_secure_x/bad_config.yaml'

    CISCO_SECURE_X_BODY_JSON = 'tests/api_body/cisco_secure_x_body.json'

    cisco_secure_x_json_body: dict = None

    @classmethod
    def setUpClass(cls) -> None:
        with open(cls.CISCO_SECURE_X_BODY_JSON, 'r') as json_file:
            cls.cisco_secure_x_json_body = json.load(json_file)

    def setUp(self) -> None:
        self.tests_utils = TestUtils(CiscoSecureX.HTTP_METHOD, CiscoSecureX.URL,
                                     CiscoSecureXApiTests.cisco_secure_x_json_body)

        with open(self.tests_utils.LAST_START_DATES_FILE, 'w'):
            pass

    def test_fetch_data(self) -> None:
        total_data_bytes, total_data_num = self.tests_utils.get_cisco_secure_x_api_total_data_bytes_and_num(
            CiscoSecureXApiTests.BASE_CONFIG_FILE)
        base_cisco_secure_x = self.tests_utils.get_first_api(CiscoSecureXApiTests.BASE_CONFIG_FILE, is_auth_api=True)

        fetched_data_bytes, fetched_data_num = self.tests_utils.get_api_fetch_data_bytes_and_num(
            base_cisco_secure_x)

        self.assertEqual(total_data_bytes, fetched_data_bytes)
        self.assertEqual(total_data_num, fetched_data_num)

    def test_sending_data(self) -> None:
        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               CiscoSecureXApiTests.BASE_CONFIG_FILE,
                                                               self.tests_utils.run_auth_api_process,
                                                               status=200,
                                                               sleep_time=10)

        requests_num, sent_logs_num, sent_bytes = queue.get()
        data_bytes, data_num = self.tests_utils.get_api_data_bytes_and_num_from_json_data(
            self.cisco_secure_x_json_body['data'])

        self.assertEqual(math.ceil(sent_bytes / LogzioShipper.MAX_BULK_SIZE_BYTES), requests_num)
        self.assertEqual(data_num, sent_logs_num)
        self.assertEqual(data_bytes, sent_bytes)
