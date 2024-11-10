import glob
import json
import os
import threading
from os.path import abspath, dirname
import requests
import unittest
import yaml

from src.main import main

TEST_TYPE = "dockerhub-audit-test"

def _search_data(query):
    """
    Send given search query to logzio and returns the result.
    :param query:
    :return:
    """
    url = "https://api.logz.io/v1/search"
    headers = {
        "X-API-TOKEN": os.environ["LOGZIO_API_TOKEN"],
        "CONTENT-TYPE": "application/json",
        "ACCEPT": "application/json"
    }
    body = {
        "query": {
            "query_string": {
                "query": query
            }
        }
    }

    r = requests.post(url=url, headers=headers, json=body)
    if r:
        data = json.loads(r.text)
        hits = data.get("hits").get("hits")
        return hits
    return []


def delete_temp_files():
    """
    delete the temp config that generated for the test
    """
    curr_path = abspath(dirname(dirname(__file__)))
    test_configs_path = f"{curr_path}/testdata/*_temp.yaml"

    for file in glob.glob(test_configs_path):
        os.remove(file)


def _update_config_tokens(file_path):
    """
    Updates the tokens in the given file.
    """
    with open(file_path, "r") as conf:
        content = yaml.safe_load(conf)
    e = os.environ
    if "DOCKERHUB_TOKEN" not in os.environ:
        raise EnvironmentError("DOCKERHUB_TOKEN environment variable is missing")
    content["apis"][0]["dockerhub_token"] = os.environ["DOCKERHUB_TOKEN"]

    if "DOCKERHUB_USER" not in os.environ:
        raise EnvironmentError("DOCKERHUB_USER environment variable is missing")
    content["apis"][0]["dockerhub_user"] = os.environ["DOCKERHUB_USER"]

    if "LOGZIO_SHIPPING_TOKEN" not in os.environ:
        raise EnvironmentError("LOGZIO_SHIPPING_TOKEN environment variable is missing")
    content["logzio"]["token"] = os.environ["LOGZIO_SHIPPING_TOKEN"]

    path, ext = file_path.rsplit(".", 1)
    temp_test_path = f"{path}_temp.{ext}"

    with open(temp_test_path, "w") as file:
        yaml.dump(content, file)

    return temp_test_path


class TestDockerhubE2E(unittest.TestCase):
    """
    Test data arrived to logzio
    """

    def test_data_in_logz(self):
        curr_path = abspath(dirname(__file__))
        config_path = f"{curr_path}/testdata/valid_dockerhub_config.yaml"
        temp_config_path = _update_config_tokens(config_path)
        thread = threading.Thread(target=main, kwargs={"conf_path": temp_config_path})
        thread.daemon = True
        thread.start()
        thread.join(timeout=60)
        azure_logs_in_acc = _search_data(f"type:{TEST_TYPE}")
        self.assertTrue(azure_logs_in_acc)
        self.assertTrue(all([log.get("_source").get("eventType") == "auditevents" for log in azure_logs_in_acc]))
        delete_temp_files()


if __name__ == '__main__':
    unittest.main()
