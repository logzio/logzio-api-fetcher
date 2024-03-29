import logging
from dateutil import parser
import re

from datetime import datetime
from src.api import Api
from src.data.oauth_api_data import OAuthApiData
from src.oauth_api import OAuthApi

logger = logging.getLogger(__name__)


class AzureMailReports(OAuthApi):
    MAIL_REPORTS_DATA_LINK = 'd.results'
    MAIL_REPORTS_FILTER_CONCAT = '&$'
    MAIL_REPORTS_MAX_PAGE_SIZE = 1000
    DATE_REGEX_FILTER = '\d+'

    def __init__(self, oauth_api_data: OAuthApiData) -> None:
        oauth_api_data.general_type_data.general_type_data.json_paths.data = self.MAIL_REPORTS_DATA_LINK
        self._previous_end_date = None
        super().__init__(oauth_api_data.base_data, oauth_api_data.general_type_data)

    def get_last_start_date(self) -> str:
        return self._current_data_last_date

    def _build_api_url(self) -> str:
        api_url = self._data_request.url
        api_filters_num = self._base_data.get_filters_size()
        new_end_date = self.get_new_end_date()
        new_start_date = self.get_start_date_filter()
        api_url += f"?$filter={self._general_type_data.start_date_name} eq datetime'{new_start_date}' and {self._general_type_data.end_date_name} eq datetime'{new_end_date}'"
        self._previous_end_date = new_end_date
        if api_filters_num > 0:
            api_url += self.MAIL_REPORTS_FILTER_CONCAT
        for api_filter in self._base_data.filters:
            api_url += api_filter.key + '=' + str(api_filter.value)
            api_filters_num -= 1
            if api_filters_num > 0:
                api_url += self.MAIL_REPORTS_FILTER_CONCAT
        return api_url

    def _get_last_date(self, first_item: dict) -> str:
        first_item_date = self._get_json_path_value_from_data(
            self._general_type_data.json_paths.data_date, first_item)

        if first_item_date is None:
            logger.error(
                "The json path for api {}'s data date is wrong. Please change your configuration.".format(
                    self._base_data.name))
            raise Api.ApiError
        return self._get_formatted_date_from_date_path_value(first_item_date)

    def _is_item_in_fetch_frame(self, item: dict, last_datetime_to_fetch: datetime) -> bool:
        item_date = self._get_json_path_value_from_data(
            self._general_type_data.json_paths.data_date, item)
        item_datetime = parser.parse(self._get_formatted_date_from_date_path_value(item_date))
        if item_datetime < last_datetime_to_fetch:
            return False

        return True

    def _get_formatted_date_from_date_path_value(self, date_path_value: str) -> str:
        epoch_milisec_date = re.findall(self.DATE_REGEX_FILTER, date_path_value)
        date = datetime.fromtimestamp(int(int(epoch_milisec_date[0]) / 1000))
        formatted_date = date.isoformat(' ', 'seconds')
        formatted_date = formatted_date.replace(' ', 'T')
        formatted_date += 'Z'
        return formatted_date

    def _set_current_data_last_date(self, date):
        # This comparison might not work on other date formats
        if (self._previous_end_date and date and self._previous_end_date > date) or not date:
            self._set_current_data_last_date(self._previous_end_date)
        else:
            self._current_data_last_date = date

    def get_new_end_date(self):
        return self.get_current_time_utc_string()
