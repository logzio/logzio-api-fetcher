import logging
import json
import requests

from typing import Generator, Optional
from datetime import datetime, timedelta
from dateutil import parser
from requests import Response
from .api import Api
from .data.api_http_request import ApiHttpRequest
from .data.base_data.auth_api_base_data import AuthApiBaseData
from .data.general_type_data.auth_api_general_type_data import AuthApiGeneralTypeData


logger = logging.getLogger(__name__)


class AuthApi(Api):

    def __init__(self, api_base_data: AuthApiBaseData, api_general_type_data: AuthApiGeneralTypeData) -> None:
        self._api_http_request = api_general_type_data.http_request
        super().__init__(api_base_data.base_data, api_general_type_data.general_type_data)

    def fetch_data(self) -> Generator[str, None, list[str]]:
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
                logger.info("No new data available from api {}.".format(self._base_data.name))
                return data

            if is_first_fetch:
                first_item_date = self._get_last_date(data[0])
                last_datetime_to_fetch = parser.parse(first_item_date) - timedelta(
                    days=self._base_data.settings.days_back_to_fetch)
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

        logger.info("Got {0} total data from api {1}".format(total_data_num, self._base_data.name))

        self._current_data_last_date = first_item_date

    def _build_api_url(self) -> str:
        api_url = self._api_http_request.url
        api_filters_num = self._base_data.get_filters_size()

        if api_filters_num > 0:
            api_url += '?'

        for api_filter in self._base_data.filters:
            api_url += api_filter.key + '=' + str(api_filter.value)
            api_filters_num -= 1

            if api_filters_num > 0:
                api_url += '&'

        return api_url

    def _send_request(self, url) -> Response:
        if self._api_http_request.method == ApiHttpRequest.GET_METHOD:
            response = requests.get(url=url,
                                    auth=(self._base_data.credentials.id,
                                          self._base_data.credentials.key),
                                    headers=self._api_http_request.headers)
        else:
            response = requests.post(url=url,
                                     auth=(self._base_data.credentials.id,
                                           self._base_data.credentials.key),
                                     headers=self._api_http_request.headers,
                                     data=self._api_http_request.body)

        return response
