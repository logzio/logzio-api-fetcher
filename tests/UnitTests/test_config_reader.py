from os.path import abspath, dirname
import unittest

from src.config.ConfigReader import ConfigReader


curr_path = abspath(dirname(dirname(__file__)))


class TestConfigReader(unittest.TestCase):
    """
    Test reading config from YAML
    """

    def test_invalid_config(self):
        with self.assertLogs("src.config.ConfigReader", level='INFO') as log:
            ConfigReader(f"{curr_path}/testConfigs/invalid_conf.yaml")
        self.assertIn("ERROR:src.config.ConfigReader:No inputs defined. Please make sure your API input is configured under 'apis'", log.output)

    def test_multiple_apis(self):
        conf = ConfigReader(f"{curr_path}/testConfigs/multiple_apis_conf.yaml")

        self.assertEqual(len(conf.api_instances), 2)
        self.assertEqual(conf.api_instances[0].pagination_settings.max_calls, 20)
        self.assertEqual(conf.api_instances[1].scrape_interval_minutes, 5)

    def test_missing_logzio_output(self):
        with self.assertLogs("src.config.ConfigReader", level='INFO') as log:
            conf = ConfigReader(f"{curr_path}/testConfigs/missing_logz_output_conf.yaml")
        self.assertIn("WARNING:src.config.ConfigReader:No Logzio shipper output defined. Please make sure your Logzio config is configured under logzio", log.output)
        self.assertEqual(conf.logzio_shipper, None)

    def test_open_config_file_fail(self):
        with self.assertLogs("src.config.ConfigReader", level='INFO') as log:
            conf = ConfigReader(f"./not/existing/conf.yaml")
        self.assertEqual(conf.api_instances, [])
        self.assertEqual(conf.logzio_shipper, None)
