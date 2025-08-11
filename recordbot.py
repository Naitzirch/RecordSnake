import discord
from discord.commands import Option
from discord.ext.commands import has_permissions, CheckFailure
from discord.message import Attachment
from discord.member import Member

from simplejsondb import Database

from enum import Enum

intents = discord.Intents.default()
intents.members = True
 
# Read info from json database
db_json = Database("database/db.json", default=dict())
queue_json = Database("database/queue.json", default=dict())
record_db_json = Database("database/record_db.json", default=dict())
db = db_json.data
queue = queue_json.data
record_db = record_db_json.data


bot = discord.Bot(intents=intents)

import leaderboard
leaderboard.setup(bot)


# setting variables
botInfo = db["botInfo"]
users   = db["users"]
guilds  = botInfo["guilds"]
records = record_db["records"]
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


connect = bot.create_group("connect", "Connect your Discord to your IGN and forums account.", guilds)

from commands.connect_forums import forums_impl
@connect.command(description="Connect your Discord to your CubeCraft forums account.")
async def forums(ctx, forums_link=Option(str, "link to your forums page")):
    await forums_impl(ctx, forums_link, users, db_json, cubecraft_link)

from commands.connect_minecraft import minecraft_impl
@connect.command(description="Connect your Discord to your Minecraft account.")
async def minecraft(ctx, platform=Option(Enum('Platform', ['Java', 'Bedrock']), "Platform type"), ign=Option(str, "Your in-game name")):
    await minecraft_impl(ctx, platform, ign, users, db_json)

record_group = bot.create_group("record", "Modify the record database.", guilds)

from commands.record_register import register_impl
@record_group.command(guild_ids=guilds, description="Add a record to the database")
async def register(ctx: discord.ApplicationContext, 
                   platform=Option(Enum('Platform', ['Java', 'Bedrock']), "Platform type"),
                   game=Option(str, "Eggwars, Skywars, etc."),
                   record=Option(str, "e.g. Most kills, Fastes win"),
                   mode=Option(str, "Solo, Easy, etc.", default=""),
                   username=Option(str, "discord/mc", default=""),
                   evidence_link=Option(str, "Evidence message link", default="")):
    await register_impl(ctx, bot, platform, game, record, mode, username, evidence_link, db_json, record_db_json, users, records)

from commands.record_remove import remove_impl
@record_group.command(guild_ids=guilds)
async def remove(ctx: discord.ApplicationContext, id):
    await remove_impl(ctx, id)

# run the bot
bot.run(botInfo["token"])