import discord
from discord.commands import Option
from discord.ext.commands import has_permissions, CheckFailure
from discord.message import Attachment
from discord.member import Member

from simplejsondb import Database

from helperfunctions import *

intents = discord.Intents.default()
intents.members = True
 
# Read info from json database
db_json = Database("db.json", default=dict())
queue_json = Database("queue.json", default=dict())
db = db_json.data
queue = queue_json.data


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


# ping
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

@bot.slash_command(guild_ids=guilds, description="Get user info via Discord or Minecraft IGN (leave empty for your own info)")
async def info(ctx,
               user_name: Option(Member, "Discord name", required=False, name="discord"),
               ign: Option(str, "Minecraft name", required=False)):
    discord_id = ""

    # Get user info by looking in the db for discord id or Minecraft IGN
    user = None
    if user_name:
        user = get_user_info(str(user_name.id), users)
    elif ign:
        user = get_user_info_by_ign(ign, users)
    else:
        user = get_user_info(str(ctx.author.id), users)

    if user == None and ign == None:
        if user_name == None:
            await ctx.respond("Please connect your account using `/connect` to view your stats!")
            return
        await ctx.respond("This person has not connected their account 🥲")
        return

    if user != None:
        ign = user["IGN"]
        discord_id = user["id"]

    # Get discord details of the user (In case we only knew the IGN)
    display_name = ign

    forums = "Account not connected"
    disc_user = None
    if user is not None:
        disc_user = bot.get_user(int(user["id"]))
        forums = f"[Forums profile]({user['forums']})"
    if disc_user is not None:
        display_name = disc_user.display_name

    # Get external data of this player
    df = get_ext_player_data()
    xpd = df.loc[df['Player'].str.lower() == ign.lower()]

    description = ""
    description += f"**Minecraft:** {ign}\n"
    if ' ' in ign:
        platform = 'Bedrock'
    else:
        platform = 'Java?'

    position = "_"
    if len(xpd) == 1:
        platform = xpd['Platform'].values[0]
        position = xpd['Position'].values[0]
        records = xpd['Records'].values[0]
        LCR = xpd['LCR'].values[0]
        OCR = xpd['OCR'].values[0]

        if xpd['discord_id'].values[0] != '??':
            discord_id = xpd['discord_id'].values[0]
        
        description += f"**Platform:** {platform}\n"
        description += f"**Position:** # {position}\n"
        description += f"**Records:** {records}\n\n"
        description += f"**Latest Record:**\n{LCR}\n"
        description += f"**Oldest Record:**\n{OCR}\n\n"
    else:
        description += f"**Platform:** {platform}\n"
        description += f"**Records:** 0\n\n"

    description += f"{forums}"


    # Fancy colours for top 3
    colour = discord.Colour.blurple()
    if position == 1:
        colour = discord.Colour.gold()
    if position == 2:
        colour = discord.Colour.from_rgb(192,192,192)
    if position == 3:
        colour = discord.Colour.orange()

    embed = discord.Embed(
        title=f"{display_name}'s user info",
        description=description,
        color=colour
    )
 
    embed.set_author(name="CCGRC", icon_url=ctx.guild.icon.url)

    if platform == 'Bedrock':
        ign = 'bedrock'

    embed.set_thumbnail(url=f"https://mc-heads.net/head/{ign}/left")

    embed.set_footer(text=f"{discord_id}")

    await ctx.respond(embed=embed)


# submission command
@bot.slash_command(guild_ids=guilds, description="Submit your record, it should appear in the queue.")
async def submit(ctx, 
                 game: Option(str, "Eggwars, Skywars, etc."), 
                 record: Option(str, "What record are you submitting for? Example: Most kills."), 
                 evidence: Option(str, description="Links go here. An image can be pasted or uploaded in the optional attachment field"),
                 attachment: Option(Attachment, description="Image or video", required=False)):
    user = get_user_info(str(ctx.author.id))
    # Check if the user has connected their account.
    if (user == None):
        await ctx.respond("Use /connect to connect your account before making a submission.")
        return
    
    # Check if the queue isn't full
    if queue["inqueue"] >= 9999:
        await ctx.respond("Queue full, wait for submissions to be reviewed.")
        return

    # Send a summary of the submission in the submission channel
    ats_string = ""
    if attachment is not None:
        ats_string = f"\n > {attachment}"
    summary = f"> **Game:** {game}\n> **Record:** {record}\n> **Evidence:**\n> {evidence}{ats_string}\n"
    interaction: discord.Interaction = await ctx.respond(summary + f"Your submission will be reviewed! <@{ctx.author.id}>")

    # Get a link to the summary message
    message = await interaction.original_response()
    message_link = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"

    # Create the message for in the queue
    s_id = generate_random_id(queue)

    # Create the embed for in the queue
    embedVar = discord.Embed(title=f"New submission by {ctx.author.display_name}", description="", color=0xfecc52)
    embedVar.add_field(name="Details", value=f"**IGN:** {user['IGN']}\n**Game:** {game}\n[{user['IGN']}'s forumes profile]({user['forums']})", inline=False)
    embedVar.add_field(name="Record", value=record, inline=False)
    embedVar.add_field(name=f"Evidence: {message_link}", value="", inline=False)
    embedVar.set_footer(text=f"Submission code: {s_id}")

    # Send the submission in the queue
    queue_channel = bot.get_channel(int(botInfo["queueChannelID"]))
    submissionMessage = await queue_channel.send(embed=embedVar)

    # submission object for in the queue db
    submission = {
        "id": s_id,
        "botMessage": submissionMessage.id,
        "submissionMessage": message_link,
        "Uid": ctx.author.id,
        "IGN": user["IGN"],
        "forums": user["forums"],
        "GM": game,
        "message": record
    }

    queue["submissions"].append(submission)
    queue["inqueue"] += 1
    queue_json.save(indent=2)

    # update submission count
    botInfo["submissions"] += 1
    db_json.save(indent=2)

# command for accepting a submission   
@has_permissions(administrator=True)
@bot.slash_command(guild_ids=guilds, description="Accept a record.")
async def accept(ctx, scode, prevholder):

    # Find the submission in the queue db
    submission = None
    for sub in queue["submissions"]:
        if sub["id"] == scode:
            submission = sub

    # If the submission is not found
    if submission == None:
        await ctx.respond(f"Submission {scode} was not found.")
        return
    
    # remove submission from queue database
    queue["submissions"].remove(submission)
    queue["inqueue"] -= 1
    queue_json.save(indent=2)

    # remove entry from queue channel
    queue_channel = bot.get_channel(int(botInfo["queueChannelID"]))
    msg = await queue_channel.fetch_message(int(submission["botMessage"]))
    await msg.delete()

    # send accept message
    subMessage = submission["message"][0:47]
    if len(submission["message"]) > 47:
        subMessage = subMessage + "..."
    
    if (submission["submissionMessage"]):
        linkToSubmission = f"\nLink to your submission: {submission['submissionMessage']}"

    feedback_channel = bot.get_channel(int(botInfo["feedbackChannelID"]))
    await feedback_channel.send(f"✅ <@{submission['Uid']}> Your {submission['GM']} submission for \"{subMessage}\" has been accepted!{linkToSubmission}")


    # update the changelog
    changelog_channel = bot.get_channel(int(botInfo["changelogChannelID"]))
    await changelog_channel.send(f"> {submission['GM']}\n> {subMessage}\n> \n> `{prevholder} -> {submission['IGN']}`\n> \n> {submission['submissionMessage']}")

    # Send reply to the reviewer that submitted the record
    await ctx.respond(f"Submission {scode} accepted")

@accept.error
async def accept_error(ctx, error):
    if isinstance(error, CheckFailure):
        await ctx.respond("You're not an admin")

# command for denying a submission   
@has_permissions(administrator=True)
@bot.slash_command(guild_ids=guilds, description="Deny a record.")
async def deny(ctx, scode, feedback):
    # Find the submission in the queue db
    submission = None
    for sub in queue["submissions"]:
        if sub["id"] == scode:
            submission = sub

    # If the submission is not found
    if submission == None:
        await ctx.respond(f"Submission {scode} was not found.")
        return
    
    # remove submission from queue database
    queue["submissions"].remove(submission)
    queue["inqueue"] -= 1
    queue_json.save(indent=2)

    # remove entry from queue
    queue_channel = bot.get_channel(int(botInfo["queueChannelID"]))
    msg = await queue_channel.fetch_message(int(submission["botMessage"]))
    await msg.delete()

    # send deny message
    subMessage = submission["message"][0:47]
    if len(submission["message"]) > 47:
        subMessage = subMessage + "..."
    
    if (submission["submissionMessage"]):
        linkToSubmission = f"\nLink to your submission: {submission['submissionMessage']}"

    fbembed = discord.Embed(title=f"Staff Feedback", description=feedback, color=0xfecc52)

    feedback_channel = bot.get_channel(int(botInfo["feedbackChannelID"]))
    await feedback_channel.send(f"❌ <@{submission['Uid']}> Your {submission['GM']} submission for \"{subMessage}\" has been denied :c{linkToSubmission}", embed=fbembed)

    await ctx.respond(f"Submission {scode} denied")

@deny.error
async def deny_error(ctx, error):
    if isinstance(error, CheckFailure):
        await ctx.respond("You're not an admin")

# command for deleting a submission   
@has_permissions(administrator=True)
@bot.slash_command(guild_ids=guilds, description="Deny a record.")
async def delete(ctx, scode):
    # Find the submission in the queue db
    submission = None
    for sub in queue["submissions"]:
        if sub["id"] == scode:
            submission = sub

    # If the submission is not found
    if submission == None:
        await ctx.respond(f"Submission {scode} was not found.")
        return
    
    # remove submission from queue database
    queue["submissions"].remove(submission)
    queue["inqueue"] -= 1
    queue_json.save(indent=2)

    # remove entry from queue
    queue_channel = bot.get_channel(int(botInfo["queueChannelID"]))
    msg = await queue_channel.fetch_message(int(submission["botMessage"]))
    await msg.delete()

    await ctx.respond(f"Submission {scode} deleted")

@delete.error
async def delete_error(ctx, error):
    if isinstance(error, CheckFailure):
        await ctx.respond("You're not an admin")


#command for connecting accounts
@bot.slash_command(guild_ids=guilds, description="Connect your Discord to your IGN and forums account.")
async def connect(ctx,
                  ign: Option(str, "Your ingame name"),
                  forums_link: Option(str, "link to your forums page")):
    
    # Check if the right link was used
    if not forums_link[0:len(cubecraft_link)] == cubecraft_link:
        await ctx.respond("Please use the link to your members page, it looks like:\nhttps://www.cubecraft.net/members/naitzirch.375456/")
        return

    user = {
        "id": str(ctx.author.id),
        "IGN": ign,
        "forums": forums_link
    }

    msg = "Successfully connected your account!"

    # Check if user already connected their account
    old_profile = None
    for u in users:
        if u["id"] == str(ctx.author.id):
            old_profile = u

    # remove old details if found
    if old_profile is not None:
        users.remove(old_profile)
        msg = "Successfully updated your account details."

    users.append(user)
    db_json.save(indent=2)

    await ctx.respond(msg)



# run the bot
bot.run(botInfo["token"])