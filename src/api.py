import json
import logging
import urllib.parse
import requests
import xmltodict

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Generator, Any, Optional
from jsonpath_ng import parse
from dateutil import parser
from requests import Response
from .data.base_data.api_base_data import ApiBaseData
from .data.base_data.api_filter import ApiFilter
from .data.base_data.api_custom_field import ApiCustomField
from .data.general_type_data.api_general_type_data import ApiGeneralTypeData

logger = logging.getLogger(__name__)


class Api(ABC):

    def __init__(self, api_base_data: ApiBaseData, api_general_type_data: ApiGeneralTypeData):
        self._base_data = api_base_data
        self._general_type_data = api_general_type_data
        self._current_data_last_date: Optional[str] = None

    @property
    def base_data(self) -> ApiBaseData:
        return self._base_data

    @property
    def general_type_data(self) -> ApiGeneralTypeData:
        return self._general_type_data

    class ApiError(Exception):
        pass

    @abstractmethod
    def fetch_data(self) -> Generator[str, None, list[str]]:
        pass

    @abstractmethod
    def _send_request(self, url) -> Response:
        pass

    def _get_json_path_value_from_data(self, json_path: str, data: dict) -> Any:
        match = parse(json_path).find(data)

        if not match:
            return None

        return match[0].value

    def update_start_date_filter(self) -> None:
        new_start_date = self._get_new_start_date()
        filter_index = self._base_data.get_filter_index(
            self._general_type_data.start_date_name)

        # If date is a filter in the filters list, update the list value (cisco secure x).
        if filter_index != -1:
            self._base_data.update_filter_value(filter_index, new_start_date)

    def get_last_start_date(self) -> Optional[str]:
        for api_filter in self._base_data.filters:
            if api_filter.key != self._general_type_data.start_date_name:
                continue

            return api_filter.value

        return None

    def get_api_name(self):
        return self._base_data.name

    def get_api_time_interval(self) -> int:
        return self._base_data.settings.time_interval

    def get_api_custom_fields(self) -> Generator[ApiCustomField, None, None]:
        for custom_field in self._base_data.custom_fields:
            yield custom_field

    def _get_last_date(self, first_item: dict) -> str:
        first_item_date = self._get_json_path_value_from_data(
            self._general_type_data.json_paths.data_date, first_item)

        if first_item_date is None:
            logger.error(
                "The json path for api {}'s data date is wrong. Please change your configuration.".format(
                    self._base_data.name))
            raise Api.ApiError

        return first_item_date

    def _is_item_in_fetch_frame(self, item: dict, last_datetime_to_fetch: datetime) -> bool:
        item_date = self._get_json_path_value_from_data(
            self._general_type_data.json_paths.data_date, item)
        item_datetime = parser.parse(item_date)
        if item_datetime < last_datetime_to_fetch:
            return False

        return True

    def get_start_date_filter(self) -> str:
        if self._current_data_last_date is not None:
            start_date_str = self._get_new_start_date()
            new_start_date = start_date_str.split('.')[0]
        else:
            start_date = datetime.utcnow() - timedelta(days=self.base_data.settings.days_back_to_fetch)
            new_start_date = start_date.isoformat(' ', 'seconds')
            new_start_date = new_start_date.replace(' ', 'T')
            new_start_date += 'Z'
        return new_start_date

    def _get_new_start_date(self) -> str:
        new_start_date = str(parser.parse(self._current_data_last_date) + timedelta(seconds=1))
        new_start_date = new_start_date.replace(' ', 'T')
        new_start_date = urllib.parse.quote(new_start_date)

        return new_start_date

    def _get_data_from_api(self, url: str) -> tuple[Optional[str], list]:
        next_url = None
        try:
            response = self._get_response_from_api(url)
        except Exception:
            raise

        json_data = json.loads(response.content)
        if self._general_type_data.json_paths.next_url:
            next_url = self._get_json_path_value_from_data(
                self._general_type_data.json_paths.next_url, json_data)
        data = self._get_json_path_value_from_data(
            self._general_type_data.json_paths.data, json_data)
        if data is None:
            logger.error(
                "The json path for api {}'s data is wrong. Please change your configuration.".format(
                    self._base_data.name))
            raise Api.ApiError
        data_size = len(data)
        if data:
            logger.info("Successfully got {0} data from api {1}.".format(data_size, self._base_data.name))
        return next_url, data

    def _get_response_from_api(self, url: str) -> Response:
        try:
            response = self._send_request(url)
            response.raise_for_status()
        except requests.HTTPError as e:
            logger.error(
                "Something went wrong while trying to get the data from api {0}. response: {1}".format(
                    self._base_data.name, e))
            if e.response.status_code == 400 or e.response.status_code == 401:
                raise Api.ApiError()
            raise
        except Exception as e:
            logger.error("Something went wrong with api {0}. response: {1}".format(self._base_data.name, e))
            raise
        return response
