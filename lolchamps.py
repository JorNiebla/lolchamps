from distutils.command.clean import clean
import discord
import gspread
import random
import string

sa = gspread.service_account()
sh = sa.open("lolchamps")

def cords_to_cellname(row,col):
    alph = string.ascii_uppercase
    return(alph[col-1]+str(row))

users = {'discordid': 'Worksheet'}
lanes = {'top': 9, 'jg': 10, 'jungle': 10, 'mid': 11, 'adc': 12, 'bot': 12, 'supp': 13, 'sup': 13}

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        #Atiende a mensajes en los que se menciona al bot
        for x in message.mentions:
            if(x==self.user):
                lane = message.clean_content.replace('@' + self.user.name + ' ' , '')
                react = True
                if not message.author.id in users:
                    await message.channel.send('No se quien eres bro te doy uno cualquiera')
                    wks = sh.worksheet("Clean")
                    react = False
                else: 
                    wks = sh.worksheet(users[message.author.id])
                    print("Abriendo la hoja de " + users[message.author.id])
                if lane in lanes:
                    laneid = lanes[lane]
                    limit = int(wks.cell(2,laneid).value)
                    champ = wks.cell(random.randint(3, limit+2), laneid).value
                    champmsg = await message.channel.send(champ)
                    if react:
                        await champmsg.add_reaction("👍")
                    return
                else:
                    await message.channel.send('No se que linea es esa bro')
                    return
    async def on_reaction_add(self, reaction, user):
        #No reacciona un bot
        if user.bot:
            return
        #Reacciona a un mensaje del bot
        if reaction.message.author != self.user:
            return
        #El que reacciona tiene una hoja
        if not user.id in users:
            return
        #Reacciono con el like
        if reaction.emoji != "👍":
            return

        wks = sh.worksheet(users[user.id])
        champ = reaction.message.content
        if not champ in wks.col_values(8):
            return

        cell_list = wks.findall(champ)
        while len(cell_list) > 0:
            currentrow = cell_list[-1].row
            currentcol = cell_list[-1].col
            if currentcol < 8:
                cell_list.pop()
                continue
            limit = int(wks.cell(2,currentcol).value)
            range = cords_to_cellname(currentrow,currentcol) + ":" + cords_to_cellname(limit+1,currentcol)
            range2 = cords_to_cellname(currentrow+1,currentcol) + ":" + cords_to_cellname(limit+2,currentcol)
            listofchamps = wks.get(range2)
            wks.update(range,listofchamps)
            wks.update_cell(limit+2,currentcol,'')
            cell_list.pop()
        return


intents = discord.Intents(messages=True, reactions=True)
client = MyClient(intents=intents)
client.run('TOKEN')