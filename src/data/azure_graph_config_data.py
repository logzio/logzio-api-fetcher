from .azure_ad_client_data import AzureADClientData
from .config_base_data import ConfigBaseData
from .oauth_api_config_data import OAuthApiConfigData


class AzureGraphConfigData:
    USER_ID_CONFIG_KEY = 'user_id'
    SUBSCRIPTION_ID_CONFIG_KEY = 'subscription_id'
    TENANT_ID_CONFIG_KEY = 'tenant_id'
    OAUTH_GRAPH_TOKEN_SCOPE = 'scope'
    GRAPH_TOKEN_SCOPE_CONFIG_KEY = 'scope'
    GRAPH_TENANT_ID_CONFIG_KEY = 'tenantId'

    def __init__(self, oauth_config: OAuthApiConfigData, azure_ad_client: AzureADClientData):
        self._oauth_config = oauth_config
        self._azure_ad_client = azure_ad_client

    @property
    def oauth_config(self) -> OAuthApiConfigData:
        return self._oauth_config

    @property
    def azure_ad_client(self) -> AzureADClientData:
        return self._azure_ad_client

    @property
    def config_base_data(self) -> ConfigBaseData:
        return self._oauth_config.config_base_data
