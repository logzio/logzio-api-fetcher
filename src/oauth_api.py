import json
import logging
import time
import urllib.parse
from datetime import datetime, timedelta
from typing import Generator, Optional

import requests
from dateutil import parser
from .api import Api
from .data.api_filter import ApiFilter
from .data.oauth_api_config_data import OAuthApiConfigData

logger = logging.getLogger(__name__)


class OAuthApi(Api):
    OAUTH_GRANT_TYPE = 'grant_type'
    OAUTH_CLIENT_CREDENTIALS = 'client_credentials'
    OAUTH_CLIENT_ID = 'client_id'
    OAUTH_CLIENT_SECRET = 'client_secret'
    OAUTH_ACCESS_TOKEN = 'access_token'
    OAUTH_TOKEN_EXPIRE = 'expires_in'
    OAUTH_AUTHORIZATION_HEADER = 'Authorization'
    OAUTH_TOKEN_REQUEST_CONTENT_TYPE = 'content-type'
    OAUTH_APPLICATION_JSON_CONTENT_TYPE = 'application/json'

    def __init__(self, oauth_config: OAuthApiConfigData):
        self.oauth_config = oauth_config
        self.token = None
        self.token_expire = 0
        self._current_data_last_date: Optional[str] = None

    def get_token(self) -> [str, int]:
        token_response = requests.post(self.oauth_config.urls.token_url.api_url,
                                       self.oauth_config.urls.token_url.body)
        return json.loads(token_response.content)[self.OAUTH_ACCESS_TOKEN], json.loads(token_response.content)[
            self.OAUTH_TOKEN_EXPIRE]

    def get_api_name(self):
        return self.oauth_config.config_base_data.name

    def fetch_data(self) -> Generator:
        if time.time() > (self.token_expire - 60):
            self.token, token_expire = self.get_token()
            self.token_expire = time.time() + token_expire
        total_events, total_events_num = self._get_total_data_from_api()

        if not total_events:
            logger.info("No new events available for api {}.".format(self.oauth_config.config_base_data.name))
            return total_events

        logger.info("Successfully got {0} total events from api {1}.".format(total_events_num,
                                                                             self.oauth_config.config_base_data.name))

        for event in total_events:
            yield json.dumps(event)

        try:
            self._current_data_last_date = self._get_last_date_in_data(total_events)
        except Exception:
            raise

    def update_start_date_filter(self) -> None:
        new_start_date = self._get_new_start_date()

        for api_filter in self.oauth_config.config_base_data.filters:
            if api_filter.key != self.oauth_config.config_base_data.start_date_name:
                continue

            api_filter.value = new_start_date
            self.oauth_config.config_base_data.filters.append(
                ApiFilter(self.oauth_config.config_base_data.start_date_name, new_start_date))
            return

    def get_last_start_date(self) -> Optional[str]:
        for api_filter in self.oauth_config.config_base_data.filters:
            if api_filter.key != self.oauth_config.config_base_data.start_date_name:
                continue

            return api_filter.value

        return None

    def _get_total_data_from_api(self) -> tuple[list, int]:
        total_events = []
        total_events_num = 0
        api_url = self._build_api_url()

        while True:
            try:
                next_url, events, events_num = self.__get_data_from_api(api_url)
            except Exception:
                raise

            total_events.extend(events)
            total_events_num += events_num

            if next_url is None or total_events_num >= self.oauth_config.config_base_data.max_bulk_size:
                break

            api_url = next_url

        return total_events, total_events_num

    def _build_api_url(self) -> str:
        api_url = self.oauth_config.config_base_data.url.api_url
        api_filters_num = len(self.oauth_config.config_base_data.filters)

        if api_filters_num > 0:
            api_url += '?'

        for api_filter in self.oauth_config.config_base_data.filters:
            api_url += api_filter.key + '=' + str(api_filter.value)
            api_filters_num -= 1

            if api_filters_num > 0:
                api_url += '&'

        return api_url

    def __get_data_from_api(self, url: str) -> tuple[str, list, int]:
        try:
            response = requests.get(url=url,
                                    headers={self.OAUTH_AUTHORIZATION_HEADER: self.token,
                                             self.OAUTH_TOKEN_REQUEST_CONTENT_TYPE: self.OAUTH_APPLICATION_JSON_CONTENT_TYPE})
            response.raise_for_status()
        except requests.HTTPError as e:
            logger.error("Something went wrong while trying to get the events. response: {}".format(e))

            if e.response.status_code == 400 or e.response.status_code == 401:
                raise Api.ApiError()

            raise
        except Exception as e:
            logger.error("Something went wrong. response: {}".format(e))
            raise

        json_data = json.loads(response.content)

        next_url = None
        if self.oauth_config.json_paths.next_url in json_data:
            next_url = json_data[self.oauth_config.json_paths.next_url]
        data = json_data[self.oauth_config.json_paths.data]
        return next_url, data, len(data)

    def _get_last_date_in_data(self, data: list[dict]):
        last_date: Optional[datetime] = None

        for event in data:
            event_date = event.get(self.oauth_config.json_paths.data_date)

            if event_date is None:
                logger.error(
                    "The json path for api {}'s data date is wrong. Please change your configuration.".format(
                        self.oauth_config.config_base_data.name))
                raise Api.ApiError

            event_date_datetime = parser.parse(event_date) + timedelta(seconds=1)

            if last_date is None:
                last_date = event_date_datetime
                continue

            if last_date < event_date_datetime:
                last_date = event_date_datetime

        return str(last_date)

    def _get_new_start_date(self) -> str:
        new_start_date = str(parser.parse(self._current_data_last_date))
        new_start_date = new_start_date.replace(' ', 'T')
        new_start_date = urllib.parse.quote(new_start_date)

        return new_start_date

    def __set_last_start_date(self, last_start_date) -> None:
        new_start_date = str(
            datetime.strptime(last_start_date, '%Y-%m-%dT%H:%M:%S%z') + timedelta(seconds=1))
        new_start_date = new_start_date.replace(' ', 'T')
        new_start_date = new_start_date.replace(':', '%3A')

        if '+' in new_start_date:
            new_start_date = new_start_date.replace('+', '%2B')

        self.last_start_date = new_start_date
