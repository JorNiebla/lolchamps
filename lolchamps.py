import discord
from discord_components import DiscordComponents, Button
import random
import string

from openpyxl import load_workbook

import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')

users = {}
lanes = {'all': 8, 'top': 9, 'jg': 10, 'jung': 10, 'jng': 10,'jungle': 10, 'jungler': 10, 'mid': 11, 'adc': 12, 'bot': 12, 'supp': 13, 'sup': 13}

def cords_to_cellname(row,col):
    alph = string.ascii_uppercase
    return(alph[col-1]+str(row))

def random_champ(wks, lane):
    laneid = lanes[lane]
    limit = 0
    for cell in wks[string.ascii_uppercase[laneid-1]]:
        if cell.value != None:
            limit+=1

    if limit == 2: return "Cualquier"
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
        #Atiende a mensajes en los que se menciona al bot
        for x in message.mentions:
            if(x==self.user):
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
                    embedVar = discord.Embed(color=0x00ff00)
                    embedVar.add_field(name="Champion", value=champ, inline=False)
                    embedVar.add_field(name="Linea", value=lane, inline=False)
                    file = discord.File("images/xd.png", filename="xd.png")
                    embedVar.set_thumbnail(url="attachment://xd.png")
                    champmsg = await message.reply(embed=embedVar, file=file, components = [[Button(label="Win", style="3", emoji = "✅", custom_id="win"), 
                    Button(label="Re-Roll", style="1", emoji = "🔁", custom_id="roll")]])
                    while True:
                        try:
                            interaction = await client.wait_for("button_click", timeout=120.0)

                            if interaction.component.custom_id == "roll":
                                # if interaction.user != message.author:
                                #     await interaction.send("No es tu campeón amigo")
                                champ = random_champ(wks,lane)
                                await champmsg.delete()

                                embedVar = discord.Embed(color=0x00ff00)
                                embedVar.add_field(name="Champion", value=champ, inline=False)
                                embedVar.add_field(name="Linea", value=lane, inline=False)
                                file = discord.File("images/xd.png", filename="xd.png")
                                embedVar.set_thumbnail(url="attachment://xd.png")
                                champmsg = await interaction.send(embed=embedVar, file=file, components = [[Button(label="Win", style="3", emoji = "✅", custom_id="win"), 
                                Button(label="Re-Roll", style="1", emoji = "🔁", custom_id="roll")]], ephemeral=False)


                            elif interaction.component.custom_id == "win":
                                if interaction.user != message.author:
                                    await interaction.send("No es tu campeón amigo")
                                elif knownuser:
                                    wks = wb[str(message.author.id)]
                                    print(interaction.message)
                                    champ = interaction.message.content.rsplit(' ', 1)[0]
                                    remove_champ(wks,champ)
                                    wb.save('lolchamps.xlsx')
                                    await interaction.send("Quitado de la lista")
                                else:
                                    await interaction.send("No tienes ficha creada")

                            else: break
                        except:
                            await champmsg.delete()
                            await message.delete()
                            break

                else:
                    await message.channel.send('No se que linea es esa bro')

    # async def on_reaction_add(self, reaction, user):
    #     wb = load_workbook('lolchamps.xlsx')
    #     #El que reacciona tiene una hoja
    #     if user.id in users:
    #         wks = wb[str(user.id)]
    #     else:
    #         wks = wb["Clean"]
    #     if reaction.emoji == "✅":
    #         champ = reaction.message.content.rsplit(' ', 1)[0]
    #         remove_champ(wks,champ)
    #         wb.save('lolchamps.xlsx')
    #         return


intents = discord.Intents(messages=True, guilds=True, reactions=True)
client = MyClient(intents=intents)
DiscordComponents(client)
client.run(str(TOKEN))