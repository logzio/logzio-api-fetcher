from datetime import datetime, timedelta, UTC
import logging
from pydantic import Field
import re

from src.apis.general.Api import ApiFetcher
from src.apis.general.PaginationSettings import PaginationSettings
from src.apis.general.StopPaginationSettings import StopPaginationSettings


DATE_FILTER_PARAMETER = "since="
FIND_DATE_PATTERN = re.compile(r'since=(\S+?)(?:&|$)')

logger = logging.getLogger(__name__)


class Cloudflare(ApiFetcher):
    """
    :param cloudflare_account_id: The CloudFlare Account ID
    :param cloudflare_bearer_token: The cloudflare Bearer token
    :param pagination_off: True if pagination should be off, False otherwise
    :param days_back_fetch: Amount of days to fetch back in the first request, Optional (adds a filter on 'since')
    """
    cloudflare_account_id: str = Field(frozen=True)
    cloudflare_bearer_token: str = Field(frozen=True)
    pagination_off: bool = Field(default=False)
    days_back_fetch: int = Field(default=-1, frozen=True)

    def __init__(self, **data):
        res_data_path = "result"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {data.get('cloudflare_bearer_token')}"
        }
        pagination = None
        if not data.get("pagination_off"):
            if "?" in data.get("url"):
                url_format = "&page={res.result_info.page+1}"
            else:
                url_format = "?page={res.result_info.page+1}"
            pagination = PaginationSettings(type="url",
                                            url_format=url_format,
                                            update_first_url=True,
                                            stop_indication=StopPaginationSettings(field=res_data_path,
                                                                                   condition="empty"))

        super().__init__(headers=headers, pagination=pagination, response_data_path=res_data_path, **data)

        # Update the cloudflare account id in both the url and next url
        self.url = self.url.replace("{account_id}", self.cloudflare_account_id)
        self.next_url = self.next_url.replace("{account_id}", self.cloudflare_account_id)

        if self.days_back_fetch > 0:
            self._initialize_url_date()

    def _initialize_url_date(self):
        if "?" in self.url:
            self.url += f"&since={self._generate_start_fetch_date()}"
        else:
            self.url += f"?since={self._generate_start_fetch_date()}"

    def _generate_start_fetch_date(self):
        return (datetime.now(UTC) - timedelta(days=self.days_back_fetch)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def send_request(self):
        data = super().send_request()

        # Add 1 second to a known date filter to avoid duplicates in the logs
        if DATE_FILTER_PARAMETER in self.url:
            try:
                org_date = re.search(FIND_DATE_PATTERN, self.url).group(1)
                org_date_date = datetime.strptime(org_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                org_date_plus_second = (org_date_date + timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                self.url = self.url.replace(org_date, org_date_plus_second)
            except IndexError:
                logger.error(f"Failed to add 1s to the {self.name} api 'since' filter value, on url {self.url}")
            except ValueError:
                logger.error(f"Failed to parse API {self.name} date in URL: {self.url}")

        return data
