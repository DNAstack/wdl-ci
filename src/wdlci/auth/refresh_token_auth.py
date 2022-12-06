import base64
import datetime
import requests
from wdlci.config import Config
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliException

class RefreshTokenAuth(object):

    REFRESH_EVERY = 2700.0

    def __init__(self, refresh_token, scopes):
        self.refresh_token = refresh_token
        self.scopes = scopes
        self._access_token = None
        self._access_token_issued_at = None

    @property
    def access_token(self):
        if not self._access_token:
            self.__obtain_access_token()
        
        now = datetime.datetime.now()
        time_diff = (now - self._access_token_issued_at).total_seconds()
        if time_diff > self.__class__.REFRESH_EVERY:
            self.__obtain_access_token()
        
        return self._access_token
    
    def __obtain_access_token(self):
        config = Config.instance()
        
        url = f"{config.wallet_url}/oauth/token"
        params = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "scope": " ".join(self.scopes)
        }

        headers = {
            "Authorization": "Basic " + self.__base64_encode_string(f"{config.wallet_client_id}:{config.wallet_client_secret}")
        }

        response = requests.post(url, params=params, headers=headers)
        if response.status_code != 200:
            raise WdlTestCliException("could not obtain access token from refresh token", 1)

        response_json = response.json()

        self._access_token = response_json["access_token"]
        self._access_token_issued_at = datetime.datetime.now()
    
    def __base64_encode_string(self, message):
        message_bytes = message.encode('utf-8')
        base64_bytes = base64.b64encode(message_bytes)
        base64_message = base64_bytes.decode('utf-8')
        return base64_message
