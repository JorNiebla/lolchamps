# REWRITTING ON PYCORD :)

from xmlrpc.client import MAXINT, MININT
from numpy import mat
import riotwatcher
import psycopg2
import random
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
import riotwatcher
from riotwatcher import RiotWatcher, LolWatcher
from PIL import Image, ImageFont, ImageDraw, ImageOps
import discord
from dotenv import load_dotenv
import os
import db
import traceback

load_dotenv()
TOKEN = os.getenv('TESTTOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
bot = discord.Bot()


lanes = {'top': "TOP", 'jg': "JGL", 'jung': "JGL", 'jng': "JGL",'jungle': "JGL",
    'jungler': "JGL", 'mid': "MID", 'middle': "MID", 'adc': "ADC", 'bot': "ADC",
    'supp': "SUP", 'sup': "SUP", 'support': "SUP"}

regionalias = {"euw":"euw1", "na":"na1", "br":"br1", "eun":"eun1", "jp":"jp1",
    "kr":"kr", "lan":"la1", "las":"la2", "oc":"oc1", "ru":"ru", "tr":"tr1"}

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

def generate_embed(champ,lane):
    embedVar = discord.Embed(color=0x00ff00)
    embedVar.add_field(name="Champion", value=champ[0])
    embedVar.add_field(name="Lane", value=lane)
    embedVar.set_image(url=champ[2])
    return embedVar

class TestView(discord.ui.View):
    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.delete()

    @discord.ui.button(label="Prueba", style=discord.ButtonStyle.primary)
    async def button_callback(self, boton, interaction): #_messagesend("LETS GO", delete_after=0.5)
        con = psycopg2.connect(DATABASE_URL)
        cur = con.cursor()
        await printlaner("top",0,interaction,cur)
        con.close()
        #await interaction.message.delete()

async def printlaner(lane,userid,interaction,cur):
    champ = random_champ(lanes[lane],userid,cur)
    embedVar = generate_embed(champ, lane)
    await interaction.response.edit_message(content='',embed=embedVar,view=TestView)

@bot.slash_command(name="help",description="Shows commands and usage")
async def help_command(ctx):
    embedVar = discord.Embed(title="List of commands and usage")
    embedVar.add_field(name="/help", value="Used to display this message.", inline=False)
    embedVar.add_field(name="/stats lane", value="Used to display your stats in a certain lane (lane is optional, it defaults to all lanes).", inline=False)
    embedVar.add_field(name="/win champ1, champ2...", value="Used to register wins on several champs manually.", inline=False)
    embedVar.add_field(name="/connect summonerName region", value="Used to link your profile with a riot account.", inline=False)
    embedVar.add_field(name="/disconnect", value="Used to unlink your profile from your riot account.", inline=False)
    embedVar.add_field(name="/random lane", value="Used to fetch a random champ without a win in a certain lane (lane is optional, it defaults to select a lane).", inline=False)
    examplefile = discord.File(f'images/logo.png', filename="logo.png")
    embedVar.set_image(url="attachment://logo.png")
    await ctx.respond(file=examplefile, embed=embedVar)

@bot.slash_command(name="stats",description="Stats with missing wins")
async def stats_command(ctx,
    lane1:discord.Option(str,"Lane1", autocomplete=discord.utils.basic_autocomplete(['top','jg','mid','adc','supp']),required=False), 
    lane2:discord.Option(str,"Lane2", autocomplete=discord.utils.basic_autocomplete(['top','jg','mid','adc','supp']),required=False),
    lane3:discord.Option(str,"Lane3", autocomplete=discord.utils.basic_autocomplete(['top','jg','mid','adc','supp']),required=False),
    lane4:discord.Option(str,"Lane4", autocomplete=discord.utils.basic_autocomplete(['top','jg','mid','adc','supp']),required=False),
    name="stats"):
    userid = ctx.author.id
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    msglanes = [lane1,lane2,lane3,lane4]
    try:
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

        colors = ["#14A8A8", "#A536E5"] 
        sns.set_theme(font="serif",font_scale=1.5)
        explode = [0.2, 0]

        plt.pie(nowinsandwins, labels=[f"", f"Wins"],explode=explode,colors=colors,autopct='%.0f%%')
        plt.savefig(f'temp{userid}.png')
        
        bgdummy = Image.open(f'temp{userid}.png')
        background = ImageOps.invert(bgdummy.convert('RGB'))
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

        ImageDraw.Draw(background).text((5,background.height - 30),f"Champion count for {textlanes}{nowinsandwins[1]}/{nowinsandwins[0]+nowinsandwins[1]}",fill=(255,0,0,255),font=font)
        background.save(f'temp{userid}.png')

        plt.clf()
        embed = discord.Embed(title=f"Stats for {ctx.author.name}",color=0x00ff00) #creates embed
        piefile = discord.File(f'temp{userid}.png', filename="grahp.png")
        embed.set_image(url="attachment://grahp.png")
        await ctx.respond(file=piefile, embed=embed)
        os.remove(f'temp{userid}.png')
        con.close()

    except psycopg2.errors.UndefinedTable:
        await ctx.respond("You don't have a profile, create one by mentioning me and typing 'new'", delete_after=10)
        con.close()
    except:
        print(traceback.format_exc())
        await ctx.respond("Something went wrong, sorry I couldn't get your stats", delete_after=10) 
        con.close()

@bot.slash_command(name="win",description="Mark a champ as won with")
async def win_command(ctx,champname: discord.Option(str,"Champion")):
    userid = ctx.author.id
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
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
        await ctx.respond("I dont know that champion, please type a valid champion", delete_after=10)
    else:
        try:
            cur.execute(f"""INSERT INTO wins (CHAMPID, PLAYERID)
                        VALUES({champid}, {userid})""")
            con.commit()
            await ctx.respond(f"Congratulations on the win with {champname}", delete_after=10)
        except psycopg2.errors.UniqueViolation:
            #await channel.send(f"You have already won with {champname}, try another champ", delete_after=5)
            con.rollback()
        except:
            print(traceback.format_exc())
            await ctx.respond(f"Something went wrong, sorry I couldn't register the win with {champname}", delete_after=5) 

@bot.slash_command(name="connect",description="Connect your discord account with your riot account")    
async def connect_command(ctx,name="connect"):
    await ctx.respond("To be implemented")

@bot.slash_command(name="disconnect",description="Disconnect your discord account with your riot account")    
async def disconnect_command(ctx,name="disconnect"):
    await ctx.respond("To be implemented")

@bot.slash_command(name="random",description="Disconnect your discord account with your riot account")    
async def random_command(ctx,lane:discord.Option(str,"Champion",required=False)):
    await ctx.respond("To be implemented")

# grupito = bot.create_group("grupito", "Comandos guapos")

# @grupito.command(description="Latencia")
# async def pong(ctx):
#     await ctx.respond(f"Ping! La latencia es {bot.latency}")

# @grupito.command(description="Suma de dos numeros")
# async def suma(ctx, num1: discord.Option(int,"Primer numero"), num2: discord.Option(int,"Segundo numero")):
#     sum = num1 + num2
#     await ctx.respond(f"Ping! La suma de {num1} y {num2} es {sum}")

# @grupito.command(description="Activa el botón de prueba")
# async def boton(ctx):
#     await ctx.respond("Dale al boton", view=TestView(timeout=None))

bot.run(TOKEN)

# class MyClient(discord.Client):
#     async def on_ready(self):
#         await bot.tree.sync(guild=discord.Object(id=518907819513217034))
#         print('Logged on as', self.user)

#     async def on_message(self, message):
#         botpinged = False
#         for role in message.role_mentions:
#             if role.tags.is_bot_managed() and role.tags.bot_id == self.user.id:
#                 botpinged = True
#                 break
#         if(self.user in message.mentions and not message.author.bot):
#             botpinged = True

#         if botpinged:
#             con = psycopg2.connect(DATABASE_URL)
#             cur = con.cursor()
#             pid = random.randint(MININT,MAXINT)
#             userid = message.author.id
#             channel = message.channel

#             elif("update" in message.content) and (userid == 371076929022984196):
#                 await channel.send("Updating database...", delete_after=10)
#                 db.update_champions_DB(con,cur)
#                 await channel.send("Database updated!", delete_after=10)
#                 await message.delete(delay=10)

#             elif("disconnect" in message.content):
#                 try:
#                     cur.execute(f"""DELETE FROM profiles 
#                                     WHERE PLAYERID = '{userid}'""")
#                     con.commit()   
#                     await channel.send(f"Account disconnected succesfully!", delete_after=10) 
#                 except:
#                     print(traceback.format_exc())
#                     await channel.send("Something went wrong, sorry I couldn't disconnect with your account", delete_after=10)

#                 await message.delete(delay=10)

#             elif("connect" in message.content):
#                 info = message.content.split("connect", 1)[1].strip().rsplit(" ", 1)
#                 
#                 if len(info) != 2:
#                     pass
#                 else:
#                     gameName = info[0]
#                     region = info[1].lower()
#                     try:
#                         summoner = lol_watcher.summoner.by_name(f"{regionalias[region]}",gameName)
#                         puuid = summoner['puuid']
#                         cur.execute(f"""INSERT INTO profiles (PLAYERID,PUUID,REGION,GAMENAME)
#                             VALUES('{userid}','{puuid}','{regionalias[region]}','{gameName}')""")
#                         con.commit()
#                         await channel.send(f"Account connected succesfully!", delete_after=10)
#                     except psycopg2.errors.UniqueViolation:
#                         await channel.send(f"You have already have an account connected, if you wish to change it mention me with \"disconnect\"", delete_after=10)            
#                     except:
#                         print(traceback.format_exc())
#                         await channel.send("Something went wrong, sorry I couldn't connect with your account", delete_after=10)       
#                 await message.delete(delay=10)         

#             elif("load" in message.content):
#                 def get_games_postchall(matchlist,puuid,region,queue):
#                     newlist = lol_watcher.match.matchlist_by_puuid(region,puuid,start_time=1652270400,queue=queue,count=100)
#                     matchlist.extend(newlist)
#                     start = 100
#                     while len(newlist) > 0:
#                         newlist = lol_watcher.match.matchlist_by_puuid(region,puuid,start_time=1652270400,queue=queue,count=100,start=start)
#                         matchlist.extend(newlist)
#                         start+=100
#                 try:
#                     await channel.send(f"Loading all matches, this may take a while")
#                     cur.execute(f"""SELECT PUUID, REGION 
#                             FROM profiles
#                             WHERE PLAYERID = '{userid}'""")
#                     data = cur.fetchone()
#                     puuid = data[0]
#                     region = data[1]
#                     matchlist = []
#                     get_games_postchall(matchlist,puuid,region,400) #DRAFT PICK
#                     get_games_postchall(matchlist,puuid,region,420) #SOLO DUO
#                     get_games_postchall(matchlist,puuid,region,430) #BLIND PICK
#                     get_games_postchall(matchlist,puuid,region,440) #FLEX
#                     for matchid in matchlist:
#                         match = lol_watcher.match.by_id(region, matchid)
#                         for summoner in match["info"]["participants"]:
#                             if (summoner["puuid"] == puuid) and (summoner["win"]):
#                                 await win_champ(cur,con,summoner['championName'],userid,channel)
#                     await channel.send(f"Loaded all matches!")
#                 except:
#                     print(traceback.format_exc())

#             else:
#                 championbuttons = [
#                 discord.ui.Button(label="Win", style=discord.ButtonStyle.green, emoji = self.get_emoji(987155911766335520), custom_id=f"win{pid}"), 
#                 discord.ui.Button(label="Re-Roll", style=discord.ButtonStyle.blurple, emoji = "🔁", custom_id=f"roll{pid}"), 
#                 discord.ui.Button(label="Delete", style=discord.ButtonStyle.red, emoji = self.get_emoji(987331408093642822), custom_id=f"del{pid}"),
#                 discord.ui.Button(label="Lanes", style=discord.ButtonStyle.grey, emoji =self.get_emoji(987173438907088966) , custom_id=f"lanes{pid}")]

#                 championview = discord.ui.View()
#                 for button in championbuttons:
#                     championview.add_item(button)

#                 lanebuttons = [
#                 discord.ui.Button(emoji = self.get_emoji(987155912890417154),custom_id=f"top{pid}"), 
#                 discord.ui.Button(emoji = self.get_emoji(987155914362589184),custom_id=f"jg{pid}"),
#                 discord.ui.Button(emoji = self.get_emoji(987155915541205002),custom_id=f"mid{pid}"), 
#                 discord.ui.Button(emoji = self.get_emoji(987172387277656104),custom_id=f"adc{pid}"),
#                 discord.ui.Button(emoji = self.get_emoji(987155917961318440),custom_id=f"supp{pid}")]

#                 laneview = discord.ui.View()
#                 for button in lanebuttons:
#                     laneview.add_item(button)

#                 confirmbuttons = [
#                 discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, emoji = self.get_emoji(987155911766335520), custom_id=f"yeswin{pid}"),
#                 discord.ui.Button(label="No", style=discord.ButtonStyle.red, emoji = self.get_emoji(987155911766335520), custom_id=f"nowin{pid}")]

#                 confirmview = discord.ui.View()
#                 for button in confirmbuttons:
#                     confirmview.add_item(button)

#                 lane = message.clean_content.replace(f"@{self.user.name} ", '').lower()

#                 buttons = {f"roll{pid}":0, f"win{pid}":1, f"del{pid}":2, f"lanes{pid}":3,f"top{pid}":4,f"jg{pid}":5,f"mid{pid}":6,f"adc{pid}":7,f"supp{pid}":8,f"yeswin{pid}":9,f"nowin{pid}":10}

#                 lanembed = discord.Embed(color=0x00ff00).set_image(url="https://cdn.discordapp.com/attachments/518907821081755672/987335003371364452/unknown.png")

#                 if lane in lanes:
#                     champ = random_champ(lanes[lane],userid,cur)
#                     embedVar = generate_embed(champ,lane)
#                     await message.reply(embed=embedVar, view=championview)

#                 else:
#                     await message.reply('What lane do you want to see?', embed=lanembed, view=laneview)

#                 while True:
#                     try:
#                         interaction = await client.wait_for("interaction",timeout=5400)
#                         if interaction.type != discord.InteractionType.component:
#                             continue
#                         customid = interaction.data['custom_id']
#                         if not customid in buttons: #If this interaction doesnt belong to the original message
#                             continue
                        
#                         await interaction.message.delete()

#                         match buttons[customid]:
#                             case 0: #Button for re-rolling
#                                 pass
#                             case 1: #Button for selecting a win
#                                 if interaction.user != message.author:
#                                     await channel.send("This is not your profile to change!")
#                                 else:
#                                     await message.reply("Are you sure you want to register the win?", view=confirmview)
#                                 continue
#                             case 2: #Button for deleting the messages
#                                 await message.delete()
#                                 break
#                             case 3: #Button for selecting lanes
#                                 await message.reply('What lane do you want to see?', embed=lanembed, view=laneview)
#                                 continue
#                             case 4: #Button for selecting top
#                                 lane = "top"
#                             case 5: #Button for selecting jungle
#                                 lane = "jungle"
#                             case 6: #Button for selecting mid
#                                 lane = "mid"
#                             case 7: #Button for selecting ADCarry
#                                 lane = "adc"
#                             case 8: #Button for selecting support
#                                 lane = "supp"
#                             case 9: #Confirm win
#                                 await win_champ(cur,con,champ[0],userid,channel)
#                             case 10: #Cancel win
#                                 continue
#                         champ = random_champ(lanes[lane],userid,cur)
#                         embedVar = generate_embed(champ, lane)
#                         await message.reply(content=None,embed=embedVar, view=championview)
#                     except asyncio.TimeoutError:
#                         await channel.send("Timeout, deleting message...", delete_after=10)
#                         await interaction.message.delete()
#                         await message.delete()
#                         break
#                     except:
#                         print(traceback.format_exc())
#                         await channel.send("Exception", delete_after=10)
#                         await interaction.message.delete()
#                         await message.delete()
#                         break
#             con.close()
        
# 
# RIOT_API_KEY = os.getenv('RIOT_API_KEY')

# lol_watcher = LolWatcher(RIOT_API_KEY)
# riot_watcher = RiotWatcher(RIOT_API_KEY)
# client = MyClient(intents=intents)
# client.run(str(TOKEN))