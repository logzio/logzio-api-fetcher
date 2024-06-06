from datetime import datetime, timedelta
import logging
import re

from src.apis.azure.AzureApi import AzureApi
from src.apis.general.Api import ApiFetcher
from src.apis.general.PaginationSettings import PaginationSettings
from src.apis.general.StopPaginationSettings import StopPaginationSettings


DATE_FROM_END_PATTERN = re.compile(r'\S+$')


logger = logging.getLogger(__name__)


class AzureGraph(AzureApi):

    def __init__(self, **data):
        """
        Initialize request for Azure Mail Reports API/

        Example of url after initialization:
        https://url/from/input?$filter=createdDateTime gt 2024-05-28T13:08:54Z

        Example of next_url after initialization:
        https://url/from/input?$filter=createdDateTime gt {res.value.[0].createdDateTime}
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
        self.data_request.url += f"?$filter={self.date_filter_key} gt {self.generate_start_fetch_date()}"

        # Initialize data request next_url format to allow updating the date filter every call
        self.data_request.update_next_url(re.sub(DATE_FROM_END_PATTERN, f"{{res.value.[0].{self.date_filter_key}}}",
                                                 self.data_request.url))

    def send_request(self):
        """
        1. Sends request using the super class
        2. Add 1 second to the date from the end of the URL to avoid duplicates in the next call
        :return: all the responses that were received
        """
        data = super().send_request()

        # Add 1s to the time we took from the response to avoid duplicates
        org_date = re.search(DATE_FROM_END_PATTERN, self.data_request.url).group(0)
        try:
            org_date = datetime.strptime(org_date, "%Y-%m-%dT%H:%M:%SZ")
            org_date_plus_second = (org_date + timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
            self.data_request.url = re.sub(DATE_FROM_END_PATTERN, org_date_plus_second, self.data_request.url)
        except ValueError:
            logger.error(f"Failed to parse API {self.name} date in URL: {self.data_request.url}")

        return data
