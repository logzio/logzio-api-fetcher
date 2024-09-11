from datetime import datetime, UTC, timedelta
import json
from os.path import abspath, dirname
from pydantic import ValidationError
import responses
import unittest

from src.apis.azure.AzureApi import AzureApi
from src.apis.azure.AzureGraph import AzureGraph
from src.apis.azure.AzureMailReports import AzureMailReports


curr_path = abspath(dirname(__file__))


class TestAzureApi(unittest.TestCase):
    """
    Test cases for Azure API
    """

    def test_invalid_setup(self):
        with self.assertRaises(ValidationError):
            AzureApi(azure_ad_tenant_id="some-tenant",
                     azure_ad_client_id="some-client",
                     data_request={"url": "https://azure"})
            AzureApi(azure_ad_tenant_id="some-tenant",
                     azure_ad_secret_value="some-secret",
                     data_request={"url": "https://azure"})
            AzureApi(azure_ad_secret_value="some-secret",
                     azure_ad_client_id="some-client",
                     data_request={"url": "https://azure"})

    def test_valid_setup(self):
        ag = AzureGraph(azure_ad_tenant_id="some-tenant",
                        azure_ad_client_id="some-client",
                        azure_ad_secret_value="some-secret",
                        data_request={"url": "https://azure-graph"})

        am = AzureMailReports(azure_ad_tenant_id="some-tenant",
                              azure_ad_client_id="some-client",
                              azure_ad_secret_value="some-secret",
                              data_request={"url": "https://azure-mail"})

        # Important note: test for 'expected_data_body' is >>SPACE SENSITIVE !!! <<
        # For any change at AzureAPI token_request body, make sure to update the amount of tabs here if needed
        expected_token_body = """client_id=some-client
                        &scope=https://graph.microsoft.com/.default
                        &client_secret=some-secret
                        &grant_type=client_credentials
                        """

        expected_token_body2 = """client_id=some-client
                        &scope=https://outlook.office365.com/.default
                        &client_secret=some-secret
                        &grant_type=client_credentials
                        """

        # Validate the token request
        self.assertEqual(ag.token_request.url, "https://login.microsoftonline.com/some-tenant/oauth2/v2.0/token")
        self.assertEqual(am.token_request.url, "https://login.microsoftonline.com/some-tenant/oauth2/v2.0/token")
        self.assertEqual(ag.token_request.body, expected_token_body)
        self.assertEqual(am.token_request.body, expected_token_body2)

        # Validate the data request URL was updated
        self.assertIn("https://azure-graph?$filter=createdDateTime gt", ag.data_request.url)
        self.assertIn("https://azure-mail?$filter=StartDate eq datetime", am.data_request.url)
        self.assertIn("EndDate eq datetime", am.data_request.url)

        # Validate the data request next URL was updated
        self.assertEqual("https://azure-graph?$filter=createdDateTime gt {res.value.[0].createdDateTime}",
                         ag.data_request.next_url)
        self.assertEqual(
            "https://azure-mail?$filter=StartDate eq datetime'{res.d.results.[0].EndDate}' and EndDate eq datetime'NOW_DATE'&$format=json",
            am.data_request.next_url)

    def test_start_date_generator(self):
        day_back = AzureApi(azure_ad_tenant_id="some-tenant",
                            azure_ad_client_id="some-client",
                            azure_ad_secret_value="some-secret",
                            data_request={"url": "https://some-api"})

        five_days_back = AzureApi(azure_ad_tenant_id="some-tenant",
                                  azure_ad_client_id="some-client",
                                  azure_ad_secret_value="some-secret",
                                  data_request={"url": "https://some-api"},
                                  days_back_fetch=5)

        # Make sure the current format and needed dates are generated
        self.assertLessEqual(datetime.strptime(day_back.generate_start_fetch_date(), "%Y-%m-%dT%H:%M:%SZ").timestamp(),
                             datetime.now(UTC).timestamp())
        self.assertLessEqual(
            datetime.strptime(five_days_back.generate_start_fetch_date(), "%Y-%m-%dT%H:%M:%SZ").timestamp(),
            (datetime.now(UTC) - timedelta(days=5)).timestamp())

    @responses.activate
    def test_azure_graph_send_request(self):
        # Mock response from Azure Graph API
        token_res_body = {"token_type": "Bearer", "expires_in": 3599,
                          "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6Ik1uQ19WWmNBVGZNNXBP"}
        with open(f"{curr_path}/responsesExamples/azure_graph_res_example.json", "r") as data_res_example_file:
            data_res_body = json.loads(data_res_example_file.read())

        # token response
        responses.add(responses.POST,
                      "https://login.microsoftonline.com/some-tenant/oauth2/v2.0/token",
                      json=token_res_body,
                      status=200)

        # data response
        responses.add(responses.GET,
                      "https://graph.microsoft.com/v1.0/auditLogs/signIns",
                      json=data_res_body,
                      status=200)

        # Pagination data response
        responses.add(responses.GET,
                      "https://graph.microsoft.com/v1.0/auditLogs/signIns?$top=1&$skiptoken=9177f2e3532fcd4c4d225f68f7b9bdf7_1",
                      json={"value": []},
                      status=200)

        # Test sending request
        a = AzureGraph(azure_ad_tenant_id="some-tenant",
                       azure_ad_client_id="some-client",
                       azure_ad_secret_value="some-secret",
                       data_request={"url": "https://graph.microsoft.com/v1.0/auditLogs/signIns"})
        result = a.send_request()

        # Make sure we get the needed data and the url for next request is updated properly
        self.assertEqual(result, data_res_body.get("value"))
        self.assertEqual(a.data_request.url,
                         "https://graph.microsoft.com/v1.0/auditLogs/signIns?$filter=createdDateTime gt 2020-03-13T19:15:41.6195833Z")

    @responses.activate
    def test_azure_mail_send_request(self):
        # Mock response from Azure Mail API
        token_res_body = {"token_type": "Bearer", "expires_in": 3599,
                          "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6Ik1uQ19WWmNBVGZNNXBP"}
        with open(f"{curr_path}/responsesExamples/azure_mail_res_example.json", "r") as data_res_example_file:
            data_res_body = json.loads(data_res_example_file.read())

            # token response
            responses.add(responses.POST,
                          "https://login.microsoftonline.com/some-tenant/oauth2/v2.0/token",
                          json=token_res_body,
                          status=200)

            # data response
            responses.add(responses.GET,
                          "https://reports.office365.com/ecp/reportingwebservice/reporting.svc/MessageTrace",
                          json=data_res_body,
                          status=200)

            # Pagination data response
            responses.add(responses.GET,
                          "https://reports.office365.com/ecp/ReportingWebService/Reporting.svc/MessageTrace?$skiptoken=abc123",
                          json={"d": {"results": []}},
                          status=200)

            # Test sending request
            a = AzureMailReports(azure_ad_tenant_id="some-tenant",
                                 azure_ad_client_id="some-client",
                                 azure_ad_secret_value="some-secret",
                                 data_request={"url": "https://reports.office365.com/ecp/reportingwebservice/reporting.svc/MessageTrace"})
            result = a.send_request()

            self.assertEqual(result, data_res_body.get("d").get("results"))
            self.assertEqual(a.data_request.url,
                             "https://reports.office365.com/ecp/reportingwebservice/reporting.svc/MessageTrace?$filter=StartDate eq datetime'2024-05-30T13:08:54Z' and EndDate eq datetime'NOW_DATE'&$format=json")
