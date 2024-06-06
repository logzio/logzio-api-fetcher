import logging
import os
import requests
from requests.sessions import InvalidSchema
import signal
import threading


logger = logging.getLogger(__name__)


class TaskManager:
    """
    Class to run scheduled task that collects data from given APIs and sends them with the given logzio_shipper.
    :param apis: List of ApiFetcher instances to fetch data from
    :param logzio_shipper: LogzioShipper instance to send data to
    """
    def __init__(self, apis=[], logzio_shipper=None):
        self.apis = apis
        self.logzio_shipper = logzio_shipper
        self.threads = []
        self.event = threading.Event()

    def _send_data_to_logzio(self, api):
        """
        Collects data from the API and sends it to Logzio.
        :param api: The API class instance
        """
        logger.info(f"Starting task for api {api.name}.")
        data_exists = False

        try:
            for log in api.send_request():
                data_exists = True
                self.logzio_shipper.add_log_to_send(log, api.additional_fields)
            if data_exists:
                self.logzio_shipper.send_to_logzio()

        except requests.exceptions.InvalidURL as e:
            logger.error(f"Failed to send data to Logz.io... Invalid url: {e}")
            os.kill(os.getpid(), signal.SIGTERM)
            return
        except InvalidSchema as e:
            logger.error(f"Failed to send data to Logz.io... Invalid schema: {e}")
            os.kill(os.getpid(), signal.SIGTERM)
            return
        except requests.HTTPError as e:
            logger.error(f"Failed to send data to Logz.io... HTTP error: {e}")
            if e.response.status_code == 401:
                os.kill(os.getpid(), signal.SIGTERM)
                return
        except Exception as e:
            logger.error(f"Failed to send data to Logz.io... exception: {e}")
        logger.info(f"Task finished for api {api.name}. New task will run in {api.scrape_interval_minutes} minutes.")

    def _run_api_scheduled_task(self, api):
        """
        Runs scheduled task, based on the API scrape interval, to collect and send data with _send_data_to_logzio
        function.
        :param api: The API class instance
        """
        while True:
            logger.debug(f"Starting thread to collect logs from {api.name}")
            thread = threading.Thread(target=self._send_data_to_logzio, args=(api,))
            thread.start()

            # Enforce new task to run every scrape_interval
            if self.event.wait(timeout=api.scrape_interval_minutes * 60):
                break

    def __exit_gracefully(self, signum, frame):
        """
        Clear up all threads before closing program
        :param signum: the number of signal that called the function (required for 'signal.signal' usage)
        :param frame: the frame number (required for 'signal.signal' usage)
        """
        logger.info("Signal caught... Stopping")
        self.event.set()

        for thread in self.threads:
            thread.join()

    def run(self):
        """
        Creates thread per API fetcher that runs a scheduled collection task based on the scrape interval.
        """
        if not self.apis:
            return

        for api in self.apis:
            thread = threading.Thread(target=self._run_api_scheduled_task, args=(api,))
            self.threads.append(thread)

        logger.debug(f"Configured {len(self.threads)} API inputs.")

        for thread in self.threads:
            thread.start()

        for thread in self.threads:
            thread.join()

        signal.signal(signal.SIGINT, self.__exit_gracefully)
        signal.signal(signal.SIGTERM, self.__exit_gracefully)
        signal.sigwait([signal.SIGINT, signal.SIGTERM])
