import os
import threading
import random
import string
from os.path import abspath, dirname
import unittest
import docker
import requests
from datetime import datetime, timedelta

from dotenv import load_dotenv

from src.main import main
from e2e_tests.utils.config_utils import update_config_tokens, delete_temp_files, validate_config_tokens
from e2e_tests.utils.log_utils import search_data

DOCKER_IMAGE = "logzio/dummy-docker-image"
DOCKER_TAG = "latest"


def generate_random_string(length=6):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def was_tag_pushed_recently(image, tag, days=14):
    url = f"https://hub.docker.com/v2/repositories/{image}/tags/{tag}"
    response = requests.get(url)
    if response.status_code == 200:
        tag_info = response.json()
        last_updated = datetime.strptime(tag_info['last_updated'], "%Y-%m-%dT%H:%M:%S.%fZ")
        return datetime.utcnow() - last_updated < timedelta(days=days)
    return False


class TestDockerhubE2E(unittest.TestCase):
    """
    Test data arrived to logzio
    """

    def setUp(self):
        self.client = docker.from_env()
        self.curr_path = abspath(dirname(__file__))
        self.config_path = f"{self.curr_path}/testdata/valid_dockerhub_config.yaml"
        self.dockerfile_path = f"{self.curr_path}/testdata/test.dockerfile"
        self.test_type = f"dockerhub-audit-test-{generate_random_string()}"
        os.environ["TEST_TYPE"] = self.test_type
        self.token_map = {
            "apis.0.dockerhub_token": "DOCKERHUB_TOKEN",
            "apis.0.dockerhub_user": "DOCKERHUB_USER",
            "logzio.token": "LOGZIO_SHIPPING_TOKEN",
            "apis.0.additional_fields.type": "TEST_TYPE"
        }
        load_dotenv(dotenv_path='testdata/.env')
        validate_config_tokens(self.token_map)
        self.temp_config_path = update_config_tokens(self.config_path, self.token_map)

        if not was_tag_pushed_recently(DOCKER_IMAGE, DOCKER_TAG):
            self.client.images.build(path=self.curr_path, dockerfile=self.dockerfile_path,
                                     tag=f"{DOCKER_IMAGE}:{DOCKER_TAG}")
            self.client.images.push(DOCKER_IMAGE, tag=DOCKER_TAG)

    def tearDown(self):
        delete_temp_files()

    def test_dockerhub_audit_logs_e2e(self):
        thread = threading.Thread(target=main,
                                  kwargs={"conf_path": self.temp_config_path, "test": False})
        thread.daemon = True
        thread.start()
        thread.join(timeout=60)

        logs = search_data(f"type:{self.test_type}")
        self.assertTrue(logs)
        self.assertTrue(all([log.get("_source").get("eventType") == "auditevents" for log in logs]))


if __name__ == '__main__':
    unittest.main()
