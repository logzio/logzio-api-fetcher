import base64
from pydantic import Field

from src.apis.oauth.OAuth import OAuthApi
from src.apis.general.Api import ApiFetcher, ReqMethod


class CiscoXdr(OAuthApi):
    cisco_client_id: str = Field(frozen=True)
    client_password: str = Field(frozen=True)

    def __init__(self, **data):
        credentials = f"{data.get('cisco_client_id')}:{data.get('client_password')}"
        token_request = ApiFetcher(
            url=f"https://visibility.amp.cisco.com/iroh/oauth2/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "Authorization": f"Basic {base64.b64encode(credentials.encode()).decode()}"
            },
            body="grant_type=client_credentials",
            method=ReqMethod.POST)

        data_request_config = data.pop("data_request")
        default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Merge custom headers with default headers
        if 'headers' in data_request_config:
            default_headers.update(data_request_config['headers'])
        
        data_request_config['headers'] = default_headers
        data_request = ApiFetcher(**data_request_config)

        super().__init__(token_request=token_request, data_request=data_request, **data) 