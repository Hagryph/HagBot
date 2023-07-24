import json, requests
from hag_logger import Logger

class OAuth:
    client_id = None
    client_secret = None
    redirect_uri = None
    logger = Logger("oauth_error.txt")
    scope = {"channel:moderate", "chat:edit", "chat:read"}

    @staticmethod
    def get_credentials():
        with open("credentials.json") as f:
            credentials = json.load(f)
        return credentials["client_id"], credentials["client_secret"], credentials["redirect_uri"]

    @staticmethod
    def get_login_url():
        scope_str = " ".join(OAuth.scope)
        client_id, _, _ = OAuth.get_credentials()
        login_url = f"https://id.twitch.tv/oauth2/authorize?client_id={client_id}&redirect_uri={OAuth.redirect_uri}&response_type=code&scope={scope_str}"
        return login_url

    @staticmethod
    def get_user_information(access_token):
        api_url = "https://api.twitch.tv/helix/users"
        client_id, _, _ = OAuth.get_credentials()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Client-ID": client_id,
        }

        try:
            response = requests.get(api_url, headers=headers)
        except requests.exceptions.RequestException as e:
            OAuth.logger.log(f"An error occurred while making request to endpoint {api_url}: {e}")
            return None, None, None

        if response.status_code != 200:
            OAuth.logger.log(f"Failed to get user ID: {response.json()['message']}", True)
            return None, None, None
        
        try:
            user_id = int(response.json()["data"][0]["id"])
            user_name = response.json()["data"][0]["display_name"]
            user_avatar_path = response.json()["data"][0]["profile_image_url"]
        except (KeyError, IndexError) as e:
            OAuth.logger.log(f"An error occurred while parsing the response JSON: {e}")
            return None, None, None

        return user_id, user_name, user_avatar_path

    @staticmethod
    def get_access_token(code):
        client_id, client_secret, _ = OAuth.get_credentials()
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": OAuth.redirect_uri,
        }
        response = requests.post("https://id.twitch.tv/oauth2/token", data=data)
        token_response = response.json()
        access_token = token_response["access_token"]
        refresh_token = token_response["refresh_token"]
        user_id, user_name, user_avatar_path = OAuth.get_user_information(access_token)
        return access_token, refresh_token, user_id, user_name, user_avatar_path

    @staticmethod
    def refresh_access_token(refresh_token):
        client_id, client_secret, _ = OAuth.get_credentials()
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        response = requests.post("https://id.twitch.tv/oauth2/token", data=data)
        token_response = response.json()
        if "error" in token_response:
            raise Exception(f"Failed to refresh access token: {token_response['error']}")
        return token_response["access_token"]
    
_, _, OAuth.redirect_uri = OAuth.get_credentials()
creds = None