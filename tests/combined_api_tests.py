import unittest
import logging
import multiprocessing
import json
import math

from src.azure_graph import AzureGraph
from src.cisco_secure_x import CiscoSecureX
from src.logzio_shipper import LogzioShipper
from .azure_graph_api_tests import AzureGraphApiTests
from .cisco_secure_x_api_tests import CiscoSecureXApiTests
from .tests_utils import TestUtils

logger = logging.getLogger(__name__)


class CombinedApiTests(unittest.TestCase):
    BASE_CONFIG_FILE = 'tests/config/combined_config/base_config.yaml'
    DAYS_BACK_FETCH_CONFIG_FILE = 'tests/config/combined_config/days_back_fetch_config.yaml'
    FILTERS_CONFIG_FILE = 'tests/config/combined_config/filters_config.yaml'
    azure_graph_json_body: dict = None
    azure_graph_token_json_body: dict = None
    cisco_secure_json_body: dict = None

    @classmethod
    def setUpClass(cls) -> None:
        with open(AzureGraphApiTests.AZURE_GRAPH_BODY_JSON, 'r') as json_file:
            cls.azure_graph_json_body = json.load(json_file)
        with open(AzureGraphApiTests.AZURE_GRAPH_TOKEN_BODY_JSON, 'r') as json_file:
            cls.azure_graph_token_json_body = json.load(json_file)
        with open(CiscoSecureXApiTests.CISCO_SECURE_X_BODY_JSON, 'r') as json_file:
            cls.cisco_secure_json_body = json.load(json_file)

    def setUp(self) -> None:
        self.tests_utils = TestUtils("GET", AzureGraphApiTests.AZURE_GRAPH_TEST_URL,
                                     self.azure_graph_json_body,
                                     "POST", AzureGraphApiTests.AZURE_GRAPH_TOKEN_TEST_URL,
                                     self.azure_graph_token_json_body, CiscoSecureX.HTTP_METHOD, CiscoSecureX.URL,
                                     self.cisco_secure_json_body)

        with open(self.tests_utils.LAST_START_DATES_FILE, 'w'):
            pass

    def int_sum_data(self):
        self.total_bytes = 0
        self.fetched_bytes = 0
        self.total_data_num = 0
        self.fetched_data_num = 0

    def add_to_sum_data(self, bytes, fetched_bytes, data_num, fetched_data_num):
        self.total_bytes += bytes
        self.total_data_num += data_num
        self.fetched_bytes += fetched_bytes
        self.fetched_data_num += fetched_data_num

    def test_fetch_data(self) -> None:
        self.int_sum_data()
        data_bytes, data_num = self.tests_utils.get_azure_graph_api_total_data_bytes_and_num(
            self.BASE_CONFIG_FILE)
        base_azure_graph = self.tests_utils.get_first_api(self.BASE_CONFIG_FILE, is_auth_api=False)
        fetched_data_bytes, fetched_data_num = self.tests_utils.get_api_fetch_data_bytes_and_num(
            base_azure_graph)
        self.add_to_sum_data(data_bytes, fetched_data_bytes, data_num, fetched_data_num)

        data_bytes, data_num = self.tests_utils.get_cisco_secure_x_api_total_data_bytes_and_num(
            CiscoSecureXApiTests.BASE_CONFIG_FILE)
        base_cisco_secure_x = self.tests_utils.get_first_api(CiscoSecureXApiTests.BASE_CONFIG_FILE, is_auth_api=True)
        fetched_data_bytes, fetched_data_num = self.tests_utils.get_api_fetch_data_bytes_and_num(
            base_cisco_secure_x)
        self.add_to_sum_data(data_bytes, fetched_data_bytes, data_num, fetched_data_num)

        self.assertEqual(self.total_bytes, self.fetched_bytes)
        self.assertEqual(self.total_data_num, self.fetched_data_num)

    def test_fetch_data_with_days_back_fetch(self) -> None:
        self.int_sum_data()
        data_bytes, data_num = self.tests_utils.get_azure_graph_api_total_data_bytes_and_num(
            self.DAYS_BACK_FETCH_CONFIG_FILE)
        azure_graph_days_back_fetch = self.tests_utils.get_first_api(
            self.DAYS_BACK_FETCH_CONFIG_FILE, is_auth_api=False)
        fetched_data_bytes, fetched_data_num = self.tests_utils.get_api_fetch_data_bytes_and_num(
            azure_graph_days_back_fetch)
        self.add_to_sum_data(data_bytes, fetched_data_bytes, data_num, fetched_data_num)

        data_bytes, data_num = self.tests_utils.get_cisco_secure_x_api_total_data_bytes_and_num(
            CiscoSecureXApiTests.DAYS_BACK_FETCH_CONFIG_FILE)
        days_back_fetch_cisco_secure_x = self.tests_utils.get_first_api(
            CiscoSecureXApiTests.DAYS_BACK_FETCH_CONFIG_FILE, is_auth_api=True)
        fetched_data_bytes, fetched_data_num = self.tests_utils.get_api_fetch_data_bytes_and_num(
            days_back_fetch_cisco_secure_x)
        self.add_to_sum_data(data_bytes, fetched_data_bytes, data_num, fetched_data_num)

        self.assertNotEqual(self.total_bytes, self.fetched_bytes)
        self.assertNotEqual(self.total_data_num, self.fetched_data_num)

    def test_fetch_data_with_filters(self) -> None:
        total_data_bytes, total_data_num = self.tests_utils.get_azure_graph_api_total_data_bytes_and_num(
            self.FILTERS_CONFIG_FILE)
        filters_azure_graph = self.tests_utils.get_first_api(self.FILTERS_CONFIG_FILE,
                                                             is_auth_api=False)

        fetched_data_bytes, fetched_data_num = self.tests_utils.get_api_fetch_data_bytes_and_num(
            filters_azure_graph)

        self.assertNotEqual(total_data_bytes, fetched_data_bytes)
        self.assertNotEqual(total_data_num, fetched_data_num)

    def test_sending_data(self) -> None:
        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               self.BASE_CONFIG_FILE,
                                                               self.tests_utils.run_oauth_api_process,
                                                               status=200,
                                                               sleep_time=10,
                                                               is_multi_test=True)

        requests_num, sent_logs_num, sent_bytes = queue.get()
        data_bytes, data_num = self.tests_utils.get_api_data_bytes_and_num_from_json_data(
            self.azure_graph_json_body[AzureGraph.DEFAULT_GRAPH_DATA_LINK])

        data_bytes2, data_num2 = self.tests_utils.get_api_data_bytes_and_num_from_json_data(
            self.cisco_secure_json_body['data'])

        self.assertEqual(math.ceil(sent_bytes / LogzioShipper.MAX_BULK_SIZE_BYTES) * 2, requests_num)
        self.assertEqual(data_num + data_num2, sent_logs_num)
        self.assertEqual(data_bytes + data_bytes2, sent_bytes)
