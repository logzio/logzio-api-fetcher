import logging

from .auth_api import AuthApi
from .data.api_json_paths import ApiJsonPaths
from .data.api_url import ApiUrl
from .data.config_base_data import ConfigBaseData

logger = logging.getLogger(__name__)


class CiscoSecureX(AuthApi):

    GET_EVENTS_URL = 'https://api.amp.cisco.com/v1/events?'
    START_DATE_NAME = 'start_date'

    def __init__(self, base_config: ConfigBaseData) -> None:
        json_paths = ApiJsonPaths(api_next_url_json_path='$.metadata.links.next', api_data_json_path='$.data',
                                  api_data_date_json_path='$.date')
        base_config.start_date_name = CiscoSecureX.START_DATE_NAME
        super().__init__(base_config,
                         ApiUrl(CiscoSecureX.GET_EVENTS_URL), json_paths)
