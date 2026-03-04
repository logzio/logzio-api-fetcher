from datetime import datetime, timedelta, timezone
import json
import logging
from pydantic import Field
from typing import Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from src.apis.general.Api import ApiFetcher

DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
MAX_WINDOW = timedelta(hours=1)
END_BUFFER = timedelta(minutes=5)

logger = logging.getLogger(__name__)


class CloudflareLogs(ApiFetcher):
    """
    Cloudflare Logs Received API integration.
    Supports the /zones/{zone_id}/logs/received endpoint which requires
    start and end query parameters and returns newline-delimited JSON (NDJSON).

    :param cloudflare_account_id: The CloudFlare Account ID
    :param cloudflare_bearer_token: The Cloudflare Bearer token
    :param days_back_fetch: Amount of days to fetch back in the first request (default: 1, max: 7)
    """
    cloudflare_account_id: str = Field(frozen=True)
    cloudflare_bearer_token: str = Field(frozen=True)
    days_back_fetch: int = Field(default=1, frozen=True, ge=1, le=7)

    next_start_time: Optional[datetime] = Field(default=None, init=False, init_var=True)
    base_url: str = Field(default="", init=False, init_var=True)

    def __init__(self, **data):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {data.get('cloudflare_bearer_token')}"
        }

        super().__init__(headers=headers, **data)

        self.url = self.url.replace("{account_id}", self.cloudflare_account_id)

        self.base_url = self._strip_time_params(self.url)

        self.next_start_time = datetime.now(timezone.utc) - timedelta(days=self.days_back_fetch)

    @staticmethod
    def _strip_time_params(url):
        """Remove start and end query parameters from the URL to get the base URL."""
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        params.pop("start", None)
        params.pop("end", None)
        clean_query = urlencode(params, doseq=True)
        return urlunparse(parsed._replace(query=clean_query))

    def _build_url(self, start, end):
        """Build the full URL with start and end parameters."""
        separator = "&" if "?" in self.base_url and self.base_url.split("?")[1] else "?"
        # If base_url ends with '?' or has no query string, use '?'
        if "?" not in self.base_url:
            separator = "?"
        start_str = start.strftime(DATE_FORMAT)
        end_str = end.strftime(DATE_FORMAT)
        return f"{self.base_url}{separator}start={start_str}&end={end_str}"

    @staticmethod
    def _parse_ndjson(text):
        """Parse newline-delimited JSON response into a list of dicts."""
        logs = []
        for line in text.strip().split("\n"):
            line = line.strip()
            if line:
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.debug(f"Failed to parse NDJSON line: {line[:200]}")
        return logs

    def send_request(self):
        """
        Fetches logs using time-windowed requests.
        Loops through 1-hour windows (Cloudflare max) from next_start_time up to now - 5 minutes.
        """
        all_responses = []
        now = datetime.now(timezone.utc)
        end_limit = now - END_BUFFER

        if self.next_start_time >= end_limit:
            logger.debug(f"No new time window to fetch for {self.name}. "
                         f"Next start: {self.next_start_time.strftime(DATE_FORMAT)}, "
                         f"end limit: {end_limit.strftime(DATE_FORMAT)}")
            return all_responses

        start = self.next_start_time

        while start < end_limit:
            end = min(start + MAX_WINDOW, end_limit)

            self.url = self._build_url(start, end)
            logger.debug(f"Fetching {self.name} logs window: {start.strftime(DATE_FORMAT)} -> {end.strftime(DATE_FORMAT)}")

            response = self._make_call()

            if response is None:
                logger.warning(f"Failed to fetch {self.name} logs for window "
                               f"{start.strftime(DATE_FORMAT)} -> {end.strftime(DATE_FORMAT)}, stopping.")
                break

            if isinstance(response, str):
                logs = self._parse_ndjson(response)
            elif isinstance(response, list):
                logs = response
            elif isinstance(response, dict):
                logs = self._extract_data_from_path(response)
            else:
                logs = [response]

            all_responses.extend(logs)
            start = end

        self.next_start_time = start
        return all_responses
