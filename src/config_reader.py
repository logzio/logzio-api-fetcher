import logging
import yaml

from typing import Optional, Generator
from .data.logzio_config_data import LogzioConfigData
from .data.settings_config_data import SettingsConfigData
from .data.api_credentials import ApiCredentials
from .data.api_filter import ApiFilter
from .data.api_json_paths import ApiJsonPaths
from .data.oauth_api_urls import OAuthApiUrls
from .data.auth_api_config_data import AuthApiConfigData
from .data.oauth_api_config_data import OAuthApiConfigData


logger = logging.getLogger(__name__)


class ConfigReader:

    LOGZIO_CONFIG_KEY = 'logzio'
    LOGZIO_URL_CONFIG_KEY = 'url'
    LOGZIO_TOKEN_CONFIG_KEY = 'token'
    SETTINGS_CONFIG_KEY = 'settings'
    SETTINGS_TIME_INTERVAL_CONFIG_KEY = 'time_interval'
    AUTH_APIS_CONFIG_KEY = 'auth_apis'
    OAUTH_APIS_CONFIG_KEY = 'oauth_apis'
    API_TYPE_CONFIG_KEY = 'type'
    API_NAME_CONFIG_TYPE = 'name'
    API_CREDENTIALS_CONFIG_KEY = 'credentials'
    API_CREDENTIALS_ID_CONFIG_KEY = 'id'
    API_CREDENTIALS_KEY_CONFIG_KEY = 'key'
    API_START_DATE_NAME_CONFIG_KEY = 'name'
    API_FILTERS_CONFIG_KEY = 'filters'
    API_FILTER_KEY_CONFIG_KEY = 'key'
    API_FILTER_VALUE_CONFIG_KEY = 'value'
    GENERAL_AUTH_API_URL_CONFIG_KEY = 'url'
    GENERAL_OAUTH_API_TOKEN_URL_CONFIG_KEY = 'token_url'
    GENERAL_OAUTH_API_DATA_URL_CONFIG_KEY = 'data_url'
    GENERAL_API_JSON_PATHS_CONFIG_KEY = 'json_paths'
    GENERAL_API_JSON_PATHS_NEXT_URL_CONFIG_KEY = 'next_url'
    GENERAL_API_JSON_PATHS_DATA_CONFIG_KEY = 'data'
    GENERAL_API_JSON_PATHS_DATA_DATE_CONFIG_KEY = 'data_date'

    def __init__(self, config_file: str, api_general_type: str):
        with open(config_file, 'r') as config:
            self.config_data = yaml.safe_load(config)

        self.api_general_type = api_general_type

    def get_logzio_config_data(self) -> Optional[LogzioConfigData]:
        try:
            logzio_url = self.config_data[ConfigReader.LOGZIO_CONFIG_KEY][ConfigReader.LOGZIO_URL_CONFIG_KEY]
            logzio_token = self.config_data[ConfigReader.LOGZIO_CONFIG_KEY][ConfigReader.LOGZIO_TOKEN_CONFIG_KEY]
        except KeyError:
            logger.error(
                "Your configuration is not valid: logzio must have url and token. Please check your configuration.")
            return None

        return LogzioConfigData(logzio_url, logzio_token)

    def get_settings_config_data(self) -> Optional[SettingsConfigData]:
        try:
            settings = self.config_data[ConfigReader.SETTINGS_CONFIG_KEY]

            time_interval = settings[ConfigReader.SETTINGS_TIME_INTERVAL_CONFIG_KEY] * 60
        except KeyError:
            logger.error(
                "Your configuration is not valid: settings must have time_interval. Please check your configuration.")
            return None
        except TypeError:
            logger.error("Your configuration is not valid: time_interval in settings must be whole positive integer. "
                         "Please check your configuration.")
            return None

        return SettingsConfigData(time_interval)

    def get_auth_apis_config_data(self) -> Generator:
        if ConfigReader.AUTH_APIS_CONFIG_KEY in self.config_data:
            for config_auth_api_data in self.config_data[ConfigReader.AUTH_APIS_CONFIG_KEY]:
                yield self._get_auth_api_config_data(config_auth_api_data)

    def get_oauth_apis_config_data(self) -> Generator:
        if ConfigReader.OAUTH_APIS_CONFIG_KEY in self.config_data:
            for config_oauth_api_data in self.config_data[ConfigReader.OAUTH_APIS_CONFIG_KEY]:
                yield self._get_oauth_api_config_data(config_oauth_api_data)

    def _get_auth_api_config_data(self, config_auth_api_data: dict) -> Optional[AuthApiConfigData]:
        api_type = self._get_api_type(config_auth_api_data)
        api_name = self._get_api_name(config_auth_api_data)
        api_credentials = self._get_api_credentials(config_auth_api_data)
        api_filters = self._get_api_filters(config_auth_api_data)

        if api_type is None or api_name is None or api_credentials is None or api_filters is None:
            return None

        if api_type == self.api_general_type:
            api_url = self._get_auth_api_url(config_auth_api_data)
            api_start_date_name = self._get_api_start_date_name(config_auth_api_data)
            api_json_paths = self._get_api_json_paths(config_auth_api_data)

            if api_url is None or api_start_date_name is None or api_json_paths is None:
                return None

            return AuthApiConfigData(api_type, api_name, api_credentials, api_filters, api_url, api_start_date_name,
                                     api_json_paths)

        return AuthApiConfigData(api_type, api_name, api_credentials, api_filters)

    def _get_oauth_api_config_data(self, config_oauth_api_data: dict) -> Optional[OAuthApiConfigData]:
        api_type = self._get_api_type(config_oauth_api_data)
        api_name = self._get_api_name(config_oauth_api_data)
        api_credentials = self._get_api_credentials(config_oauth_api_data)
        api_filters = self._get_api_filters(config_oauth_api_data)

        if api_type is None or api_name is None or api_credentials is None or api_filters is None:
            return None

        if api_type == self.api_general_type:
            api_urls = self._get_oauth_urls(config_oauth_api_data)
            api_start_date_name = self._get_api_start_date_name(config_oauth_api_data)
            api_json_paths = self._get_api_json_paths(config_oauth_api_data)

            if api_urls is None or api_start_date_name is None or api_json_paths is None:
                return None

            return OAuthApiConfigData(api_type, api_name, api_credentials, api_filters, api_urls, api_start_date_name,
                                      api_json_paths)

        return OAuthApiConfigData(api_type, api_name, api_credentials, api_filters)

    def _get_api_type(self, config_api_data: dict) -> Optional[str]:
        try:
            api_type = config_api_data[ConfigReader.API_TYPE_CONFIG_KEY]
        except KeyError:
            logger.error(
                "Your configuration is not valid: auth_api/oauth_api must have type. Please check your configuration.")
            return None

        return api_type

    def _get_api_name(self, config_api_data: dict) -> Optional[str]:
        try:
            api_name = config_api_data[ConfigReader.API_NAME_CONFIG_TYPE]
        except KeyError:
            logger.error(
                "Your configuration is not valid: auth_api/oauth_api must have name. Please check your configuration.")
            return None

        return api_name

    def _get_api_credentials(self, config_api_data: dict) -> Optional[ApiCredentials]:
        try:
            api_credentials = config_api_data[ConfigReader.API_CREDENTIALS_CONFIG_KEY]

            api_credentials_id = api_credentials[ConfigReader.API_CREDENTIALS_ID_CONFIG_KEY]
            api_credentials_key = api_credentials[ConfigReader.API_CREDENTIALS_KEY_CONFIG_KEY]
        except KeyError:
            logger.error(
                "Your configuration is not valid: auth_api/oauth_api must have credentials with id and key. "
                "Please check your configuration.")
            return None

        return ApiCredentials(api_credentials_id, api_credentials_key)

    def _get_api_start_date_name(self, config_api_data: dict) -> Optional[str]:
        try:
            api_start_date_name = config_api_data[ConfigReader.API_START_DATE_NAME_CONFIG_KEY]
        except KeyError:
            logger.error(
                "Your configuration is not valid: general type auth_api/oauth_api must have start_date_name. "
                "Please check your configuration.")
            return None

        return api_start_date_name

    def _get_api_filters(self, config_api_data: dict) -> Optional[list[ApiFilter]]:
        api_filters = []

        if ConfigReader.API_FILTERS_CONFIG_KEY in config_api_data:
            for api_filter in config_api_data[ConfigReader.API_FILTERS_CONFIG_KEY]:
                try:
                    api_filter_key = api_filter[ConfigReader.API_FILTER_KEY_CONFIG_KEY]
                    api_filter_value = api_filter[ConfigReader.API_FILTER_VALUE_CONFIG_KEY]
                except KeyError:
                    logger.error("Your configuration is not valid: auth_api/oauth_api filter must have key and value. "
                                 "Please check your configuration.")
                    return None

                api_filters.append(ApiFilter(api_filter_key, api_filter_value))

        return api_filters

    def _get_auth_api_url(self, config_auth_api_data: dict) -> Optional[str]:
        try:
            api_url = config_auth_api_data[ConfigReader.GENERAL_AUTH_API_URL_CONFIG_KEY]
        except TypeError:
            logger.error(
                "Your configuration is not valid: general type auth_api must have url. "
                "Please check your configuration.")
            return None

        return api_url

    def _get_oauth_urls(self, config_oauth_api_data: dict) -> Optional[OAuthApiUrls]:
        try:
            api_data_url = config_oauth_api_data[ConfigReader.GENERAL_OAUTH_API_DATA_URL_CONFIG_KEY]
            api_token_url = config_oauth_api_data[ConfigReader.GENERAL_OAUTH_API_TOKEN_URL_CONFIG_KEY]
        except TypeError:
            logger.error(
                "Your configuration is not valid: general type oauth_api must have data_url and token_url. "
                "Please check your configuration.")
            return None

        return OAuthApiUrls(api_data_url, api_token_url)

    def _get_api_json_paths(self, config_api_data: dict) -> Optional[ApiJsonPaths]:
        try:
            api_json_paths = config_api_data[ConfigReader.GENERAL_API_JSON_PATHS_CONFIG_KEY]

            api_next_url_json_path = api_json_paths[ConfigReader.GENERAL_API_JSON_PATHS_NEXT_URL_CONFIG_KEY]
            api_data_json_path = api_json_paths[ConfigReader.GENERAL_API_JSON_PATHS_DATA_CONFIG_KEY]
            api_data_date_json_path = api_json_paths[ConfigReader.GENERAL_API_JSON_PATHS_DATA_DATE_CONFIG_KEY]
        except KeyError:
            logger.error(
                "Your configuration is not valid: general type auth_api/oauth_api must have json_paths with next_url, "
                "data and data_date. Please check your configuration.")
            return None

        return ApiJsonPaths(api_next_url_json_path, api_data_json_path, api_data_date_json_path)
