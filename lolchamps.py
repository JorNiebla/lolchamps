from xmlrpc.client import MAXINT, MININT
import discord
from discord_components import DiscordComponents, Button
import random
import psycopg2
import riotwatcher
import db
import os
import traceback
import asyncio
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
from riotwatcher import RiotWatcher, LolWatcher, ApiError
from PIL import Image

lanes = {'top': "TOP", 'jg': "JGL", 'jung': "JGL", 'jng': "JGL",'jungle': "JGL", 'jungler': "JGL", 'mid': "MID", 'middle' : "MID", 'adc': "ADC", 'bot': "ADC", 'supp': "SUP", 'sup': "SUP"}

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
    cur.execute("SELECT CHAMP, CHAMPID FROM champions")
    champlist = cur.fetchall()
    for champ in champlist:
        if champname.lower() == champ[0].lower():
            champid = champ[1]
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
            await channel.send(f"You have already won with {champname}, try another champ", delete_after=10) 
        except:
            print(traceback.format_exc())
            await channel.send(f"Something went wrong, sorry I couldn't register the win with {champname}", delete_after=10) 

async def printlaner(lane,userid,champmsg,interaction,components,cur):
    champ = random_champ(lanes[lane],userid,cur)
    embedVar = generate_embed(champ, lane)
    await champmsg.edit('',embed=embedVar, **components)
    await interaction.send(content=f"<a:kirby:759485375718359081>Re-Roll {lane}<a:kirby:759485375718359081>",ephemeral=False, delete_after=0.1)
    
class MyClient(discord.Client):

    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        con = psycopg2.connect(DATABASE_URL)
        cur = con.cursor()
        pid = random.randint(MININT,MAXINT)
        userid = message.author.id
        channel = message.channel

        botpinged = False
        for role in message.role_mentions:
            if role.tags.is_bot_managed() and role.tags.bot_id == self.user.id:
                botpinged = True
                break
        if(self.user in message.mentions):
            botpinged = True

        if not botpinged:
            pass
        
        elif message.author.bot:
            pass

        elif("help" in message.content):
            embedVar = discord.Embed()
            embedVar.add_field(name=f"@{self.user.name} help", value="to display this message", inline=False)
            embedVar.add_field(name=f"@{self.user.name} stats lane", value="Used to display your stats in a certain lane, (lane is optional, it defaults to all lanes)", inline=False)
            embedVar.add_field(name=f"@{self.user.name} win champ1, champ2...", value="Used to register wins on various champs manually", inline=False)
            embedVar.add_field(name=f"@{self.user.name} connect RIOTNAME TAGLINE", value="Used to link your profile with a riot account", inline=False)
            embedVar.add_field(name=f"@{self.user.name} disconnect", value="Used to unlink your profile from your riot", inline=False)
            examplefile = discord.File(f'images/EXAMPLEINFO.png', filename="example.png")
            embedVar.set_image(url="attachment://example.png")
            await channel.send(file=examplefile, embed=embedVar)

        elif("update" in message.content) and (userid == 371076929022984196):
            await channel.send("Updating database...", delete_after=10)
            db.update_champions_DB(con,cur)
            await channel.send("Database updated!", delete_after=10)
            await message.delete(delay=10)

        elif("stats" in message.content):
            try:
                msglanes = message.clean_content.split(f"stats", 1)[1].strip().split()
                lanecount = 0
                conditions = "("
                for lane in msglanes:
                    if lane in lanes:
                        lanecount +=1
                        if lane == msglanes[-1]:
                            conditions += f" {lanes[lane]} = True"
                            break
                        conditions += f" {lanes[lane]} = True OR"
                conditions += ") AND"
                if lanecount == 0: 
                    conditions = ""
                    msglanes.extend(["top","jg","mid","adc","supp"])

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

                plt.pie(nowinsandwins, labels=[f"NoWin", f"Win"],explode=explode,colors=colors,autopct='%.0f%%',rotatelabels='true')
                plt.savefig(f'temp{pid}.png')
                
                background = Image.open(f'temp{pid}.png')
                posy = 0
                for lane in msglanes:
                    if lane in lanes:
                        foreground = Image.open(f"images/{lanes[lane]}.png")
                        background.paste(foreground, (background.width - foreground.width,posy), foreground)
                        posy += foreground.height

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
            champs = message.clean_content.split("win", 1)[1].replace("'", "''").strip()
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
                                WHERE PUUID = '{userid}')""")
                con.commit()   
                await channel.send(f"Account disconnected succesfully!", delete_after=10) 
            except:
                print(traceback.format_exc())
                await channel.send("Something went wrong, sorry I couldn't disconnect with your account", delete_after=10)

            await message.delete(delay=10)

        elif("connect" in message.content):
            info = message.content.split("connect", 1)[1].strip().rsplit(" ", 1)
            if len(info) != 2:
                pass
            else:
                gameName = info[0]
                tagLine = info[1]
                try:
                    account = riot_watcher.account.by_riot_id('europe',gameName,tagLine)
                    puuid = account['puuid']
                    cur.execute(f"""INSERT INTO profiles (PLAYERID,PUUID)
                        VALUES('{userid}', '{puuid}')""")
                    con.commit()
                    await channel.send(f"Account connected succesfully!", delete_after=10) 
                except psycopg2.errors.UniqueViolation:
                    await channel.send(f"You have already have an account connected, if you wish to change it mention me with \"disconnect\"", delete_after=10)            
                except:
                    print(traceback.format_exc())
                    await channel.send("Something went wrong, sorry I couldn't connect with your account", delete_after=10)       
            await message.delete(delay=10)         

        else:
            components = {"components" : [[Button(label="Win", style="3", emoji = self.get_emoji(id=987155911766335520), custom_id=f"win{pid}"), 
            Button(label="Re-Roll", style="1", emoji = "🔁", custom_id=f"roll{pid}"), Button(label="Delete", style="4", emoji = self.get_emoji(id=987331408093642822), custom_id=f"del{pid}"),
            Button(label="Lanes", style="2", emoji =self.get_emoji(id=987173438907088966) , custom_id=f"lanes{pid}")]]}

            lanebuttons = [Button(emoji = self.get_emoji(id=987155912890417154),custom_id=f"top{pid}"),Button(emoji = self.get_emoji(id=987155914362589184),custom_id=f"jg{pid}"),
            Button(emoji = self.get_emoji(id=987155915541205002),custom_id=f"mid{pid}"),Button(emoji = self.get_emoji(id=987172387277656104),custom_id=f"adc{pid}"),
            Button(emoji = self.get_emoji(id=987155917961318440),custom_id=f"supp{pid}")]

            lane = message.clean_content.replace(f"@{self.user.name} ", '').lower()

            buttons = {f"roll{pid}":0, f"win{pid}":1, f"del{pid}":2, f"lanes{pid}":3,f"top{pid}":4,f"jg{pid}":5,f"mid{pid}":6,f"adc{pid}":7,f"supp{pid}":8,f"yeswin{pid}":9,f"nowin{pid}":10}

            lanembed = discord.Embed(color=0x00ff00).set_image(url="https://cdn.discordapp.com/attachments/518907821081755672/987335003371364452/unknown.png")

            if lane in lanes:
                champ = random_champ(lanes[lane],userid,cur)
                embedVar = generate_embed(champ,lane)
                champmsg = await message.reply(embed=embedVar, **components)

            else:
                champmsg = await message.reply('What lane do you want to see?', embed=lanembed, components=[lanebuttons])

            while True:
                try:
                    interaction = await client.wait_for("button_click",timeout=5400)
                    customid=interaction.component.custom_id

                    if not customid in buttons: #If this interaction doesnt belong to the original message
                        continue

                    match buttons[customid]:
                        case 0: #Button for re-rolling
                            pass
                        case 1: #Button for selecting a win
                            if interaction.user != message.author:
                                await interaction.send("This is not your profile to change!")
                            else:
                                await interaction.send("Are you sure you want to register the win?",
                                components=[[Button(label="Yes", style="3", emoji = self.get_emoji(id=987155911766335520), custom_id=f"yeswin{pid}"),
                                Button(label="No", style="4", emoji = self.get_emoji(id=987155911766335520), custom_id=f"nowin{pid}")]])
                            continue
                        case 2: #Button for deleting the messages
                            await champmsg.delete()
                            await message.delete()
                            break
                        case 3: #Button for selecting lanes
                            await champmsg.edit('What lane do you want to see?', embed=lanembed, components=[lanebuttons])
                            await interaction.send(content="<a:kirby:759485375718359081>Lineas<a:kirby:759485375718359081>",ephemeral=False, delete_after=0.1)
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
                    await champmsg.edit('',embed=embedVar, **components)
                    await interaction.send(content=f"<a:kirby:759485375718359081>Re-Roll {lane}<a:kirby:759485375718359081>",ephemeral=False, delete_after=0.1)
                except asyncio.TimeoutError:
                    await channel.send("Timeout, deleting message...", delete_after=10)
                    await champmsg.delete()
                    await message.delete()
                    break
                except:
                    print(traceback.format_exc())
                    await channel.send("Exception", delete_after=10)
                    await champmsg.delete()
                    await message.delete()
                    break
        con.close()


TOKEN = os.getenv('TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
RIOT_API_KEY = os.getenv('RIOT_API_KEY')

lol_watcher = LolWatcher(RIOT_API_KEY)
riot_watcher = RiotWatcher(RIOT_API_KEY)
intents = discord.Intents(messages=True, guilds=True)
client = MyClient(intents=intents)
DiscordComponents(client)
client.run(str(TOKEN))