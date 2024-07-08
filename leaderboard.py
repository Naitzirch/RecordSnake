import discord
from discord.ext import commands
from discord.commands import slash_command
from discord.ext.pages import Paginator
import numpy as np
from helperfunctions import *

from simplejsondb import Database
db_json = Database("db.json", default=dict())
db = db_json.data
botInfo = db["botInfo"]
guilds  = botInfo["guilds"]

class Base(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(guild_ids=guilds, description="Sends a leaderboard of who own the most records!")
    async def leaderboard(self, ctx):
        pages = []
        rows_10 = np.empty((0, 3), dtype=object)
        description = "```\n"

        ext_player_data = get_ext_player_data()
        if ext_player_data.empty:
            await ctx.respond("The player data could not be fetched :(")
            return
        xpd = ext_player_data[['Position', 'Player', 'Records']]
        for index, row in enumerate(xpd.values):
            rows_10 = np.vstack((rows_10, row)) # create array of <= 10 consecutive rows
            if (index + 1) % 20 == 0 or index == len(xpd.values) - 1:
                # Check max values of len(index), len(player) and len(records)
                #max_len_index = len(str(rows_10[len(rows_10)-1][0]))
                #max_len_player = max(map(lambda x: len(str(x)), rows_10[:, 1]))
                #max_len_record = max(map(lambda x: len(str(x)), rows_10[:, 2]))

                for row in rows_10:
                    positi, player, record = row
                    description += " "*(3 - len(str(positi))) + f"{positi}  "
                    description += f"{player}" + " "*(26 - len(player))
                    description += " "*(3 - len(str(record))) + f"{record}\n"
                description += "```"
                
                embed = discord.Embed(
                    title="Records Leaderboard",
                    url=SHEET_URL,
                    description="Leaderboard of records in CCGRC!",
                    color=discord.Colour.green()
                )
                #embed.set_thumbnail(url=ctx.guild.icon.url)
                name_string = "‎ ‎ ‎ ‎ ‎ ‎ #     Player                                                    Records‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ "
                embed.add_field(name=name_string, value=description)

                pages.append(embed) # Add the embed to the page list

                # reset string so the next page can be created
                description = "```\n"
                rows_10 = np.empty((0, 3), dtype=object)
        
        paginator = Paginator(pages=pages)
        await paginator.respond(ctx.interaction)

def setup(bot):
    bot.add_cog(Base(bot))