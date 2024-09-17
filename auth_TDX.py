import aiohttp
import time


class AsyncTDXAuth:
    def __init__(self, app_id, app_key):
        self.app_id = app_id
        self.app_key = app_key
        self.token_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        self.access_token = None
        self.expire_time = 0  # Token expiration time (epoch timestamp)

    async def get_access_token(self):
        # If the token is still valid, return it
        if self.access_token and time.time() < self.expire_time:
            return self.access_token

        data = {
            'grant_type': 'client_credentials',
            'client_id': self.app_id,
            'client_secret': self.app_key
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.token_url, data=data, headers=headers) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data['access_token']
                    expires_in = token_data['expires_in']  # Token validity duration in seconds
                    self.expire_time = time.time() + expires_in - 60  # Refresh token 60 seconds before it expires
                    return self.access_token
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to get access token: {response.status}, {error_text}")
