# End-to-End Tests

## Overview
This guide provides instructions for developers on how to add new end-to-end (E2E) tests for different modules using the `ApiE2ETest` base class. It also outlines the necessary environment variables that need to be set.

### Environment Variables

Ensure the following environment variables are set:
- `LOGZIO_API_TOKEN`: Your Logz.io API token.
- `LOGZIO_SHIPPING_TOKEN`: Your Logz.io shipping token.
- `AZURE_AD_TENANT_ID`: Your Azure AD tenant ID.
- `AZURE_AD_CLIENT_ID`: Your Azure AD client ID.
- `AZURE_AD_SECRET_VALUE`: Your Azure AD secret value.

Or any other environment variables that are required for the tests to run.

### Adding New E2E Tests
1. **Create a New Test File**: Add a new test file in the `e2e_tests/apis/` directory. Follow the naming convention `test_<module_name>_e2e.py`.
2. **Extend the Base Class**: Inherit from the `ApiE2ETest` base class to leverage common setup and teardown functionalities.
3. **Implement Module-Specific Methods**: Override the `module_specific_setup`, `module_specific_teardown`, and other necessary methods as needed.
4. **Add Configuration Files**: Place any necessary configuration files in the `e2e_tests/testdata/` directory.

### Example
```python
from e2e_tests.api_e2e_test import ApiE2ETest
import unittest
from os.path import abspath, dirname

class TestNewModuleE2E(ApiE2ETest):

    def module_specific_setup(self):
        # Add module-specific setup here
        pass

    def module_specific_teardown(self):
        # Add module-specific teardown here
        pass

    def test_new_module_e2e(self):
        secrets_map = {
            "apis.0.new_module_token": "NEW_MODULE_TOKEN",
            "logzio.token": "LOGZIO_SHIPPING_TOKEN",
            "apis.0.additional_fields.type": "TEST_TYPE"
        }
        curr_path = abspath(dirname(__file__))
        config_path = f"{curr_path}/testdata/valid_new_module_config.yaml"
        self.run_main_program(config_path=config_path, secrets_map=secrets_map)
        logs = self.search_logs(f"type:{self.test_type}")
        self.assertTrue(logs)
        self.assertTrue(all([log.get("_source").get("eventType") == "new_event" for log in logs]))

if __name__ == '__main__':
    unittest.main()
```
### Utility Functions
- `run_main_program`: Runs the main program with the specified configuration file and secrets map.
- `search_logs`: Searches for logs in logzio based on the specified query.