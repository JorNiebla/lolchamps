from flask import Flask, render_template, request, session
from oauth import Oauth
from riotwatcher import RiotWatcher, LolWatcher
from dotenv import load_dotenv
import psycopg2
import os
import db

app = Flask(__name__)

load_dotenv()
app.config["SECRET_KEY"] = os.getenv('FLASK_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
RIOT_API_KEY = os.getenv('RIOT_API_KEY')
riot_watcher = RiotWatcher(RIOT_API_KEY)
lol_watcher = LolWatcher(RIOT_API_KEY)

@app.route("/")
def home():
  session.clear()
  return render_template("index.html", discord_url=Oauth.discord_login_url)

@app.route("/login")
def login():
  code = request.args.get("code")
  return render_template("login.html",code=code)

@app.route("/postlogin",methods=['POST'])
def postlogin():
  if request.form["action"] == "disconnect":
    userid = Oauth.get_user_json(session["token"]).get("id")
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    db.disconnect_account(con,cur,userid)
    con.close()
  if not ("token" in session):
    code = request.form["action"]
    at = Oauth.get_access_token(code)
    session["token"] = at
  else:
    at = session["token"]
  if (at != None):
    connections = Oauth.get_user_connections_json(at)
    nameset = set()
    for game in connections:
      if (game["type"] == "leagueoflegends"):
        nameset.add(game["name"])
    namelist = list(nameset)

    return render_template("postlogin.html", names=namelist)
  else:
    return render_template("index.html", discord_url=Oauth.discord_login_url)

@app.route("/info",methods=['POST'])
def info():
  at = session["token"]
  user = Oauth.get_user_json(at)
  user_name, user_discriminator, user_avatar, user_id = (
    user.get("username"),
    user.get("discriminator"),
    user.get("avatar"),
    user.get("id"),
  )

  region = request.form['region']
  account_name = request.form['name']
  summoner = lol_watcher.summoner.by_name(region, account_name)
  lavatar = f'https://raw.communitydragon.org/latest/game/assets/ux/summonericons/profileicon{summoner["profileIconId"]}.png'
  lname = f"{account_name}#{region}"
  davatar = f"https://cdn.discordapp.com/avatars/{user_id}/{user_avatar}.png"
  dname = f"{user_name}#{user_discriminator}"
  puuid = summoner["puuid"]
  con = psycopg2.connect(DATABASE_URL)
  cur = con.cursor()
  info = db.connect_account(con,cur,user_id,puuid,account_name,region)
  con.close()
  return render_template("info.html", lname=lname, lavatar=lavatar, davatar=davatar, dname=dname, info=info)

if __name__ == "__main__":
  app.run(host='0.0.0.0', port=5000, debug=True, ssl_context='adhoc')