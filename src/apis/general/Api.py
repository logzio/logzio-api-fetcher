from enum import Enum
import json
import logging
from pydantic import BaseModel, Field
import requests
from typing import Union

from src.utils.processing_functions import extract_vars, substitute_vars
from src.apis.general.PaginationSettings import PaginationSettings, PaginationType
from src.utils.processing_functions import break_key_name, get_nested_value

SUCCESS_CODES = [200, 204]
logger = logging.getLogger(__name__)


class ReqMethod(Enum):
    """
    Supported methods for the API request
    """
    GET = "GET"
    POST = "POST"


class ApiFetcher(BaseModel):
    """
    Class to initialize an API request
    :param url: Required, the URL to send the request to
    :param headers: Optional, the headers to use for the request
    :param body: Optional, the body of the request
    :param method: Optional, the method to use for the request (default: GET)
    :param pagination_settings: Optional, PaginationSettings object that defines how to perform pagination
    :param next_url: Optional, If needed update a param in the url according to the response as we go
    :param response_data_path: Optional, The path to find the data within the response.
    :param additional_fields: Optional, 'key: value' pairs that should be added to the API logs.
    :param scrape_interval_minutes: the interval between scraping jobs.
    :param url_vars: Not passed to the class, array of params that is generated based on next_url.
    """
    name: str = Field(default="")
    url: str
    headers: dict = Field(default={})
    body: Union[str, dict, list] = Field(default=None)
    method: ReqMethod = Field(default=ReqMethod.GET, frozen=True)
    pagination_settings: PaginationSettings = Field(default=None, frozen=True, alias="pagination")
    next_url: str = Field(default=None)
    response_data_path: str = Field(default=None, frozen=True)
    additional_fields: dict = Field(default={})
    scrape_interval_minutes: int = Field(default=1, alias="scrape_interval", ge=1)
    url_vars: list = Field(default=[], init=False, init_var=True)

    def __init__(self, **data):
        """
        Makes sure to format the body and generate the url_vars based on next_url.
        :param data: the fields for creation of the class.
        """
        super().__init__(**data)
        self.body = self._format_body(self.body)
        self.url_vars = extract_vars(self.next_url)
        if not self.name:
            self.name = self.url
        if not self.additional_fields.get("type"):
            self.additional_fields["type"] = "api-fetcher"

    @staticmethod
    def _format_body(body):
        """
        Makes sure to 'json.dumps' dictionaries to allow valid request to be made.
        :param body: the request body.
        :return: body in format for a request.
        """
        if isinstance(body, dict) or isinstance(body, list):
            return json.dumps(body)
        return body

    def _extract_data_from_path(self, response):
        """
        Extract the value from the given 'self.response_data_path' if it exists.
        Returns array with the logs to support sending each log in a ''self.response_data_path' array as it's own log.
        :param response: the requests' response.
        :return: array with the logs to send from the response.
        """
        if self.response_data_path:
            data_path_value = get_nested_value(response, break_key_name(self.response_data_path))
            if data_path_value and isinstance(data_path_value, list):
                return data_path_value
            if data_path_value:
                return [data_path_value]
            else:
                # This is set to debug and not error since it could be expected (no new data)
                logger.debug(f"Did not find data in given '{self.response_data_path}' path. Response: {response}")
        return []

    def _make_call(self):
        """
        Sends the request and returns the response, or None if there was an issue.
        :return: the response of the request.
        """
        logger.debug(f"Sending API call with details:\nURL: {self.url}\nHeaders: {self.headers}\nBody: {self.body}")

        r = requests.request(method=self.method.value, url=self.url, headers=self.headers, data=self.body)
        if r.status_code in SUCCESS_CODES:
            try:
                return json.loads(r.text)
            except json.decoder.JSONDecodeError:
                return r.text
        else:
            logger.warning("Issue with fetching data from the API: %s", r.text)
        return None

    def _perform_pagination(self, res):
        """
        Performs pagination calls until reaches stop condition or the max allowed calls.
        :param res: the response of the first call
        """
        logger.debug(f"Starting pagination for {self.name}")
        call_count = 0
        first_url = self.url

        while not self.pagination_settings.did_pagination_end(res, call_count):

            if self.pagination_settings.pagination_type == PaginationType.URL:
                new_url = self.pagination_settings.get_next_url(res, first_url)
                if new_url:
                    self.url = new_url
                else:
                    logger.debug(f"Stopping pagination due to issue with replacing the URL.")
                    break
            elif self.pagination_settings.pagination_type == PaginationType.BODY:
                new_body = self._format_body(self.pagination_settings.get_next_body(res))
                if new_body:
                    self.body = new_body
                else:
                    logger.debug(f"Stopping pagination due to issue with replacing the Body.")
                    break
            elif self.pagination_settings.pagination_type == PaginationType.HEADERS:
                new_headers = self.pagination_settings.get_next_headers(res)
                if new_headers:
                    self.headers = new_headers
                else:
                    logger.debug(f"Stopping pagination due to issue with replacing the Headers.")
                    break

            logger.debug(f"Sending pagination call {call_count + 1} for api {self.name} in path '{self.url}'")
            res = self._make_call()
            call_count += 1

            if not res:
                # Had issue with sending request to the API, stopping the pagination
                break

            yield self._extract_data_from_path(res)

    def update_next_url(self, new_next_url):
        """
        Supports updating the next URL format to make sure the 'self.url_vars' is updated accordingly.
        :param new_next_url: new format for the next URL (relevant for customized APIs support)
        """
        self.next_url = new_next_url
        self.url_vars = extract_vars(self.next_url)

    def send_request(self):
        """
        Manages the request:
        - Calls _make_call() function to send request
        - If Pagination is configured, calls _perform_pagination
        - Updates the URL for the next request per 'next_url' if defined
        :return: all the responses that were received
        """
        responses = []
        r = self._make_call()
        if r:
            r_data_path = self._extract_data_from_path(r)

            if not r_data_path:
                logger.info(f"No new data available from api {self.name}.")
                return responses

            # New data found >> add to responses
            responses.extend(r_data_path)

            # Perform pagination
            if self.pagination_settings:
                for data in self._perform_pagination(r):
                    responses.extend(data)  # bug need to make it go through the extract data path

            # Update the url if needed
            if self.next_url:
                self.url = substitute_vars(self.next_url, self.url_vars, r)
        return responses