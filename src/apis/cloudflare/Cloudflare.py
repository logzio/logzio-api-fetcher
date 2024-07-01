from pydantic import Field

from src.apis.general.Api import ApiFetcher
from src.apis.general.PaginationSettings import PaginationSettings
from src.apis.general.StopPaginationSettings import StopPaginationSettings


class Cloudflare(ApiFetcher):
    """
    :param cloudflare_account_id: The CloudFlare Account ID
    :param cloudflare_bearer_token: The cloudflare Bearer token
    :param pagination_off: True if pagination should be off, False otherwise
    """
    cloudflare_account_id: str = Field(frozen=True)
    cloudflare_bearer_token: str = Field(frozen=True)
    pagination_off: bool = Field(default=False)

    def __init__(self, **data):
        res_data_path = "result"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {data.get('cloudflare_bearer_token')}"
        }
        pagination = None
        if not data.get("pagination_off"):
            if "?" in data.get("url"):
                url_format = "&page={res.result_info.page+1}"
            else:
                url_format = "?page={res.result_info.page+1}"
            pagination = PaginationSettings(type="url",
                                            url_format=url_format,
                                            update_first_url=True,
                                            stop_indication=StopPaginationSettings(field=res_data_path,
                                                                                   condition="empty"))

        super().__init__(headers=headers, pagination=pagination, response_data_path=res_data_path, **data)

        # Update the cloudflare account id in both the url and next url
        self.url = self.url.replace("{account_id}", self.cloudflare_account_id)
        self.next_url = self.next_url.replace("{account_id}", self.cloudflare_account_id)
