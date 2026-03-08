import json
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from pydantic import ValidationError
import responses
import unittest

from src.apis.cloudflare.Cloudflare import Cloudflare
from src.apis.cloudflare_logs.CloudflareLogs import CloudflareLogs


curr_path = os.path.abspath(os.path.dirname(__file__))


class TestCloudflareApi(unittest.TestCase):
    """
    Test cases for Cloudflare API
    """

    def test_invalid_setup(self):
        with self.assertRaises(ValidationError):
            Cloudflare(cloudflare_account_id="abcd-efg",
                       url="https://api.cloudflare.com/client/v4/accounts/{account_id}/alerting/v3/history")
            Cloudflare(cloudflare_bearer_token="mYbeReartOKen",
                       url="https://api.cloudflare.com/client/v4/accounts/{account_id}/alerting/v3/history")
            Cloudflare(cloudflare_account_id="abcd-efg", cloudflare_bearer_token="mYbeReartOKen")

    @responses.activate
    def test_valid_setup(self):
        # Mock response from Cloudflare API
        with open(f"{curr_path}/responsesExamples/cloudflare_res_example.json", "r") as res_example_file:
            res = json.loads(res_example_file.read())

        # First Data Request
        responses.add(responses.GET, "https://api.cloudflare.com/client/v4/accounts/abcd-efg/alerting/v3/history",
                      json=res,
                      status=200)

        # Pagination Request
        responses.add(responses.GET, "https://api.cloudflare.com/client/v4/accounts/abcd-efg/alerting/v3/history?page=2",
                      json={"result": [], "result_info": {"page": 2, "total_pages": 1}},
                      status=200)

        a = Cloudflare(cloudflare_account_id="abcd-efg",
                       cloudflare_bearer_token="mYbeReartOKen",
                       url="https://api.cloudflare.com/client/v4/accounts/{account_id}/alerting/v3/history",
                       next_url="https://api.cloudflare.com/client/v4/accounts/{account_id}/alerting/v3/history?since={res.result.[0].sent}")

        # Test sending request
        results = a.send_request()

        self.assertEqual(a.url, "https://api.cloudflare.com/client/v4/accounts/abcd-efg/alerting/v3/history?since=2024-05-24T03:22:46.410294Z")
        self.assertEqual(results, res.get("result"))


class TestCloudflareLogsApi(unittest.TestCase):
    """
    Test cases for Cloudflare Logs Received API (cloudflare_logs type)
    """

    NDJSON_RESPONSE = (
        '{"ClientIP":"1.2.3.4","RayID":"abc123","EdgeStartTimestamp":1700000000}\n'
        '{"ClientIP":"5.6.7.8","RayID":"def456","EdgeStartTimestamp":1700000001}\n'
    )

    BASE_URL = "https://api.cloudflare.com/client/v4/zones/zone123/logs/received"

    def _create_instance(self, **overrides):
        defaults = {
            "cloudflare_account_id": "acc-123",
            "cloudflare_bearer_token": "myToken",
            "url": self.BASE_URL,
            "days_back_fetch": 1,
        }
        defaults.update(overrides)
        return CloudflareLogs(**defaults)

    def test_invalid_setup_missing_fields(self):
        with self.assertRaises(ValidationError):
            CloudflareLogs(
                cloudflare_account_id="acc-123",
                url=self.BASE_URL,
            )
        with self.assertRaises(ValidationError):
            CloudflareLogs(
                cloudflare_bearer_token="myToken",
                url=self.BASE_URL,
            )

    def test_no_since_param_in_url(self):
        """The logs/received endpoint should never get a 'since' parameter."""
        a = self._create_instance()
        self.assertNotIn("since=", a.url)
        self.assertNotIn("since=", a.base_url)

    def test_strips_start_end_from_user_url(self):
        """If the user provides start/end in URL, they should be stripped for the base URL."""
        a = self._create_instance(
            url=f"{self.BASE_URL}?start=2026-02-23T10:00:00Z&end=2026-02-23T10:01:00Z"
        )
        self.assertNotIn("start=", a.base_url)
        self.assertNotIn("end=", a.base_url)

    def test_auth_header(self):
        a = self._create_instance()
        self.assertEqual(a.headers["Authorization"], "Bearer myToken")

    def test_parse_ndjson(self):
        logs = CloudflareLogs._parse_ndjson(self.NDJSON_RESPONSE)
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0]["ClientIP"], "1.2.3.4")
        self.assertEqual(logs[1]["RayID"], "def456")

    def test_parse_ndjson_empty(self):
        logs = CloudflareLogs._parse_ndjson("")
        self.assertEqual(logs, [])

    def test_parse_ndjson_with_blank_lines(self):
        text = '{"a":1}\n\n{"b":2}\n'
        logs = CloudflareLogs._parse_ndjson(text)
        self.assertEqual(len(logs), 2)

    def test_build_url(self):
        a = self._create_instance()
        start = datetime(2026, 2, 23, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 2, 23, 11, 0, 0, tzinfo=timezone.utc)
        url = a._build_url(start, end)
        self.assertIn("start=2026-02-23T10:00:00Z", url)
        self.assertIn("end=2026-02-23T11:00:00Z", url)
        self.assertTrue(url.startswith(self.BASE_URL))

    def test_build_url_with_existing_params(self):
        """If base URL has other params (e.g., fields=), start/end should be appended with &."""
        a = self._create_instance(url=f"{self.BASE_URL}?fields=ClientIP,RayID")
        start = datetime(2026, 2, 23, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 2, 23, 11, 0, 0, tzinfo=timezone.utc)
        url = a._build_url(start, end)
        self.assertIn("fields=ClientIP%2CRayID", url)
        self.assertIn("&start=2026-02-23T10:00:00Z", url)
        self.assertIn("&end=2026-02-23T11:00:00Z", url)

    @responses.activate
    def test_send_request_ndjson(self):
        """Test full send_request flow with NDJSON response."""
        # Set next_start_time to 30 minutes ago so we get a single window
        fixed_now = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)

        a = self._create_instance()
        a.next_start_time = fixed_now - timedelta(minutes=30)

        # Mock any GET to the zone logs endpoint
        responses.add(
            responses.GET,
            self.BASE_URL,
            body=self.NDJSON_RESPONSE,
            status=200,
        )

        with patch("src.apis.cloudflare_logs.CloudflareLogs.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now
            mock_dt.strptime = datetime.strptime
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            results = a.send_request()

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["ClientIP"], "1.2.3.4")
        self.assertEqual(results[1]["RayID"], "def456")

    @responses.activate
    def test_send_request_advances_start_time(self):
        """After fetching, next_start_time should advance to the end of the last window."""
        fixed_now = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)

        a = self._create_instance()
        a.next_start_time = fixed_now - timedelta(minutes=30)

        responses.add(
            responses.GET,
            self.BASE_URL,
            body=self.NDJSON_RESPONSE,
            status=200,
        )

        with patch("src.apis.cloudflare_logs.CloudflareLogs.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now
            mock_dt.strptime = datetime.strptime
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            a.send_request()

        # end_limit = fixed_now - 5 min = 11:55
        # Single window: start=11:30, end=min(11:30+1h, 11:55)=11:55
        expected_end = fixed_now - timedelta(minutes=5)
        self.assertEqual(a.next_start_time, expected_end)

    @responses.activate
    def test_send_request_multiple_windows(self):
        """When the time gap exceeds 1 hour, multiple windows should be fetched."""
        fixed_now = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)

        a = self._create_instance()
        # Set start time 2.5 hours ago → should need 3 windows
        a.next_start_time = fixed_now - timedelta(hours=2, minutes=30)

        responses.add(
            responses.GET,
            self.BASE_URL,
            body='{"log":"window1"}\n',
            status=200,
        )
        responses.add(
            responses.GET,
            self.BASE_URL,
            body='{"log":"window2"}\n',
            status=200,
        )
        responses.add(
            responses.GET,
            self.BASE_URL,
            body='{"log":"window3"}\n',
            status=200,
        )

        with patch("src.apis.cloudflare_logs.CloudflareLogs.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now
            mock_dt.strptime = datetime.strptime
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            results = a.send_request()

        self.assertEqual(len(results), 3)
        # 3 windows: 9:30-10:30, 10:30-11:30, 11:30-11:55
        self.assertEqual(len(responses.calls), 3)

    @responses.activate
    def test_send_request_skips_when_no_new_window(self):
        """If next_start_time is recent enough, no request should be made."""
        fixed_now = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)

        a = self._create_instance()
        # Set start time to 3 minutes ago → within the 5-minute buffer
        a.next_start_time = fixed_now - timedelta(minutes=3)

        with patch("src.apis.cloudflare_logs.CloudflareLogs.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now
            mock_dt.strptime = datetime.strptime
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            results = a.send_request()

        self.assertEqual(results, [])
        self.assertEqual(len(responses.calls), 0)
