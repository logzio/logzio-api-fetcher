import logging
import os
import signal
import sched
import threading
import time
import re
import requests

from typing import Optional
from requests.sessions import InvalidSchema
from api import Api
from cisco_secure_x import CiscoSecureX
from logzio_shipper import LogzioShipper


logger = logging.getLogger(__name__)


class ApiHandler:

    API_ID_VAR_NAME = 'API_ID'
    API_KEY_VAR_NAME = 'API_KEY'
    API_NAME_VAR_NAME = 'API_NAME'
    START_DATE_VAR_NAME = 'START_DATE'
    TIME_INTERVAL_VAR_NAME = 'TIME_INTERVAL'
    LOGZIO_URL_VAR_NAME = 'LOGZIO_URL'
    LOGZIO_TOKEN_VAR_NAME = 'LOGZIO_TOKEN'

    CISCO_SECURE_X_API_NAME = 'cisco_secure_x'
    API_NAMES = [CISCO_SECURE_X_API_NAME]

    START_DATE_REGEX = '[12][0-9]{3}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01]) ([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]'

    TIME_INTERVAL = 10 * 60                                  # 10 min
    LAST_START_DATE_FILE_PATH = 'last_start_date.txt'

    def __init__(self) -> None:
        if not self.__are_environment_variables_valid():
            exit(0)

        self.api = self.__get_api()
        self.logzio_shipper = LogzioShipper(os.environ[ApiHandler.LOGZIO_URL_VAR_NAME],
                                            os.environ[ApiHandler.LOGZIO_TOKEN_VAR_NAME])
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.time_interval = self.__get_time_interval()
        self.scheduler_task: Optional[threading.Thread] = None

    def run(self) -> None:
        self.scheduler.enter(0, 0, self.__run_scheduler_task)
        self.scheduler.run()

        signal.sigwait([signal.SIGINT, signal.SIGTERM])
        self.__exit_gracefully()

    def __are_environment_variables_valid(self) -> bool:
        if not self.__is_environment_variable_exists(ApiHandler.API_ID_VAR_NAME):
            return False

        if not self.__is_environment_variable_exists(ApiHandler.API_KEY_VAR_NAME):
            return False

        if not self.__is_environment_variable_exists(ApiHandler.API_NAME_VAR_NAME):
            return False

        if not self.__is_environment_variable_exists(ApiHandler.LOGZIO_URL_VAR_NAME):
            return False

        if not self.__is_environment_variable_exists(ApiHandler.LOGZIO_TOKEN_VAR_NAME):
            return False

        if not self.__is_api_name_supported(os.getenv(ApiHandler.API_NAME_VAR_NAME)):
            return False

        if not self.__is_start_date_valid(os.getenv(ApiHandler.START_DATE_VAR_NAME)):
            return False

        if not self.__is_time_interval_valid(os.getenv(ApiHandler.TIME_INTERVAL_VAR_NAME)):
            return False

        return True

    def __is_environment_variable_exists(self, environment_variable_name: str) -> bool:
        if os.getenv(environment_variable_name) is None:
            logger.error("{} environment variable does not exist.".format(environment_variable_name))
            return False

        return True

    def __is_api_name_supported(self, api_name: str) -> bool:
        if api_name not in ApiHandler.API_NAMES:
            logger.error("Api name {0} does not supported. The supported apis are: {1}.".format(api_name,
                                                                                                ApiHandler.API_NAMES))
            return False

        return True

    def __is_start_date_valid(self, start_date: str) -> bool:
        if start_date is not None:
            if re.fullmatch(ApiHandler.START_DATE_REGEX, start_date) is None:
                logger.error("Start date must be in the format: `yyyy-mm-dd hh:mm:ss`")
                return False

        return True

    def __is_time_interval_valid(self, time_interval: str) -> bool:
        if time_interval is not None:
            try:
                int(time_interval)
            except ValueError:
                logger.error("Time interval must be a positive whole number.")
                return False

        return True

    def __get_start_date(self) -> Optional[str]:
        start_date = os.getenv(ApiHandler.START_DATE_VAR_NAME)

        if start_date is not None:
            return start_date

        with open(ApiHandler.LAST_START_DATE_FILE_PATH, 'r') as file:
            start_date = file.readline()

        if start_date != '':
            return start_date

        return None

    def __get_time_interval(self) -> int:
        time_interval = os.getenv(ApiHandler.TIME_INTERVAL_VAR_NAME)

        if time_interval is None:
            return int(ApiHandler.TIME_INTERVAL)

        return int(time_interval) * 60

    def __get_api(self) -> Api:
        api_name = os.environ[ApiHandler.API_NAME_VAR_NAME]
        start_date = self.__get_start_date()

        if api_name == ApiHandler.CISCO_SECURE_X_API_NAME:
            return CiscoSecureX(os.environ[ApiHandler.API_ID_VAR_NAME], os.environ[ApiHandler.API_KEY_VAR_NAME], start_date)

    def __run_scheduler_task(self) -> None:
        self.scheduler_task = threading.Thread(target=self.__send_events_to_logzio)

        self.scheduler_task.start()

    def __send_events_to_logzio(self):
        logger.info("Task is running...")

        are_events_exist = False
        are_events_sent_successfully = True

        try:
            for event in self.api.get_events():
                are_events_exist = True
                self.logzio_shipper.add_log_to_send(event)

            self.logzio_shipper.send_to_logzio()
        except requests.exceptions.InvalidURL:
            logger.error("Failed to send events to Logz.io...")
            exit(1)
        except InvalidSchema:
            logger.error("Failed to send events to Logz.io...")
            exit(1)
        except requests.HTTPError as e:
            logger.error("Failed to send events to Logz.io...")

            if e.response.status_code == 401:
                exit(1)
        except Exception:
            logger.error("Failed to send events to Logz.io...")
            are_events_sent_successfully = False

        if are_events_exist and are_events_sent_successfully:
            self.api.update_start_date()

        self.scheduler.enter(self.time_interval, 0, self.__run_scheduler_task)

        logger.info("Task is over. A new Task will run in {} minutes.".format(self.time_interval / 60))

    def __exit_gracefully(self) -> None:
        logger.info("Signal caught...")

        self.scheduler_task.join()
        self.scheduler.cancel(self.scheduler.queue[0])

        with open(ApiHandler.LAST_START_DATE_FILE_PATH, 'w') as file:
            file.write(self.api.get_last_start_date())

        logger.info("Successfully wrote last start date into {} file".format(ApiHandler.LAST_START_DATE_FILE_PATH))
