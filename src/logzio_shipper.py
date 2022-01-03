import logging
import requests
import gzip
import json

from requests.adapters import HTTPAdapter, RetryError
from requests.sessions import InvalidSchema, Session
from urllib3.util.retry import Retry
from .data.base_data.api_custom_field import ApiCustomField


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

VERSION = "1.0.1"


class LogzioShipper:
    MAX_BODY_SIZE_BYTES = 10 * 1024 * 1024              # 10 MB
    MAX_BULK_SIZE_BYTES = MAX_BODY_SIZE_BYTES / 10      # 1 MB
    MAX_LOG_SIZE_BYTES = 500 * 1000                     # 500 KB

    MAX_RETRIES = 3
    BACKOFF_FACTOR = 1
    STATUS_FORCELIST = [500, 502, 503, 504]
    CONNECTION_TIMEOUT_SECONDS = 5

    def __init__(self, logzio_url: str, token: str) -> None:
        self._logzio_url = "{0}/?token={1}".format(logzio_url, token)
        self._logs = []
        self._bulk_size = 0
        self._custom_fields = {'type': 'api_fetcher'}

    def add_log_to_send(self, log: str) -> None:
        enriched_log = self._add_custom_fields_to_log(log)
        enriched_log_size = len(enriched_log)

        if not self._is_log_valid_to_be_sent(enriched_log, enriched_log_size):
            return

        if not self._bulk_size + enriched_log_size > LogzioShipper.MAX_BULK_SIZE_BYTES:
            self._logs.append(enriched_log)
            self._bulk_size += enriched_log_size
            return

        try:
            self.send_to_logzio()
        except Exception:
            raise

        self._logs.append(enriched_log)
        self._bulk_size = enriched_log_size

    def send_to_logzio(self) -> None:
        if self._logs is None:
            return

        try:
            headers = {"Content-Type": "application/json",
                       "Content-Encoding": "gzip",
                       "Logzio-Shipper": "logzio-azure-blob-trigger/v{0}/0/0.".format(VERSION)}
            compressed_data = gzip.compress(str.encode('\n'.join(self._logs)))
            response = self._get_request_retry_session().post(url=self._logzio_url,
                                                              data=compressed_data,
                                                              headers=headers,
                                                              timeout=LogzioShipper.CONNECTION_TIMEOUT_SECONDS)
            response.raise_for_status()
            logger.info("Successfully sent bulk of {} bytes to Logz.io.".format(self._bulk_size))
            self._reset_logs()
        except requests.ConnectionError as e:
            logger.error(
                "Can't establish connection to {0} url. Please make sure your url is a Logz.io valid url. Max retries of {1} has reached. response: {2}".format(
                    self._logzio_url, LogzioShipper.MAX_RETRIES, e))
            raise
        except RetryError as e:
            logger.error(
                "Something went wrong. Max retries of {0} has reached. response: {1}".format(LogzioShipper.MAX_RETRIES,
                                                                                             e))
            raise
        except requests.exceptions.InvalidURL:
            logger.error("Invalid url. Make sure your url is a valid url.")
            raise
        except InvalidSchema:
            logger.error(
                "No connection adapters were found for {}. Make sure your url starts with http:// or https://".format(
                    self._logzio_url))
            raise
        except requests.HTTPError as e:
            status_code = e.response.status_code

            if status_code == 400:
                logger.error("The logs are bad formatted. response: {}".format(e))
                raise

            if status_code == 401:
                logger.error("The token is missing or not valid. Make sure you’re using the right account token.")
                raise

            logger.error("Somthing went wrong. response: {}".format(e))
            raise
        except Exception as e:
            logger.error("Something went wrong. response: {}".format(e))
            raise

    def add_custom_field_to_list(self, custom_field: ApiCustomField) -> None:
        self._custom_fields[custom_field.key] = custom_field.value

    def _is_log_valid_to_be_sent(self, log: str, log_size: int) -> bool:
        if log_size > LogzioShipper.MAX_LOG_SIZE_BYTES:
            logger.error(
                "The following log's size is greater than the max log size - {0} bytes, that can be sent to Logz.io: {1}".format(
                    LogzioShipper.MAX_LOG_SIZE_BYTES, log))

            return False

        return True

    def _add_custom_fields_to_log(self, log: str) -> str:
        json_log = json.loads(log)

        for key, value in self._custom_fields.items():
            json_log[key] = value

        return json.dumps(json_log)

    def _get_request_retry_session(
            self,
            retries=MAX_RETRIES,
            backoff_factor=BACKOFF_FACTOR,
            status_forcelist=STATUS_FORCELIST
    ) -> Session:
        session = requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            status=retries,
            backoff_factor=backoff_factor,
            allowed_methods=frozenset(['GET', 'POST']),
            status_forcelist=status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retry)

        session.mount('http://', adapter)
        session.mount('https://', adapter)
        session.headers.update({"Content-Type": "application/json"})

        return session

    def _reset_logs(self) -> None:
        self._logs.clear()
        self._bulk_size = 0
