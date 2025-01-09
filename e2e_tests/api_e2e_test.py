import os
import threading
import random
import string
import unittest

from src.main import main
from e2e_tests.utils.config_utils import update_config_tokens, delete_temp_files, validate_config_tokens
from e2e_tests.utils.log_utils import search_data


class ApiE2ETest(unittest.TestCase):
    """
    Base class for API End-to-End tests. Provides common setup and teardown functionalities,
    as well as utility methods for running the main program and searching logs in logzio.
    """

    def setUp(self):
        """
        Set up the test environment. Generates a random test type, sets environment variables,
        updates configuration tokens, validates the configuration, and performs module-specific setup.
        """
        self.test_type = f"api-fetcher-e2e-test-{self.generate_random_string()}"
        os.environ["TEST_TYPE"] = self.test_type
        self.token_map = self.get_token_map()
        self.config_path = self.get_config_path()
        self.temp_config_path = update_config_tokens(self.config_path, self.token_map)
        validate_config_tokens(self.token_map)
        self.module_specific_setup()

    def tearDown(self):
        """
        Tear down the test environment. Performs module-specific teardown and deletes temporary files.
        """
        self.module_specific_teardown()
        delete_temp_files()

    @staticmethod
    def generate_random_string(length=5):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def run_main_program(self, test=False):
        """
        Run the main program in a separate thread.

        Args:
            test (bool): Whether to run the program in test mode. Default is False.
        """
        thread = threading.Thread(target=main, kwargs={"conf_path": self.temp_config_path, "test": test})
        thread.daemon = True
        thread.start()
        thread.join(timeout=60)

    def search_logs(self, query):
        """
        Search logs in logzio based on the provided query.

        Args:
            query (str): The query string to search for in the logs.

        Returns:
            list: A list of log entries that match the query.
        """
        return search_data(query)

    def get_token_map(self):
        """
        Get the token map for the configuration. This method should be implemented by subclasses. The `get_token_map`
        method is crucial for mapping environment variables to the configuration tokens used in your test
        configuration files. This method should return a dictionary where the keys are the paths to the tokens in the
        configuration file, and the values are the corresponding environment variable names.

        Returns:
            dict: A dictionary mapping configuration token paths to environment variable names.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses should implement this method")

    def get_config_path(self):
        """
        Get the path to the configuration file. This method should be implemented by subclasses.

        Returns:
            str: The path to the configuration file.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses should implement this method")

    def module_specific_setup(self):
        """
        Perform module-specific setup. This method can be overridden by subclasses.
        """
        pass

    def module_specific_teardown(self):
        """
        Perform module-specific teardown. This method can be overridden by subclasses.
        """
        pass
