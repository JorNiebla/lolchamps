from flask import Flask, render_template, request, session
from oauth import Oauth

app = Flask(__name__)
app.config["SECRET_KEY"] = "test123"

@app.route("/")
def home():
    return render_template("index.html", discord_url=Oauth.discord_login_url)

@app.route("/login")
def login():
  code = request.args.get("code")
  at = Oauth.get_access_token(code)
  session["token"] = at
  user = Oauth.get_user_json(at)
  print(user)
  user_name, user_id = user.get("username"), user.get("discriminator")
  connections = Oauth.get_user_connections_json(at)
  content = ""
  for game in connections:
    if (game["type"] == "riotgames") or (game["type"] == "leagueoflegends"):
      if content != "":
        content += "\n"
      print(game)
      content += f'The connection for {game["type"]} has name {game["name"]} and id {game["id"]}'
  print(content)
  # print(user)
  # print(connections)

  return render_template("postlogin.html", user_name=user_name,user_id=user_id, content=content.replace('\n', '<br>'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)