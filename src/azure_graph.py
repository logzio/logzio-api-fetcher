import logging
import requests
import json
import time

from typing import Generator
from api import Api
from datetime import datetime, timedelta

from src.data.azure_graph_config_data import AzureGraphConfigData
from src.oauth_api import OAuthApi

logger = logging.getLogger(__name__)


class AzureGraph(OAuthApi):
    GET_TOKEN_URL = 'https://login.microsoftonline.com/{}/oauth2/token'
    NEXT_LINK = '@odata.nextLink'
    MAX_EVENTS_BULK = 2500

    def __init__(self, config_data: AzureGraphConfigData) -> None:
        super().__init__(config_data.oauth_config.config_base_data.credentials.id,
                         config_data.oauth_config.config_base_data.credentials.key,
                         config_data.oauth_config.config_base_data.start_date_name)
        self.tenant_id = config_data.azure_ad_client.tenant_id
        self.token_expire = 0
        self.token = ''
        self.data_url = config_data.oauth_config.urls.data_url + "?$top=100"
        self.token_url = config_data.oauth_config.urls.token_url
        self.config_data = config_data

    def get_token(self) -> list:
        token_response = requests.post(self.GET_TOKEN_URL.format(self.tenant_id),
                                       [("grant_type", "client_credentials"), ("client_id", self.api_id)
                                           , ("scope", self.config_data.azure_ad_client.scope)
                                           , ("client_secret", self.api_key)])
        return [json.loads(token_response.content)["access_token"], json.loads(token_response.content)["expires_in"]]

    def fetch_data(self) -> Generator:
        total_data = []
        if time.time() > (self.token_expire - 60):
            token_data = self.get_token()
            self.token_expire = time.time() + int(token_data[1])
            self.token = token_data[0]

        while True:
            try:
                next_url, data, data_length = self.__get_data_from_api(self.data_url)
            except Exception:
                raise

            total_data.extend(data)
            total_data_length = len(data)

            if next_url is None:
                break

        if total_data_length == 0:
            logger.info("No new data available.")
            return []

        logger.info("Successfully got {} total logs from api.".format(total_data_length))

        for data in reversed(total_data):
            yield json.dumps(data)

    def update_start_date_filter(self) -> None:
        for api_filter in self.api_filters:
            if api_filter['key'] != 'start_date':
                continue

            api_filter['key'] = self.last_start_date
            return

        self.api_filters.append({'key': 'start_date', 'value': self.last_start_date})

    def get_last_start_date(self) -> str:
        return self.last_start_date

    def update_start_date_filter(self) -> None:
        for api_filter in self.api_filters:
            if api_filter['key'] != 'start_date':
                continue

            api_filter['key'] = self.last_start_date
            return

        self.api_filters.append({'key': 'start_date', 'value': self.last_start_date})

    def get_last_start_date(self) -> str:
        return self.last_start_date

    def __get_api_url(self) -> str:
        api_url = self.data_url
        api_filters_num = len(self.api_filters)
        if api_filters_num > 0:
            api_url += "?$filter="
        for api_filter in self.api_filters:
            api_url += api_filter['key'] + '=' + str(api_filter['value'])
            api_filters_num -= 1

            if api_filters_num > 0:
                api_url += '&'

        return api_url

    def __get_data_from_api(self, url: str) -> tuple[str, list, int]:
        try:
            response = requests.get(url=url,
                                    headers={"Authorization": self.token, "content-type": "application/json"})
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
        if self.NEXT_LINK in json_data:
            next_url = json_data[self.NEXT_LINK]
        data = json_data['value']
        return next_url, data, len(data)

    # def __set_last_start_date(self, last_start_date) -> None:
    #     new_start_date = str(
    #         datetime.strptime(last_start_date, '%Y-%m-%dT%H:%M:%S%z') + timedelta(seconds=1))
    #     new_start_date = new_start_date.replace(' ', 'T')
    #     new_start_date = new_start_date.replace(':', '%3A')
    #
    #     if '+' in new_start_date:
    #         new_start_date = new_start_date.replace('+', '%2B')
    #
    #     self.last_start_date = new_start_date_api(self, url: str) -> tuple[str, list, int]:
    #     try:
    #         response = requests.get(url=url,
    #                                 headers={"Authorization": self.token, "content-type": "application/json"})
    #         response.raise_for_status()
    #     except requests.HTTPError as e:
    #         logger.error("Something went wrong while trying to get the events. response: {}".format(e))
    #
    #         if e.response.status_code == 400 or e.response.status_code == 401:
    #             raise Api.ApiError()
    #
    #         raise
    #     except Exception as e:
    #         logger.error("Something went wrong. response: {}".format(e))
    #         raise
    #
    #     json_data = json.loads(response.content)
    #
    #     next_url=''
    #     if self.NEXT_LINK in json_data:
    #         next_url = json_data[self.NEXT_LINK]
    #     data = json_data['value']
    #
    #     logger.info("Successfully got {} events from api.".format(len(data)))
    #
    #     return next_url, data, len(data)

    def __set_last_start_date(self, last_start_date) -> None:
        new_start_date = str(
            datetime.strptime(last_start_date, '%Y-%m-%dT%H:%M:%S%z') + timedelta(seconds=1))
        new_start_date = new_start_date.replace(' ', 'T')
        new_start_date = new_start_date.replace(':', '%3A')

        if '+' in new_start_date:
            new_start_date = new_start_date.replace('+', '%2B')

        self.last_start_date = new_start_date
