from pydantic import ValidationError
import responses
import unittest

from src.apis.general.Api import ApiFetcher, ReqMethod
from src.apis.oauth.OAuth import OAuthApi


class TestOAuthApi(unittest.TestCase):
    """
    Test cases for the OAuth API
    """

    def test_invalid_setup(self):
        with self.assertRaises(ValidationError):
            # missing token_request
            OAuthApi(data_request=ApiFetcher(url="http://my-data-url"))

            # missing data_request
            OAuthApi(token_request=ApiFetcher(url="http://my-token-url"))

            # scrape_interval too big
            OAuthApi(token_request=ApiFetcher(url="http://my-token-url"),
                     data_request=ApiFetcher(url="http://my-data-url"),
                     scrape_interval=0)

    def test_headers_setup(self):
        # No initializing to headers
        a = OAuthApi(token_request=ApiFetcher(url="http://my-token-url"),
                     data_request=ApiFetcher(url="http://my-data-url"))
        self.assertEqual(a.data_request.headers.get("Content-Type"), "application/json")

        # Initializing to headers
        a = OAuthApi(token_request=ApiFetcher(url="http://my-token-url"),
                     data_request=ApiFetcher(url="http://my-data-url",
                                             headers={"Content-Type": "application/gzip"}))
        self.assertEqual(a.data_request.headers.get("Content-Type"), "application/gzip")

    def test_additional_fields_init(self):
        a = OAuthApi(token_request=ApiFetcher(url="http://my-token-url"),
                     data_request=ApiFetcher(url="http://my-data-url"),
                     additional_fields={"type": "test"})
        self.assertEqual("test", a.additional_fields.get("type"))

        a = OAuthApi(token_request=ApiFetcher(url="http://my-token-url"),
                     data_request=ApiFetcher(url="http://my-data-url"))
        self.assertEqual("api-fetcher", a.additional_fields.get("type"))

    @responses.activate
    def test_send_request(self):
        token_res = {"access_token": "epZliHdLuj", "expires_in": 1}
        data_res = {"data": [{"msg": "hi"}, {"msg": "hello", "field": 567}]}

        # Mock response from some API
        responses.add(responses.POST, "http://my-token-url",
                      json=token_res,
                      status=200)
        responses.add(responses.GET, "http://my-data-url",
                      json=data_res,
                      status=200)

        a = OAuthApi(token_request=ApiFetcher(url="http://my-token-url", method=ReqMethod.POST),
                     data_request=ApiFetcher(url="http://my-data-url", response_data_path="data"))
        result = a.send_request()

        # Ensure we got the needed results
        self.assertEqual([{"msg": "hi"}, {"msg": "hello", "field": 567}], result)

        # Test needing to update the token (gave super short expiration in 'token_res')
        with self.assertLogs("src.apis.oauth.OAuth", level='DEBUG') as log:
            a.send_request()
        self.assertIn("DEBUG:src.apis.oauth.OAuth:Sending request to update the access token.", log.output)
