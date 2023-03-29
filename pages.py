import discord
from discord.ext.pages import Page

logofile = discord.File(f'images/logo.png', filename="logo.png")

embedHelp0 = discord.Embed(title="List of commands and usage", description="\
                           TEST TEST")
embedHelp0.set_image(url="attachment://logo.png")

embedHelp1 = discord.Embed(title="List of commands and usage")
embedHelp1.add_field(name="/help", value="Used to display this message.", inline=False)
embedHelp1.add_field(name="/win", value="Used to register wins on several champions manually.\n \
                     Example **/win jax, /win lux mordekaiser zed, etc.**", inline=False)
embedHelp1.add_field(name="/connect", value="Used to link your profile with a riot account.", inline=False)
embedHelp1.add_field(name="/disconnect", value="Used to unlink your profile from your riot account.", inline=False)

embedHelp1.set_image(url="attachment://logo.png")

embedHelp2 = discord.Embed(title="List of commands and usage")
embedHelp2.add_field(name="/random", value=" Used to fetch a random champ without a win in a certain **lane**. \n \
                     Example **/random top, /random, /random adc, etc.**", inline=False)
embedHelp2.add_field(name="/stats", value="Used to display your stats in a certain lane (lane is optional, it defaults to all lanes).", inline=False)
#embedHelp2.set_image(url="attachment://logo.png")

helpPages = [
    Page(
        embeds=[
            embedHelp0
        ],
        files=[
            logofile
        ]
    ),
    Page(
        embeds=[
            embedHelp1
        ]
    ),
    Page(
        embeds=[
            embedHelp2
        ]
    )
]