import discord
from discord.commands import Option
from discord.ext.commands import has_permissions, CheckFailure
from discord.message import Attachment
from discord.member import Member

from simplejsondb import Database

from enum import Enum

from helperfunctions import get_subkeys

intents = discord.Intents.default()
intents.members = True
 
# Read info from json database
db_json = Database("database/db.json", default=dict())
queue_json = Database("database/queue.json", default=dict())
parkour_db_json = Database("database/parkour_db.json", default=dict())
db = db_json.data
queue = queue_json.data
parkour_db = parkour_db_json.data

bot = discord.Bot(intents=intents)

import leaderboard
leaderboard.setup(bot)


# setting variables
botInfo = db["botInfo"]
users   = db["users"]
guilds  = botInfo["guilds"]

cubecraft_link = "https://www.cubecraft.net/members/"



# bot ready
@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


### Structure for command implementation arguments
### (ctx, bot, [slash command parameters], [glob db variables], [databases])


@bot.slash_command(guild_ids=guilds, description="Sends the bot's latency.")
async def ping(ctx):
    await ctx.respond(f"Pong! Latency is `{bot.latency:.4}` seconds")

# link to the book java
@bot.slash_command(guild_ids=guilds, description="Sends a link to the book for java.")
async def java(ctx):
    await ctx.respond(f"<https://www.cubecraft.net/threads/cubecraft-book-of-world-records.344750/>")

# link to the book bedrock
@bot.slash_command(guild_ids=guilds, description="Sends a link to the book for bedrock.")
async def bedrock(ctx):
    await ctx.respond(f"<https://www.cubecraft.net/threads/cubecraft-book-of-world-records.344750/post-1535640>")


info = bot.create_group("info", "Get info about a player through discord or Minecraft.", guilds)

from commands.info_disc import disc_impl
@info.command(description="Get user info via Discord (leave empty for your own info)")
async def disc(ctx, other_user=Option(Member, "Discord name", required=False, name="discord")):
    await disc_impl(ctx, bot, other_user, users)

# command for submitting a record
from commands.submit import submit_impl
@bot.slash_command(guild_ids=guilds, description="Submit your record, it should appear in the queue!")
async def submit(ctx, 
                 platform=Option(Enum('Platform', ['Java', 'Bedrock']), "Platform type"),
                 game=Option(str, "Eggwars, Skywars, etc."),
                 record=Option(str, "What record are you submitting for? Example: Most kills."), 
                 evidence=Option(str, description="Links go here. An image can be pasted or uploaded in the optional attachment field"),
                 attachment=Option(Attachment, description="Image or video", required=False)):
    await submit_impl(ctx, bot, platform, game, record, evidence, attachment, botInfo, users, db_json, queue_json, queue)

# command for accepting a submission
from commands.accept import accept_impl 
@has_permissions(administrator=True)
@bot.slash_command(guild_ids=guilds, description="Accept a record.")
async def accept(ctx, scode, prevholder, newholder=Option(str, "Only use this option if the submitter submitted for somebody else.", required=False)):
    await accept_impl(ctx, bot, scode, prevholder, newholder, botInfo, queue_json, queue)

@accept.error
async def accept_error(ctx, error):
    if isinstance(error, CheckFailure):
        await ctx.respond("You're not an admin")

# command for denying a submission
from commands.deny import deny_impl
@has_permissions(administrator=True)
@bot.slash_command(guild_ids=guilds, description="Deny a record.")
async def deny(ctx, scode, feedback):
    await deny_impl(ctx, bot, scode, feedback, botInfo, queue_json, queue)

@deny.error
async def deny_error(ctx, error):
    if isinstance(error, CheckFailure):
        await ctx.respond("You're not an admin")

# command for deleting a submission
from commands.cancel import cancel_impl
@bot.slash_command(guild_ids=guilds, description="Remove your submission from the queue")
async def cancel(ctx, scode=Option(int, "Submission code, you can find it at the bottom of your submission.")):
    await cancel_impl(ctx, bot, scode, botInfo, queue_json, queue)


# Connect group
connect = bot.create_group("connect", "Connect your Discord to your IGN and forums account.", guilds)

from commands.connect_forums import forums_impl
@connect.command(description="Connect your Discord to your CubeCraft forums account.")
async def forums(ctx, forums_link=Option(str, "link to your forums page")):
    await forums_impl(ctx, forums_link, users, db_json, cubecraft_link)

from commands.connect_minecraft import minecraft_impl
@connect.command(description="Connect your Discord to your Minecraft account.")
async def minecraft(ctx, platform=Option(Enum('Platform', ['Java', 'Bedrock']), "Platform type"), ign=Option(str, "Your in-game name")):
    await minecraft_impl(ctx, platform, ign, users, db_json)

# Parkour group
parkour = bot.create_group("parkour", "Modify the record database.", guilds)

async def get_types(ctx: discord.AutocompleteContext):
    platform = ctx.options['platform']
    mode = ctx.options['mode']
    map_name = ctx.options['map']
    
    path = platform # for modes (final else case)
    if map_name != '' and map_name is not None: # for level numbers
        path =  ".".join((platform, mode, map_name))
    elif mode != '': # for maps
        path = ".".join((platform, mode))

    return get_subkeys(parkour_db, path)

from commands.parkour_register import register_impl
@has_permissions(administrator=True)
@parkour.command(guild_ids=guilds, description="Add a record to the database")
async def register(ctx: discord.ApplicationContext,
                   platform=Option(str, "Platform type", choices=['Java', 'Bedrock']),
                   mode=Option(str, "Simple, Easy, Medium, ...", autocomplete=discord.utils.basic_autocomplete(get_types)),
                   map_name=Option(str, "Name of the map", name="map", autocomplete=discord.utils.basic_autocomplete(get_types)),
                   level=Option(int, "Level of the map", autocomplete=discord.utils.basic_autocomplete(get_types)),
                   discord_id=Option(str, "Can be @ or numeric discord ID. Use comma to seperate when adding multiple IDs/tags", default=None),
                   value=Option(str, "Time as mm:ss:ttt", default="00:00:000"),
                   evidence_link=Option(str, "Link to the discord evidence message (also use comma to seperate links if adding multiple)", default="")):
    await register_impl(ctx, bot, platform, mode, map_name, str(level), discord_id, value, evidence_link, db_json, parkour_db_json, users)

@register.error
async def accept_error(ctx, error):
    if isinstance(error, CheckFailure):
        await ctx.respond("You're not an admin")


from commands.parkour_delete import delete_impl
@has_permissions(administrator=True)
@parkour.command(guilds_ids=guilds, name="delete", description="Remove records from the database")
async def delete_parkour(ctx: discord.ApplicationContext,
                         platform=Option(str, "Platform type", choices=['Java', 'Bedrock']),
                         mode=Option(str, "Simple, Easy, Medium, ...", autocomplete=discord.utils.basic_autocomplete(get_types)),
                         map_name=Option(str, "Name of the map", name="map", autocomplete=discord.utils.basic_autocomplete(get_types)),
                         level=Option(int, "Level of the map", autocomplete=discord.utils.basic_autocomplete(get_types), default="")):
    await delete_impl(ctx, platform, mode, map_name, str(level), db_json, parkour_db_json, users)



# run the bot
bot.run(botInfo["token"])