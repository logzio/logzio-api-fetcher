from pydantic import Field

from src.apis.google.GoogleWorkspace import GoogleWorkspace

DEFAULT_USER_KEY = "all"


class GoogleWorkspaceActivity(GoogleWorkspace):
    """
    :param application_name: The application name to fetch the data from.
    :param user_key: The user key to fetch the data for.
    """
    application_name: str
    user_key: str = Field(default=DEFAULT_USER_KEY)

    def __init__(self, **data):
        url = f"https://admin.googleapis.com/admin/reports/v1/activity/users/{data.get("user_key", DEFAULT_USER_KEY)}/applications/{data.get("application_name")}"
        data_req = {
            "url": url,
            "next_url": url + "?startTime={res.items.[0].id.time}"
        }
        super().__init__(data_request=data_req, **data)
