class AzureADClientData:

    def __init__(self, tenant_id: str, scope: str, subscription_id: str = None, user_id: str = None):
        self._tenant_id = tenant_id
        self._subscription_id = subscription_id
        self._user_id = user_id
        self._scope = scope

    @property
    def tenant_id(self) -> str:
        return self.tenant_id

    @property
    def subscription_id(self) -> str:
        return self.subscription_id

    @property
    def user_id(self) -> str:
        return self.user_id

    @property
    def scope(self) -> str:
        return self._scope
