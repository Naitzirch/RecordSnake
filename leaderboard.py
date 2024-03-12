import discord
from discord.ext import commands
from discord.commands import slash_command
from discord.ext.pages import Paginator, Page

from helperfunctions import *

class Base(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command()
    async def leaderboard(self, ctx):
        ext_player_data = get_ext_player_data()
        pages = []
        positi_field = "```\n"
        player_field = "```\n"
        record_field = "```\n"

        for index, row in enumerate(ext_player_data.values):
            positi, player, record = row
            positi_field += f"{positi}\n"
            player_field += f"{player}\n"
            record_field += f"{record}\n"

            if (index + 1) % 10 == 0 or index == len(ext_player_data.values) - 1:
                positi_field += "```"
                player_field += "```"
                record_field += "```"
                embed = discord.Embed(
                    title="Records Leaderboard",
                    description="Leaderboard of records in CCGRC!",
                    color=discord.Colour.green()
                )
                #embed.set_thumbnail(url=ctx.guild.icon.url)
                embed.add_field(name="‎ ‎ #", value=positi_field, inline=True)
                embed.add_field(name="‎ ‎ Player", value=player_field, inline=True)
                embed.add_field(name="‎ ‎ Records", value=record_field, inline=True)

                # reset strings so the next page can be created
                pages.append(embed)
                positi_field = "```\n"
                player_field = "```\n"
                record_field = "```\n"
        
        paginator = Paginator(pages=pages)
        await paginator.respond(ctx.interaction)

def setup(bot):
    bot.add_cog(Base(bot))