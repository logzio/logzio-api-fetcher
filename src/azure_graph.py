import logging
import urllib

from datetime import datetime, timedelta
from src.data.oauth_api_data import OAuthApiData
from src.oauth_api import OAuthApi

logger = logging.getLogger(__name__)


class AzureGraph(OAuthApi):
    DEFAULT_GRAPH_DATA_LINK = 'value'
    AZURE_GRAPH_TOKEN_SCOPE = 'scope'
    AZURE_GRAPH_FILTER_CONCAT = '&$'
    NEXT_LINK = '@odata.nextLink'

    def __init__(self, oauth_api_data: OAuthApiData) -> None:
        oauth_api_data.general_type_data.general_type_data.json_paths.next_url = self.NEXT_LINK
        oauth_api_data.general_type_data.general_type_data.json_paths.data = self.DEFAULT_GRAPH_DATA_LINK
        super().__init__(oauth_api_data.base_data, oauth_api_data.general_type_data)

    def get_last_start_date(self) -> str:
        return self._current_data_last_date

    def _build_api_url(self) -> str:
        api_url = self._data_request.url
        api_filters_num = self._base_data.get_filters_size()
        if self._current_data_last_date is not None:
            start_date_str = self._get_new_start_date()
            new_start_date = start_date_str.split('.')[0]
        else:
            start_date = datetime.utcnow() - timedelta(days=self.base_data.settings.days_back_to_fetch)
            new_start_date = start_date.isoformat(' ', 'seconds')
            new_start_date = new_start_date.replace(' ', 'T')
        api_url += "?$filter=" + self._general_type_data.json_paths.data_date + ' gt ' + new_start_date + 'Z'
        if api_filters_num > 0:
            api_url += '&$'
        for api_filter in self._base_data.filters:
            api_url += api_filter.key + '=' + str(api_filter.value)
            api_filters_num -= 1

            if api_filters_num > 0:
                api_url += self.AZURE_GRAPH_FILTER_CONCAT
        return api_url
