# End-to-End Tests

## Overview
This guide provides instructions for developers on how to add new end-to-end (E2E) tests for different modules using the ApiE2ETest base class. It also outlines the necessary environment variables that need to be set.

### Environment Variables

Ensure the following environment variables are set:
- LOGZIO_API_TOKEN: Your Logz.io API token.
- LOGZIO_SHIPPING_TOKEN: Your Logz.io shipping token.

Or any other environment variables that are required you're the tests to run.

### Adding New E2E Tests
1. Create a New Test File: Add a new test file in the `e2e_tests/apis/` directory. Follow the naming convention `test_<module_name>_e2e.py`.
2. Extend the Base Class: Inherit from the `ApiE2ETest` base class to leverage common setup and teardown functionalities.
3. Implement Module-Specific Methods: Override the `get_token_map`, `get_config_path`, `module_specific_setup`, and `module_specific_teardown` methods as needed.
4. Add Configuration Files: Place any necessary configuration files in the `e2e_tests/testdata/` directory.

### Example
```python
from e2e_tests.api_e2e_test import ApiE2ETest
import unittest
from os.path import abspath, dirname

class TestNewModuleE2E(ApiE2ETest):

    def module_specific_setup(self):
        # Add module-specific setup here
        pass

    def get_token_map(self):
        return {
            "apis.0.new_module_token": "NEW_MODULE_TOKEN",
            "logzio.token": "LOGZIO_SHIPPING_TOKEN",
            "apis.0.additional_fields.type": "TEST_TYPE"
        }

    def get_config_path(self):
        self.curr_path = abspath(dirname(__file__))
        return f"{self.curr_path}/testdata/valid_new_module_config.yaml"

    def test_new_module_e2e(self):
        self.run_main_program()
        logs = self.search_logs(f"type:{self.test_type}")
        self.assertTrue(logs)
        self.assertTrue(all([log.get("_source").get("eventType") == "new_event" for log in logs]))

if __name__ == '__main__':
    unittest.main()
```

### Implementing get_token_map Method
The `get_token_map` method is crucial for mapping environment variables to the configuration tokens used in your test configuration files. This method should return a dictionary where the keys are the paths to the tokens in the configuration file, and the values are the corresponding environment variable names.

### Utility Functions
- `search_data(query)`: Searches logs based on the provided query.
