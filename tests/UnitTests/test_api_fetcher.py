from pydantic import ValidationError
import responses
import unittest

from src.apis.general.Api import ApiFetcher, ReqMethod
from src.apis.general.PaginationSettings import PaginationSettings, PaginationType
from src.apis.general.StopPaginationSettings import StopPaginationSettings, StopCondition


class TestApiFetcher(unittest.TestCase):
    """
    Test cases for the API Fetcher
    """

    def test_log_type(self):
        a = ApiFetcher(url="https://some/url", additional_fields={"type": "custom-type"})
        self.assertEqual(a.additional_fields.get("type"), "custom-type")

        a = ApiFetcher(url="https://some/url")
        self.assertEqual(a.additional_fields.get("type"), "api-fetcher")

    def test_invalid_setup(self):
        with self.assertRaises(ValidationError):
            # Missing Required 'url' field
            ApiFetcher(headers={"hi": "test"})

            # Not supported method
            ApiFetcher(url="https://random", method="DELETE")

            # scrape_interval too small
            ApiFetcher(url="https://my-url", scrape_interval=0.5)

            # Invalid stop pagination condition
            ApiFetcher(url="https://my-url",
                       pagination=PaginationSettings(type="headers",
                                                     headers_format={"header": "{res.field}"},
                                                     stop_indication=StopPaginationSettings(field="results",
                                                                                            condition="not-existing")))

    def test_invalid_pagination_setup(self):
        with self.assertRaises(ValueError):
            # Missing a required field
            ApiFetcher(url="https://my-url", pagination=PaginationSettings(type="url"))

            # Missing field for stop condition
            ApiFetcher(url="https://my-url",
                       pagination=PaginationSettings(type="headers",
                                                     headers_format={"header": "{res.field}"},
                                                     stop_indication=StopPaginationSettings(field="results",
                                                                                            condition="contains")))

    def test_change_next_url(self):
        # Init no variables in the URL
        a = ApiFetcher(url="https://random")
        self.assertEqual(a.url_vars, [])

        # Vars should update
        a.update_next_url("https://random?p={res.some_field}")
        self.assertEqual(a.url_vars, ["some_field"])

        # Vars should update to empty
        a.update_next_url("https://random?")
        self.assertEqual(a.url_vars, [])

    def test_extract_data_from_path(self):
        # field does not exist in response
        a = ApiFetcher(url="https://random", response_data_path="not_exist")
        self.assertEqual(a._extract_data_from_path({"exists": "field value"}), [])

        # field exist in response
        a = ApiFetcher(url="https://random", response_data_path="exists")
        self.assertEqual(a._extract_data_from_path({"exists": "field value"}), ["field value"])

        # invalid response
        a = ApiFetcher(url="https://random", response_data_path="field")
        self.assertEqual(a._extract_data_from_path("not proper res"), [])

    @responses.activate
    def test_send_successful_request(self):
        success_res_body = {"field": "abc", "arr": [1, 2], "objArr": [{"f2": "hi"}, {"f2": "hello"}]}

        # Mock response from some API
        responses.add(responses.GET, "http://some/api", json=success_res_body, status=200)

        a = ApiFetcher(url="http://some/api",
                       next_url="http://some/api/{res.field}/{res.arr.[0]}/{res.objArr.[1].f2}")
        result = a.send_request()

        # Validate we got the needed response
        self.assertEqual([success_res_body], result)

        # Validate that next_url updates the url for next request as expected
        self.assertEqual("http://some/api/abc/1/hello", a.url)

    @responses.activate
    def test_send_bad_request(self):
        # Mock response from some API
        responses.add(responses.GET, "http://not/existing/api", status=404)

        a = ApiFetcher(name="test", url="http://not/existing/api",
                       next_url="http://some/api/{res.field}/{res.arr[0]}/{res.objArr[1].f2}")

        # Validate we get the needed error and no data
        with self.assertLogs("src.apis.general.Api", level='INFO') as log:
            result = a.send_request()
        self.assertIn("ERROR:src.apis.general.Api:Failed to get data from test API due to error 404 Client Error: Not Found for url: http://not/existing/api", log.output)
        self.assertEqual(result, [])

    @responses.activate
    def test_pagination_stop_at_max_calls(self):
        first_req_body = {"query": "some query that filters the data"}
        pagination_req_body = {"page": "2"}

        first_res_body = {"data": [{"message": "log1"}, {"message": "log2"}], "info": {"page": 1}}
        pagination_res_body = {"data": [{"message": "log3"}], "info": {"page": 2}}

        # Mock response from some API that had pagination
        responses.add(responses.POST, "https://some/api",
                      match=[responses.matchers.json_params_matcher(first_req_body)],
                      json=first_res_body,
                      status=200)
        responses.add(responses.POST, "https://some/api",
                      match=[responses.matchers.json_params_matcher(pagination_req_body)],
                      json=pagination_res_body,
                      status=200)

        a = ApiFetcher(url="https://some/api",
                       body=first_req_body,
                       method=ReqMethod.POST,
                       response_data_path="data",
                       pagination=PaginationSettings(type=PaginationType("body"),
                                                     body_format={"page": "{res.info.page+1}"},
                                                     max_calls=1))
        result = a.send_request()

        # Ensure the final logs list contains only the necessary data in the correct format
        self.assertEqual(result, [{"message": "log1"}, {"message": "log2"}, {"message": "log3"}])

    @responses.activate
    def test_pagination_stop_indication(self):
        first_res_body = {"result": [{"msg": "random log1"}, {"msg": "random log2"}], "page": 1}
        pagination_res_body = {"result": [{"msg": "random log3"}, {"msg": "random log4"}], "page": 2}
        pagination_last_res_body = {"result": [], "page": 3}

        # Mock response from some API that had pagination
        responses.add(responses.GET, "https://some/api",
                      json=first_res_body,
                      status=200)
        responses.add(responses.GET, "https://some/api?page=2",
                      json=pagination_res_body,
                      status=200)
        responses.add(responses.GET, "https://some/api?page=3",
                      json=pagination_last_res_body,
                      status=200)

        a = ApiFetcher(url="https://some/api",
                       response_data_path="result",
                       pagination=PaginationSettings(type=PaginationType("url"),
                                                     url_format="?page={res.page+1}",
                                                     update_first_url=True,
                                                     stop_indication=StopPaginationSettings(field="result",
                                                                                            condition=StopCondition.EMPTY)))
        result = a.send_request()

        # Ensure the final logs list contains only the necessary data in the correct format
        self.assertEqual(result, [{"msg": "random log1"}, {"msg": "random log2"}, {"msg": "random log3"},
                                  {"msg": "random log4"}])
