import logging
import urllib.parse
import requests
import json

from typing import Generator, Optional, Any
from datetime import datetime, timedelta
from jsonpath_ng import parse
from dateutil import parser
from .api import Api
from .data.base_data.auth_api_base_data import AuthApiBaseData
from .data.general_type_data.auth_api_general_type_data import AuthApiGeneralTypeData
from .data.base_data.api_filter import ApiFilter
from .data.api_http_request import ApiHttpRequest


logger = logging.getLogger(__name__)


class AuthApi(Api):

    def __init__(self, api_base_data: AuthApiBaseData, api_general_type_data: AuthApiGeneralTypeData) -> None:
        self._base_data = api_base_data
        self._general_type_data = api_general_type_data
        self._current_data_last_date: Optional[str] = None

    def fetch_data(self) -> Generator:
        total_data_num = 0
        api_url = self._build_api_url()
        is_first_fetch = True
        is_last_data_to_fetch = False
        first_item_date: Optional[str] = None
        last_datetime_to_fetch: Optional[datetime] = None

        while True:
            try:
                next_url, data = self._get_data_from_api(api_url)
            except Exception:
                raise

            if not data:
                logger.info("No new data available from api {}.".format(self._base_data.base_data.name))
                return data

            if is_first_fetch:
                first_item_date = self._get_last_date(data[0])
                last_datetime_to_fetch = parser.parse(first_item_date) - timedelta(
                    days=self._base_data.base_data.settings.days_back_to_fetch)
                is_first_fetch = False

            for item in data:
                if not self._is_item_in_fetch_frame(item, last_datetime_to_fetch):
                    is_last_data_to_fetch = True
                    break

                yield json.dumps(item)
                total_data_num += 1

            if next_url is None or is_last_data_to_fetch:
                break

            api_url = next_url

        logger.info("Got {0} total data from api {1}".format(total_data_num, self._base_data.base_data.name))

        self._current_data_last_date = first_item_date

    def update_start_date_filter(self) -> None:
        new_start_date = self._get_new_start_date()

        filter_index = self._base_data.base_data.get_filter_index(
            self._general_type_data.general_type_data.start_date_name)

        if filter_index == -1:
            self._base_data.base_data.append_filters(ApiFilter(
                self._general_type_data.general_type_data.start_date_name, new_start_date))
            return

        self._base_data.base_data.update_filter_value(filter_index, new_start_date)

    def get_last_start_date(self) -> Optional[str]:
        for api_filter in self._base_data.base_data.filters:
            if api_filter.key != self._general_type_data.general_type_data.start_date_name:
                continue

            return api_filter.value

        return None

    def get_api_name(self):
        return self._base_data.base_data.name

    def get_api_time_interval(self) -> int:
        return self._base_data.base_data.settings.time_interval

    def get_api_custom_fields(self) -> Generator:
        for custom_field in self._base_data.base_data.custom_fields:
            yield custom_field

    def _build_api_url(self) -> str:
        api_url = self._general_type_data.http_request.url
        api_filters_num = self._base_data.base_data.get_filters_size()

        if api_filters_num > 0:
            api_url += '?'

        for api_filter in self._base_data.base_data.filters:
            api_url += api_filter.key + '=' + str(api_filter.value)
            api_filters_num -= 1

            if api_filters_num > 0:
                api_url += '&'

        return api_url

    def _get_data_from_api(self, url: str) -> tuple[Optional[str], list]:
        try:
            response = self._get_response_from_api(url)
        except Exception:
            raise

        json_data = json.loads(response.content)
        next_url = self._get_json_path_value_from_data(
            self._general_type_data.general_type_data.json_paths.next_url, json_data)
        data = self._get_json_path_value_from_data(
            self._general_type_data.general_type_data.json_paths.data, json_data)

        if data is None:
            logger.error(
                "The json path for api {}'s data is wrong. Please change your configuration.".format(
                    self._base_data.base_data.name))
            raise Api.ApiError

        data_size = len(data)

        if data:
            logger.info("Successfully got {0} data from api {1}.".format(data_size, self._base_data.base_data.name))

        return next_url, data

    def _get_response_from_api(self, url: str):
        try:
            if self._general_type_data.http_request.method == ApiHttpRequest.GET_METHOD:
                response = requests.get(url=url,
                                        auth=(self._base_data.base_data.credentials.id,
                                              self._base_data.base_data.credentials.key),
                                        headers=self._general_type_data.http_request.headers)
            else:
                response = requests.post(url=url,
                                         auth=(self._base_data.base_data.credentials.id,
                                               self._base_data.base_data.credentials.key),
                                         headers=self._general_type_data.http_request.headers,
                                         data=self._general_type_data.http_request.body)
            response.raise_for_status()
        except requests.HTTPError as e:
            logger.error(
                "Something went wrong while trying to get the data from api {0}. response: {1}".format(
                    self._base_data.base_data.name, e))

            if e.response.status_code == 400 or e.response.status_code == 401:
                raise Api.ApiError()

            raise
        except Exception as e:
            logger.error("Something went wrong with api {0}. response: {1}".format(self._base_data.base_data.name, e))
            raise

        return response

    def _get_last_date(self, first_item: dict) -> str:
        first_item_date = self._get_json_path_value_from_data(
            self._general_type_data.general_type_data.json_paths.data_date, first_item)

        if first_item_date is None:
            logger.error(
                "The json path for api {}'s data date is wrong. Please change your configuration.".format(
                    self._base_data.base_data.name))
            raise Api.ApiError

        return first_item_date

    def _get_json_path_value_from_data(self, json_path: str, data: dict) -> Any:
        match = parse(json_path).find(data)

        if not match:
            return None

        return match[0].value

    def _is_item_in_fetch_frame(self, item: dict, last_datetime_to_fetch: datetime) -> bool:
        item_date = self._get_json_path_value_from_data(
            self._general_type_data.general_type_data.json_paths.data_date, item)

        item_datetime = parser.parse(item_date)

        if item_datetime < last_datetime_to_fetch:
            return False

        return True

    def _get_new_start_date(self) -> str:
        new_start_date = str(parser.parse(self._current_data_last_date) + timedelta(seconds=1))
        new_start_date = new_start_date.replace(' ', 'T')
        new_start_date = urllib.parse.quote(new_start_date)

        return new_start_date
