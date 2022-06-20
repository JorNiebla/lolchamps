from xmlrpc.client import MAXINT, MININT
import discord
from discord_components import DiscordComponents, Button
import random
import string
import cassiopeia as cass
import psycopg2
import db
import os

TOKEN = os.getenv('TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
con = psycopg2.connect(DATABASE_URL)
cur = con.cursor()

def generate_embed(champ,lane):
    embedVar = discord.Embed(color=0x00ff00)
    embedVar.add_field(name="Champion", value=champ)
    embedVar.add_field(name="Linea", value=lane)
    #embedVar.set_image(url=urls[champ])
    return embedVar

def random_champ(lane):
    pass

def remove_champ(wks, champ):
   pass

async def printlaner(lane,champmsg,interaction,components):
    champ = random_champ(lane)
    embedVar = generate_embed(champ, lane)
    await champmsg.edit('',embed=embedVar, **components)
    await interaction.send(content=f"<a:kirby:759485375718359081>Re-Roll {lane}<a:kirby:759485375718359081>",ephemeral=False, delete_after=1)
    
class MyClient(discord.Client):

    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        if(self.user in message.mentions) and (message.content == f"@{self.user.name} rebuild") and (message.author == 371076929022984196):
            print("rebuilding")
        elif (self.user in message.mentions) or (f"<@&{self.user.id}>" in message.content):
            pid = random.randint(MININT,MAXINT)
            components = {"components" : [[Button(label="Win", style="3", emoji = self.get_emoji(id=987155911766335520), custom_id=f"win{pid}"), 
            Button(label="Re-Roll", style="1", emoji = "🔁", custom_id=f"roll{pid}"), Button(label="Delete", style="4", emoji = self.get_emoji(id=987331408093642822), custom_id=f"del{pid}"),
            Button(label="Lanes", style="2", emoji =self.get_emoji(id=987173438907088966) , custom_id=f"lanes{pid}")]]}
            lanebuttons = [Button(emoji = self.get_emoji(id=987155912890417154),custom_id=f"top{pid}"),Button(emoji = self.get_emoji(id=987155914362589184),custom_id=f"jg{pid}"),
            Button(emoji = self.get_emoji(id=987155915541205002),custom_id=f"mid{pid}"),Button(emoji = self.get_emoji(id=987172387277656104),custom_id=f"adc{pid}"),
            Button(emoji = self.get_emoji(id=987155917961318440),custom_id=f"supp{pid}")]
            lane = message.clean_content.replace(f"@{self.user.name} ", '').lower()
            buttons = {f"roll{pid}":0, f"win{pid}":1, f"del{pid}":2, f"lanes{pid}":3,f"top{pid}":4,f"jg{pid}":5,f"mid{pid}":6,f"adc{pid}":7,f"supp{pid}":8,f"yescreate{pid}":9,f"nocreate{pid}":10}
            lanembed = discord.Embed(color=0x00ff00).set_image(url="https://cdn.discordapp.com/attachments/518907821081755672/987335003371364452/unknown.png")

            cur.execute("SELECT EXISTS(SELECT * FROM information_schema.tables WHERE table_name=%s)", (f'{message.author.id}_table',))
            if not (cur.fetchone()[0]): #Check if the user has a table created
                knownuser = False
                tablename = "clean"
            else:
                knownuser = True
                tablename = str(message.author.id)

            lanes = []
            cur.execute(f"Select ID from clean_table where TOP = True")
            lanes.append([item for t in cur.fetchall() for item in t])
            cur.execute(f"Select ID from {tablename}_table where JGL = True")
            lanes.append([item for t in cur.fetchall() for item in t])
            cur.execute(f"Select ID from {tablename}_table where MID = True")
            lanes.append([item for t in cur.fetchall() for item in t])
            cur.execute(f"Select ID from {tablename}_table where ADC = True")
            lanes.append([item for t in cur.fetchall() for item in t])
            cur.execute(f"Select ID from {tablename}_table where SUP = True")
            lanes.append([item for t in cur.fetchall() for item in t])

            if lane in lanes:
                champ = random_champ(lane)
                embedVar = generate_embed(champ,lane)
                champmsg = await message.reply(embed=embedVar, **components)

            else:
                champmsg = await message.reply('Que linea quieres bro', embed=lanembed, components=[lanebuttons])

            while True:
                try:
                    interaction = await client.wait_for("button_click")
                    customid=interaction.component.custom_id

                    match buttons[customid]:
                        case 0: #Button for re-rolling
                            pass
                        case 1: #Button for selecting a win
                        #     if interaction.user != message.author:
                        #         await interaction.send("No es tu campeón amigo")
                            if knownuser:
                                # champ = interaction.message.content.rsplit(' ', 1)[0]
                                # await champmsg.delete()
                                # await message.delete()
                                await interaction.send("Quitado de la lista")
                            else:
                                print("Confirmacion empezada")
                                confirmmsg = await interaction.send("No tienes ficha creada. ¿Quieres crear una?", 
                                components[[Button(label="Yes", style="3", emoji = self.get_emoji(id=987155911766335520), custom_id=f"yescreate{pid}"),
                                Button(label="No", style="4", emoji = self.get_emoji(id=987155911766335520), custom_id=f"nocreate{pid}")]])
                                print("Confirmacion creada")
                            continue
                        case 2: #Button for deleting the messages
                            await champmsg.delete()
                            await message.delete()
                            break
                        case 3: #Button for selecting lanes
                            await champmsg.edit('Que linea quieres bro', embed=lanembed, components=[lanebuttons])
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
                            # cur.execute(f"""CREATE TABLE {interaction.user}_table AS SELECT *
                            #             FROM clean_table""")
                            # con.commit()
                            await confirmmsg.delete()
                        case 10: ##Button for not creating a table for the user
                            await confirmmsg.delete()

                    #await printlaner(lane,champmsg,interaction,components)
                except:
                    await message.channel.send("Exception", delete_after=10)
                    await champmsg.delete()
                    await message.delete()
                    break

intents = discord.Intents(messages=True, guilds=True)
client = MyClient(intents=intents)
DiscordComponents(client)
client.run(str(TOKEN))