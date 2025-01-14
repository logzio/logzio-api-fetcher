import unittest
from os.path import abspath, dirname
from e2e_tests.api_e2e_test import ApiE2ETest
import docker
import requests
from datetime import datetime, timedelta, timezone

DOCKER_IMAGE = "logzio/dummy-docker-image"
DOCKER_TAG = "latest"


def was_tag_pushed_recently(image, tag, days=14):
    url = f"https://hub.docker.com/v2/repositories/{image}/tags/{tag}"
    response = requests.get(url)
    if response.status_code == 200:
        tag_info = response.json()
        last_updated = datetime.strptime(tag_info['last_updated'], "%Y-%m-%dT%H:%M:%S.%fZ")
        last_updated = last_updated.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - last_updated < timedelta(days=days)
    return False


class TestDockerhubE2E(ApiE2ETest):

    def module_specific_setup(self):
        curr_path = abspath(dirname(__file__))
        self.client = docker.from_env()
        self.dockerfile_path = f"{curr_path}/testdata/test.dockerfile"
        if not was_tag_pushed_recently(DOCKER_IMAGE, DOCKER_TAG):
            self.client.images.build(path=curr_path, dockerfile=self.dockerfile_path,
                                     tag=f"{DOCKER_IMAGE}:{DOCKER_TAG}")
            self.client.images.push(DOCKER_IMAGE, tag=DOCKER_TAG)

    def test_dockerhub_audit_logs_e2e(self):
        secrets_map = {
            "apis.0.dockerhub_token": "DOCKERHUB_PASSWORD",
            "apis.0.dockerhub_user": "DOCKERHUB_USER",
            "logzio.token": "LOGZIO_SHIPPING_TOKEN",
            "apis.0.additional_fields.type": "TEST_TYPE"
        }
        curr_path = abspath(dirname(__file__))
        config_path = f"{curr_path}/testdata/valid_dockerhub_config.yaml"
        self.run_main_program(config_path=config_path, secrets_map=secrets_map)
        logs = self.search_logs(f"type:{self.test_type}")
        self.assertTrue(logs)
        self.assertTrue(all([log.get("_source").get("eventType") == "auditevents" for log in logs]))


if __name__ == '__main__':
    unittest.main()
