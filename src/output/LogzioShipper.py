import gzip
import json
import logging
from pydantic import BaseModel, Field
import requests
from requests.adapters import HTTPAdapter, RetryError
from requests.sessions import InvalidSchema
from urllib3.util.retry import Retry

# Current integration version
INT_VERSION = "0.2.0"

# Size limitations
MAX_BODY_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_BULK_SIZE_BYTES = MAX_BODY_SIZE_BYTES / 10  # 1 MB
MAX_LOG_SIZE_BYTES = 500 * 1000  # 500 KB

# Retry Settings
MAX_RETRIES = 3
BACKOFF_FACTOR = 1
STATUS_FORCELIST = [500, 502, 503, 504]
CONNECTION_TIMEOUT_SECONDS = 5

logger = logging.getLogger(__name__)


class LogzioShipper(BaseModel):
    """
    Class to send data to logzio
    :param listener: The listener endpoint to send the logs to (Default: https://listener.logz.io:8071)
    :param token: Required, the logzio shipping token
    :param curr_logs: Not passed to the class, array of the logs that were yet to sent
    :param curr_bulk_size: Not passed to the class, size of the current logs bulk (of data in 'self.curr_logs')
    """
    listener: str = Field(default="https://listener.logz.io:8071", alias="url")
    token: str = Field(frozen=True)
    curr_logs: list = Field(default=[], init=False, init_var=True)
    curr_bulk_size: int = Field(default=0, init=False, init_var=True)

    def __init__(self, **data):
        super().__init__(**data)
        self.listener = f"{self.listener}/?token={self.token}"

    @staticmethod
    def _add_custom_fields_to_log(log, custom_fields):
        """
        Makes sure the given log is in JSON format (if not, makes it) and adds the given custom fields to it.
        :param log: the log
        :param custom_fields: the fields to add to it
        :return: the log in json format with the custom fields added to it
        """

        try:
            json_log = json.loads(log)
        except json.decoder.JSONDecodeError:
            json_log = {"message": log}
        except TypeError:
            json_log = log
        if custom_fields:
            json_log.update(custom_fields)
        return json.dumps(json_log)

    @staticmethod
    def _is_valid_log(log_to_send, log_size):
        """
        Validates that the given log size does not pass MAX_LOG_SIZE_BYTES.
        :param log_to_send: the actual log
        :param log_size: the log size
        :return: True if log_size < MAX_LOG_SIZE_BYTES, false otherwise
        """
        if log_size > MAX_LOG_SIZE_BYTES:
            logger.error(f"The following log size of {log_size} bytes is passing the allowed "
                         f"{MAX_LOG_SIZE_BYTES} bytes logzio limit. Not sending the log: '{log_to_send}'")
            return False
        return True

    @staticmethod
    def _get_request_retry_session(retries=MAX_RETRIES, backoff_factor=BACKOFF_FACTOR,
                                   status_forcelist=STATUS_FORCELIST):
        """
        Creates a retry session for the shipping request.
        :param retries: amount of retries
        :param backoff_factor: exponential backoff factor between attempts
        :param status_forcelist: HTTP status codes to force retry on
        :return: session object
        """
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

    def _reset_logs(self):
        """
        Removes logs from the current queue and resets the bulk size.
        """
        self.curr_logs.clear()
        self.curr_bulk_size = 0

    @staticmethod
    def _handle_exception(exp, msg, *args):
        """
        Logs the given error message and raises the exception.
        :param exp: the exception
        :param msg: error message to log regarding it
        :param args: message arguments
        """
        logger.error(msg.format(*args))
        raise exp

    def _handle_http_errors(self, status_code, exp):
        """
        Handles HTTP error codes from an exception.
        :param status_code: the HTTP status code
        :param exp: the exception itself
        """
        if status_code == 400:
            self._handle_exception(exp, "The logs are bad formatted. Response: {}", exp)
        elif status_code == 401:
            logger.error("Logzio Shipping Token is missing or invalid. Make sure you’re using the right account "
                         "token.")
            self._handle_exception(exp, "Logzio Shipping Token is missing or invalid. Make sure you’re using the right "
                                        "account token.")
        else:
            self._handle_exception(exp, "Somthing went wrong. Response: {}", exp)

    def send_to_logzio(self):
        """
        Sends logs from 'self.curr_logs' to logzio with retry mechanism.
        """
        if not self.curr_logs:
            return

        if self.curr_bulk_size == 0:
            logger.info("bulk is 0 but logs are:", self.curr_logs)

        try:
            headers = {"Content-Type": "application/json",
                       "Content-Encoding": "gzip",
                       "Logzio-Shipper": f"logzio-api-fetcher/{INT_VERSION}"}
            compressed_data = gzip.compress(str.encode('\n'.join(self.curr_logs)))
            response = self._get_request_retry_session().post(url=self.listener,
                                                              data=compressed_data,
                                                              headers=headers,
                                                              timeout=CONNECTION_TIMEOUT_SECONDS)
            response.raise_for_status()
            logger.info(f"Successfully sent bulk of {self.curr_bulk_size} bytes to Logz.io.")
            self._reset_logs()

        except requests.ConnectionError as e:
            self._handle_exception(e, "Failed to establish connection to the listener, max retries {} reached. "
                                      "Please make sure '{}' is valid. Response: {}", MAX_RETRIES, self.listener, e)
        except RetryError as e:
            self._handle_exception(e, "Something went wrong, max retries {} reached. Response: {}", MAX_RETRIES, e)
        except requests.exceptions.InvalidURL:
            self._handle_exception(requests.exceptions.InvalidURL, "Invalid url. Make sure your url is a valid url.")
        except InvalidSchema:
            self._handle_exception(InvalidSchema, "No connection adapters were found for {}. Make sure your url "
                                                  "starts with http:// or https://")
        except requests.HTTPError as e:
            self._handle_http_errors(e.response.status_code, e)
        except Exception as e:
            self._handle_exception(e, "Something went wrong. response: {}", e)

    def add_log_to_send(self, log, custom_fields=None):
        """
        Receives log to send, adds the given additional fields to it, validates it and adds it to a bulk.
        If the bulk reaches the MAX_BULK_SIZE_BYTES >> send data. Otherwise, add the logs to the bulk.
        :param log: log to add to the bulk
        :param custom_fields: custom fields to add to the log
        """
        enriched_log = self._add_custom_fields_to_log(log, custom_fields)

        if not self._is_valid_log(enriched_log, len(enriched_log)):
            return

        # Bulk size was not reached yet
        if not self.curr_bulk_size + len(enriched_log) > MAX_BULK_SIZE_BYTES:
            self.curr_logs.append(enriched_log)
            self.curr_bulk_size += len(enriched_log)
            return

        # Bulk size was reached >> send current logs and append the new logs to the new bulk
        try:
            self.send_to_logzio()
        except Exception:
            raise

        self.curr_logs.append(enriched_log)
        self.curr_bulk_size = len(enriched_log)
