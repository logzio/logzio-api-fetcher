from datetime import datetime, timedelta, UTC
import json
import logging
from pydantic import Field

from src.apis.general.Api import ApiFetcher
from src.apis.general.PaginationSettings import PaginationSettings
from src.apis.general.StopPaginationSettings import StopPaginationSettings

logger = logging.getLogger(__name__)


class OnePassword(ApiFetcher):
    """
    :param onepassword_bearer_token: The cloudflare Bearer token
    :param pagination_off: True if pagination should be off, False otherwise
    :param days_back_fetch: Amount of days to fetch back in the first request, Optional (adds a filter on 'since')
    :param onepassword_limit: 1Password limit for number of events to return in a single request (for pagination)
    """
    onepassword_bearer_token: str = Field(frozen=True)
    pagination_off: bool = Field(default=False)
    days_back_fetch: int = Field(default=-1, frozen=True)
    onepassword_limit: int = Field(default=100, ge=1, le=1000)

    def __init__(self, **data):
        # Initialize 1Password limit for number of events to return in a single request
        if not data.get('onepassword_limit'):
            limit = 100
        else:
            limit = data.pop('onepassword_limit')

        # Configure the request
        res_data_path = "items"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {data.get('onepassword_bearer_token')}"
        }
        body = {
            "limit": limit
        }
        next_body = {
            "limit": limit,
            "start_time": "{res.items.[0].timestamp}"
        }
        pagination = None
        if not data.get("pagination_off"):
            pagination = PaginationSettings(type="body",
                                            body_format={"cursor": "{res.cursor}"},
                                            stop_indication=StopPaginationSettings(field="has_more",
                                                                                   condition="equals",
                                                                                   value=False))
        super().__init__(headers=headers, body=body, next_body=next_body, pagination=pagination, response_data_path=res_data_path, **data)

        # Initialize the date filter for the first request
        if self.days_back_fetch > 0:
            self._initialize_body_date()

    def _initialize_body_date(self):
        """
        Initialize the first request's 'start_time' body argument.
        """
        try:
            start_time_field = {"start_time": (datetime.now(UTC) - timedelta(days=self.days_back_fetch)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")}
            new_body = json.loads(self.body)
            new_body.update(start_time_field)
            self.body = json.dumps(new_body)
        except json.decoder.JSONDecodeError:
            logger.error(f"Failed to update 'start_time' filter in the request body: {self.body}. Sending request with "
                         f"no date filter.")

    def send_request(self):
        """
        1. Sends request using the super class
        2. In 1Password the latest timestamp is ordered last in the response items >> make sure to take it instead of
           the first item.
        :return: all the responses that were received
        """
        data = super().send_request()

        if data:
            latest_timestamp = data[-1].get("timestamp")
            self.body = json.loads(self.body)
            self.body["start_time"] = latest_timestamp
            self.body = json.dumps(self.body)
        return data
