from datetime import datetime, timedelta
import logging
import re

from src.apis.azure.AzureApi import AzureApi
from src.apis.general.Api import ApiFetcher
from src.apis.general.PaginationSettings import PaginationSettings
from src.apis.general.StopPaginationSettings import StopPaginationSettings


DATE_FROM_END_PATTERN = re.compile(r'\S+$')
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

logger = logging.getLogger(__name__)


class AzureGraph(AzureApi):

    def __init__(self, **data):
        """
        Initialize request for Azure Graph API.
        """
        # Initializing the data requests
        data_request = ApiFetcher(**data.pop("data_request"),
                                  pagination=PaginationSettings(
                                      type="url",
                                      url_format="{res.@odata\\.nextLink}",
                                      stop_indication=StopPaginationSettings(field="value",
                                                                             condition="empty")),
                                  response_data_path="value")
        super().__init__(data_request=data_request, **data)

        # Initialize date filter in the first data request
        self._initialize_url_date()

        # Initialize data request next_url format
        self._initialize_next_url()

    def _initialize_url_date(self):
        """
        initializing the data request url to be in format:
        https://url/from/input?$filter=createdDateTime gt 2024-05-28T13:08:54Z
        """
        self.data_request.url += f"?$filter={self.date_filter_key} gt {self.generate_start_fetch_date()}"

    def _initialize_next_url(self):
        """
        initializing the data request next url to be in format:
        https://url/from/input?$filter=createdDateTime gt {res.value.[0].createdDateTime}

        done to allow updating the date filter with each call.
        """
        self.data_request.update_next_url(self._replace_url_date(f"{{res.value.[0].{self.date_filter_key}}}"))

    def _replace_url_date(self, req_val):
        """
        replaces the date at the end of the URL (found with regex pattern DATE_FROM_END_PATTERN) with the given req_val.
        :param req_val: the new date value
        :return: the original URL with the new req_val as the date.
        """
        return re.sub(DATE_FROM_END_PATTERN, req_val, self.data_request.url)

    def send_request(self):
        """
        1. Sends request using the super class
        2. Add 1 second to the date from the end of the URL to avoid duplicates in the next call
        :return: all the responses that were received
        """
        data = super().send_request()

        # Add 1s to the time we took from the response to avoid duplicates
        self.data_request.add_seconds_to_url_date_filter(1, DATE_FORMAT, DATE_FROM_END_PATTERN)

        return data
