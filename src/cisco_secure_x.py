import logging
import requests
import json

from typing import Generator
from api import Api
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


class CiscoSecureX(Api):

    GET_EVENTS_URL = 'https://api.amp.cisco.com/v1/events'
    MAX_EVENTS_BULK = 2500

    def __init__(self, api_id: str, api_key: str, start_date: str) -> None:
        super().__init__(api_id, api_key, start_date)

        if start_date is None:
            return

        self.__format_start_date(self.start_date)

    def get_events(self) -> Generator:
        events = []
        total_events = 0
        api_url = self.__get_api_url()

        while True:
            try:
                data = self.__get_data_from_api(api_url)
            except Exception:
                raise

            events.extend(data['events'])
            total_events += data['events_num']

            if data['next_url'] is None or total_events >= CiscoSecureX.MAX_EVENTS_BULK:
                break

            api_url = data['next_url']

        if total_events == 0:
            logger.info("No new events available.")
            return []

        logger.info("Successfully got {} total events from api.".format(total_events))

        for event in reversed(events):
            yield json.dumps(event)

        self.last_start_date = events[0]['date'].split('+')[0]

    def update_start_date(self) -> None:
        new_start_date = str(
            datetime.strptime(self.last_start_date, '%Y-%m-%dT%H:%M:%S') + timedelta(seconds=1))

        self.__format_start_date(new_start_date)

    def get_last_start_date(self) -> str:
        last_start_date = self.start_date.split('%2B')[0]
        last_start_date = last_start_date.replace('T', ' ')
        last_start_date = last_start_date.replace('%3A', ':')

        return last_start_date

    def __format_start_date(self, start_date: str) -> None:
        formatted_start_date = start_date.replace(' ', 'T')
        formatted_start_date = formatted_start_date.replace(':', '%3A')
        formatted_start_date += '%2B00%3A00'

        self.start_date = formatted_start_date

    def __get_api_url(self) -> str:
        if self.start_date is None:
            return CiscoSecureX.GET_EVENTS_URL

        return "{0}?start_date={1}".format(CiscoSecureX.GET_EVENTS_URL, self.start_date)

    def __get_data_from_api(self, url: str) -> dict[str, list[str], int]:
        data = {
            "next_url": None,
            "events": [],
            "events_num": 0
        }

        try:
            response = requests.get(url=url, auth=(self.api_id, self.api_key))
            response.raise_for_status()
        except requests.HTTPError as e:
            logger.error("Something went wrong while trying to get the events. response: {}".format(e))
            raise
        except Exception as e:
            logger.error("Something went wrong. response: {}".format(e))
            raise

        json_data = json.loads(response.content)

        data['next_url'] = json_data['metadata']['links'].get('next')
        data['events'] = json_data['data']
        data['events_num'] = json_data['metadata']['results']['current_item_count']

        logger.info("Successfully got {} events from api.".format(data['events_num']))

        return data
