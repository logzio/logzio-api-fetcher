import requests
from pydantic import Field
from datetime import datetime, timedelta, UTC
from enum import Enum
import json
import logging
from src.apis.general.Api import ApiFetcher
from src.apis.general.PaginationSettings import PaginationSettings
from src.apis.general.StopPaginationSettings import StopPaginationSettings
import urllib.parse

logger = logging.getLogger(__name__)
DEFAULT_SCOPES = ["https://www.googleapis.com/auth/admin.reports.audit.readonly",
                  "https://www.googleapis.com/auth/admin.reports.usage.readonly"]
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob:auto"


class ReqMethod(Enum):
    """
    Supported methods for the API request
    """
    GET = "GET"
    POST = "POST"


class GoogleWorkspace(ApiFetcher):
    """
    :param google_workspace_developer_key: The Google Workspace developer key
    :param pagination_off: True if pagination should be off, False otherwise
    :param days_back_fetch: Amount of days to fetch back in the first request, Optional (adds a filter on 'start_time')
    :param google_workspace_limit: Limit for number of events to return in a single request (for pagination)
    """

    google_workspace_client_id: str = Field(frozen=True)
    google_workspace_client_secret: str = Field(frozen=True)
    pagination_off: bool = Field(default=False)
    days_back_fetch: int = Field(default=-1, frozen=True)
    google_workspace_limit: int = Field(default=100, ge=1, le=1000)
    method: ReqMethod = Field(default=ReqMethod.GET, frozen=True)
    scopes: str = Field(default=DEFAULT_SCOPES, frozen=True)

    def __init__(self, **data):
        super().__init__(**data)
        # Initialize Google Workspace limit for number of events to return in a single request
        limit = data.pop('google_workspace_limit', 100)
        # Configure the request
        res_data_path = "items"
        headers = {
            "Content-Type": "application/json"
        }
        body = {
            "limit": limit
        }
        next_body = {
            "limit": limit,
            "start_time": "{res.items.[-1].timestamp}"
        }
        pagination = None
        if not data.get("pagination_off"):
            pagination = PaginationSettings(type="body",
                                            body_format={"cursor": "{res.cursor}"},
                                            stop_indication=StopPaginationSettings(field="has_more",
                                                                                   condition="equals",
                                                                                   value=False))
        super().__init__(headers=headers, body=body, next_body=next_body, pagination=pagination,
                         response_data_path=res_data_path, **data)
        # Initialize the date filter for the first request
        if self.days_back_fetch > 0:
            self._initialize_body_date()
        self._generate_access_token()

    def _get_refresh_token(self):
        """
        Obtain the OAuth2 refresh token for the Google Workspace API.
        :return: The OAuth2 refresh token
        """

        # Step 1: Get authorization code
        auth_url = (
            f"https://accounts.google.com/o/oauth2/auth"
            f"?client_id={self.google_workspace_client_id}"
            f"&redirect_uri={REDIRECT_URI}"
            f"&scope={urllib.parse.quote(' '.join(self.scopes))}"
            f"&response_type=code"
            f"&access_type=offline"
        )

        print(f"Go to the following URL to authorize the application: \n{auth_url}")

        # Wait for user to complete authorization
        input("Press Enter after authorizing the application and obtaining the authorization code...")

        # Step 2: User authorizes the application and gets an authorization code
        response_url = input("Copy the response URL: ")
        decoded_url = urllib.parse.unquote(response_url)
        try:
            auth_code = decoded_url.split("code=")[1].split("&")[0]
        except IndexError:
            logger.error("Failed to extract authorization code from the response URL.")
            return None
        # Step 3: Exchange authorization code for access token and refresh token
        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": self.google_workspace_client_id,
            "client_secret": self.google_workspace_client_secret,
            "code": auth_code,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code"
        }

        response = requests.post(token_url, data=payload)
        if response.status_code == 200:
            tokens = response.json()
            return tokens.get('refresh_token')
        else:
            logger.error(f"Failed to obtain Google OAuth refresh tokens: {response.text}")
            return None

    def _generate_access_token(self):
        """
        Generate the OAuth2 access token for the Google Workspace API.
        :return: The OAuth2 access token
        """
        google_workspace_refresh_token = self._get_refresh_token()
        access_token = None
        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": self.google_workspace_client_id,
            "client_secret": self.google_workspace_client_secret,
            "refresh_token": google_workspace_refresh_token,
            "grant_type": "refresh_token"
        }
        response = requests.post(token_url, data=payload)
        if response.status_code == 200:
            access_token = response.json().get("access_token")
        else:
            logger.error(f"Failed to obtain access token: {response.text}")

        if not access_token:
            raise ValueError(f"Failed to generate Google Workspace access token with payload:\n{payload}.")
        else:
            self.headers.update({"Authorization": f"Bearer {access_token}"})
            print(f"OAuth Access token: {access_token} generated successfully.")

    def _initialize_body_date(self):
        """
        Initialize the first request's 'start_time' body argument.
        """
        try:
            start_time_field = {"start_time": (datetime.now(UTC) - timedelta(days=self.days_back_fetch)).strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ")}
            new_body = json.loads(self.body)
            new_body.update(start_time_field)
            self.body = json.dumps(new_body)
        except json.decoder.JSONDecodeError:
            logger.error(f"Failed to update 'start_time' filter in the request body: {self.body}. Sending {self.name} "
                         f"request with no date filter.")
        except TypeError:
            logger.error(f"Got unexpected request body parameter. Please make sure the {self.name} API request body is "
                         f"a valid json.")

    def send_request(self):
        """
        Send a request to the Google Workspace API and handle the response.
        :return: The response data
        """
        try:
            # Log the request details
            logger.debug(f"Sending request to URL: {self.url}")
            logger.debug(f"Request headers: {self.headers}")
            logger.debug(f"Request body: {self.body}")

            if self.method == ReqMethod.POST:
                response = requests.post(self.url, headers=self.headers, json=self.body)
            elif self.method == ReqMethod.GET:
                response = requests.get(self.url, headers=self.headers, params=self.body)
            else:
                raise ValueError(f"Unsupported request method: {self.method}")

            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
            data = response.json().get(self.response_data_path, [])

            if data:
                # Update the 'start_time' filter for the next request
                latest_timestamp = data[-1].get("timestamp")
                self.body = json.loads(self.body)
                self.body["start_time"] = latest_timestamp
                self.body = json.dumps(self.body)

            return data
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request error occurred: {req_err}")
        except json.decoder.JSONDecodeError as json_err:
            logger.error(f"JSON decode error: {json_err}")
        except Exception as err:
            logger.error(f"An error occurred: {err}")
        return None