from xmlrpc.client import MAXINT, MININT
import discord
from discord_components import DiscordComponents, Button
import random
import string
import subprocess
import cassiopeia as cass
import requests, json

from openpyxl import load_workbook

import os
from dotenv import load_dotenv

load_dotenv()

#subprocess.call("./scrape_champions.sh")

TOKEN = os.getenv('TOKEN')
# RIOT = os.getenv('RIOT')

# cass.set_riot_api_key(str(RIOT))

# Gatoxulo = cass.get_summoner(name="Gatoxulo", region="EUW")

clp = requests.get('https://ddragon.leagueoflegends.com/api/versions.json').json()[0] #CurrentLeaguePatch
champs = requests.get(f'https://ddragon.leagueoflegends.com/cdn/{clp}/data/en_US/champion.json').json()["data"] #CurrentLeaguePatch
#print(champs)

urls = {}

for champ in champs.values():
    name=champ["name"]
    key=champ["id"]
    splash=f'https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{key}_0.jpg'
    urls[name]=splash


# with open("urls.txt") as file_in:
#     while True:
#         name=file_in.readline()[:-1]
#         url=file_in.readline()[:-1]
#         urls[name]=url
#         if not url: break

lanes = {'all': 8, 'top': 9, 'jg': 10, 'jung': 10, 'jng': 10,'jungle': 10, 'jungler': 10, 'mid': 11, 'adc': 12, 'bot': 12, 'supp': 13, 'sup': 13}

def generate_embed(champ,lane):
    embedVar = discord.Embed(color=0x00ff00)
    embedVar.add_field(name="Champion", value=champ)
    embedVar.add_field(name="Linea", value=lane)
    embedVar.set_image(url=urls[champ])
    return embedVar

def cords_to_cellname(row,col):
    alph = string.ascii_uppercase
    return(alph[col-1]+str(row))

def random_champ(wks, lane):
    laneid = lanes[lane]
    limit = 0
    for cell in wks[string.ascii_uppercase[laneid-1]]:
        if cell.value != None:
            limit+=1

    if limit == 2: return "Azir"
    return (wks.cell(random.randint(3, limit), laneid).value)

def remove_champ(wks, champ):
    champs = []
    for ch in wks[string.ascii_uppercase[7]]:
        champs.append(ch.value)

    if not champ in champs:
        return

    cols = ['H', 'I', 'J', 'K', 'L', 'M']
    cell_list = []

    for col in cols:
        for cell in wks[col]:
            if cell.value == champ:
                cell_list.append(cell)

    while len(cell_list) > 0:
        currentrow = cell_list[-1].row
        currentcol = cell_list[-1].column
        if currentcol < 8:
            cell_list.pop()
            continue
        limit = 0
        for cell in wks[string.ascii_uppercase[currentcol-1]]:
            if cell.value != None:
                limit+=1
        

        listofchamps = []
        for i in range(currentrow+1,limit+1):
            listofchamps.append(wks.cell(row=i,column=currentcol).value)

        j = currentrow
        for i in listofchamps:
            wks.cell(row=j,column=currentcol,value=i)
            j+=1
        wks.cell(row=limit,column=currentcol,value='')
        cell_list.pop() 

class MyClient(discord.Client):

    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        # print(message.guild.emojis)
        #Atiende a mensajes en los que se menciona al bot
        # print(f"<@&{self.user.id}>")
        # print(message.content)
        if (self.user in message.mentions) or (f"<@&{self.user.id}>" in message.content):
            pid = random.randint(MININT,MAXINT)
            components = {"components" : [[Button(label="Win", style="3", emoji = self.get_emoji(id=987155911766335520), custom_id=f"win{pid}"), 
            Button(label="Re-Roll", style="1", emoji = "🔁", custom_id=f"roll{pid}"), Button(label="Delete", style="4", emoji = "🗑️", custom_id=f"del{pid}"),
            Button(label="Lanes", style="2", emoji =self.get_emoji(id=987173438907088966) , custom_id=f"lanes{pid}")]]}
            lanebuttons = [Button(emoji = self.get_emoji(id=987155912890417154),custom_id=f"top{pid}"),Button(emoji = self.get_emoji(id=987155914362589184),custom_id=f"jg{pid}"),
            Button(emoji = self.get_emoji(id=987155915541205002),custom_id=f"mid{pid}"),Button(emoji = self.get_emoji(id=987172387277656104),custom_id=f"adc{pid}"),
            Button(emoji = self.get_emoji(id=987155917961318440),custom_id=f"supp{pid}")]
            lane = message.clean_content.replace(f"@{self.user.name} ", '').lower()
            knownuser = True
            wb = load_workbook('lolchamps.xlsx')
            wks = wb["Clean"]
            if not str(message.author.id) in wb.sheetnames:
                knownuser = False
            else: 
                wks = wb[str(message.author.id)]
                #print("Abriendo la hoja de " + users[message.author.id])
            if lane in lanes:
                champ = random_champ(wks,lane)
                embedVar = generate_embed(champ,lane)
                champmsg = await message.reply(embed=embedVar, **components)

            else:
                champmsg = await message.reply('Que linea quieres bro', components=[lanebuttons])

            while True:
                try:
                    interaction = await client.wait_for("button_click")
                    customid=interaction.component.custom_id

                    if customid == f"roll{pid}":
                        # if interaction.user != message.author:
                        #     await interaction.send("No es tu campeón amigo")
                        champ = random_champ(wks,lane)
                        embedVar = generate_embed(champ, lane)
                        await champmsg.edit(embed=embedVar, **components)
                        msg = await interaction.send(content="Re-Roll<a:kirby:759485375718359081>",ephemeral=False)
                        await msg.delete()

                    elif customid == f"win{pid}":
                        if interaction.user != message.author:
                            await interaction.send("No es tu campeón amigo")
                        elif knownuser:
                            wks = wb[str(message.author.id)]
                            champ = interaction.message.content.rsplit(' ', 1)[0]
                            remove_champ(wks,champ)
                            wb.save('lolchamps.xlsx')
                            await interaction.send("Quitado de la lista")
                        else:
                            await interaction.send("No tienes ficha creada")
                    
                    elif customid == f"del{pid}":
                        await champmsg.delete()
                        await message.delete()
                        break

                    elif customid == f"lanes{pid}":
                        await champmsg.edit('Que linea quieres bro', embed=None, components=[lanebuttons])
                        msg = await interaction.send(content="Re-Roll<a:kirby:759485375718359081>",ephemeral=False)
                        await msg.delete()

                    elif customid == f"top{pid}":
                        lane = "top"
                        champ = random_champ(wks,lane)
                        embedVar = generate_embed(champ, lane)
                        await champmsg.edit(embed=embedVar, **components)
                        msg = await interaction.send(content="Re-Roll<a:kirby:759485375718359081>",ephemeral=False)
                        await msg.delete()

                    elif customid == f"jg{pid}":
                        lane = "jg"
                        champ = random_champ(wks,lane)
                        embedVar = generate_embed(champ, lane)
                        await champmsg.edit(embed=embedVar, **components)
                        msg = await interaction.send(content="Re-Roll<a:kirby:759485375718359081>",ephemeral=False)
                        await msg.delete()

                    elif customid == f"mid{pid}":
                        lane = "mid"
                        champ = random_champ(wks,lane)
                        embedVar = generate_embed(champ, lane)
                        await champmsg.edit(embed=embedVar, **components)
                        msg = await interaction.send(content="Re-Roll<a:kirby:759485375718359081>",ephemeral=False)
                        await msg.delete()

                    elif customid == f"adc{pid}":
                        lane = "adc"
                        champ = random_champ(wks,lane)
                        embedVar = generate_embed(champ, lane)
                        await champmsg.edit(embed=embedVar, **components)
                        msg = await interaction.send(content="Re-Roll<a:kirby:759485375718359081>",ephemeral=False)
                        await msg.delete()

                    elif customid == f"supp{pid}":
                        lane = "supp"
                        champ = random_champ(wks,lane)
                        embedVar = generate_embed(champ, lane)
                        await champmsg.edit(embed=embedVar, **components)
                        msg = await interaction.send(content="Re-Roll<a:kirby:759485375718359081>",ephemeral=False)
                        await msg.delete()
                    
                except:
                    await message.channel.send("Exception")
                    await champmsg.delete()
                    await message.delete()
                    break

intents = discord.Intents(messages=True, guilds=True)
client = MyClient(intents=intents)
DiscordComponents(client)
client.run(str(TOKEN))