import os
import threading
import random
import string
import unittest
from os.path import join, abspath, dirname

from dotenv import load_dotenv

from src.main import main
from e2e_tests.utils.config_utils import update_config_tokens, delete_temp_files, validate_config_tokens
from e2e_tests.utils.log_utils import search_data


class ApiE2ETest(unittest.TestCase):

    def setUp(self):
        self.test_type = f"api-fetcher-e2e-test-{self.generate_random_string()}"
        os.environ["TEST_TYPE"] = self.test_type
        self.token_map = self.get_token_map()
        self.config_path = self.get_config_path()
        self.temp_config_path = update_config_tokens(self.config_path, self.token_map)
        validate_config_tokens(self.token_map)
        self.module_specific_setup()

    def tearDown(self):
        self.module_specific_teardown()
        delete_temp_files()

    @staticmethod
    def generate_random_string(length=6):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def run_main_program(self, test=False):
        thread = threading.Thread(target=main, kwargs={"conf_path": self.temp_config_path, "test": test})
        thread.daemon = True
        thread.start()
        thread.join(timeout=60)

    def search_logs(self, query):
        return search_data(query)

    def get_token_map(self):
        raise NotImplementedError("Subclasses should implement this method")

    def get_config_path(self):
        raise NotImplementedError("Subclasses should implement this method")

    def module_specific_setup(self):
        pass

    def module_specific_teardown(self):
        pass
