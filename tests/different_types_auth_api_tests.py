import unittest
import logging
import multiprocessing
import json
import math

from src.cisco_secure_x import CiscoSecureX
from src.logzio_shipper import LogzioShipper
from .tests_utils import TestUtils


logger = logging.getLogger(__name__)


class DifferentTypesAuthApiTests(unittest.TestCase):

    CONFIG_FILE = 'tests/config/different_types_auth_api/different_types_config.yaml'

    CISCO_SECURE_X_BODY_JSON = 'tests/api_body/cisco_secure_x_body.json'

    cisco_secure_x_json_body: dict = None

    @classmethod
    def setUpClass(cls) -> None:
        with open(cls.CISCO_SECURE_X_BODY_JSON, 'r') as json_file:
            cls.cisco_secure_x_json_body = json.load(json_file)

    def setUp(self) -> None:
        self.tests_utils = TestUtils(CiscoSecureX.HTTP_METHOD, CiscoSecureX.URL,
                                     DifferentTypesAuthApiTests.cisco_secure_x_json_body)

    def test_sending_data(self) -> None:
        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               DifferentTypesAuthApiTests.CONFIG_FILE,
                                                               self.tests_utils.run_auth_api_process,
                                                               status=200,
                                                               sleep_time=10)

        requests_num, sent_logs_num, sent_bytes = queue.get()
        data_bytes, data_num = self.tests_utils.get_api_data_bytes_and_num_from_json_data(
            self.cisco_secure_x_json_body['data'])

        self.assertEqual(math.ceil(sent_bytes / 2 / LogzioShipper.MAX_BULK_SIZE_BYTES) * 2, requests_num)
        self.assertEqual(data_num * 2, sent_logs_num)
        self.assertEqual(data_bytes * 2, sent_bytes)

    def test_sending_data_iterations(self) -> None:
        queue = multiprocessing.Queue()
        self.tests_utils.start_process_and_wait_until_finished(queue,
                                                               DifferentTypesAuthApiTests.CONFIG_FILE,
                                                               self.tests_utils.run_auth_api_process,
                                                               status=200,
                                                               sleep_time=70)

        requests_num, sent_logs_num, sent_bytes = queue.get()
        data_bytes, data_num = self.tests_utils.get_api_data_bytes_and_num_from_json_data(
            self.cisco_secure_x_json_body['data'])

        self.assertEqual(math.ceil(sent_bytes / 4 / LogzioShipper.MAX_BULK_SIZE_BYTES) * 4, requests_num)
        self.assertEqual(data_num * 4, sent_logs_num)
        self.assertEqual(data_bytes * 4, sent_bytes)
