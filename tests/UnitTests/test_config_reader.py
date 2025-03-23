from os.path import abspath, dirname
import unittest

from src.config.ConfigReader import ConfigReader


curr_path = abspath(dirname(dirname(__file__)))


class TestConfigReader(unittest.TestCase):
    """
    Test reading config from YAML
    """

    def test_invalid_input_config(self):
        with self.assertLogs("src.config.ConfigReader", level='INFO') as log:
            ConfigReader(f"{curr_path}/testConfigs/invalid_input_conf.yaml")
        self.assertIn("ERROR:src.config.ConfigReader:No inputs defined. Please make sure your API input is configured under 'apis'", log.output)

    def test_multiple_apis(self):
        conf = ConfigReader(f"{curr_path}/testConfigs/multiple_apis_conf.yaml")

        self.assertEqual(len(conf.api_instances), 2)
        self.assertEqual(conf.api_instances[0].pagination_settings.max_calls, 20)
        self.assertEqual(conf.api_instances[1].scrape_interval_minutes, 5)
        for a in conf.api_instances:
            self.assertEqual(len(a.outputs), 1)

    def test_missing_logzio_output(self):
        with self.assertLogs("src.config.ConfigReader", level='INFO') as log:
            conf = ConfigReader(f"{curr_path}/testConfigs/missing_logz_output_conf.yaml")
        self.assertIn("WARNING:src.config.ConfigReader:No Logzio shipper output defined. Please make sure your Logzio config is configured under logzio", log.output)

        for a in conf.api_instances:
            self.assertEqual(a.outputs, [])

    def test_open_config_file_fail(self):
        with self.assertLogs("src.config.ConfigReader", level='INFO') as log:
            conf = ConfigReader(f"./not/existing/conf.yaml")
        self.assertEqual(conf.api_instances, [])
        self.assertIn("ERROR:src.config.ConfigReader:Did not find file ./not/existing/conf.yaml.", log.output)


    def test_multiple_outputs(self):
        with self.assertLogs("src.config.ConfigReader", level='DEBUG') as log:
            conf = ConfigReader(f"{curr_path}/testConfigs/multiple_outputs_conf.yaml")

        self.assertEqual(len(conf.api_instances), 2)
        self.assertEqual(len(conf.api_instances[0].outputs), 2)
        self.assertEqual(len(conf.api_instances[1].outputs), 1)

    def test_multiple_outputs_missing_inputs_conf(self):
        with self.assertLogs("src.config.ConfigReader", level='INFO') as log:
            conf = ConfigReader(f"{curr_path}/testConfigs/multiple_outputs_missing_input_conf.yaml")
        self.assertIn("WARNING:src.config.ConfigReader:Detected a Logzio shipper configuration without any defined inputs. No API data will be exported to it.", log.output)


    def test_invalid_output_config(self):
        with self.assertLogs("src.config.ConfigReader", level='INFO') as log:
            ConfigReader(f"{curr_path}/testConfigs/invalid_output_conf.yaml")
        self.assertIn("ERROR:src.config.ConfigReader:Invalid Logzio output config. Please make sure your Logzio config is an object for single output or a list for multiple outputs.", log.output)
