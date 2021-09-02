import logging
import yaml

from typing import Optional
from .auth_api import AuthApi
from .oauth_api import OAuthApi
from .cisco_secure_x import CiscoSecureX
from .logzio_shipper import LogzioShipper


logger = logging.getLogger(__name__)


class ApisManager:

    CONFIG_FILE = 'config.yaml'
    LOGZIO_CONFIG_KEY = 'logzio'
    LOGZIO_URL_CONFIG_KEY = 'url'
    LOGZIO_TOKEN_CONFIG_KEY = 'token'
    AUTH_APIS_CONFIG_KEY = 'auth_apis'
    OAUTH_APIS_CONFIG_KEY = 'oauth_apis'
    API_TYPE_CONFIG_KEY = 'type'
    API_ID_CONFIG_KEY = 'id'
    API_KEY_CONFIG_KEY = 'key'
    API_FILTERS_CONFIG_KEY = 'filters'
    GENERAL_AUTH_API_URL_CONFIG_KEY = 'url'
    GENERAL_OAUTH_API_TOKEN_URL_CONFIG_KEY = 'token_url'
    GENERAL_OAUTH_API_DATA_URL_CONFIG_KEY = 'data_url'
    GENERAL_API_NEXT_URL_JSON_PATH_CONFIG_KEY = 'next_url_json_path'
    GENERAL_API_DATA_JSON_PATH_CONFIG_KEY = 'data_json_path'

    API_GENERAL_TYPE = 'general'
    API_CISCO_SECURE_X_TYPE = 'cisco_secure_x'
    API_AZURE_GRAPH_TYPE = 'azure_graph'

    def __init__(self) -> None:
        self.auth_apis: list[AuthApi] = []
        self.oauth_apis: list[OAuthApi] = []
        self.logzio_shipper = None

        if not self.__read_data_from_config():
            exit(1)

    def run(self) -> None:
        if len(self.auth_apis) == 0 and len(self.oauth_apis) == 0:
            return

        for auth_api in self.auth_apis:
            for data in auth_api.fetch_data():
                print(data)

    def __read_data_from_config(self) -> bool:
        with open(ApisManager.CONFIG_FILE, 'r') as config_file:
            config_data = yaml.safe_load(config_file)

        logzio_url, logzio_token = self.__get_logzio_data(config_data)

        if logzio_url is None or logzio_token is None:
            return False

        self.logzio_shipper = LogzioShipper(logzio_url, logzio_token)

        if not self.__add_auth_apis(config_data):
            return False

        return True

    def __get_logzio_data(self, config_data: dict) -> tuple[str, str]:
        logzio_url = None
        logzio_token = None

        try:
            logzio_url = config_data['logzio']['url']
            logzio_token = config_data['logzio']['token']
        except KeyError:
            logger.error(
                "Your configuration is not valid: logzio must have url and token. Please check your configuration.")

        return logzio_url, logzio_token

    def __add_auth_apis(self, config_data: dict) -> bool:
        if ApisManager.AUTH_APIS_CONFIG_KEY in config_data:
            for auth_api in config_data[ApisManager.AUTH_APIS_CONFIG_KEY]:
                auth_api = self.__get_auth_api(auth_api)

                if auth_api is None:
                    return False

                self.auth_apis.append(auth_api)

        return True

    def __get_auth_api(self, auth_api_data: dict) -> Optional[AuthApi]:
        api_type, api_id, api_key = self.__get_api_data(auth_api_data)

        if api_type is None or api_id is None or api_key is None:
            return None

        api_filters = self.__get_api_filters(auth_api_data)

        if api_filters is None:
            return None

        if api_type == ApisManager.API_CISCO_SECURE_X_TYPE:
            return CiscoSecureX(api_id, api_key, api_filters)

        if api_type == ApisManager.API_GENERAL_TYPE:
            api_url, api_next_url_json_path, api_data_json_path = self.__get_general_type_auth_api_data(auth_api_data)

            if api_url is None or api_next_url_json_path is None or api_data_json_path is None:
                return None

        logger.error("Your configuration is not valid: one of the auth apis has invalid type - {}.".format(api_type))
        return None

    def __get_oauth_api(self, oauth_api_data: dict) -> Optional[OAuthApi]:
        api_type, api_id, api_key = self.__get_api_data(oauth_api_data)

        if api_type is None or api_id is None or api_key is None:
            return None

        api_filters = self.__get_api_filters(oauth_api_data)

        if api_type == ApisManager.API_AZURE_GRAPH_TYPE:
            pass

        if api_type == ApisManager.API_GENERAL_TYPE:
            api_token_url, api_data_url, api_next_url_json_path, api_data_json_path = self.__get_general_type_oauth_api_data(oauth_api_data)

            if api_token_url is None or api_data_url is None or api_next_url_json_path is None or api_data_json_path is None:
                return None

        logger.error("Your configuration is not valid: one of the oauth apis has invalid type - {}.".format(api_type))
        return None

    def __get_api_data(self, api_data: dict) -> tuple[str, str, str]:
        api_type = None
        api_id = None
        api_key = None

        try:
            api_type = api_data[ApisManager.API_TYPE_CONFIG_KEY]
            api_id = api_data[ApisManager.API_ID_CONFIG_KEY]
            api_key = api_data[ApisManager.API_KEY_CONFIG_KEY]
        except KeyError:
            logger.error(
                "Your configuration is not valid: auth_api must have type, id and key. Please check your configuration.")

        return api_type, api_id, api_key

    def __get_api_filters(self, api_data: dict) -> Optional[list[dict]]:
        api_filters = []

        if ApisManager.API_FILTERS_CONFIG_KEY in api_data:
            for api_filter in api_data[ApisManager.API_FILTERS_CONFIG_KEY]:
                if 'key' not in api_filter or 'value' not in api_filter:
                    return None

                api_filters.append(api_filter)

        return api_filters

    def __get_general_type_auth_api_data(self, auth_api_data: dict) -> tuple[str, str, str]:
        api_url = None
        next_url_json_path = None
        data_json_path = None

        try:
            api_url = auth_api_data[ApisManager.GENERAL_AUTH_API_URL_CONFIG_KEY]
            next_url_json_path = auth_api_data[ApisManager.GENERAL_API_NEXT_URL_JSON_PATH_CONFIG_KEY]
            data_json_path = auth_api_data[ApisManager.GENERAL_API_DATA_JSON_PATH_CONFIG_KEY]
        except KeyError:
            logger.error(
                "Your configuration is not valid: auth_api with type general must have url, next_url_json_path and "
                "data_json_path. Please check your configuration.")

        return api_url, next_url_json_path, data_json_path

    def __get_general_type_oauth_api_data(self, oauth_api_data: dict) -> tuple[str, str, str, str]:
        api_token_url = None
        api_data_url = None
        next_url_json_path = None
        data_json_path = None

        try:
            api_token_url = oauth_api_data[ApisManager.GENERAL_OAUTH_API_TOKEN_URL_CONFIG_KEY]
            api_data_url = oauth_api_data[ApisManager.GENERAL_OAUTH_API_DATA_URL_CONFIG_KEY]
            next_url_json_path = oauth_api_data[ApisManager.GENERAL_API_NEXT_URL_JSON_PATH_CONFIG_KEY]
            data_json_path = oauth_api_data[ApisManager.GENERAL_API_DATA_JSON_PATH_CONFIG_KEY]
        except KeyError:
            logger.error(
                "Your configuration is not valid: oauth_api with type general must have token_url, data_url, "
                "next_url_json_path and data_json_path. Please check your configuration.")

        return api_token_url, api_data_url, next_url_json_path, data_json_path
