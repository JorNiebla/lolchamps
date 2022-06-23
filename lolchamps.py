from xmlrpc.client import MAXINT, MININT
import discord
from discord_components import DiscordComponents, Button
import random
import string
import cassiopeia as cass
import psycopg2
import db
import os
import traceback
import asyncio

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
    print("voy a pillar uno random")
    champ = random_champ(lanes[lane],userid,cur)
    print("pillado")
    print("voy a hacer un embed")
    embedVar = generate_embed(champ, lane)
    print("hecho")
    await champmsg.edit('',embed=embedVar, **components)
    await interaction.send(content=f"<a:kirby:759485375718359081>Re-Roll {lane}<a:kirby:759485375718359081>",ephemeral=False, delete_after=1)
    
class MyClient(discord.Client):

    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        con = psycopg2.connect(DATABASE_URL)
        cur = con.cursor()
        if(self.user in message.mentions) and (message.content == f"@{self.user.name} rebuild") and (message.author == 371076929022984196):
            print("rebuilding")
            db.create_clean_DB(con,cur)
        elif (self.user in message.mentions) or (f"<@&{self.user.id}>" in message.content):
            pid = random.randint(MININT,MAXINT)

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
                            print("Le dieron que si")
                            cur.execute(f"""CREATE TABLE table_{interaction.user.id} AS (
                                SELECT
                                 * 
                                 FROM
                                  table_clean
                                )""")
                            print("ejecuto")
                            con.commit()
                            print("comiteo")
                            await interaction.send("Created (Remember to remove this message)")
                            continue
                        case 10: #Button for not creating a table for the user
                            print("Le dieron que no")
                            await interaction.send("Cancelled (Remember to remove this message)")
                            continue
                        case 11: #Confirm win
                            cur.execute(f"""UPDATE table_{interaction.user.id}
                                SET WIN = True 
                                WHERE CHAMP='{champmsg.embeds[0].fields[0].value}'""")
                            con.commit()
                            await champmsg.delete()
                            await message.delete()
                            interaction.send("Congratulations on the win!")
                            continue
                        case 12: #Cancel win
                            continue
                    await printlaner(lane,userid,champmsg,interaction,components,cur)
                    print("todo perfe")
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


TOKEN = os.getenv('TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

intents = discord.Intents(messages=True, guilds=True)
client = MyClient(intents=intents)
DiscordComponents(client)
client.run(str(TOKEN))