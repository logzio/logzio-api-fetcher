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

    def test_fetch_data_with_days_back_fetch(self) -> None:
        total_data_bytes, total_data_num = self.tests_utils.get_cisco_secure_x_api_total_data_bytes_and_num(
            CiscoSecureXApiTests.DAYS_BACK_FETCH_CONFIG_FILE)
        days_back_fetch_cisco_secure_x = self.tests_utils.get_first_api(
            CiscoSecureXApiTests.DAYS_BACK_FETCH_CONFIG_FILE, is_auth_api=True)

        fetched_data_bytes, fetched_data_num = self.tests_utils.get_api_fetch_data_bytes_and_num(
            days_back_fetch_cisco_secure_x)

        self.assertNotEqual(total_data_bytes, fetched_data_bytes)
        self.assertNotEqual(total_data_num, fetched_data_num)

    def test_fetch_data_with_filters(self) -> None:
        total_data_bytes, total_data_num = self.tests_utils.get_cisco_secure_x_api_total_data_bytes_and_num(
            CiscoSecureXApiTests.FILTERS_CONFIG_FILE)
        filters_cisco_secure_x = self.tests_utils.get_first_api(CiscoSecureXApiTests.FILTERS_CONFIG_FILE,
                                                                is_auth_api=True)

        fetched_data_bytes, fetched_data_num = self.tests_utils.get_api_fetch_data_bytes_and_num(
            filters_cisco_secure_x)

        self.assertNotEqual(total_data_bytes, fetched_data_bytes)
        self.assertNotEqual(total_data_num, fetched_data_num)

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

    def test_sending_data_iterations(self) -> None:
        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               CiscoSecureXApiTests.DAYS_BACK_FETCH_CONFIG_FILE,
                                                               self.tests_utils.run_auth_api_process,
                                                               status=200,
                                                               sleep_time=70)

        requests_num, sent_logs_num, sent_bytes = queue.get()
        data_bytes, data_num = self.tests_utils.get_api_data_bytes_and_num_from_json_data(
            self.cisco_secure_x_json_body['data'])

        self.assertEqual(math.ceil(sent_bytes / 2 / LogzioShipper.MAX_BULK_SIZE_BYTES) * 2, requests_num)
        self.assertEqual(data_num * 2, sent_logs_num)
        self.assertEqual(data_bytes * 2, sent_bytes)

    def test_sending_data_multiple_cisco_secure_x(self) -> None:
        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               CiscoSecureXApiTests.MULTIPLE_CONFIG_FILE,
                                                               self.tests_utils.run_auth_api_process,
                                                               status=200,
                                                               sleep_time=10)

        requests_num, sent_logs_num, sent_bytes = queue.get()
        data_bytes, data_num = self.tests_utils.get_api_data_bytes_and_num_from_json_data(
            self.cisco_secure_x_json_body['data'])

        self.assertEqual(math.ceil(sent_bytes / 2 / LogzioShipper.MAX_BULK_SIZE_BYTES) * 2, requests_num)
        self.assertEqual(data_num * 2, sent_logs_num)
        self.assertEqual(data_bytes * 2, sent_bytes)

    def test_sending_data_with_custom_fields(self) -> None:
        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               CiscoSecureXApiTests.CUSTOM_FIELDS_CONFIG_FILE,
                                                               self.tests_utils.run_auth_api_process,
                                                               status=200,
                                                               sleep_time=10)

        requests_num, sent_logs_num, sent_bytes = queue.get()
        data_bytes, data_num = self.tests_utils.get_api_data_bytes_and_num_from_json_data(
            self.cisco_secure_x_json_body['data'])
        custom_fields_cisco_secure_x = self.tests_utils.get_first_api(CiscoSecureXApiTests.CUSTOM_FIELDS_CONFIG_FILE,
                                                                      is_auth_api=True)
        data_bytes += data_num * self.tests_utils.get_api_custom_fields_bytes(custom_fields_cisco_secure_x)

        self.assertEqual(math.ceil(sent_bytes / LogzioShipper.MAX_BULK_SIZE_BYTES), requests_num)
        self.assertEqual(data_num, sent_logs_num)
        self.assertEqual(data_bytes, sent_bytes)

    def test_time_interval(self) -> None:
        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               CiscoSecureXApiTests.TIME_INTERVAL_CONFIG_FILE,
                                                               self.tests_utils.run_auth_api_process,
                                                               status=200,
                                                               sleep_time=70)

        requests_num, sent_logs_num, sent_bytes = queue.get()
        data_bytes, data_num = self.tests_utils.get_api_data_bytes_and_num_from_json_data(
            self.cisco_secure_x_json_body['data'])

        self.assertEqual(math.ceil(sent_bytes / LogzioShipper.MAX_BULK_SIZE_BYTES), requests_num)
        self.assertEqual(data_num, sent_logs_num)
        self.assertEqual(data_bytes, sent_bytes)

    @httpretty.activate
    def test_last_start_date(self) -> None:
        httpretty.register_uri(httpretty.GET, CiscoSecureX.URL,
                               body=json.dumps(CiscoSecureXApiTests.cisco_secure_x_json_body), status=200)

        base_cisco_secure_x = self.tests_utils.get_first_api(CiscoSecureXApiTests.CUSTOM_FIELDS_CONFIG_FILE,
                                                             is_auth_api=True)

        for _ in base_cisco_secure_x.fetch_data():
            continue

        base_cisco_secure_x.update_start_date_filter()

        self.assertEqual('2021-10-05T10%3A10%3A11%2B00%3A00', base_cisco_secure_x.get_last_start_date())

    def test_bad_config(self) -> None:
        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               CiscoSecureXApiTests.BAD_CONFIG_FILE,
                                                               self.tests_utils.run_auth_api_process,
                                                               status=200,
                                                               sleep_time=1)

        requests_num, sent_logs_num, sent_bytes = queue.get()

        self.assertEqual(0, requests_num)
        self.assertEqual(0, sent_logs_num)
        self.assertEqual(0, sent_bytes)
