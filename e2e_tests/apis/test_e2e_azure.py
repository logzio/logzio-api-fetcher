import os
import time

from e2e_tests.api_e2e_test import ApiE2ETest
import unittest
from os.path import abspath, dirname


class TestAzureE2E(ApiE2ETest):

    def module_specific_setup(self):
        # Add module-specific setup here if needed
        pass

    def module_specific_teardown(self):
        # Add module-specific teardown here if needed
        pass

    def test_azure_data_in_logz(self):
        secrets_map = {
            "apis.0.azure_ad_tenant_id": "AZURE_AD_TENANT_ID",
            "apis.0.azure_ad_client_id": "AZURE_AD_CLIENT_ID",
            "apis.0.azure_ad_secret_value": "AZURE_AD_SECRET_VALUE",
            "logzio.0.token": "LOGZIO_SHIPPING_TOKEN",
            "logzio.1.token": "LOGZIO_SHIPPING_TOKEN_2",
            "apis.0.additional_fields.type": "TEST_TYPE"
        }
        curr_path = abspath(dirname(__file__))
        config_path = f"{curr_path}/testdata/azure_api_conf.yaml"
        self.run_main_program(config_path=config_path, secrets_map=secrets_map)
        time.sleep(120)
        logs = self.search_logs(f"type:{self.test_type}")
        self.assertTrue(logs, "No logs found in logzio account1")
        logs2 = self.search_logs(f"type:{self.test_type}", "2")
        self.assertTrue(logs2, "No logs found in logzio account2")

if __name__ == '__main__':
    unittest.main()
