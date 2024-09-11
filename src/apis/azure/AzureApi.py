from datetime import datetime, timedelta, UTC
from pydantic import Field

from src.apis.oauth.OAuth import OAuthApi
from src.apis.general.Api import ReqMethod, ApiFetcher


class AzureApi(OAuthApi):
    """
    Initialize a general Azure API call to prevent duplication of 'token_request' in subclasses.
    :param name: Optional custom name for the API.
    :param azure_ad_tenant_id: The Azure AD Tenant id
    :param azure_ad_client_id: The Azure AD Client id
    :param azure_ad_secret_value: The Azure AD Secret value
    :param days_back_fetch: The amount of days to fetch back in the first request
    :param date_filter_key: The name of key to use for the date filter in the request URL params.
    """
    name: str = Field(default="azure api")
    azure_ad_tenant_id: str = Field(frozen=True)
    azure_ad_client_id: str = Field(frozen=True)
    azure_ad_secret_value: str = Field(frozen=True)
    days_back_fetch: int = Field(default=1, frozen=True)
    date_filter_key: str = Field(default="createdDateTime")

    def __init__(self, **data):
        scope = data.pop('scope', "https://graph.microsoft.com/.default")

        token_request = ApiFetcher(
            url=f"https://login.microsoftonline.com/{data.get('azure_ad_tenant_id')}/oauth2/v2.0/token",
            body=f"""client_id={data.get('azure_ad_client_id')}
                        &scope={scope}
                        &client_secret={data.get('azure_ad_secret_value')}
                        &grant_type=client_credentials
                        """,
            method=ReqMethod.POST)

        super().__init__(token_request=token_request, **data)

    def generate_start_fetch_date(self):
        return (datetime.now(UTC) - timedelta(days=self.days_back_fetch)).strftime("%Y-%m-%dT%H:%M:%SZ")
