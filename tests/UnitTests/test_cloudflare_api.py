import json
import os
from pydantic import ValidationError
import responses
import unittest

from src.apis.cloudflare.Cloudflare import Cloudflare


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

        self.assertEqual(a.url, "https://api.cloudflare.com/client/v4/accounts/abcd-efg/alerting/v3/history?since=2024-05-24T03:22:45.410294Z")
        self.assertEqual(results, res.get("result"))
