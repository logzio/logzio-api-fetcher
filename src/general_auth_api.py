import logging

from .auth_api import AuthApi
from .data.api_credentials import ApiCredentials
from .data.api_filter import ApiFilter
from .data.api_json_paths import ApiJsonPaths
from .data.api_url import ApiUrl
from .data.config_base_data import ConfigBaseData

logger = logging.getLogger(__name__)


class GeneralAuthApi(AuthApi):

    def __init__(self, base_config: ConfigBaseData, api_url: ApiUrl, api_json_paths: ApiJsonPaths) -> None:
        super().__init__(base_config, api_url, api_json_paths)
