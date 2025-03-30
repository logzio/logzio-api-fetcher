import json
import os
import time
import unittest
from os.path import abspath, dirname

from e2e_tests.api_e2e_test import ApiE2ETest
from e2e_tests.utils.config_utils import update_json_tokens


class TestGoogleE2E(ApiE2ETest):
    def module_specific_setup(self):
        secrets_map = {
            "private_key_id": "GOOGLE_PRIVATE_KEY_ID",
            "private_key": "GOOGLE_PRIVATE_KEY",
            "client_email": "GOOGLE_CLIENT_EMAIL",
            "client_id": "GOOGLE_CLIENT_ID",
            "client_x509_cert_url": "GOOGLE_CERT_URL",
        }
        curr_path = abspath(dirname(__file__))
        creds_path = f"{curr_path}/testdata/google_sa_creds.json"
        os.environ["GOOGLE_SA_CREDS"] = creds_path
        os.environ["GOOGLE_PRIVATE_KEY"] = os.getenv("GOOGLE_PRIVATE_KEY").encode().decode("unicode_escape")
        update_json_tokens(creds_path, secrets_map)

    def test_google_data_in_logz(self):
        secrets_map = {
            "apis.0.google_ws_delegated_account": "GOOGLE_DELEGATED_ACCOUNT",
            "logzio.token": "LOGZIO_SHIPPING_TOKEN",
            "apis.0.additional_fields.type": "TEST_TYPE",
            "apis.0.google_ws_sa_file_path": "GOOGLE_SA_CREDS"
        }
        curr_path = abspath(dirname(__file__))
        config_path = f"{curr_path}/testdata/google_api_conf.yaml"
        self.run_main_program(config_path=config_path, secrets_map=secrets_map)
        time.sleep(120)
        logs = self.search_logs(f"type:{self.test_type}")
        self.assertTrue(logs)


if __name__ == '__main__':
    unittest.main()
