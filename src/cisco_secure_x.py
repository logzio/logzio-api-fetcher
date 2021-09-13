import logging

from .auth_api import AuthApi
from .data.api_credentials import ApiCredentials
from .data.api_filter import ApiFilter
from .data.api_json_paths import ApiJsonPaths


logger = logging.getLogger(__name__)


class CiscoSecureX(AuthApi):

    GET_EVENTS_URL = 'https://api.amp.cisco.com/v1/events?'
    START_DATE_NAME = 'start_date'

    def __init__(self, api_name: str, api_credentials: ApiCredentials, api_filters: list[ApiFilter]) -> None:
        json_paths = ApiJsonPaths(api_next_url_json_path='$.metadata.links.next', api_data_json_path='$.data',
                                  api_data_date_json_path='$.date')
        super().__init__(api_name, api_credentials, api_filters, CiscoSecureX.GET_EVENTS_URL,
                         CiscoSecureX.START_DATE_NAME, json_paths)
