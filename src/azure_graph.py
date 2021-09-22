import logging

from src.data.oauth_api_config_data import OAuthApiConfigData
from src.oauth_api import OAuthApi

logger = logging.getLogger(__name__)


class AzureGraph(OAuthApi):
    DEFAULT_GRAPH_DATA_LINK = 'value'
    AZURE_GRAPH_TOKEN_SCOPE = 'scope'
    AZURE_GRAPH_FILTER_CONCAT = '&$'
    NEXT_LINK = '@odata.nextLink'

    def __init__(self, config_data: OAuthApiConfigData) -> None:
        config_data.json_paths.next_url = self.NEXT_LINK
        config_data.json_paths.data = self.DEFAULT_GRAPH_DATA_LINK
        super().__init__(config_data)

    def get_last_start_date(self) -> str:
        return self._current_data_last_date

    def _build_api_url(self) -> str:
        api_url = self.oauth_config.urls.data_url.api_url
        api_filters_num = len(self.oauth_config.config_base_data.filters)
        if self._current_data_last_date is not None:
            api_url += "?$filter=" + self.oauth_config.json_paths.data_date + ' ge ' + self._get_new_start_date()
        if api_filters_num > 0:
            if self._current_data_last_date is not None:
                api_url += self.AZURE_GRAPH_FILTER_CONCAT
            else:
                api_url += '?$'
        for api_filter in self.oauth_config.config_base_data.filters:
            api_url += api_filter.key + '=' + str(api_filter.value)
            api_filters_num -= 1

            if api_filters_num > 0:
                api_url += self.AZURE_GRAPH_FILTER_CONCAT

        return api_url

