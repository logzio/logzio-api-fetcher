import json
import unittest
from os.path import abspath, dirname
from unittest.mock import patch, MagicMock

import responses
from google.auth.credentials import TokenState
from pydantic import ValidationError

from src.apis.google.GoogleWorkspace import GoogleWorkspace
from src.apis.google.GoogleWorkspaceActivity import GoogleWorkspaceActivity

curr_path = abspath(dirname(__file__))


class TestGoogleApi(unittest.TestCase):
    """
    Test cases for Google API
    """

    def test_invalid_setup(self):
        with self.assertRaises(ValidationError):
            GoogleWorkspace(google_ws_sa_file_path="some-path",
                            data_request={"url": "https://admin.googleapis"})
            GoogleWorkspace(google_ws_sa_file_name="file-name",
                            data_request={"url": "https://admin.googleapis"})
            GoogleWorkspace(google_ws_delegated_account="user@email.com",
                            data_request={"url": "https://admin.googleapis"})
            GoogleWorkspaceActivity(google_ws_sa_file_path="some-path",
                                    google_ws_delegated_account="user@email.com")

    def test_valid_setup(self):
        gw = GoogleWorkspace(google_ws_sa_file_path="some-path",
                             google_ws_delegated_account="user@email.com",
                             data_request={"url": "https://admin.googleapis"})
        gwf = GoogleWorkspace(google_ws_sa_file_name="some-file",
                             google_ws_delegated_account="user@email.com",
                             data_request={"url": "https://admin.googleapis"})

        gwa = GoogleWorkspaceActivity(google_ws_sa_file_path="some-path",
                                      google_ws_delegated_account="user@email.com",
                                      application_name="some-app")

        # Assert token request
        self.assertEqual(gw.token_request.url, "dummy")
        self.assertEqual(gwf.token_request.url, "dummy")
        self.assertEqual(gwa.token_request.url, "dummy")

        # Assert data request
        self.assertIn("https://admin.googleapis?startTime=", gw.data_request.url)
        self.assertIn("https://admin.googleapis?startTime=", gwf.data_request.url)
        self.assertIn("https://admin.googleapis.com/admin/reports/v1/activity/users/all/applications/some-app?startTime=", gwa.data_request.url)
        self.assertEqual("https://admin.googleapis.com/admin/reports/v1/activity/users/all/applications/some-app?startTime={res.items.[0].id.time}", gwa.data_request.next_url)

        # Assert initialization
        self.assertEqual(gw.google_ws_sa_file_path, "some-path")
        self.assertEqual(gwf.google_ws_sa_file_path, "./src/shared/some-file")

    @responses.activate
    @patch("src.apis.google.GoogleWorkspace.GoogleWorkspace._generate_creds")
    def test_google_send_request(self, mock_generate_creds_func):
        # Mock the token request
        mock_generate_creds_func.return_value = ("access-token", "2025-03-26 08:21:39.946360")
        mock_creds = MagicMock()
        mock_creds.token = "access-token"
        mock_creds.expiry = "2025-03-26 08:21:39.946360"
        mock_creds.valid = True
        mock_creds.token_state.return_value = TokenState.FRESH

        # Mock the data request
        with open(f"{curr_path}/responsesExamples/google_user_accounts_res_example.json", "r") as data_res_example_file:
            data_res_body = json.loads(data_res_example_file.read())

        responses.add(responses.GET,
                      "https://admin.googleapis.com/admin/reports/v1/activity/users/all/applications/user_accounts",
                      json=data_res_body,
                      status=200)

        # Test sending request
        gwa = GoogleWorkspaceActivity(google_ws_sa_file_path="some-path",
                                      google_ws_delegated_account="user@email.com",
                                      application_name="user_accounts")
        gwa.creds = mock_creds
        result = gwa.send_request()
        self.assertEqual(result, data_res_body.get("items"))
        self.assertEqual(gwa.data_request.url, "https://admin.googleapis.com/admin/reports/v1/activity/users/all/applications/user_accounts?startTime=2024-11-26T08:22:31.072Z")
