import threading
from os.path import abspath, dirname
import unittest

from src.main import main
from e2e_tests.utils.config_utils import update_config_tokens, delete_temp_files
from e2e_tests.utils.log_utils import search_data

TEST_TYPE = "dockerhub-audit-test"

class TestDockerhubE2E(unittest.TestCase):
    """
    Test data arrived to logzio
    """

    def test_dockerhub_audit_logs_e2e(self):
        curr_path = abspath(dirname(__file__))
        config_path = f"{curr_path}/testdata/valid_dockerhub_config.yaml"
        token_updates = {
            "apis.0.dockerhub_token": "DOCKERHUB_TOKEN",
            "apis.0.dockerhub_user": "DOCKERHUB_USER",
            "logzio.token": "LOGZIO_SHIPPING_TOKEN"
        }
        temp_config_path = update_config_tokens(config_path, token_updates)
        thread = threading.Thread(target=main, kwargs={"conf_path": temp_config_path, "test": False})
        thread.daemon = True
        thread.start()
        thread.join(timeout=60)
        logs = search_data(f"type:{TEST_TYPE}")
        self.assertTrue(logs)
        self.assertTrue(all([log.get("_source").get("eventType") == "auditevents" for log in logs]))
        delete_temp_files()


if __name__ == '__main__':
    unittest.main()
