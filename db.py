from unittest import result
import psycopg2
import requests
import os
import pathlib
import json
import re

def dump_data():
    pathlib.Path("data").mkdir(parents=True, exist_ok=True)
    all_champs = {}
    data = requests.get("https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-champion-statistics/global/default/rcp-fe-lol-champion-statistics.js")
    matches = re.findall('.exports=({.*)},', data.text)
    if len(matches) > 0:
        match = matches[0]
        match = re.sub("([A-Z0-9]*):", r'"\1":', match)
        match = re.sub("\.([0-9]*)", r'0.\1', match)
        roles = json.loads(match)
        champs = requests.get("https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-summary.json").json()
        all_roles = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
        all_champs = {str(champ['id']):{role:{"playRate": 0, "banRate": 0, "winRate": 0} for role in all_roles} for champ in champs if champ['id'] != -1}
        for role in all_roles:
            for champion, rate in roles["SUPPORT" if role == "UTILITY" else role].items():
                all_champs[champion][role]['playRate'] = round(rate * 100, 5)

    version_split = requests.get("https://raw.communitydragon.org/latest/content-metadata.json").json()["version"].split(".")
    version = version_split[0] + "." + version_split[1]

    with open("data/championrates.json", "w") as f:
        json.dump({"data":all_champs,"patch":version}, f)

def is_played(champid,lane):
    with open("data/championrates.json") as data:
        rates = json.load(data)["data"]
        return rates[str(champid)][lane]["playRate"] > 0

def update_champions_DB(con,cur):
    dump_data()
    championsjson = requests.get('http://cdn.merakianalytics.com/riot/lol/resources/latest/en-US/champions.json').json()

    cur.execute("DROP TABLE IF EXISTS champions")

    cur.execute("""CREATE TABLE champions (
    CHAMP VARCHAR(255),
    ALIAS VARCHAR(255),
    CHAMPID INTEGER, 
    TOP BOOLEAN, 
    JGL BOOLEAN, 
    MID BOOLEAN, 
    ADC BOOLEAN, 
    SUP BOOLEAN,
    SPLASH VARCHAR(255),
    PRIMARY KEY(CHAMPID));""")

    for champ in championsjson.values():
        champname=champ["name"]
        champalias=champ["key"]
        champid=champ["id"]
        champsplash=f'https://cdn.communitydragon.org/latest/champion/{champid}/splash-art'
        aquery = "INSERT INTO champions(CHAMP,ALIAS,CHAMPID,TOP,JGL,MID,ADC,SUP,SPLASH) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        data = (champname,champalias,champid,is_played(champid,"TOP"),is_played(champid,"JUNGLE"),is_played(champid,"MIDDLE"),is_played(champid,"BOTTOM"),is_played(champid,"UTILITY"),champsplash,)
        cur.execute(aquery,data)
    con.commit()


# ------------------------------------------------------------------------------------------------------------------------------------------------------ #
DATABASE_URL = os.getenv('DATABASE_URL')

con = psycopg2.connect(DATABASE_URL)
cur = con.cursor()

cur.execute("""SELECT 
                EXISTS(SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME=%s),
                EXISTS(SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME=%s),
                EXISTS(SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME=%s)""", ('champions','profiles','wins',))

results=cur.fetchall()[0]
if not (results[0]):
    update_champions_DB(con,cur)

if not (results[1]):
    cur.execute("""CREATE TABLE profiles (
        PLAYERID VARCHAR(255),
        PRIMARY KEY(PLAYERID));""")
    con.commit()

if not (results[2]):
    cur.execute("""CREATE TABLE wins (
        CHAMPID INTEGER,
        PLAYERID VARCHAR(255),
        PRIMARY KEY(PLAYERID,CHAMPID));""")
    con.commit()

con.close()