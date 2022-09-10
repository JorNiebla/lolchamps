from xmlrpc.client import MAXINT, MININT
import discord
import random
from numpy import mat
import psycopg2
import riotwatcher
import db
from dotenv import load_dotenv
import os
import traceback
import asyncio
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
from riotwatcher import RiotWatcher, LolWatcher
from PIL import Image, ImageFont, ImageDraw

lanes = {'top': "TOP", 'jg': "JGL", 'jung': "JGL", 'jng': "JGL",'jungle': "JGL", 'jungler': "JGL", 'mid': "MID", 'middle': "MID", 'adc': "ADC", 'bot': "ADC", 'supp': "SUP", 'sup': "SUP", 'support': "SUP"}

def generate_embed(champ,lane):
    embedVar = discord.Embed(color=0x00ff00)
    embedVar.add_field(name="Champion", value=champ[0])
    embedVar.add_field(name="Lane", value=lane)
    embedVar.set_image(url=champ[2])
    return embedVar

def random_champ(lane,userid,cur):
    cur.execute(f"""SELECT CHAMP, CHAMPID, SPLASH 
                    FROM champions 
                    WHERE {lane} = True AND CHAMPID NOT IN
                        (SELECT CHAMPID
                         FROM wins
                         WHERE PLAYERID = '{userid}'
                        )""")
    champ = random.choice(cur.fetchall())
    return champ

async def win_champ(cur,con,champname,userid,channel):
    champid=MAXINT
    cur.execute("SELECT CHAMP, ALIAS, CHAMPID FROM champions")
    champlist = cur.fetchall()
    for champ in champlist:
        if champname.lower() == champ[0].lower():
            champid = champ[2]
            break
        if champname.lower() == champ[1].lower():
            champid = champ[2]
            break

    if champid == MAXINT:
        await channel.send("I dont know that champion, please type a valid champion", delete_after=10)
    else:
        try:
            cur.execute(f"""INSERT INTO wins (CHAMPID, PLAYERID)
                        VALUES({champid}, {userid})""")
            con.commit()
            await channel.send(f"Congratulations on the win with {champname}", delete_after=10)
        except psycopg2.errors.UniqueViolation:
            #await channel.send(f"You have already won with {champname}, try another champ", delete_after=5)
            con.rollback()
        except:
            print(traceback.format_exc())
            await channel.send(f"Something went wrong, sorry I couldn't register the win with {champname}", delete_after=5) 

async def printlaner(lane,userid,champmsg,interaction,components,cur):
    champ = random_champ(lanes[lane],userid,cur)
    embedVar = generate_embed(champ, lane)
    await champmsg.edit('',embed=embedVar, **components)
    await interaction.send(content=f"<a:kirby:759485375718359081>Re-Roll {lane}<a:kirby:759485375718359081>",ephemeral=False, delete_after=0.1)
    
class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        botpinged = False
        for role in message.role_mentions:
            if role.tags.is_bot_managed() and role.tags.bot_id == self.user.id:
                botpinged = True
                break
        if(self.user in message.mentions and not message.author.bot):
            botpinged = True

        if botpinged:
            con = psycopg2.connect(DATABASE_URL)
            cur = con.cursor()
            pid = random.randint(MININT,MAXINT)
            userid = message.author.id
            channel = message.channel
            if("help" in message.content):
                embedVar = discord.Embed(title="List of commands and usage")
                embedVar.add_field(name=f"@{self.user.name} help", value="Used to display this message.", inline=False)
                embedVar.add_field(name=f"@{self.user.name} stats lane", value="Used to display your stats in a certain lane (lane is optional, it defaults to all lanes).", inline=False)
                embedVar.add_field(name=f"@{self.user.name} win champ1, champ2...", value="Used to register wins on several champs manually.", inline=False)
                embedVar.add_field(name=f"@{self.user.name} connect summonerName region", value="Used to link your profile with a riot account.", inline=False)
                embedVar.add_field(name=f"@{self.user.name} disconnect", value="Used to unlink your profile from your riot.", inline=False)
                embedVar.add_field(name=f"@{self.user.name} lane", value="Used to fetch a random champ without a win in a certain lane (lane is optional, it defaults to select a lane).", inline=False)
                examplefile = discord.File(f'images/logo.png', filename="logo.png")
                embedVar.set_image(url="attachment://logo.png")
                await channel.send(file=examplefile, embed=embedVar)

            elif("update" in message.content) and (userid == 371076929022984196):
                await channel.send("Updating database...", delete_after=10)
                db.update_champions_DB(con,cur)
                await channel.send("Database updated!", delete_after=10)
                await message.delete(delay=10)

            elif("stats" in message.content):
                try:
                    msglanes = message.clean_content.split(f"stats", 1)[1].strip().split()
                    
                    laneflags = {"TOP":False,"JGL":False,"MID":False,"ADC":False,"SUP":False}
                    conditions = "("
                    for lane in msglanes:
                        if lane in lanes:
                            laneflags[lanes[lane]] = True
                            conditions += f" {lanes[lane]} = True OR"
                    conditions = "".join(conditions.rsplit("OR", 1))
                    conditions += ") AND"

                    if not any(laneflags.values()): 
                        conditions = ""
                        for lane in laneflags:
                            laneflags[lane] =  True

                    cur.execute(f"""SELECT 
                                    sum(case when {conditions} CHAMPID NOT IN
                                        (SELECT CHAMPID
                                        FROM wins
                                        WHERE PLAYERID = '{userid}') then 1 else 0 end),
                                    sum(case when {conditions} CHAMPID IN
                                        (SELECT CHAMPID
                                        FROM wins
                                        WHERE PLAYERID = '{userid}') then 1 else 0 end)
                                    FROM champions""")
                    nowinsandwins = (cur.fetchall()[0])

                    colors = ["#EB5757", "#5AC91A"]
                    sns.set_theme(font="serif",font_scale=1.5)
                    explode = [0.2, 0]

                    plt.pie(nowinsandwins, labels=[f"", f"Wins"],explode=explode,colors=colors,autopct='%.0f%%')
                    plt.savefig(f'temp{pid}.png')
                    
                    background = Image.open(f'temp{pid}.png')
                    posyicon = 0
                    font = ImageFont.FreeTypeFont("fonts/Objectivity-Medium.otf",20)
                    textlanes = ""
                    for lane in laneflags.items():
                        if lane[1] == True:
                            foreground = Image.open(f"images/{lane[0]}.png")
                            textlanes += f"{lane[0]} "
                        else:
                            foreground = Image.open(f"images/{lane[0]}.png").convert("LA")
                        background.paste(foreground, (background.width - foreground.width,posyicon), foreground)
                        posyicon += foreground.height

                    ImageDraw.Draw(background).text((5,background.height - 30),f"Champion count for {textlanes}{nowinsandwins[1]}/{nowinsandwins[0]+nowinsandwins[1]}",fill=(0,0,0),font=font)
                    background.save(f'temp{pid}.png')

                    plt.clf()
                    embed = discord.Embed(title=f"Stats for {message.author.name}",color=0x00ff00) #creates embed
                    piefile = discord.File(f'temp{pid}.png', filename="grahp.png")
                    embed.set_image(url="attachment://grahp.png")
                    await channel.send(file=piefile, embed=embed)
                    os.remove(f'temp{pid}.png')

                except psycopg2.errors.UndefinedTable:
                    await channel.send("You don't have a profile, create one by mentioning me and typing 'new'", delete_after=10)
                except:
                    print(traceback.format_exc())
                    await channel.send("Something went wrong, sorry I couldn't get your stats", delete_after=10) 
            
            elif("win" in message.content):
                champs = message.clean_content.split("win", 1)[1].strip()
                if champs=='':
                    await channel.send("You didn't type a champion, please type a valid champion", delete_after=10)
                else:
                    champlist = champs.split(",")
                    for champname in champlist:
                        await win_champ(cur,con,champname.strip(),userid,channel)

                await message.delete(delay=10)

            elif("disconnect" in message.content):
                try:
                    cur.execute(f"""DELETE FROM profiles 
                                    WHERE PLAYERID = '{userid}'""")
                    con.commit()   
                    await channel.send(f"Account disconnected succesfully!", delete_after=10) 
                except:
                    print(traceback.format_exc())
                    await channel.send("Something went wrong, sorry I couldn't disconnect with your account", delete_after=10)

                await message.delete(delay=10)

            elif("connect" in message.content):
                info = message.content.split("connect", 1)[1].strip().rsplit(" ", 1)
                regionalias = {"euw":"euw1","na":"na1","br":"br1","eun":"eun1","jp":"jp1","kr":"kr","lan":"la1","las":"la2","oc":"oc1","ru":"ru","tr":"tr1"}
                if len(info) != 2:
                    pass
                else:
                    gameName = info[0]
                    region = info[1].lower()
                    try:
                        summoner = lol_watcher.summoner.by_name(f"{regionalias[region]}",gameName)
                        puuid = summoner['puuid']
                        cur.execute(f"""INSERT INTO profiles (PLAYERID,PUUID,REGION,GAMENAME)
                            VALUES('{userid}','{puuid}','{regionalias[region]}','{gameName}')""")
                        con.commit()
                        await channel.send(f"Account connected succesfully!", delete_after=10)
                    except psycopg2.errors.UniqueViolation:
                        await channel.send(f"You have already have an account connected, if you wish to change it mention me with \"disconnect\"", delete_after=10)            
                    except:
                        print(traceback.format_exc())
                        await channel.send("Something went wrong, sorry I couldn't connect with your account", delete_after=10)       
                await message.delete(delay=10)         

            elif("load" in message.content):
                def get_games_postchall(matchlist,puuid,region,queue):
                    newlist = lol_watcher.match.matchlist_by_puuid(region,puuid,start_time=1652270400,queue=queue,count=100)
                    matchlist.extend(newlist)
                    start = 100
                    while len(newlist) > 0:
                        newlist = lol_watcher.match.matchlist_by_puuid(region,puuid,start_time=1652270400,queue=queue,count=100,start=start)
                        matchlist.extend(newlist)
                        start+=100
                try:
                    await channel.send(f"Loading all matches, this may take a while")
                    cur.execute(f"""SELECT PUUID, REGION 
                            FROM profiles
                            WHERE PLAYERID = '{userid}'""")
                    data = cur.fetchone()
                    puuid = data[0]
                    region = data[1]
                    matchlist = []
                    get_games_postchall(matchlist,puuid,region,400) #DRAFT PICK
                    get_games_postchall(matchlist,puuid,region,420) #SOLO DUO
                    get_games_postchall(matchlist,puuid,region,430) #BLIND PICK
                    get_games_postchall(matchlist,puuid,region,440) #FLEX
                    for matchid in matchlist:
                        match = lol_watcher.match.by_id(region, matchid)
                        for summoner in match["info"]["participants"]:
                            if (summoner["puuid"] == puuid) and (summoner["win"]):
                                await win_champ(cur,con,summoner['championName'],userid,channel)
                    await channel.send(f"Loaded all matches!")
                except:
                    print(traceback.format_exc())

            else:
                championbuttons = [
                discord.ui.Button(label="Win", style=discord.ButtonStyle.green, emoji = self.get_emoji(987155911766335520), custom_id=f"win{pid}"), 
                discord.ui.Button(label="Re-Roll", style=discord.ButtonStyle.blurple, emoji = "🔁", custom_id=f"roll{pid}"), 
                discord.ui.Button(label="Delete", style=discord.ButtonStyle.red, emoji = self.get_emoji(987331408093642822), custom_id=f"del{pid}"),
                discord.ui.Button(label="Lanes", style=discord.ButtonStyle.grey, emoji =self.get_emoji(987173438907088966) , custom_id=f"lanes{pid}")]

                championview = discord.ui.View()
                for button in championbuttons:
                    championview.add_item(button)

                lanebuttons = [
                discord.ui.Button(emoji = self.get_emoji(987155912890417154),custom_id=f"top{pid}"), 
                discord.ui.Button(emoji = self.get_emoji(987155914362589184),custom_id=f"jg{pid}"),
                discord.ui.Button(emoji = self.get_emoji(987155915541205002),custom_id=f"mid{pid}"), 
                discord.ui.Button(emoji = self.get_emoji(987172387277656104),custom_id=f"adc{pid}"),
                discord.ui.Button(emoji = self.get_emoji(987155917961318440),custom_id=f"supp{pid}")]

                laneview = discord.ui.View()
                for button in lanebuttons:
                    laneview.add_item(button)

                confirmbuttons = [
                discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, emoji = self.get_emoji(987155911766335520), custom_id=f"yeswin{pid}"),
                discord.ui.Button(label="No", style=discord.ButtonStyle.red, emoji = self.get_emoji(987155911766335520), custom_id=f"nowin{pid}")]

                confirmview = discord.ui.View()
                for button in confirmbuttons:
                    confirmview.add_item(button)

                lane = message.clean_content.replace(f"@{self.user.name} ", '').lower()

                buttons = {f"roll{pid}":0, f"win{pid}":1, f"del{pid}":2, f"lanes{pid}":3,f"top{pid}":4,f"jg{pid}":5,f"mid{pid}":6,f"adc{pid}":7,f"supp{pid}":8,f"yeswin{pid}":9,f"nowin{pid}":10}

                lanembed = discord.Embed(color=0x00ff00).set_image(url="https://cdn.discordapp.com/attachments/518907821081755672/987335003371364452/unknown.png")

                if lane in lanes:
                    champ = random_champ(lanes[lane],userid,cur)
                    embedVar = generate_embed(champ,lane)
                    await message.reply(embed=embedVar, view=championview)

                else:
                    await message.reply('What lane do you want to see?', embed=lanembed, view=laneview)

                while True:
                    try:
                        interaction = await client.wait_for("interaction",timeout=5400)
                        if interaction.type != discord.InteractionType.component:
                            continue
                        customid = interaction.data['custom_id']
                        if not customid in buttons: #If this interaction doesnt belong to the original message
                            continue
                        
                        await interaction.message.delete()

                        match buttons[customid]:
                            case 0: #Button for re-rolling
                                pass
                            case 1: #Button for selecting a win
                                if interaction.user != message.author:
                                    await channel.send("This is not your profile to change!")
                                else:
                                    await message.reply("Are you sure you want to register the win?", view=confirmview)
                                continue
                            case 2: #Button for deleting the messages
                                await message.delete()
                                break
                            case 3: #Button for selecting lanes
                                await message.reply('What lane do you want to see?', embed=lanembed, view=laneview)
                                continue
                            case 4: #Button for selecting top
                                lane = "top"
                            case 5: #Button for selecting jungle
                                lane = "jungle"
                            case 6: #Button for selecting mid
                                lane = "mid"
                            case 7: #Button for selecting ADCarry
                                lane = "adc"
                            case 8: #Button for selecting support
                                lane = "supp"
                            case 9: #Confirm win
                                await win_champ(cur,con,champ[0],userid,channel)
                            case 10: #Cancel win
                                continue
                        champ = random_champ(lanes[lane],userid,cur)
                        embedVar = generate_embed(champ, lane)
                        await message.reply(content=None,embed=embedVar, view=championview)
                    except asyncio.TimeoutError:
                        await channel.send("Timeout, deleting message...", delete_after=10)
                        await interaction.message.delete()
                        await message.delete()
                        break
                    except:
                        print(traceback.format_exc())
                        await channel.send("Exception", delete_after=10)
                        await interaction.message.delete()
                        await message.delete()
                        break
            con.close()
        
load_dotenv()
TOKEN = os.getenv('TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
RIOT_API_KEY = os.getenv('RIOT_API_KEY')

lol_watcher = LolWatcher(RIOT_API_KEY)
riot_watcher = RiotWatcher(RIOT_API_KEY)
intents = discord.Intents(messages=True, message_content=True, guilds=True)
client = MyClient(intents=intents)
# DiscordComponents(client)
client.run(str(TOKEN))