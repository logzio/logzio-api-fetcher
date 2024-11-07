from datetime import datetime, UTC, timedelta
import json
from os.path import abspath, dirname
from pydantic import ValidationError
import responses
import unittest

from src.apis.dockerhub.Dockerhub import DockerHub

curr_path = abspath(dirname(__file__))

default_dockerhub_config = {
    "dockerhub_user": "some-user",
    "dockerhub_token": "some-token",
    "url": "https://hub.docker.com/v2/auditlogs/test",
}


class TestDockerHubApi(unittest.TestCase):
    """
    Test cases for DockerHub API
    """

    def test_invalid_setup(self):
        invalid_configs = [
            {
                "dockerhub_user": default_dockerhub_config.get("dockerhub_user"),
                "dockerhub_token": default_dockerhub_config.get("dockerhub_token"),
                "data_request": {
                    "url": default_dockerhub_config.get("url")
                }
            },
            {
                "dockerhub_user": default_dockerhub_config.get("dockerhub_user"),
                "url": default_dockerhub_config.get("url")
            },
            {
                "dockerhub_token": default_dockerhub_config.get("dockerhub_token"),
            },
        ]

        for config in invalid_configs:
            with self.assertRaises(ValidationError):
                DockerHub(**config)

    def test_valid_setup(self):
        dh = DockerHub(**default_dockerhub_config)

        self.assertIn(default_dockerhub_config.get("url"), dh.url)

        self.assertEqual(dh.headers["Content-Type"], "application/json")

        self.assertEqual(dh.response_data_path, "logs")

        self.assertIsNone(dh._jwt_token)

    def test_invalid_days_back_fetch(self):
        dh = DockerHub(**default_dockerhub_config,
                       days_back_fetch=-1)
        self.assertNotIn("from=", dh.url)

    def test_url_with_existing_query(self):
        dh = DockerHub(dockerhub_user=default_dockerhub_config.get("dockerhub_user"),
                       dockerhub_token=default_dockerhub_config.get("dockerhub_token"),
                       url="https://hub.docker.com/v2/auditlogs/test?existing_param=value",
                       days_back_fetch=1)
        self.assertIn("&from=", dh.url)
        self.assertIn("?existing_param=value", dh.url)

    def test_url_without_existing_query(self):
        dh = DockerHub(**default_dockerhub_config,
                       days_back_fetch=1)
        self.assertIn("&from=", dh.url)

    def test_start_date_generator(self):
        zero_days_back = DockerHub(**default_dockerhub_config,
                                   days_back_fetch=0)

        day_back = DockerHub(**default_dockerhub_config,
                             days_back_fetch=1)

        five_days_back = DockerHub(**default_dockerhub_config,
                                   days_back_fetch=5)

        # Make sure the current format and needed dates are generated
        from_date_zero_days_back = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        from_date_day_back = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        from_date_five_days_back = (datetime.now(UTC) - timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        self.assertNotIn(f"from={from_date_zero_days_back[:19]}", zero_days_back.url)
        self.assertIn(f"from={from_date_day_back[:19]}", day_back.url)
        self.assertIn(f"from={from_date_five_days_back[:19]}", five_days_back.url)

    @responses.activate
    def test_dockerhub_send_request(self):
        # Mock response from DockerHub API
        with open(f"{curr_path}/responsesExamples/dockerhub_audit_logs_res_example.json", "r") as data_res_example_file:
            data_res_body = json.loads(data_res_example_file.read())

        # Mock token response
        token_res_body = {
            "token": "mocked_jwt_token",
        }
        responses.add(responses.POST,
                      "https://hub.docker.com/v2/users/login",
                      json=token_res_body,
                      status=200)

        responses.add(responses.GET,
                      default_dockerhub_config.get("url"),
                      json=data_res_body,
                      status=200)

        dh = DockerHub(**default_dockerhub_config)
        result = dh.send_request()

        self.assertEqual(result, data_res_body.get("logs"))
        self.assertEqual(dh.url,
                         default_dockerhub_config.get("url") + "?page_size=100")

    @responses.activate
    def test_jwt_token_success(self):
        token_res_body = {
            "token": "mocked_jwt_token",
        }
        responses.add(responses.POST,
                      "https://hub.docker.com/v2/users/login",
                      json=token_res_body,
                      status=200)

        dh = DockerHub(**default_dockerhub_config)
        token = dh._get_jwt_token()

        self.assertEqual(token, "mocked_jwt_token")
        self.assertEqual(dh._jwt_token, "mocked_jwt_token")

    @responses.activate
    def test_jwt_token_failure(self):
        responses.add(responses.POST,
                      "https://hub.docker.com/v2/users/login",
                      status=401)

        dh = DockerHub(**default_dockerhub_config)
        token = dh._get_jwt_token()

        self.assertIsNone(token)
        self.assertIsNone(dh._jwt_token)

    @responses.activate
    def test_send_request_unauthorized(self):
        token_res_body = {
            "token": "mocked_jwt_token",
        }
        responses.add(responses.POST,
                      "https://hub.docker.com/v2/users/login",
                      json=token_res_body,
                      status=200)

        responses.add(responses.GET,
                      default_dockerhub_config.get("url"),
                      status=401)

        dh = DockerHub(**default_dockerhub_config)
        result = dh.send_request()

        self.assertEqual(result, [])
        self.assertEqual(dh.headers["Authorization"], "Bearer mocked_jwt_token")


if __name__ == '__main__':
    unittest.main()
