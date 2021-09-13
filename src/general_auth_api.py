import logging

from .auth_api import AuthApi
from .data.api_credentials import ApiCredentials
from .data.api_filter import ApiFilter
from .data.api_json_paths import ApiJsonPaths


logger = logging.getLogger(__name__)


class GeneralAuthApi(AuthApi):

    def __init__(self, api_name: str, api_credentials: ApiCredentials, api_filters: list[ApiFilter],
                 api_url: str, api_start_date_name: str, api_json_paths: ApiJsonPaths) -> None:
        super().__init__(api_name, api_credentials, api_filters, api_url, api_start_date_name, api_json_paths)
