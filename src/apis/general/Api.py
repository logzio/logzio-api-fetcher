from enum import Enum
import json
import logging
from pydantic import BaseModel, Field
import requests
from typing import Union, Optional
from re import search
from datetime import datetime, timedelta

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
    :param next_body: Optional, If needed update a param in the body according to the response as we go
    :param response_data_path: Optional, The path to find the data within the response.
    :param additional_fields: Optional, 'key: value' pairs that should be added to the API logs.
    :param scrape_interval_minutes: the interval between scraping jobs.
    :param url_vars: Not passed to the class, array of params that is generated based on next_url.
    :param body_vars: Not passed to the class, array of params that is generated based on next_body.
    """
    name: str = Field(default="")
    url: str
    headers: dict = Field(default={})
    body: Union[str, dict, list] = Field(default=None)
    method: ReqMethod = Field(default=ReqMethod.GET, frozen=True)
    pagination_settings: Optional[PaginationSettings] = Field(default=None, frozen=True, alias="pagination")
    next_url: str = Field(default=None)
    next_body: Union[str, dict, list] = Field(default=None)
    response_data_path: str = Field(default=None, frozen=True)
    additional_fields: dict = Field(default={})
    scrape_interval_minutes: int = Field(default=1, alias="scrape_interval", ge=1)
    url_vars: list = Field(default=[], init=False, init_var=True)
    body_vars: list = Field(default=[], init=False, init_var=True)

    def __init__(self, **data):
        """
        Makes sure to format the body and generate the url_vars based on next_url and body_vars based on next_body.
        :param data: the fields for creation of the class.
        """
        super().__init__(**data)
        self.body = self._format_body(self.body)
        self.next_body = self._format_body(self.next_body)
        self.url_vars = extract_vars(self.next_url)
        self.body_vars = extract_vars(self.next_body)
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
        return [response]

    def _make_call(self):
        """
        Sends the request and returns the response, or None if there was an issue.
        :return: the response of the request.
        """
        logger.debug(f"Sending API call with details:\nURL: {self.url}\nHeaders: {self.headers}\nBody: {self.body}")

        try:
            r = requests.request(method=self.method.value, url=self.url, headers=self.headers, data=self.body)
            r.raise_for_status()
        except requests.ConnectionError:
            logger.error(f"Failed to establish connection to the {self.name} API.")
            return None
        except requests.HTTPError as e:
            logger.error(f"Failed to get data from {self.name} API due to error {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to send request to {self.name} API due to error {e}")
            return None

        if r.status_code in SUCCESS_CODES:
            try:
                return json.loads(r.text)
            except json.decoder.JSONDecodeError:
                return r.text
        else:
            logger.warning(f"Issue with fetching data from {self.name} API: %s", r.text)
        return None

    def _prepare_pagination_next_call(self, res, first_url):
        """
        Updates the next pagination call according to the response from the last call.
        :param res: the response from the last call
        :param first_url: needed to support in URL pagination option to append params to the same base URL
        :return: True if succeeded to update the pagination request, False if failed.
        """
        # URL Pagination
        if self.pagination_settings.pagination_type == PaginationType.URL:
            new_url = self.pagination_settings.get_next_url(res, first_url)
            if new_url:
                self.url = new_url
            else:
                logger.debug(f"Stopping pagination due to issue with replacing the URL.")
                return False

        # Body Pagination
        elif self.pagination_settings.pagination_type == PaginationType.BODY:
            new_body = self._format_body(self.pagination_settings.get_next_body(res))
            if new_body:
                self.body = new_body
            else:
                logger.debug(f"Stopping pagination due to issue with replacing the Body.")
                return False

        # Headers Pagination
        else:
            new_headers = self.pagination_settings.get_next_headers(res)
            if new_headers:
                self.headers = new_headers
            else:
                logger.debug(f"Stopping pagination due to issue with replacing the Headers.")
                return False
        return True

    def _revert_pagination_changes(self, org_url, org_headers, org_body):
        """
        The pagination changes the original request information.
        After it's done, we want to make sure we go reset the info to the original needed request.
        Specifically for the URL, we will only reset it if there is no next_url defined (because otherwise it will be
        overwritten anyway after the end of the pagination).
        :param org_url: the original request URL
        :param org_headers: the original request headers
        :param org_body: the original request body
        """
        if self.pagination_settings.pagination_type == PaginationType.URL and not self.next_url:
            self.url = org_url
        elif self.pagination_settings.pagination_type == PaginationType.BODY:
            self.body = org_body
        else:
            self.headers = org_headers

    def _perform_pagination(self, res):
        """
        Performs pagination calls until reaches stop condition or the max allowed calls.
        :param res: the response of the first call
        """
        logger.debug(f"Starting pagination for {self.name}")
        call_count = 0
        first_url = self.url
        org_headers = self.headers
        org_body = self.body

        while not self.pagination_settings.did_pagination_end(res, call_count):

            # Prepare the next call, if fails >> stop pagination
            if not self._prepare_pagination_next_call(res, first_url):
                break

            logger.debug(f"Sending pagination call {call_count + 1} for api {self.name} in path '{self.url}'")
            res = self._make_call()
            call_count += 1

            if not res:
                # Had issue with sending request to the API, stopping the pagination
                break

            yield self._extract_data_from_path(res)

        self._revert_pagination_changes(first_url, org_headers, org_body)

    def update_next_url(self, new_next_url):
        """
        Supports updating the next URL format to make sure the 'self.url_vars' is updated accordingly.
        :param new_next_url: new format for the next URL (relevant for customized APIs support)
        """
        self.next_url = new_next_url
        self.url_vars = extract_vars(self.next_url)

    def update_next_body(self, new_next_body):
        """
        Supports updating the next request body format to make sure the 'self.body_vars' is updated accordingly.
        :param new_next_body: new format for the next body. (if in future some customized APIs will need it supported)
        """
        self.next_body = new_next_body
        self.body_vars = extract_vars(self.next_body)

    def add_seconds_to_url_date_filter(self, seconds, date_format, date_re_pattern):
        """
        Replaces the date in the URL with a new date that is 'seconds' seconds later to prevent getting duplicate data.
        This method is not called by default, to use it a subclass API should call it.
        :param seconds: seconds to add to the date
        :param date_format: the required format of the date in the URL
        :param date_re_pattern: the regex pattern to find the date in the URL
        """
        try:
            org_date = search(date_re_pattern, self.url).group(1)
            org_date_date = datetime.strptime(org_date, date_format)
            org_date_plus_second = (org_date_date + timedelta(seconds=seconds)).strftime(date_format)
            self.url = self.url.replace(org_date, org_date_plus_second)
        except IndexError:
            logger.error(f"Failed to add {seconds}s to the {self.name} api filter value, on url {self.url}")
        except ValueError:
            logger.error(f"Failed to parse API {self.name} date in URL: {self.url}")

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
                    responses.extend(data)

            # Update the url if needed
            if self.next_url:
                self.url = substitute_vars(self.next_url, self.url_vars, r)

            # Update the body if needed
            if self.next_body:
                self.body = substitute_vars(self.next_body, self.body_vars, r)
        return responses
