from xmlrpc.client import MAXINT, MININT
import discord
from discord_components import DiscordComponents, Button
import random
import psycopg2
import db
import os
import traceback
import asyncio
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
from PIL import Image

lanes = {'top': "TOP", 'jg': "JGL", 'jung': "JGL", 'jng': "JGL",'jungle': "JGL", 'jungler': "JGL", 'mid': "MID", 'middle' : "MID", 'adc': "ADC", 'bot': "ADC", 'supp': "SUP", 'sup': "SUP"}

def generate_embed(champ,lane):
    embedVar = discord.Embed(color=0x00ff00)
    embedVar.add_field(name="Champion", value=champ[0])
    embedVar.add_field(name="Lane", value=lane)
    embedVar.set_image(url=champ[2])
    return embedVar

def random_champ(lane,userid,cur):
    cur.execute(f"SELECT CHAMP, ID, SPLASH FROM table_{userid} WHERE {lane} = True AND WIN = False")
    champ = random.choice(cur.fetchall())
    print(champ)
    return champ

def remove_champ(wks, champ):
   pass

async def printlaner(lane,userid,champmsg,interaction,components,cur):
    champ = random_champ(lanes[lane],userid,cur)
    embedVar = generate_embed(champ, lane)
    await champmsg.edit('',embed=embedVar, **components)
    await interaction.send(content=f"<a:kirby:759485375718359081>Re-Roll {lane}<a:kirby:759485375718359081>",ephemeral=False, delete_after=1)
    
class MyClient(discord.Client):

    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        con = psycopg2.connect(DATABASE_URL)
        cur = con.cursor()
        pid = random.randint(MININT,MAXINT)

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

        elif(message.content == f"<@{self.user.id}> rebuild") and (message.author == 371076929022984196):
            print("rebuilding")
            cur.execute("DROP TABLE clean_table")
            db.create_clean_DB(con,cur)

        elif(f"<@{self.user.id}> stats" in message.content):
            try:
                cur.execute(f"""SELECT 
                    sum(case when WIN = False then 1 else 0 end) AS total,
                    sum(case when WIN = True then 1 else 0 end) AS totalwinned,
                    sum(case when TOP = True and WIN = False then 1 else 0 end) AS totaltop,
                    sum(case when TOP = True and WIN = True then 1 else 0 end) AS totalwinnedtop,
                    sum(case when JGL = True and WIN = False then 1 else 0 end) AS totaljgl,
                    sum(case when JGL = True and WIN = True then 1 else 0 end) AS totalwinnedjgl,
                    sum(case when MID = True and WIN = False then 1 else 0 end) AS totalmid,
                    sum(case when MID = True and WIN = True then 1 else 0 end) AS totalwinnedmid,
                    sum(case when ADC = True and WIN = False then 1 else 0 end) AS totaladc,
                    sum(case when ADC = True and WIN = True then 1 else 0 end) AS totalwinnedadc,
                    sum(case when SUP = True and WIN = False then 1 else 0 end) AS totalsupp,
                    sum(case when SUP = True and WIN = True then 1 else 0 end) AS totalwinnedsupp
                FROM table_{message.author.id}""")

                data = list(cur.fetchall()[0])
                totallist = data[:2]
                toplist = data[2:4]
                jgllist = data[4:6]
                midlist = data[6:8]
                adclist = data[8:10]
                supplist = data[10:12]
                lists = {"Total": totallist,"TOP" : toplist , "JGL": jgllist, "MID": midlist, "ADC": adclist, "SUP": supplist}

                colors = ["#EB5757", "#5AC91A"]
                sns.set_theme(font="serif",font_scale=1.5)
                explode = [0.2, 0]

                statslist = "Total"
                lane = message.clean_content.replace(f"@{self.user.name} stats ", '')
                if lane in lanes:
                    statslist = lanes[lane]

                plt.pie(lists[statslist], labels=[f"NoWin {statslist}", f"Win {statslist}"],explode=explode,colors=colors,autopct='%.0f%%',rotatelabels='true')

                plt.savefig(f'temp{pid}.png')

                
                foreground = Image.open("images/ALL.png")
                if lane in lanes:
                    foreground = Image.open(f"images/{lanes[lane]}.png")

                background = Image.open(f'temp{pid}.png')
                background.paste(foreground, (background.width - foreground.width,0), foreground)
                background.save(f'temp{pid}.png')

                plt.clf()
                embed = discord.Embed(title=f"Stats for {message.author.name} in {statslist}",color=0x00ff00) #creates embed
                file = discord.File(f'temp{pid}.png', filename="grahp.png")
                embed.set_image(url="attachment://graph.png")
                await message.channel.send(file=file, embed=embed)
                os.remove(f'temp{pid}.png')

            except psycopg2.errors.UndefinedTable:
                await message.channel.send("You don't have a profile, create one by mentioning me and typing 'new'", delete_after=10)
            except:
                print(traceback.format_exc())
                await message.channel.send("Something went wrong, sorry I couldn't get your stats", delete_after=10) 
        
        elif(f"<@{self.user.id}> win" in message.content):
            champname = message.clean_content.replace(f"@{self.user.name} win ", '').replace("'", "''")
            if champname=='': champname="empty"
            cur.execute(f"SELECT EXISTS(SELECT * FROM table_clean WHERE CHAMP = '{champname}')")
            if not (cur.fetchone()[0]):
                await message.channel.send("I dont know that champion, please type a valid champion (full name and capital letters)", delete_after=10)
            else:
                try:
                    cur.execute(f"""UPDATE table_{message.author.id}
                                SET WIN = True 
                                WHERE CHAMP='{champname}'""")
                    con.commit()
                    print("Winning")
                    await message.channel.send("Congratulations on the win with " + champname, delete_after=10)
                except psycopg2.errors.UndefinedTable:
                    await message.channel.send("You don't have a profile, create one by mentioning me and typing 'new'", delete_after=10)
                except:
                    print(traceback.format_exc())
                    await message.channel.send("Something went wrong, sorry I couldn't register the win", delete_after=10) 

        elif(f"<@{self.user.id}> new" in message.content):
            cur.execute("SELECT EXISTS(SELECT * FROM information_schema.tables WHERE table_name=%s)", (f'table_{message.author.id}',))
            if (cur.fetchone()[0]):
                await message.channel.send("You already have profile", delete_after=10)
            else:
                try:
                    cur.execute(f"""CREATE TABLE table_{message.author.id} AS (
                                SELECT
                                 * 
                                FROM
                                  table_clean
                                )""")
                    con.commit()
                    print("Created")
                    await message.channel.send("Profile created", delete_after=10)
                except:
                    print(traceback.format_exc())
                    await message.channel.send("Something went wrong, sorry I couldn't create the profile", delete_after=10)
        else:

            components = {"components" : [[Button(label="Win", style="3", emoji = self.get_emoji(id=987155911766335520), custom_id=f"win{pid}"), 
            Button(label="Re-Roll", style="1", emoji = "🔁", custom_id=f"roll{pid}"), Button(label="Delete", style="4", emoji = self.get_emoji(id=987331408093642822), custom_id=f"del{pid}"),
            Button(label="Lanes", style="2", emoji =self.get_emoji(id=987173438907088966) , custom_id=f"lanes{pid}")]]}

            lanebuttons = [Button(emoji = self.get_emoji(id=987155912890417154),custom_id=f"top{pid}"),Button(emoji = self.get_emoji(id=987155914362589184),custom_id=f"jg{pid}"),
            Button(emoji = self.get_emoji(id=987155915541205002),custom_id=f"mid{pid}"),Button(emoji = self.get_emoji(id=987172387277656104),custom_id=f"adc{pid}"),
            Button(emoji = self.get_emoji(id=987155917961318440),custom_id=f"supp{pid}")]

            lane = message.clean_content.replace(f"@{self.user.name} ", '').lower()

            buttons = {f"roll{pid}":0, f"win{pid}":1, f"del{pid}":2, f"lanes{pid}":3,f"top{pid}":4,f"jg{pid}":5,f"mid{pid}":6,f"adc{pid}":7,f"supp{pid}":8,f"yescreate{pid}":9,f"nocreate{pid}":10,f"yeswin{pid}":11,f"nowin{pid}":12}

            lanembed = discord.Embed(color=0x00ff00).set_image(url="https://cdn.discordapp.com/attachments/518907821081755672/987335003371364452/unknown.png")

            cur.execute("SELECT EXISTS(SELECT * FROM information_schema.tables WHERE table_name=%s)", (f'table_{message.author.id}',))
            if not (cur.fetchone()[0]): #Check if the user has a table created
                knownuser = False
                userid = "clean"
            else:
                knownuser = True
                userid = str(message.author.id)

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
                            if knownuser:
                                await interaction.send("Are you sure you want to register the win?",
                                components=[[Button(label="Yes", style="3", emoji = self.get_emoji(id=987155911766335520), custom_id=f"yeswin{pid}"),
                                Button(label="No", style="4", emoji = self.get_emoji(id=987155911766335520), custom_id=f"nowin{pid}")]])
                            else:
                                await interaction.send("You don't have a profile, do you want to create one?", 
                                components=[[Button(label="Yes", style="3", emoji = self.get_emoji(id=987155911766335520), custom_id=f"yescreate{pid}"),
                                Button(label="No", style="4", emoji = self.get_emoji(id=987155911766335520), custom_id=f"nocreate{pid}")]])
                            continue
                        case 2: #Button for deleting the messages
                            await champmsg.delete()
                            await message.delete()
                            break
                        case 3: #Button for selecting lanes
                            await champmsg.edit('What lane do you want to see?', embed=lanembed, components=[lanebuttons])
                            await interaction.send(content="<a:kirby:759485375718359081>Lineas<a:kirby:759485375718359081>",ephemeral=False, delete_after=1)
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
                        case 9: #Button for creating a table for the user
                            cur.execute(f"""CREATE TABLE table_{interaction.user.id} AS (
                                SELECT
                                 * 
                                 FROM
                                  table_clean
                                )""")
                            con.commit()
                            await interaction.send("Created (Remember to remove this message)")
                            knownuser = True
                            userid = str(message.author.id)
                            continue
                        case 10: #Button for not creating a table for the user
                            await interaction.send("Cancelled (Remember to remove this message)")
                            continue
                        case 11: #Confirm win
                            cur.execute(f"""UPDATE table_{userid}
                                SET WIN = True 
                                WHERE ID='{champ[1]}'""")
                            con.commit()
                            await interaction.send(f"Congratulations on the win with {champ[0]}! I'll get you another champ")
                        case 12: #Cancel win
                            continue
                    champ = random_champ(lanes[lane],userid,cur)
                    embedVar = generate_embed(champ, lane)
                    await champmsg.edit('',embed=embedVar, **components)
                    await interaction.send(content=f"<a:kirby:759485375718359081>Re-Roll {lane}<a:kirby:759485375718359081>",ephemeral=False, delete_after=0.1)
                except asyncio.TimeoutError:
                    await message.channel.send("Timeout, deleting message...", delete_after=10)
                    await champmsg.delete()
                    await message.delete()
                    break
                except:
                    print(traceback.format_exc())
                    await message.channel.send("Exception", delete_after=10)
                    await champmsg.delete()
                    await message.delete()
                    break
        con.close()


TOKEN = os.getenv('TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

intents = discord.Intents(messages=True, guilds=True)
client = MyClient(intents=intents)
DiscordComponents(client)
client.run(str(TOKEN))