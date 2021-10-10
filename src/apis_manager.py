import logging
import os
import signal
import threading
import requests

from typing import Optional
from requests.sessions import InvalidSchema
from .azure_graph import AzureGraph
from .config_reader import ConfigReader
from .data.logzio_connection import LogzioConnection
from .data.auth_api_data import AuthApiData
from .data.oauth_api_data import OAuthApiData
from .api import Api
from .cisco_secure_x import CiscoSecureX
from .general_auth_api import GeneralAuthApi
from .logzio_shipper import LogzioShipper


logger = logging.getLogger(__name__)


class ApisManager:

    CONFIG_FILE = 'config.yaml'
    LAST_START_DATES_FILE = 'last_start_dates.txt'

    API_GENERAL_TYPE = 'general'
    API_CISCO_SECURE_X_TYPE = 'cisco_secure_x'
    API_AZURE_GRAPH_TYPE = 'azure_graph'

    AUTH_API_TYPES = [API_GENERAL_TYPE, API_CISCO_SECURE_X_TYPE]
    OAUTH_API_TYPES = [API_GENERAL_TYPE, API_AZURE_GRAPH_TYPE]

    def __init__(self) -> None:
        self._apis: list[Api] = []
        self._logzio_connection: Optional[LogzioConnection] = None
        self._threads = []
        self._event = threading.Event()
        self._lock = threading.Lock()

    def run(self) -> None:
        if not self._read_data_from_config():
            return

        if len(self._apis) == 0:
            return

        for api in self._apis:
            self._threads.append(threading.Thread(target=self._run_api_scheduled_task, args=(api,)))

        for thread in self._threads:
            thread.start()

        signal.sigwait([signal.SIGINT, signal.SIGTERM])
        self.__exit_gracefully()

    def _read_data_from_config(self) -> bool:
        config_reader = ConfigReader(ApisManager.CONFIG_FILE, ApisManager.API_GENERAL_TYPE, ApisManager.AUTH_API_TYPES,
                                     ApisManager.OAUTH_API_TYPES)

        logzio_connection = config_reader.get_logzio_connection()

        if logzio_connection is None:
            return False

        self._logzio_connection = logzio_connection

        for auth_api_config_data in config_reader.get_auth_apis_data():
            if auth_api_config_data is None:
                return False

            self._add_auth_api(auth_api_config_data)

        for oauth_api_config_data in config_reader.get_oauth_apis_data():
            if oauth_api_config_data is None:
                return False

            self._add_oauth_api(oauth_api_config_data)

        return True

    def _add_auth_api(self, auth_api_data: AuthApiData) -> None:
        if auth_api_data.base_data.base_data.type == ApisManager.API_GENERAL_TYPE:
            self._apis.append(GeneralAuthApi(auth_api_data.base_data, auth_api_data.general_type_data))
        else:
            self._apis.append(CiscoSecureX(auth_api_data.base_data))

    def _add_oauth_api(self, oauth_api_data: OAuthApiData) -> None:
        if oauth_api_data.base_data.base_data.type == ApisManager.API_GENERAL_TYPE:
            pass
        else:
            self._apis.append(AzureGraph(oauth_api_data))

    def _run_api_scheduled_task(self, api: Api) -> None:
        logzio_shipper = LogzioShipper(self._logzio_connection.url, self._logzio_connection.token)

        for api_custom_field in api.get_api_custom_fields():
            logzio_shipper.add_custom_field_to_list(api_custom_field)

        while True:
            thread = threading.Thread(target=self._send_data_to_logzio, args=(api, logzio_shipper,))

            thread.start()
            thread.join()

            if self._event.wait(timeout=api.get_api_time_interval()):
                break

    def _send_data_to_logzio(self, api: Api, logzio_shipper: LogzioShipper) -> None:
        logger.info("Task is running for api {}...".format(api.get_api_name()))

        is_data_exist = False
        is_data_sent_successfully = True

        try:
            for data in api.fetch_data():
                is_data_exist = True
                logzio_shipper.add_log_to_send(data)

            if is_data_exist:
                logzio_shipper.send_to_logzio()
        except requests.exceptions.InvalidURL:
            logger.error("Failed to send data to Logz.io...")
            os.kill(os.getpid(), signal.SIGTERM)
            return
        except InvalidSchema:
            logger.error("Failed to send data to Logz.io...")
            os.kill(os.getpid(), signal.SIGTERM)
            return
        except requests.HTTPError as e:
            logger.error("Failed to send data to Logz.io...")
            if e.response.status_code == 401:
                os.kill(os.getpid(), signal.SIGTERM)
                return
        except Api.ApiError:
            logger.error("Failed to send data to Logz.io...")
            os.kill(os.getpid(), signal.SIGTERM)
            return
        except Exception as e:
            logger.error("Failed to send data to Logz.io...")
            is_data_sent_successfully = False

        if is_data_exist and is_data_sent_successfully:
            api.update_start_date_filter()
            self._write_last_start_date_to_file(api.get_api_name(), api.get_last_start_date())

        logger.info(
            "Task is over. A new Task for api {0} will run in {1} minute/s.".format(api.get_api_name(),
                                                                                    int(api.get_api_time_interval() / 60)))

    def _write_last_start_date_to_file(self, api_name: str, last_start_date: str) -> None:
        self._lock.acquire()

        with open(ApisManager.LAST_START_DATES_FILE, 'r+') as file:
            file_lines = file.readlines()
            line_num = self._get_api_line_num_in_file(api_name, file_lines)

            if not file_lines:
                file_lines.append("{0}: {1}\n".format(api_name, last_start_date))
            elif line_num == -1:
                file_lines.append("{0}: {1}\n".format(api_name, last_start_date))
            else:
                file_lines[line_num] = "{0}: {1}\n".format(api_name, last_start_date)

            file.seek(0)
            file.writelines(file_lines)

        self._lock.release()

    def _get_api_line_num_in_file(self, api_name: str, file_lines: list[str]) -> int:
        line_num = 0

        for line in file_lines:
            if line.split(':')[0] == api_name:
                return line_num

            line_num += 1

        return -1

    def __exit_gracefully(self) -> None:
        logger.info("Signal caught...")

        self._event.set()

        for thread in self._threads:
            thread.join()
