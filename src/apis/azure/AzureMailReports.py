import re
from datetime import datetime, UTC
from pydantic import Field

from src.apis.azure.AzureApi import AzureApi
from src.apis.general.Api import ApiFetcher
from src.apis.general.PaginationSettings import PaginationSettings
from src.apis.general.StopPaginationSettings import StopPaginationSettings


class AzureMailReports(AzureApi):
    """
    :param date_filter_key: The name of key to use for the start date filter in the request URL params.
    :param end_date_filter_key: The name of key to use for the end date filter in the request URL params.
    """
    date_filter_key: str = Field(default="StartDate", alias="start_date_filter_key")  # Overwrite parent default value
    end_date_filter_key: str = Field(default="EndDate")

    def __init__(self, **data):
        """
        Initialize request for Azure Mail Reports API.

        Example of url after initialization:
        https://url/from/input?$filter=StartDate eq datetime '2024-05-28T13:08:54Z' and EndDate eq datetime '2024-05-29T13:08:54Z'

        Example of next_url after initialization:
        https://url/from/input?$filter=StartDate eq datetime '{res.d.results.[0].EndDate}' and EndDate eq datetime 'NOW_DATE'
        """
        # Initializing the data requests
        data_request = ApiFetcher(**data.pop("data_request"),
                                  pagination=PaginationSettings(
                                      type="url",
                                      url_format="{res.d.@odata.nextLink}",
                                      stop_indication=StopPaginationSettings(field="d.results",
                                                                             condition="empty")),
                                  response_data_path="d.results")
        super().__init__(data_request=data_request, **data)

        # Structure the next URL format, to automatically update start date.
        self.data_request.update_next_url(self.data_request.url + f"?$filter={self.date_filter_key} eq datetime '{{res.d.results.[0].{self.end_date_filter_key}}}' and {self.end_date_filter_key} eq datetime 'NOW_DATE'")

        # Initialize date filter in the first data request and update the url
        fetch_start_date = self.generate_start_fetch_date()
        fetch_end_date = self._get_end_date()
        self.data_request.url = (self.data_request.next_url
                                 .replace(f"{{res.value.[0].{self.end_date_filter_key}}}", fetch_start_date)
                                 .replace("NOW_DATE", fetch_end_date))

    @staticmethod
    def _get_end_date():
        return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    def send_request(self):
        """
        1. Before sending a request, updates the end date filter in the new URL to the time now. (relevant to all
           requests besides the first request)
        2. Sends request using the super class.
        :return: all the responses that were received
        """
        # Update the end date in the URL before sending a request
        self.data_request.url = self.data_request.url.replace("NOW_DATE", self._get_end_date())

        data = super().send_request()
        return data
