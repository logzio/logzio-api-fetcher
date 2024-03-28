import unittest
import logging
import multiprocessing
import json
import math
from urllib.parse import unquote
import responses

from src.azure_graph import AzureGraph
from src.logzio_shipper import LogzioShipper
from .tests_utils import TestUtils

logger = logging.getLogger(__name__)


class GeneralTypeOAuthApiTests(unittest.TestCase):
    BASE_CONFIG_FILE = 'tests/config/general_type_oauth_api/base_config.yaml'
    DAYS_BACK_FETCH_CONFIG_FILE = 'tests/config/general_type_oauth_api/days_back_fetch_config.yaml'
    FILTERS_CONFIG_FILE = 'tests/config/general_type_oauth_api/filters_config.yaml'
    CUSTOM_FIELDS_CONFIG_FILE = 'tests/config/general_type_oauth_api/custom_fields_config.yaml'
    MULTIPLE_CONFIG_FILE = 'tests/config/general_type_oauth_api/multiple_config.yaml'
    TIME_INTERVAL_CONFIG_FILE = 'tests/config/general_type_oauth_api/time_interval_config.yaml'
    HTTP_REQUEST_HEADERS_CONFIG_FILE = 'tests/config/general_type_oauth_api/http_request_headers_config.yaml'
    BAD_CONFIG_FILE = 'tests/config/general_type_oauth_api/bad_config.yaml'
    AZURE_GRAPH_BODY_JSON = 'tests/api_body/azure_graph_body.json'
    AZURE_GRAPH_TEST_URL = "https://graph.microsoft.com/v1.0/auditLogs/signIns"
    AZURE_GRAPH_TEST_TOKEN = "1234-abcd-efgh-5678"
    AZURE_GRAPH_TOKEN_TEST_URL = 'https://login.microsoftonline.com/<<AZURE_AD_TENANT_ID>>/oauth2/v2.0/token'
    AZURE_GRAPH_TOKEN_BODY_JSON = 'tests/api_body/azure_graph_token_body.json'
    azure_graph_json_body: dict = None

    @classmethod
    def setUpClass(cls) -> None:
        with open(cls.AZURE_GRAPH_BODY_JSON, 'r') as json_file:
            cls.azure_graph_json_body = json.load(json_file)
        with open(cls.AZURE_GRAPH_TOKEN_BODY_JSON, 'r') as json_file:
            cls.azure_graph_token_json_body = json.load(json_file)

    def setUp(self) -> None:
        self.tests_utils = TestUtils("GET", self.AZURE_GRAPH_TEST_URL,
                                     self.azure_graph_json_body,
                                     "POST", self.AZURE_GRAPH_TOKEN_TEST_URL,
                                     self.azure_graph_token_json_body)

        with open(self.tests_utils.LAST_START_DATES_FILE, 'w'):
            pass

    def test_fetch_data(self) -> None:
        total_data_bytes, total_data_num = self.tests_utils.get_azure_graph_api_total_data_bytes_and_num(
            GeneralTypeOAuthApiTests.BASE_CONFIG_FILE)
        base_azure_graph = self.tests_utils.get_first_api(GeneralTypeOAuthApiTests.BASE_CONFIG_FILE, is_auth_api=False)
        fetched_data_bytes, fetched_data_num = self.tests_utils.get_api_fetch_data_bytes_and_num(
            base_azure_graph)

        self.assertEqual(total_data_bytes, fetched_data_bytes)
        self.assertEqual(total_data_num, fetched_data_num)

    def test_fetch_data_with_days_back_fetch(self) -> None:
        total_data_bytes, total_data_num = self.tests_utils.get_azure_graph_api_total_data_bytes_and_num(
            GeneralTypeOAuthApiTests.DAYS_BACK_FETCH_CONFIG_FILE)
        azure_graph_days_back_fetch = self.tests_utils.get_first_api(
            GeneralTypeOAuthApiTests.DAYS_BACK_FETCH_CONFIG_FILE, is_auth_api=False)

        fetched_data_bytes, fetched_data_num = self.tests_utils.get_api_fetch_data_bytes_and_num(
            azure_graph_days_back_fetch)

        self.assertNotEqual(total_data_bytes, fetched_data_bytes)
        self.assertNotEqual(total_data_num, fetched_data_num)

    def test_fetch_data_with_filters(self) -> None:
        total_data_bytes, total_data_num = self.tests_utils.get_azure_graph_api_total_data_bytes_and_num(
            GeneralTypeOAuthApiTests.FILTERS_CONFIG_FILE)
        filters_cisco_secure_x = self.tests_utils.get_first_api(GeneralTypeOAuthApiTests.FILTERS_CONFIG_FILE,
                                                                is_auth_api=False)

        fetched_data_bytes, fetched_data_num = self.tests_utils.get_api_fetch_data_bytes_and_num(
            filters_cisco_secure_x)

        self.assertNotEqual(total_data_bytes, fetched_data_bytes)
        self.assertNotEqual(total_data_num, fetched_data_num)

    def test_sending_data(self) -> None:
        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               self.BASE_CONFIG_FILE,
                                                               self.tests_utils.run_oauth_api_process,
                                                               status=200,
                                                               sleep_time=10)

        requests_num, sent_logs_num, sent_bytes = queue.get()
        data_bytes, data_num = self.tests_utils.get_api_data_bytes_and_num_from_json_data(
            self.azure_graph_json_body[AzureGraph.DEFAULT_GRAPH_DATA_LINK])

        self.assertEqual(math.ceil(sent_bytes / LogzioShipper.MAX_BULK_SIZE_BYTES), requests_num)
        self.assertEqual(data_num, sent_logs_num)
        self.assertEqual(data_bytes, sent_bytes)

    def test_sending_data_with_http_request_headers(self) -> None:
        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               GeneralTypeOAuthApiTests.HTTP_REQUEST_HEADERS_CONFIG_FILE,
                                                               self.tests_utils.run_oauth_api_process,
                                                               status=200,
                                                               sleep_time=10)

        requests_num, sent_logs_num, sent_bytes = queue.get()
        data_bytes, data_num = self.tests_utils.get_api_data_bytes_and_num_from_json_data(
            self.azure_graph_json_body[AzureGraph.DEFAULT_GRAPH_DATA_LINK])

        self.assertEqual(math.ceil(sent_bytes / LogzioShipper.MAX_BULK_SIZE_BYTES), requests_num)
        self.assertEqual(data_num, sent_logs_num)
        self.assertEqual(data_bytes, sent_bytes)

    def test_sending_data_iterations(self) -> None:
        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               GeneralTypeOAuthApiTests.DAYS_BACK_FETCH_CONFIG_FILE,
                                                               self.tests_utils.run_oauth_api_process,
                                                               status=200,
                                                               sleep_time=70)

        requests_num, sent_logs_num, sent_bytes = queue.get()
        data_bytes, data_num = self.tests_utils.get_api_data_bytes_and_num_from_json_data(
            self.azure_graph_json_body[AzureGraph.DEFAULT_GRAPH_DATA_LINK])

        self.assertEqual(math.ceil(sent_bytes / 2 / LogzioShipper.MAX_BULK_SIZE_BYTES) * 2, requests_num)
        self.assertEqual(data_num * 2, sent_logs_num)
        self.assertEqual(data_bytes * 2, sent_bytes)

    def test_sending_data_multiple_general_type_apis(self) -> None:
        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               GeneralTypeOAuthApiTests.MULTIPLE_CONFIG_FILE,
                                                               self.tests_utils.run_oauth_api_process,
                                                               status=200,
                                                               sleep_time=10)

        requests_num, sent_logs_num, sent_bytes = queue.get()
        data_bytes, data_num = self.tests_utils.get_api_data_bytes_and_num_from_json_data(
            self.azure_graph_json_body[AzureGraph.DEFAULT_GRAPH_DATA_LINK])

        self.assertEqual(math.ceil(sent_bytes / 2 / LogzioShipper.MAX_BULK_SIZE_BYTES) * 2, requests_num)
        self.assertEqual(data_num * 2, sent_logs_num)
        self.assertEqual(data_bytes * 2, sent_bytes)

    def test_sending_data_with_custom_fields(self) -> None:
        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               GeneralTypeOAuthApiTests.CUSTOM_FIELDS_CONFIG_FILE,
                                                               self.tests_utils.run_oauth_api_process,
                                                               status=200,
                                                               sleep_time=10)

        requests_num, sent_logs_num, sent_bytes = queue.get()
        data_bytes, data_num = self.tests_utils.get_api_data_bytes_and_num_from_json_data(
            self.azure_graph_json_body[AzureGraph.DEFAULT_GRAPH_DATA_LINK])
        custom_fields_azure_graph = self.tests_utils.get_first_api(GeneralTypeOAuthApiTests.CUSTOM_FIELDS_CONFIG_FILE,
                                                                   is_auth_api=False)
        data_bytes += data_num * self.tests_utils.get_api_custom_fields_bytes(custom_fields_azure_graph)

        self.assertEqual(math.ceil(sent_bytes / LogzioShipper.MAX_BULK_SIZE_BYTES), requests_num)
        self.assertEqual(data_num, sent_logs_num)
        self.assertEqual(data_bytes, sent_bytes)

    def test_time_interval(self) -> None:
        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               GeneralTypeOAuthApiTests.TIME_INTERVAL_CONFIG_FILE,
                                                               self.tests_utils.run_oauth_api_process,
                                                               status=200,
                                                               sleep_time=70)

        requests_num, sent_logs_num, sent_bytes = queue.get()
        data_bytes, data_num = self.tests_utils.get_api_data_bytes_and_num_from_json_data(
            self.azure_graph_json_body[AzureGraph.DEFAULT_GRAPH_DATA_LINK])

        self.assertEqual(math.ceil(sent_bytes / LogzioShipper.MAX_BULK_SIZE_BYTES), requests_num)
        self.assertEqual(data_num, sent_logs_num)
        self.assertEqual(data_bytes, sent_bytes)

    @responses.activate
    def test_last_start_date(self) -> None:
        responses.add(responses.GET, self.AZURE_GRAPH_TEST_URL,
                               body=json.dumps(GeneralTypeOAuthApiTests.azure_graph_json_body), status=200)
        base_azure_graph = self.tests_utils.get_first_api(GeneralTypeOAuthApiTests.CUSTOM_FIELDS_CONFIG_FILE,
                                                          is_auth_api=False)
        responses.add(responses.POST, base_azure_graph.get_token_request.url,
                               body=json.dumps(self.azure_graph_token_json_body), status=200)

        for _ in base_azure_graph.fetch_data():
            continue

        base_azure_graph.update_start_date_filter()

        self.assertEqual('2020-03-13T19:15:42.619583+00:00', unquote(base_azure_graph.get_last_start_date()))

    def test_bad_config(self) -> None:
        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               GeneralTypeOAuthApiTests.BAD_CONFIG_FILE,
                                                               self.tests_utils.run_oauth_api_process,
                                                               status=200,
                                                               sleep_time=1)

        requests_num, sent_logs_num, sent_bytes = queue.get()

        self.assertEqual(0, requests_num)
        self.assertEqual(0, sent_logs_num)
        self.assertEqual(0, sent_bytes)
