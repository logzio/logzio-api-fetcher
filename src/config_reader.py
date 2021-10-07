import logging
import yaml

from typing import Optional, Generator
from .data.logzio_connection import LogzioConnection
from .data.auth_api_data import AuthApiData
from .data.oauth_api_data import OAuthApiData
from .data.base_data.api_base_data import ApiBaseData
from .data.base_data.auth_api_base_data import AuthApiBaseData
from .data.base_data.oauth_api_base_data import OAuthApiBaseData
from .data.base_data.api_credentials import ApiCredentials
from .data.base_data.api_settings import ApiSettings
from .data.base_data.api_filter import ApiFilter
from .data.base_data.api_custom_field import ApiCustomField
from .data.general_type_data.api_general_type_data import ApiGeneralTypeData
from .data.general_type_data.auth_api_general_type_data import AuthApiGeneralTypeData
from .data.general_type_data.oauth_api_general_type_data import OAuthApiGeneralTypeData
from .data.general_type_data.api_json_paths import ApiJsonPaths
from .data.api_http_request import ApiHttpRequest


logger = logging.getLogger(__name__)


class ConfigReader:

    AUTH_API = 'auth'
    OAUTH_API = 'oauth'

    LOGZIO_CONFIG_KEY = 'logzio'
    LOGZIO_URL_CONFIG_KEY = 'url'
    LOGZIO_TOKEN_CONFIG_KEY = 'token'

    AUTH_APIS_CONFIG_KEY = 'auth_apis'
    OAUTH_APIS_CONFIG_KEY = 'oauth_apis'
    API_TYPE_CONFIG_KEY = 'type'
    API_NAME_CONFIG_TYPE = 'name'
    API_CREDENTIALS_CONFIG_KEY = 'credentials'
    API_CREDENTIALS_ID_CONFIG_KEY = 'id'
    API_CREDENTIALS_KEY_CONFIG_KEY = 'key'
    API_SETTINGS_CONFIG_KEY = 'settings'
    API_SETTINGS_TIME_INTERVAL_CONFIG_KEY = 'time_interval'
    API_SETTINGS_DAYS_BACK_FETCH_CONFIG_KEY = 'days_back_fetch'
    API_FILTERS_CONFIG_KEY = 'filters'
    API_CUSTOM_FIELDS_CONFIG_KEY = 'custom_fields'
    API_START_DATE_NAME_CONFIG_KEY = 'start_date_name'
    GENERAL_AUTH_API_HTTP_REQUEST_CONFIG_KEY = 'http_request'
    OAUTH_API_TOKEN_HTTP_REQUEST_CONFIG_KEY = 'token_http_request'
    OAUTH_API_DATA_HTTP_REQUEST_CONFIG_KEY = 'data_http_request'
    API_HTTP_REQUEST_METHOD_CONFIG_KEY = 'method'
    API_HTTP_REQUEST_URL_CONFIG_KEY = 'url'
    API_HTTP_REQUEST_HEADERS_CONFIG_KEY = 'headers'
    API_HTTP_REQUEST_BODY_CONFIG_KEY = 'body'
    GENERAL_API_JSON_PATHS_CONFIG_KEY = 'json_paths'
    GENERAL_API_JSON_PATHS_NEXT_URL_CONFIG_KEY = 'next_url'
    GENERAL_API_JSON_PATHS_DATA_CONFIG_KEY = 'data'
    GENERAL_API_JSON_PATHS_DATA_DATE_CONFIG_KEY = 'data_date'

    def __init__(self, config_file: str, api_general_type: str, auth_api_types: list[str],
                 oauth_api_types: list[str]) -> None:
        with open(config_file, 'r') as config:
            self._config_data = yaml.safe_load(config)

        self._api_general_type = api_general_type
        self._auth_api_types = auth_api_types
        self._oauth_api_types = oauth_api_types

    def get_logzio_connection(self) -> Optional[LogzioConnection]:
        try:
            logzio = self._config_data[ConfigReader.LOGZIO_CONFIG_KEY]

            logzio_url = logzio[ConfigReader.LOGZIO_URL_CONFIG_KEY]
            logzio_token = logzio[ConfigReader.LOGZIO_TOKEN_CONFIG_KEY]
        except KeyError:
            logger.error(
                "Your configuration is not valid: logzio must have url and token.")
            return None

        return LogzioConnection(logzio_url, logzio_token)

    def get_auth_apis_data(self) -> Generator:
        auth_api_num = 1

        if ConfigReader.AUTH_APIS_CONFIG_KEY in self._config_data:
            for config_auth_api_data in self._config_data[ConfigReader.AUTH_APIS_CONFIG_KEY]:
                yield self._get_auth_api_data(config_auth_api_data, auth_api_num)
                auth_api_num += 1

    def get_oauth_apis_data(self) -> Generator:
        oauth_api_num = 1

        if ConfigReader.OAUTH_APIS_CONFIG_KEY in self._config_data:
            for config_oauth_api_data in self._config_data[ConfigReader.OAUTH_APIS_CONFIG_KEY]:
                yield self._get_oauth_api_data(config_oauth_api_data, oauth_api_num)
                oauth_api_num += 1

    def _get_auth_api_data(self, config_auth_api_data: dict, auth_api_num: int) -> Optional[AuthApiData]:
        auth_api_base_data = self._get_auth_api_base_data(config_auth_api_data, auth_api_num)

        if auth_api_base_data is None:
            return None

        if auth_api_base_data.base_data.type == self._api_general_type:
            api_general_type_data = self._get_auth_api_general_type_data(config_auth_api_data, auth_api_num)

            if api_general_type_data is None:
                return None

            return AuthApiData(auth_api_base_data, api_general_type_data)

        return AuthApiData(auth_api_base_data)

    def _get_oauth_api_data(self, config_oauth_api_data: dict, oauth_api_num: int) -> Optional[OAuthApiData]:
        oauth_api_base_data = self._get_oauth_api_base_data(config_oauth_api_data, oauth_api_num)

        if oauth_api_base_data is None:
            return None

        if oauth_api_base_data.base_data.type in self._oauth_api_types:
            api_general_type_data = self._get_oauth_api_general_type_data(config_oauth_api_data, oauth_api_num)

            if api_general_type_data is None:
                return None

            return OAuthApiData(oauth_api_base_data, api_general_type_data)

        return None

    def _get_auth_api_base_data(self, config_auth_api_data: dict, auth_api_num: int) -> Optional[AuthApiBaseData]:
        api_base_data = self._get_api_basic_data(config_auth_api_data, ConfigReader.AUTH_API, auth_api_num)

        if api_base_data is None:
            return None

        if api_base_data.type not in self._auth_api_types:
            logger.error("Your configuration is not valid: the auth api #{0} has an unsupported type - {1}. "
                         "The supported types are: {2}".format(auth_api_num,
                                                               api_base_data.type,
                                                               self._auth_api_types))
            return None

        return AuthApiBaseData(api_base_data)

    def _get_oauth_api_base_data(self, config_oauth_api_data: dict, oauth_api_num: int) -> Optional[OAuthApiBaseData]:
        api_base_data = self._get_api_basic_data(config_oauth_api_data, ConfigReader.OAUTH_API, oauth_api_num)

        if api_base_data is None:
            return None

        if api_base_data.type not in self._oauth_api_types:
            logger.error("Your configuration is not valid: the oauth api #{0} has an unsupported type - {1}. "
                         "The supported types are: {2}".format(oauth_api_num,
                                                               api_base_data.type,
                                                               self._oauth_api_types))
            return None

        api_token_http_request, api_data_http_request = self._get_oauth_api_http_requests(config_oauth_api_data,
                                                                                          oauth_api_num)

        if api_token_http_request is None or api_data_http_request is None:
            return None

        return OAuthApiBaseData(api_base_data, api_token_http_request, api_data_http_request)

    def _get_api_basic_data(self, config_api_data: dict, api_group_type: str, api_num: int) -> Optional[ApiBaseData]:
        api_type = self._get_api_type(config_api_data, api_group_type, api_num)
        api_name = self._get_api_name(config_api_data, api_group_type, api_num)
        api_credentials = self._get_api_credentials(config_api_data, api_group_type, api_num)
        api_settings = self._get_api_settings(config_api_data, api_group_type, api_num)
        api_filters = self._get_api_filters(config_api_data)
        api_custom_fields = self._get_api_custom_fields(config_api_data)

        if api_type is None or api_name is None or api_credentials is None or api_settings is None:
            return None

        return ApiBaseData(api_type, api_name, api_credentials, api_settings, api_filters, api_custom_fields)

    def _get_api_type(self, config_api_data: dict, api_group_type: str, api_num: int) -> Optional[str]:
        try:
            api_type = config_api_data[ConfigReader.API_TYPE_CONFIG_KEY]
        except KeyError:
            logger.error(
                "Your configuration is not valid: the {0} api #{1} must have type.".format(api_group_type, api_num))
            return None

        return api_type

    def _get_api_name(self, config_api_data: dict, api_group_type: str, api_num: int) -> Optional[str]:
        try:
            api_name = config_api_data[ConfigReader.API_NAME_CONFIG_TYPE]
        except KeyError:
            logger.error(
                "Your configuration is not valid: the {0} api #{1} must have name.".format(api_group_type, api_num))
            return None

        return api_name

    def _get_api_credentials(self, config_api_data: dict, api_group_type: str,
                             api_num: int) -> Optional[ApiCredentials]:
        try:
            api_credentials = config_api_data[ConfigReader.API_CREDENTIALS_CONFIG_KEY]

            api_credentials_id = api_credentials[ConfigReader.API_CREDENTIALS_ID_CONFIG_KEY]
            api_credentials_key = api_credentials[ConfigReader.API_CREDENTIALS_KEY_CONFIG_KEY]
        except KeyError:
            logger.error(
                "Your configuration is not valid: the {0} api #{1} must have credentials with id and key.".format(
                    api_group_type, api_num))
            return None

        return ApiCredentials(api_credentials_id, api_credentials_key)

    def _get_api_settings(self, config_api_data: dict, api_group_type: str, api_num: int) -> Optional[ApiSettings]:
        try:
            settings = config_api_data[ConfigReader.API_SETTINGS_CONFIG_KEY]

            time_interval = settings[ConfigReader.API_SETTINGS_TIME_INTERVAL_CONFIG_KEY] * 60
        except KeyError:
            logger.error(
                "Your configuration is not valid: the {0} api #{1} must have settings with time_interval.".format(
                    api_group_type, api_num))
            return None
        except TypeError:
            logger.error("Your configuration is not valid: the time_interval (under settings) of {0} api #{1} must "
                         "be whole positive integer.".format(api_group_type, api_num))
            return None

        days_back_to_fetch = settings.get(ConfigReader.API_SETTINGS_DAYS_BACK_FETCH_CONFIG_KEY)

        if days_back_to_fetch is None:
            return ApiSettings(time_interval)

        try:
            int(days_back_to_fetch)
        except ValueError:
            logger.error("Your configuration is not valid: the days_back_fetch (under settings) of {0} api #{1} must "
                         "be whole positive integer.".format(api_group_type, api_num))
            return None

        return ApiSettings(time_interval, days_back_to_fetch)

    def _get_api_filters(self, config_api_data: dict) -> Optional[list[ApiFilter]]:
        api_filters = []

        if ConfigReader.API_FILTERS_CONFIG_KEY in config_api_data:
            for filter_key, filter_value in config_api_data[ConfigReader.API_FILTERS_CONFIG_KEY].items():
                api_filters.append(ApiFilter(filter_key, filter_value))

        return api_filters

    def _get_api_custom_fields(self, config_api_data: dict) -> Optional[list[ApiCustomField]]:
        api_custom_fields = []

        if ConfigReader.API_CUSTOM_FIELDS_CONFIG_KEY in config_api_data:
            for api_custom_field_key, api_custom_field_value in config_api_data[ConfigReader.API_CUSTOM_FIELDS_CONFIG_KEY].items():
                api_custom_fields.append(ApiCustomField(api_custom_field_key, api_custom_field_value))

        return api_custom_fields

    def _get_auth_api_general_type_data(self, config_auth_api_data: dict,
                                        auth_api_num: int) -> Optional[AuthApiGeneralTypeData]:
        api_general_type_data = self._get_api_general_type_data(config_auth_api_data,
                                                                ConfigReader.AUTH_API,
                                                                auth_api_num)

        if api_general_type_data is None:
            return None

        api_http_request = self._get_auth_api_http_request(config_auth_api_data, auth_api_num)

        if api_http_request is None:
            return None

        return AuthApiGeneralTypeData(api_general_type_data, api_http_request)

    def _get_oauth_api_general_type_data(self, config_oauth_api_data: dict,
                                         oauth_api_num: int) -> Optional[OAuthApiGeneralTypeData]:
        api_general_type_data = self._get_api_general_type_data(config_oauth_api_data,
                                                                ConfigReader.OAUTH_API,
                                                                oauth_api_num)

        if api_general_type_data is None:
            return None

        return OAuthApiGeneralTypeData(api_general_type_data)

    def _get_api_general_type_data(self, config_api_data, api_group_type: str,
                                   api_num: int) -> Optional[ApiGeneralTypeData]:
        api_start_date_name = self._get_api_start_date_name(config_api_data, api_group_type, api_num)
        api_json_paths = self._get_api_json_paths(config_api_data, api_group_type, api_num)

        if api_start_date_name is None or api_json_paths is None:
            return None

        return ApiGeneralTypeData(api_start_date_name, api_json_paths)

    def _get_api_start_date_name(self, config_api_data: dict, api_group_type: str, api_num: int) -> Optional[str]:
        try:
            api_start_date_name = config_api_data[ConfigReader.API_START_DATE_NAME_CONFIG_KEY]
        except KeyError:
            logger.error(
                "Your configuration is not valid: the general type {0} api #{1} must have start_date_name.".format(
                    api_group_type, api_num))
            return None

        return api_start_date_name

    def _get_api_json_paths(self, config_api_data: dict, api_group_type: str, api_num: int) -> Optional[ApiJsonPaths]:
        try:
            api_json_paths = config_api_data[ConfigReader.GENERAL_API_JSON_PATHS_CONFIG_KEY]

            api_next_url_json_path = api_json_paths[ConfigReader.GENERAL_API_JSON_PATHS_NEXT_URL_CONFIG_KEY]
            api_data_json_path = api_json_paths[ConfigReader.GENERAL_API_JSON_PATHS_DATA_CONFIG_KEY]
            api_data_date_json_path = api_json_paths[ConfigReader.GENERAL_API_JSON_PATHS_DATA_DATE_CONFIG_KEY]
        except KeyError:
            logger.error(
                "Your configuration is not valid: the general type {0} api #{1} must have json_paths with next_url, "
                "data and data_date.".format(api_group_type, api_num))
            return None

        return ApiJsonPaths(api_next_url_json_path, api_data_json_path, api_data_date_json_path)

    def _get_auth_api_http_request(self, config_auth_api_data: dict, auth_api_num: int) -> Optional[ApiHttpRequest]:
        try:
            api_http_request = config_auth_api_data[ConfigReader.GENERAL_AUTH_API_HTTP_REQUEST_CONFIG_KEY]

            api_http_request_method = api_http_request[ConfigReader.API_HTTP_REQUEST_METHOD_CONFIG_KEY]
            api_url = api_http_request[ConfigReader.API_HTTP_REQUEST_URL_CONFIG_KEY]
        except TypeError:
            logger.error(
                "Your configuration is not valid: the general type auth api #{} must have http_request with "
                "method and url.".format(auth_api_num))
            return None

        if api_http_request_method not in ApiHttpRequest.HTTP_METHODS:
            logger.error(
                "Your configuration is not valid: the general type auth api #{0} has an unsupported method (under "
                "http_request) - {1}. The supported methods are: {2}".format(auth_api_num,
                                                                             api_http_request_method,
                                                                             ApiHttpRequest.HTTP_METHODS))
            return None

        return ApiHttpRequest(api_http_request_method,
                              api_url,
                              api_http_request.get(ConfigReader.API_HTTP_REQUEST_HEADERS_CONFIG_KEY),
                              api_http_request.get(ConfigReader.API_HTTP_REQUEST_BODY_CONFIG_KEY))

    def _get_oauth_api_http_requests(self, config_oauth_api_data: dict,
                                     oauth_api_num: int) -> Optional[tuple[ApiHttpRequest, ApiHttpRequest]]:
        try:
            api_token_http_request = config_oauth_api_data[ConfigReader.OAUTH_API_TOKEN_HTTP_REQUEST_CONFIG_KEY]
            api_data_http_request = config_oauth_api_data[ConfigReader.OAUTH_API_DATA_HTTP_REQUEST_CONFIG_KEY]

            api_token_http_request_method = api_token_http_request[ConfigReader.API_HTTP_REQUEST_METHOD_CONFIG_KEY]
            api_token_url = api_token_http_request[ConfigReader.API_HTTP_REQUEST_URL_CONFIG_KEY]
            api_data_http_request_method = api_token_http_request[ConfigReader.API_HTTP_REQUEST_METHOD_CONFIG_KEY]
            api_data_url = api_data_http_request[ConfigReader.API_HTTP_REQUEST_URL_CONFIG_KEY]
        except TypeError:
            logger.error(
                "Your configuration is not valid: the general type oauth api #{} must have token_http_request and"
                "data_http_request both with method and url.".format(oauth_api_num))
            return None

        if api_token_http_request_method not in ApiHttpRequest.HTTP_METHODS:
            logger.error(
                "Your configuration is not valid: the general type oauth api #{0} has an unsupported method (under "
                "token_http_request) - {1}. The supported methods are: {2}".format(oauth_api_num,
                                                                                   api_token_http_request_method,
                                                                                   ApiHttpRequest.HTTP_METHODS))
            return None

        if api_data_http_request_method not in ApiHttpRequest.HTTP_METHODS:
            logger.error(
                "Your configuration is not valid: the general type oauth api #{0} has an unsupported method (under "
                "data_http_request) - {1}. The supported methods are: {2}".format(oauth_api_num,
                                                                                  api_data_http_request_method,
                                                                                  ApiHttpRequest.HTTP_METHODS))
            return None

        token_http_request = ApiHttpRequest(api_token_http_request_method,
                                            api_token_url,
                                            api_token_http_request.get(ConfigReader.API_HTTP_REQUEST_HEADERS_CONFIG_KEY),
                                            api_token_http_request.get(ConfigReader.API_HTTP_REQUEST_BODY_CONFIG_KEY))
        data_http_request = ApiHttpRequest(api_data_http_request_method,
                                           api_data_url,
                                           api_data_http_request.get(ConfigReader.API_HTTP_REQUEST_HEADERS_CONFIG_KEY),
                                           api_data_http_request.get(ConfigReader.API_HTTP_REQUEST_BODY_CONFIG_KEY))

        return token_http_request, data_http_request

    '''
    def _get_oauth_urls(self, config_oauth_api_data: dict) -> Optional[OAuthApiUrls]:
        try:
            api_data_url = config_oauth_api_data[ConfigReader.GENERAL_OAUTH_API_DATA_URL_CONFIG_KEY][
                ConfigReader.GENERAL_API_URL_CONFIG_KEY]
            api_token_url = config_oauth_api_data[ConfigReader.GENERAL_OAUTH_API_TOKEN_URL_CONFIG_KEY][
                ConfigReader.GENERAL_API_URL_CONFIG_KEY]
            api_data_body = config_oauth_api_data[ConfigReader.GENERAL_OAUTH_API_DATA_URL_CONFIG_KEY].get(
                ConfigReader.GENERAL_API_URL_BODY_CONFIG_KEY)
            api_token_body = config_oauth_api_data[ConfigReader.GENERAL_OAUTH_API_TOKEN_URL_CONFIG_KEY].get(
                ConfigReader.GENERAL_API_URL_BODY_CONFIG_KEY)
            api_data_headers = config_oauth_api_data[ConfigReader.GENERAL_OAUTH_API_DATA_URL_CONFIG_KEY].get(
                ConfigReader.GENERAL_API_URL_HEADERS_CONFIG_KEY)
            api_token_headers = config_oauth_api_data[ConfigReader.GENERAL_OAUTH_API_TOKEN_URL_CONFIG_KEY].get(
                ConfigReader.GENERAL_API_URL_CONFIG_KEY)
        except TypeError:
            logger.error(
                "Your configuration is not valid: general type oauth_api must have data_url and token_url. "
                "Please check your configuration.")
            return None

        return OAuthApiUrls(ApiHttpRequest(api_data_url, api_data_headers, api_data_body),
                            ApiHttpRequest(api_token_url, api_token_headers, api_token_body))
    '''
