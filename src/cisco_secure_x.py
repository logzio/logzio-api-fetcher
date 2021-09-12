import logging
import requests
import json

from typing import Generator
from datetime import datetime, timedelta
from .api import Api
from .auth_api import AuthApi
from .data.api_credentials import ApiCredentials
from .data.api_filter import ApiFilter


logger = logging.getLogger(__name__)


class CiscoSecureX(AuthApi):

    GET_EVENTS_URL = 'https://api.amp.cisco.com/v1/events?'
    MAX_EVENTS_BULK = 2500

    START_DATE_NAME = 'start_date'

    def __init__(self, api_name: str, api_credentials: ApiCredentials, api_filters: list[ApiFilter]) -> None:
        super().__init__(api_name, api_credentials, api_filters)

    def fetch_data(self) -> Generator:
        total_events = []
        total_events_num = 0
        api_url = self.__get_api_url()

        while True:
            try:
                next_url, events, events_num = self.__get_data_from_api(api_url)
            except Exception:
                raise

            total_events.extend(events)
            total_events_num += events_num

            if next_url is None or total_events_num >= CiscoSecureX.MAX_EVENTS_BULK:
                break

            api_url = next_url

        if total_events_num == 0:
            logger.info("No new events available for api {}.".format(self._name))
            return []

        logger.info("Successfully got {0} total events from api {1}.".format(total_events_num, self._name))

        for event in reversed(events):
            yield json.dumps(event)

        self.__set_last_start_date(events[0]['date'])

    def update_start_date_filter(self) -> None:
        for api_filter in self.filters:
            if api_filter.key != CiscoSecureX.START_DATE_NAME:
                continue

            api_filter.value = self.last_start_date
            return

        self.filters.append(ApiFilter(CiscoSecureX.START_DATE_NAME, self.last_start_date))

    def get_last_start_date(self) -> str:
        return self.last_start_date

    def __get_api_url(self) -> str:
        api_url = CiscoSecureX.GET_EVENTS_URL
        api_filters_num = len(self.filters)

        for api_filter in self.filters:
            api_url += api_filter.key + '=' + str(api_filter.value)
            api_filters_num -= 1

            if api_filters_num > 0:
                api_url += '&'

        return api_url

    def __get_data_from_api(self, url: str) -> tuple[str, list, int]:
        try:
            response = requests.get(url=url, auth=(self.credentials.id, self.credentials.key))
            response.raise_for_status()
        except requests.HTTPError as e:
            logger.error(
                "Something went wrong while trying to get the events from api {0}. response: {1}".format(self._name, e))

            if e.response.status_code == 400 or e.response.status_code == 401:
                raise Api.ApiError()

            raise
        except Exception as e:
            logger.error("Something went wrong in api {0}. response: {1}".format(self._name, e))
            raise

        json_data = json.loads(response.content)

        next_url = json_data['metadata']['links'].get('next')
        events = json_data['data']
        events_num = json_data['metadata']['results']['current_item_count']

        logger.info("Successfully got {0} events from api {1}.".format(events_num, self._name))

        return next_url, events, events_num

    def __set_last_start_date(self, last_start_date) -> None:
        new_start_date = str(
            datetime.strptime(last_start_date, '%Y-%m-%dT%H:%M:%S%z') + timedelta(seconds=1))
        new_start_date = new_start_date.replace(' ', 'T')
        new_start_date = new_start_date.replace(':', '%3A')

        if '+' in new_start_date:
            new_start_date = new_start_date.replace('+', '%2B')

        self.last_start_date = new_start_date
