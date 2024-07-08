import glob
import json
import os
from os.path import abspath, dirname
import requests
import unittest


def _search_data(query):
    """
    Send given search query to logzio and returns the result.
    :param query:
    :return:
    """
    # Search logs in account
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
    test_configs_path = f"{curr_path}/testConfigs/*_temp.yaml"

    for file in glob.glob(test_configs_path):
        os.remove(file)


class TestDataArrived(unittest.TestCase):
    """
    Test data arrived to logzio
    """

    @classmethod
    def tearDownClass(cls):
        # Clean up temp files that the test created
        delete_temp_files()

    def test_data_in_logz(self):
        azure_logs_in_acc = _search_data("type:azure_graph_shipping_test")
        self.assertTrue(azure_logs_in_acc)  # make sure we have results
