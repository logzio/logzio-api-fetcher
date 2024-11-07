from datetime import datetime, UTC, timedelta
import json
from os.path import abspath, dirname
from pydantic import ValidationError
import responses
import unittest

from src.apis.dockerhub.Dockerhub import DockerHub

curr_path = abspath(dirname(__file__))

DOCKER_API_TEST_URL = "https://hub.docker.com/v2/auditlogs/test"


class TestDockerHubApi(unittest.TestCase):
    """
    Test cases for DockerHub API
    """

    def test_invalid_setup(self):
        invalid_configs = [
            {
                "dockerhub_user": "some-user",
                "dockerhub_token": "some-token",
                "data_request": {
                    "url": DOCKER_API_TEST_URL
                }
            },
            {
                "dockerhub_user": "some-user",
                "url": DOCKER_API_TEST_URL
            },
            {
                "dockerhub_token": "some-token",
            },
        ]

        for config in invalid_configs:
            with self.assertRaises(ValidationError):
                DockerHub(**config)

    def test_valid_setup(self):
        dh = DockerHub(dockerhub_user="some-user",
                       dockerhub_token="some-token",
                       url=DOCKER_API_TEST_URL)

        self.assertIn(DOCKER_API_TEST_URL, dh.url)

        self.assertEqual(dh.headers["Content-Type"], "application/json")

        self.assertEqual(dh.response_data_path, "logs")

        self.assertIsNone(dh._jwt_token)


    def test_start_date_generator(self):
        zero_days_back = DockerHub(dockerhub_user="some-user",
                                   dockerhub_token="some-token",
                                   url=DOCKER_API_TEST_URL,
                                   days_back_fetch=0)

        day_back = DockerHub(dockerhub_user="some-user",
                             dockerhub_token="some-token",
                             url=DOCKER_API_TEST_URL,
                             days_back_fetch=1)

        five_days_back = DockerHub(dockerhub_user="some-user",
                                   dockerhub_token="some-token",
                                   url=DOCKER_API_TEST_URL,
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
                      DOCKER_API_TEST_URL,
                      json=data_res_body,
                      status=200)

        responses.add(responses.GET,
                      DOCKER_API_TEST_URL + "?from=2024-11-01T12:34:56.789Z&page_size=100",
                      json={"logs": []},
                      status=200)

        dh = DockerHub(dockerhub_user="some-user",
                       dockerhub_token="some-token",
                       url=DOCKER_API_TEST_URL)
        result = dh.send_request()

        self.assertEqual(result, data_res_body.get("logs"))
        self.assertEqual(dh.url,
                         DOCKER_API_TEST_URL + "?page_size=100")


if __name__ == '__main__':
    unittest.main()
