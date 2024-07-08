import os
from os.path import abspath, dirname
import threading
import yaml

from src.main import main


curr_path = abspath(dirname(dirname(__file__)))
temp_int_conf_path = f"{abspath(dirname(dirname(dirname(__file__))))}/src/shared/config.yaml"
test_config_paths = [f"{curr_path}/testConfigs/azure_api_conf.yaml"]


def _update_config_tokens(file_path):
    """
    Updates the tokens in the given file.
    """
    with open(file_path, "r") as conf:
        content = yaml.safe_load(conf)

    content["apis"][0]["azure_ad_tenant_id"] = os.environ["AZURE_AD_TENANT_ID"]
    content["apis"][0]["azure_ad_client_id"] = os.environ["AZURE_AD_CLIENT_ID"]
    content["apis"][0]["azure_ad_secret_value"] = os.environ["AZURE_AD_SECRET_VALUE"]
    content["logzio"]["token"] = os.environ["LOGZIO_SHIPPING_TOKEN"]

    path, ext = file_path.split(".")
    temp_test_path = f"{path}_temp.{ext}"

    with open(temp_test_path, "w") as file:
        yaml.dump(content, file)

    return temp_test_path


def integration_test():
    """
    Runs the integration to send real data
    """
    threads = []

    # in case we want to add more configs to the integration test in the future;
    for file in test_config_paths:
        temp_file = _update_config_tokens(file)
        thread = threading.Thread(target=main, args=(temp_file, True,))
        threads.append(thread)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == '__main__':
    integration_test()
