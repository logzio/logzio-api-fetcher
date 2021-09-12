import logging
import os
import signal
import sys
import threading
import requests

from requests.sessions import InvalidSchema
from .config_reader import ConfigReader
from .data.auth_api_config_data import AuthApiConfigData
from .data.oauth_api_config_data import OAuthApiConfigData
from .api import Api
from .cisco_secure_x import CiscoSecureX
from .general_auth_api import GeneralAuthApi
from .logzio_shipper import LogzioShipper


logger = logging.getLogger(__name__)


class ApisManager:

    CONFIG_FILE = 'config.yaml'
    LAST_START_DATES_FILE = 'last_start_date.txt'

    API_GENERAL_TYPE = 'general'
    API_CISCO_SECURE_X_TYPE = 'cisco_secure_x'
    API_AZURE_GRAPH_TYPE = 'azure_graph'
    API_TYPES = [API_GENERAL_TYPE, API_CISCO_SECURE_X_TYPE, API_AZURE_GRAPH_TYPE]

    def __init__(self) -> None:
        self.apis: list[Api] = []
        self.logzio_shipper = None
        self.settings = None
        self.threads = []
        self.event = threading.Event()
        self.lock = threading.Lock()

        if not self._read_data_from_config():
            sys.exit(1)

    def run(self) -> None:
        if len(self.apis) == 0:
            return

        for api in self.apis:
            self.threads.append(threading.Thread(target=self.__run_scheduled_tasks, args=(api,)))

        for thread in self.threads:
            thread.start()

        signal.sigwait([signal.SIGINT, signal.SIGTERM])
        self.__exit_gracefully()

    def _read_data_from_config(self) -> bool:
        config_reader = ConfigReader(ApisManager.CONFIG_FILE, ApisManager.API_GENERAL_TYPE)

        logzio_config_data = config_reader.get_logzio_config_data()

        if logzio_config_data is None:
            return False

        self.logzio_shipper = LogzioShipper(logzio_config_data.url, logzio_config_data.token)

        settings_config_data = config_reader.get_settings_config_data()

        if settings_config_data is None:
            return False

        self.settings = settings_config_data

        for auth_api_config_data in config_reader.get_auth_apis_config_data():
            if auth_api_config_data is None:
                return False

            if not self._add_auth_api(auth_api_config_data):
                return False

        for oauth_api_config_data in config_reader.get_oauth_apis_config_data():
            if oauth_api_config_data is None:
                return False

            if not self._add_oauth_api(oauth_api_config_data):
                return False

        return True

    def _add_auth_api(self, auth_api_config_data: AuthApiConfigData) -> bool:
        if auth_api_config_data.type == ApisManager.API_GENERAL_TYPE:
            self.apis.append(GeneralAuthApi(auth_api_config_data.name, auth_api_config_data.credentials,
                                            auth_api_config_data.filters, auth_api_config_data.url,
                                            auth_api_config_data.start_date_name, auth_api_config_data.json_paths))
            return True

        if auth_api_config_data.type == ApisManager.API_CISCO_SECURE_X_TYPE:
            self.apis.append(CiscoSecureX(auth_api_config_data.name, auth_api_config_data.credentials,
                                          auth_api_config_data.filters))
            return True

        logger.error("the auth api {0} has an unsupported type - {1}".format(auth_api_config_data.name,
                                                                             auth_api_config_data.type))
        return False

    def _add_oauth_api(self, oauth_api_config_data: OAuthApiConfigData):
        if oauth_api_config_data.type == ApisManager.API_GENERAL_TYPE:
            pass

        if oauth_api_config_data.type == ApisManager.API_AZURE_GRAPH_TYPE:
            pass

        logger.error("One of the oauth api {0} has an unsupported type - {1}".format(oauth_api_config_data.name,
                                                                                     oauth_api_config_data.type))
        return False

    def __run_scheduled_tasks(self, api: Api):
        while True:
            thread = threading.Thread(target=self.__send_data_to_logzio, args=(api,))

            thread.start()
            thread.join()

            if self.event.wait(timeout=self.settings.time_interval):
                break

    def __send_data_to_logzio(self, api: Api):
        logger.info("Task is running for api {}...".format(api.get_api_name()))

        is_data_exist = False
        is_data_sent_successfully = True

        try:
            for data in api.fetch_data():
                is_data_exist = True
                self.logzio_shipper.add_log_to_send(data)

            self.logzio_shipper.send_to_logzio()
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
        except Exception:
            logger.error("Failed to send data to Logz.io...")
            is_data_sent_successfully = False

        if is_data_exist and is_data_sent_successfully:
            api.update_start_date_filter()
            self._write_last_start_date_to_file(api.get_api_name(), api.get_last_start_date())

        logger.info(
            "Task is over. A new Task for api {0} will run in {1} minutes.".format(api.get_api_name(),
                                                                                   self.settings.time_interval / 60))

    def _write_last_start_date_to_file(self, api_name: str, last_start_date: str):
        self.lock.acquire()

        with open(ApisManager.LAST_START_DATES_FILE, 'r+') as file:
            file_lines = file.readlines()
            line_num = self._get_api_line_num_in_file(api_name, file_lines)

            if line_num == -1:
                file_lines.append("{0}: {1}".format(api_name, last_start_date))
            else:
                file_lines[line_num] = "{0}: {1}".format(api_name, last_start_date)

            file.seek(0)
            file.writelines(file_lines)

        self.lock.release()

    def _get_api_line_num_in_file(self, api_name: str, file_lines: list[str]) -> int:
        line_num = -1

        for line in file_lines:
            line_num += 1

            if line.startswith(api_name):
                break

        return line_num

    def __exit_gracefully(self) -> None:
        logger.info("Signal caught...")

        self.event.set()

        for thread in self.threads:
            thread.join()
