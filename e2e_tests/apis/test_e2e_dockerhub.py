import unittest
from os.path import abspath, dirname
from e2e_tests.api_e2e_test import ApiE2ETest
import docker
import requests
from datetime import datetime, timedelta

DOCKER_IMAGE = "logzio/dummy-docker-image"
DOCKER_TAG = "latest"


class TestDockerhubE2E(ApiE2ETest):

    def module_specific_setup(self):
        self.client = docker.from_env()
        self.dockerfile_path = f"{self.curr_path}/testdata/test.dockerfile"
        if not self.was_tag_pushed_recently(DOCKER_IMAGE, DOCKER_TAG):
            self.client.images.build(path=self.curr_path, dockerfile=self.dockerfile_path,
                                     tag=f"{DOCKER_IMAGE}:{DOCKER_TAG}")
            self.client.images.push(DOCKER_IMAGE, tag=DOCKER_TAG)

    def get_token_map(self):
        return {
            "apis.0.dockerhub_token": "DOCKERHUB_TOKEN",
            "apis.0.dockerhub_user": "DOCKERHUB_USER",
            "logzio.token": "LOGZIO_SHIPPING_TOKEN",
            "apis.0.additional_fields.type": "TEST_TYPE"
        }

    def get_config_path(self):
        self.curr_path = abspath(dirname(__file__))
        return f"{self.curr_path}/testdata/valid_dockerhub_config.yaml"

    def was_tag_pushed_recently(self, image, tag, days=14):
        url = f"https://hub.docker.com/v2/repositories/{image}/tags/{tag}"
        response = requests.get(url)
        if response.status_code == 200:
            tag_info = response.json()
            last_updated = datetime.strptime(tag_info['last_updated'], "%Y-%m-%dT%H:%M:%S.%fZ")
            return datetime.utcnow() - last_updated < timedelta(days=days)
        return False

    def test_dockerhub_audit_logs_e2e(self):
        self.run_main_program()
        logs = self.search_logs(f"type:{self.test_type}")
        self.assertTrue(logs)
        self.assertTrue(all([log.get("_source").get("eventType") == "auditevents" for log in logs]))


if __name__ == '__main__':
    unittest.main()
