import logging

from .auth_api import AuthApi
from .data.base_data.auth_api_base_data import AuthApiBaseData
from .data.general_type_data.auth_api_general_type_data import AuthApiGeneralTypeData
from .data.general_type_data.api_general_type_data import ApiGeneralTypeData
from .data.api_http_request import ApiHttpRequest
from .data.general_type_data.api_json_paths import ApiJsonPaths


logger = logging.getLogger(__name__)


class CiscoSecureX(AuthApi):

    HTTP_METHOD = 'GET'
    URL = 'https://api.amp.cisco.com/v1/events'
    START_DATE_NAME = 'start_date'
    END_DATE_NAME = 'end_date'
    NEXT_URL_JSON_PATH = 'metadata.links.next'
    DATA_JSON_PATH = 'data'
    DATA_DATE_JSON_PATH = 'date'

    def __init__(self, api_base_data: AuthApiBaseData) -> None:
        http_request = ApiHttpRequest(CiscoSecureX.HTTP_METHOD, CiscoSecureX.URL)
        json_paths = ApiJsonPaths(api_next_url_json_path=CiscoSecureX.NEXT_URL_JSON_PATH,
                                  api_data_json_path=CiscoSecureX.DATA_JSON_PATH,
                                  api_data_date_json_path=CiscoSecureX.DATA_DATE_JSON_PATH)
        general_type_data = ApiGeneralTypeData(CiscoSecureX.START_DATE_NAME, CiscoSecureX.END_DATE_NAME, json_paths)

        super().__init__(api_base_data,
                         AuthApiGeneralTypeData(general_type_data, http_request))
