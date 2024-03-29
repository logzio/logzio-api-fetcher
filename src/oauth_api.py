import json
import logging
import time
import requests

from datetime import datetime, timedelta
from typing import Generator, Optional
from dateutil import parser
from requests import Response
from .api import Api
from .data.api_http_request import ApiHttpRequest
from .data.base_data.oauth_api_base_data import OAuthApiBaseData
from .data.general_type_data.oauth_api_general_type_data import OAuthApiGeneralTypeData

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
    OAUTH_TOKEN_BEARER_PREFIX = 'Bearer '

    def __init__(self, oauth_config: OAuthApiBaseData, general_config: OAuthApiGeneralTypeData):
        self.token = None
        self.token_expire = 0
        self._token_request = oauth_config.token_http_request
        self._data_request = oauth_config.data_http_request
        super().__init__(oauth_config.base_data, general_config.general_type_data)

    def get_token(self) -> [str, int]:
        token_response = requests.post(self._token_request.url,
                                       self._token_request.body)
        return json.loads(token_response.content)[self.OAUTH_ACCESS_TOKEN], json.loads(token_response.content)[
            self.OAUTH_TOKEN_EXPIRE]

    def fetch_data(self) -> Generator:
        if time.time() > (self.token_expire - 60):
            self.token, token_expire = self.get_token()
            self.token_expire = time.time() + int(token_expire)
        return self._get_total_data_from_api()

    def _get_total_data_from_api(self) -> Generator:
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
                self._set_current_data_last_date(first_item_date)
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

        self._set_current_data_last_date(first_item_date)

    def _build_api_url(self) -> str:
        api_url = self._data_request.url
        api_filters_num = self._base_data.get_filters_size()

        if api_filters_num > 0:
            api_url += '?'

        for api_filter in self._base_data.filters:
            api_url += api_filter.key + '=' + str(api_filter.value)
            api_filters_num -= 1

            if api_filters_num > 0:
                api_url += '&'

        return api_url

    def _send_request(self, url: str) -> Response:
        request_headers = {self.OAUTH_AUTHORIZATION_HEADER: f"Bearer {self.token}",
                           self.OAUTH_TOKEN_REQUEST_CONTENT_TYPE: self.OAUTH_APPLICATION_JSON_CONTENT_TYPE}
        if self._data_request.headers is not None:
            request_headers.update(self._data_request.headers)
        if self._data_request.method == ApiHttpRequest.GET_METHOD:
            response = requests.get(url=url,
                                    headers=request_headers,
                                    data=self._data_request.body)
        else:
            response = requests.post(url=url,
                                     headers=request_headers,
                                     data=json.dumps(self._data_request.body))

        return response

    @property
    def get_data_request(self):
        return self._data_request

    @property
    def get_token_request(self):
        return self._token_request

    def _set_current_data_last_date(self, date):
        if date:
            self._current_data_last_date = date

