from datetime import datetime, UTC, timedelta
import json
from os.path import abspath, dirname
from pydantic import ValidationError
import responses
import unittest

from src.apis.general.Api import ReqMethod
from src.apis.onepassword.OnePassword import OnePassword

curr_path = abspath(dirname(__file__))


class TestOnePasswordApi(unittest.TestCase):
    def test_invalid_setup(self):
        with self.assertRaises(ValidationError):
            OnePassword(url="https://events.1password.com/api/v1/auditevents")
            OnePassword(url="https://events.1password.com/api/v1/auditevents",
                        onepassword_bearer_token="some-token",
                        onepassword_limit=1001)
            OnePassword(url="https://events.1password.com/api/v1/auditevents",
                        onepassword_bearer_token="some-token",
                        onepassword_limit=0)

    def test_valid_setup(self):
        # Test turning pagination off
        op1 = OnePassword(onepassword_bearer_token="some-token",
                          url="https://events.1password.com/api/v1/someendpoint",
                          method="POST",
                          pagination_off=True)
        # Test changing the limit
        op2 = OnePassword(onepassword_bearer_token="some-token",
                          url="https://events.1password.com/api/v1/someendpoint",
                          method="POST",
                          onepassword_limit=1000)
        # Test the days back
        op3 = OnePassword(onepassword_bearer_token="some-token",
                          url="https://events.1password.com/api/v1/someendpoint",
                          days_back_fetch=5)

        self.assertEqual(op1.onepassword_limit, 100)
        self.assertIsNone(op1.pagination_settings)
        self.assertIsNotNone(op2.pagination_settings)
        self.assertEqual(op3.method, ReqMethod.GET)

        op3_body_start_time = json.loads(op3.body).get("start_time")
        self.assertLessEqual(datetime.strptime(op3_body_start_time, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp(),
                             datetime.now(UTC).timestamp())

    @responses.activate
    def test_onepassword_send_request(self):
        with open(f"{curr_path}/responsesExamples/onepassword_res_example.json", "r") as data_res_example_file:
            data_res_body = json.loads(data_res_example_file.read())
            # Generate an updated start_time
            data_res_body["items"][0]["timestamp"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        responses.add(responses.POST,
                      "https://events.1password.com/api/v1/auditevents",
                      json=data_res_body,
                      status=200)

        op = OnePassword(onepassword_bearer_token="some-token",
                         url="https://events.1password.com/api/v1/auditevents",
                         method="POST",
                         days_back_fetch=1)

        pre_req_start_date = json.loads(op.body).get("start_time")
        result = op.send_request()
        post_req_start_date = json.loads(op.body).get("start_time")

        self.assertLess(datetime.strptime(pre_req_start_date, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp(),
                        datetime.strptime(post_req_start_date, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp())
        self.assertEqual(result, data_res_body.get("items"))
