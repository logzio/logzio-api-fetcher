import logging

from .auth_api import AuthApi
from .data.base_data.auth_api_base_data import AuthApiBaseData
from .data.general_type_data.auth_api_general_type_data import AuthApiGeneralTypeData


logger = logging.getLogger(__name__)


class GeneralAuthApi(AuthApi):

    def __init__(self, api_base_data: AuthApiBaseData, api_general_type_data: AuthApiGeneralTypeData) -> None:
        super().__init__(api_base_data, api_general_type_data)
