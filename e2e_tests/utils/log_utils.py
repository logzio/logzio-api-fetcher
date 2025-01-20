import os
import json
import requests


def search_data(query):
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
