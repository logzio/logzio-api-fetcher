from datetime import datetime, timedelta, UTC
import json
import logging

import requests
from pydantic import Field

from src.apis.general.Api import ApiFetcher
from src.apis.general.PaginationSettings import PaginationSettings
from src.apis.general.StopPaginationSettings import StopPaginationSettings

logger = logging.getLogger(__name__)


class DockerHub(ApiFetcher):
    """
    :param dockerhub_token: The DockerHub personal access token or password
    :param pagination_off: True if pagination should be off, False otherwise
    :param days_back_fetch: Amount of days to fetch back in the first request, Optional (adds a filter on 'from')
    :param page_size: Number of events to return in a single request (for pagination)
    """
    dockerhub_user: str = Field(frozen=True)
    dockerhub_token: str = Field(frozen=False)
    days_back_fetch: int = Field(default=1, frozen=True)

    def __init__(self, **data):
        # Initialize page size for number of events to return in a single request
        # Configure the request
        res_data_path = "logs"
        headers = {
            "Content-Type": "application/json",
        }
        super().__init__(headers=headers, response_data_path=res_data_path, **data)

        self._initialize_params()

    def _initialize_params(self):
        """
        Initialize the first request's 'from' parameter.
        """
        try:
            from_date = (datetime.now(UTC) - timedelta(days=self.days_back_fetch)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            if "?" in self.url:
                self.url += f"&from={from_date}&page_size=100"
            else:
                self.url += f"?from={from_date}&page_size=100"
        except Exception as e:
            logger.error(f"Failed to update 'from' filter in the request params:. Sending {self.name} "
                         f"request with no date filter. Error: {e}")

    def _get_jwt_token(self):
        url = "https://hub.docker.com/v2/users/login"
        payload = {
            "username": self.dockerhub_user,
            "password": self.dockerhub_token
        }
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            token_response = response.json()
            return token_response.get("token")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get JWT token: {e}")

    def send_request(self):
        """
        Sends request using the super class and handles pagination if needed.
        :return: all the responses that were received
        """
        jwt_token = self._get_jwt_token()
        self.headers["Authorization"] = f"Bearer {jwt_token}"
        data = super().send_request()
        return data
