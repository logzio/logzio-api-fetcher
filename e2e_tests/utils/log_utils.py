import os
import json
import requests


def search_data(query, account=""):
    """
    Send given search query to logzio and returns the result.
    :param query:
    :param account: the account API to use, "" for LOGZIO_API_TOKEN, "2" for LOGZIO_API_TOKEN_2
    :return:
    """
    url = "https://api.logz.io/v1/search"
    account_env = {
        "": "LOGZIO_API_TOKEN",
        "2": "LOGZIO_API_TOKEN_2"
    }
    headers = {
        "X-API-TOKEN": os.environ[account_env.get(account)],
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
