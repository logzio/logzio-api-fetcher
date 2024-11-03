from datetime import datetime, timedelta, UTC
import json
import logging
from pydantic import Field

from src.apis.general.Api import ApiFetcher
from src.apis.general.PaginationSettings import PaginationSettings
from src.apis.general.StopPaginationSettings import StopPaginationSettings

logger = logging.getLogger(__name__)

class DockerHub(ApiFetcher):

    dockerhub_token: str = Field(frozen=True)
    account: str = Field(frozen=True)
    pagination_off: bool = Field(default=False)
    days_back_fetch: int = Field(default=-1, frozen=True)
    page_size: int = Field(default=25, ge=1, le=100)

    def __init__(self, **data):
        page_size = data.pop('page_size', 25)

        res_data_path = "events"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {data.get('dockerhub_token')}"
        }
        params = {
            "page_size": page_size
        }
        next_params = {
            "page_size": page_size,
            "page": "{res.next_page}"
        }
        pagination = None
        if not data.get("pagination_off"):
            pagination = PaginationSettings(type="url",
                                            url_format="&page={res.next_page}",
                                            stop_indication=StopPaginationSettings(field="next_page",
                                                                                   condition="equals",
                                                                                   value=None))
        super().__init__(headers=headers, params=params, next_params=next_params, pagination=pagination, response_data_path=res_data_path, **data)

        if self.days_back_fetch > 0:
            self._initialize_params_date()

    def _initialize_params_date(self):

        try:
            from_date = (datetime.now(UTC) - timedelta(days=self.days_back_fetch)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            self.params["from"] = from_date
        except Exception as e:
            logger.error(f"Failed to update 'from' filter in the request params: {self.params}. Sending {self.name} "
                         f"request with no date filter. Error: {e}")

    def send_request(self):

        data = super().send_request()

        if data:
            latest_timestamp = data[-1].get("timestamp")
            self.params["from"] = latest_timestamp
        return data