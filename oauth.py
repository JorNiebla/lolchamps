import requests

class Oauth:
  client_id = "986305801926869052"
  client_secret = "wqW1vs-UdB-7OI3VxtE-taDjyEFNZNHV" 
  redirect_uri = "http://217.76.159.164:5000/login"
  scope = "identify%20connections"
  discord_login_url = "https://discord.com/api/oauth2/authorize?client_id=986305801926869052&redirect_uri=http%3A%2F%2F217.76.159.164%3A5000%2Flogin&response_type=code&scope=identify%20connections"
  discord_token_url = "https://discord.com/api/oauth2/token"
  discord_api_url = "https://discord.com/api"

  @staticmethod
  def get_access_token(code):
      payload = {
        "client_id": Oauth.client_id,
        "client_secret": Oauth.client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": Oauth.redirect_uri,
        "scope": Oauth.scope
      }

      access_token = requests.post(url = Oauth.discord_token_url, data = payload).json()
      return access_token.get("access_token")

  @staticmethod
  def get_user_json(access_token):
    url = f"{Oauth.discord_api_url}/users/@me"
    headers = {"Authorization": f"Bearer {access_token}"}
    user_object = requests.get(url = url, headers = headers).json()
    return user_object
  
  @staticmethod
  def get_user_connections_json(access_token):
    url = f"{Oauth.discord_api_url}/users/@me/connections"
    headers = {"Authorization": f"Bearer {access_token}"}
    connections = requests.get(url = url, headers = headers).json()
    return connections