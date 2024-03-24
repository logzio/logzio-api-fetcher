import logging
import httpretty
import multiprocessing
import requests
import json
import gzip
import time
import os
import signal

from typing import Callable
from logging.config import fileConfig
from src.apis_manager import ApisManager
from src.api import Api
from src.azure_graph import AzureGraph
from src.config_reader import ConfigReader
from src.general_auth_api import GeneralAuthApi
from src.cisco_secure_x import CiscoSecureX
from src.oauth_api import OAuthApi

fileConfig('tests/logging_config.ini', disable_existing_loggers=False)
logger = logging.getLogger(__name__)


class TestUtils:
    LOGZIO_HTTPPRETTY_URL = 'https://listener.logz.io:8071/?token=123456789a&type=api_fetcher'
    LOGZIO_URL = 'https://listener.logz.io:8071'
    LOGZIO_TOKEN = '123456789a'
    LAST_START_DATES_FILE = 'tests/last_start_dates.txt'

    def __init__(self, api_http_method: str, api_url: str, api_body: dict, token_http_method: str = None,
                 token_url: str = None, token_body: dict = None, second_http_method: str = None,
                 second_api_url: str = None, second_api_body: dict = None) -> None:
        self.api_http_method = api_http_method
        self.api_url = api_url
        self.api_body = api_body
        self.token_http_method = token_http_method
        self.token_url = token_url
        self.token_body = token_body
        self.second_http_method = second_http_method
        self.second_api_url = second_api_url
        self.second_api_body = second_api_body

    def start_process_and_wait_until_finished(self, queue: multiprocessing.Queue, config_file: str,
                                              delegate: Callable[[str], None], status: int, sleep_time: int,
                                              is_multi_test: bool = False) -> None:
        process = multiprocessing.Process(target=delegate, args=(config_file, status, queue, is_multi_test))
        process.start()
        process.join()

        time.sleep(sleep_time)
        os.kill(process.pid, signal.SIGTERM)
        

    @httpretty.activate
    def run_auth_api_process(self, config_file: str, status: int, queue: multiprocessing.Queue,
                             is_multi_test: bool) -> None:
        httpretty.register_uri(self.api_http_method, self.api_url, body=json.dumps(self.api_body), status=200)
        httpretty.register_uri(httpretty.POST, TestUtils.LOGZIO_URL, status=status)

        ApisManager.CONFIG_FILE = config_file
        ApisManager.LAST_START_DATES_FILE = TestUtils.LAST_START_DATES_FILE
        logzio_requests = []

        ApisManager().run()

        for request in httpretty.latest_requests():
            if request.url.startswith(self.api_url):
                continue

            logzio_requests.append(request)

        queue.put(self._get_sending_data_results(logzio_requests))

    @httpretty.activate
    def run_oauth_api_process(self, config_file: str, status: int, queue: multiprocessing.Queue,
                              is_multi_test: bool) -> None:
        from tests.azure_graph_api_tests import AzureGraphApiTests
        httpretty.register_uri(httpretty.POST, TestUtils.LOGZIO_URL, status=status)
        httpretty.register_uri(self.token_http_method,
                               self.token_url,
                               body=json.dumps(self.token_body))
        httpretty.register_uri(self.api_http_method, self.api_url, body=json.dumps(self.api_body), status=200,
                               headers={AzureGraph.OAUTH_AUTHORIZATION_HEADER:
                                            AzureGraphApiTests.AZURE_GRAPH_TEST_TOKEN})
        if is_multi_test:
            httpretty.register_uri(self.second_http_method, self.second_api_url, body=json.dumps(self.second_api_body),
                                   status=200)

        ApisManager.CONFIG_FILE = config_file
        ApisManager.LAST_START_DATES_FILE = TestUtils.LAST_START_DATES_FILE
        logzio_requests = []

        ApisManager().run()

        for request in httpretty.latest_requests():
            if request.url.startswith(self.api_url):
                continue

            logzio_requests.append(request)

        queue.put(self._get_sending_data_results(logzio_requests))

    def get_first_api(self, config_file: str, is_auth_api: bool) -> Api:
        base_config_reader = ConfigReader(config_file, ApisManager.API_GENERAL_TYPE,
                                          ApisManager.AUTH_API_TYPES, ApisManager.OAUTH_API_TYPES)

        if is_auth_api:
            for auth_api_data in base_config_reader.get_auth_apis_data():
                if auth_api_data.base_data.base_data.type == ApisManager.API_GENERAL_TYPE:
                    return GeneralAuthApi(auth_api_data.base_data, auth_api_data.general_type_data)

                return CiscoSecureX(auth_api_data.base_data)

        for oauth_api_data in base_config_reader.get_oauth_apis_data():
            if oauth_api_data.base_data.base_data.type == ApisManager.API_GENERAL_TYPE:
                return OAuthApi(oauth_api_data.base_data, oauth_api_data.general_type_data)

            return AzureGraph(oauth_api_data)

    def get_cisco_secure_x_api_total_data_bytes_and_num(self, config_file: str) -> tuple[int, int]:
        url = CiscoSecureX.URL
        config_reader = ConfigReader(config_file, ApisManager.API_GENERAL_TYPE,
                                     ApisManager.AUTH_API_TYPES, ApisManager.OAUTH_API_TYPES)
        cisco_secure_x = None
        total_data_bytes = 0
        total_data_num = 0

        for auth_api_data in config_reader.get_auth_apis_data():
            cisco_secure_x = CiscoSecureX(auth_api_data.base_data)

        while True:
            response = requests.get(url=url, auth=(cisco_secure_x.base_data.credentials.id,
                                                   cisco_secure_x.base_data.credentials.key))
            json_data = json.loads(response.content)

            data_bytes, data_num = self.get_api_data_bytes_and_num_from_json_data(json_data['data'])
            total_data_bytes += data_bytes
            total_data_num += data_num

            next_url = json_data['metadata']['links'].get('next')

            if next_url is None:
                break

            url = next_url

        return total_data_bytes, total_data_num

    def get_azure_graph_api_total_data_bytes_and_num(self, config_file: str) -> tuple[int, int]:
        config_reader = ConfigReader(config_file, ApisManager.API_GENERAL_TYPE,
                                     ApisManager.AUTH_API_TYPES, ApisManager.OAUTH_API_TYPES)
        azure_graph = None
        total_data_bytes = 0
        total_data_num = 0

        for oauth_api_data in config_reader.get_oauth_apis_data():
            azure_graph = AzureGraph(oauth_api_data)
            token, token_expire = azure_graph.get_token()

        url = self.api_url
        while True:
            response = requests.get(url=url, headers={OAuthApi.OAUTH_AUTHORIZATION_HEADER:
                                                          token,
                                                      AzureGraph.OAUTH_TOKEN_REQUEST_CONTENT_TYPE: AzureGraph.OAUTH_APPLICATION_JSON_CONTENT_TYPE})
            json_data = json.loads(response.content)
            data_bytes, data_num = self.get_api_data_bytes_and_num_from_json_data(
                json_data[AzureGraph.DEFAULT_GRAPH_DATA_LINK])
            total_data_bytes += data_bytes
            total_data_num += data_num
            next_url = json_data.get(AzureGraph.NEXT_LINK)

            if next_url is None:
                break

            url = next_url

        return total_data_bytes, total_data_num

    def get_api_custom_fields_bytes(self, api: Api) -> int:
        custom_fields: dict = {}

        for custom_field in api.base_data.custom_fields:
            custom_fields[custom_field.key] = custom_field.value

        return len(json.dumps(custom_fields))

    def get_last_start_dates_file_lines(self) -> list[str]:
        with open(TestUtils.LAST_START_DATES_FILE, 'r') as file:
            file_lines = file.readlines()

        return file_lines

    def get_api_fetch_data_bytes_and_num(self, api: Api) -> tuple[int, int]:
        fetched_data_bytes = 0
        fetched_data_num = 0
        for data in api.fetch_data():
            fetched_data_bytes += len(data)
            fetched_data_num += 1

        return fetched_data_bytes, fetched_data_num

    def get_api_data_bytes_and_num_from_json_data(self, json_data: list) -> tuple[int, int]:
        data_num = 0
        data_bytes = 0
        for data in json_data:
            data_num += 1
            data_bytes += len(json.dumps(data))

        return data_bytes, data_num

    def _get_sending_data_results(self, latest_requests: list) -> tuple[int, int, int]:
        requests_num = 0
        sent_logs_num = 0
        sent_bytes = 0

        for request in latest_requests:
            if request.url == self.LOGZIO_HTTPPRETTY_URL:
                requests_num += 1

                try:
                    decompressed_gzip = gzip.decompress(request.parsed_body).splitlines()
                except TypeError:
                    continue

                for log in decompressed_gzip:
                    sent_logs_num += 1
                    sent_bytes += len(log)

        return int(requests_num / 2), int(sent_logs_num / 2), int(sent_bytes / 2)
