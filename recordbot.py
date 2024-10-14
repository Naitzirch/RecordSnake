import discord
from discord.commands import Option
from discord.ext.commands import has_permissions, CheckFailure
from discord.message import Attachment
from discord.member import Member

from simplejsondb import Database

from enum import Enum

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


info = bot.create_group("info", "Get info about a player through discord or Minecraft.", guilds)

@info.command(description="Get user info via Discord (leave empty for your own info)")
async def disc(ctx, other_user: Option(Member, "Discord name", required=False, name="discord")):
    discord_id = ""

    # Get user info by looking in the db for discord id
    user = None
    if other_user:
        user = get_user_info(str(other_user.id), users)
    else:
        user = get_user_info(str(ctx.author.id), users)

    if user == None:
        if other_user == None:
            await ctx.respond("Please connect your account using `/connect` to view your stats!")
            return
        await ctx.respond("This person has not connected their account 🥲")
        return

    disc_user = bot.get_user(int(user["id"]))
    forums = f"[Forums profile]({user["forums"]})".replace("_", "\_")
    display_name = disc_user.display_name

    # Get external data of this player
    df = get_ext_player_data()

    # Filter the df based on platform. 3 cases: either both networks, java or bedrock
    if user["java"] != "" and user["bedrock"] != "":
        df = df.loc[df['Platform'].isin(['Java & Bedrock', ''])]
        # Get row index of this player (we need the row below it as well in this case)
        ri = df.index[(df['Player'] == user["java"]) & (df["Platform"] == "Java & Bedrock")].to_list()
        xpd = df.loc[df['Player'] == user["java"]]
        if ri:
            xpd = df.loc[ri[0]:ri[0]+1, :]
    elif user["java"] != "":
        df = df.loc[df['Platform'].isin(['Java'])]
        xpd = df.loc[df['Player'] == user["java"]]
        xpd.loc[len(xpd)] = ['', '', '', '', '', '', '', ''] # append a second empty row for the "bedrock" part
    else:
        df = df.loc[df['Platform'].isin(['Bedrock'])]
        xpd = df.loc[df['Player'] == user["bedrock"]]
        xpd.loc[-1] = ['', '', '', '', '', '', '', ''] # append a second empty row for the "java" part

    description = ""
    description += f"**Java:** {user["java"]}\n".replace("_", "\_")
    description += f"**Bedrock:** {user["bedrock"]}\n".replace("_", "\_")

    position = "_"
    if len(xpd) == 2:
        platform = xpd['Platform'].values[0]
        position = xpd['Position'].values[0]
        records = xpd['Records'].values[0]
        OCR = xpd['OCR'].values[0] + "\n" + xpd['OCR'].values[1]
        LCR = xpd['LCR'].values[0] + "\n" + xpd['LCR'].values[1]

        if xpd['discord_id'].values[0] != '??':
            discord_id = xpd['discord_id'].values[0]
        
        description += f"**Platforms:** {platform}\n"
        description += f"**Position:** # {position}\n"
        description += f"**Records:** {records}\n\n"
        description += f"**Latest Record:**\n{LCR}\n"
        description += f"**Oldest Record:**\n{OCR}\n\n"
    else:
        description += f"**Platforms:** {platform}\n"
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

    embed.set_thumbnail(url=f"https://mc-heads.net/head/{ign}")

    if disc_user:
        embed.set_footer(text=f"{discord_id}", icon_url=disc_user.display_avatar)
    elif discord_id:
        embed.set_footer(text=f"{discord_id}")

    await ctx.respond(embed=embed)


# submission command
@bot.slash_command(guild_ids=guilds, description="Submit your record, it should appear in the queue.")
async def submit(ctx, 
                 platform: Option(Enum('Platform', ['Java', 'Bedrock', 'Other']), "Platform type"),
                 game: Option(str, "Eggwars, Skywars, etc."),
                 record: Option(str, "What record are you submitting for? Example: Most kills."), 
                 evidence: Option(str, description="Links go here. An image can be pasted or uploaded in the optional attachment field"),
                 attachment: Option(Attachment, description="Image or video", required=False)):
    user = get_user_info(str(ctx.author.id), users)
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
    summary = f"> **Platform:** {platform.name}\n> **Game:** {game}\n> **Record:** {record}\n> **Evidence:**\n> {evidence}\n"
    if attachment is not None:
        interaction: discord.Interaction = await ctx.respond((summary + f"Your submission will be reviewed! <@{ctx.author.id}>"), file=await attachment.to_file())
    else:
        interaction: discord.Interaction = await ctx.respond(summary + f"Your submission will be reviewed! <@{ctx.author.id}>")

    # Get a link to the summary message
    message = await interaction.original_response()
    message_link = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"

    # Create the message for in the queue
    s_id = generate_random_id(queue)

    # Create the embed for in the queue
    embedVar = discord.Embed(title=f"New submission by {ctx.author.display_name}", description="", color=0xfecc52)
    embedVar.add_field(name="Details", value=f"**IGN:** {user['IGN']}\n**Platform:** {platform.name}\n**Game:** {game}\n[{user['IGN']}'s forumes profile]({user['forums']})", inline=False)
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
        "IGN": user[platform.name.lower()],
        "forums": user["forums"],
        "platform": platform.name,
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
    await changelog_channel.send(f"> {platform_emoji(submission['platform'])} {submission['platform']}\n> {submission['GM']}\n> {subMessage}\n> \n> `{prevholder} -> {submission['IGN']}`\n> \n> {submission['submissionMessage']}")

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
@bot.slash_command(guild_ids=guilds, description="Delete a record.")
async def cancel(ctx, scode):
    # Find the submission in the queue db
    submission = None
    for sub in queue["submissions"]:
        if sub["id"] == scode:
            submission = sub

    # If the submission is not found
    if submission == None:
        await ctx.respond(f"Submission {scode} was not found.")
        return
    
    # Check if user is admin or submission is from user
    if not (ctx.author.guild_permissions.administrator or ctx.author.id == submission['Uid']):
        await ctx.respond("You can only cancel your own submission.")
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


connect = bot.create_group("connect", "Connect your Discord to your IGN and forums account.", guilds)

@connect.command(description="Connect your Discord to your CubeCraft forums account.")
async def forums(ctx, forums_link: Option(str, "link to your forums page")):

    # Check if the right link was used
    if not forums_link[0:len(cubecraft_link)] == cubecraft_link:
        await ctx.respond("Please use the link to your members page, it looks like:\nhttps://www.cubecraft.net/members/naitzirch.375456/")
        return
    
    user = {
        "id": str(ctx.author.id),
        "forums": forums_link,
        "java": "",
        "bedrock": ""
    }

    # Check if user already connected their account
    old_profile = get_user_info(str(ctx.author.id), users)

    msg = "Successfully connected your Forums account!"
    if old_profile is not None:
        user.update({"java": old_profile["java"]})
        user.update({"bedrock": old_profile["bedrock"]})
        if old_profile["forums"] != "":
            msg = "Successfully updated your account details."
        users.remove(old_profile)

    users.append(user)
    db_json.save()

    await ctx.respond(msg)

@connect.command(description="Connect your Discord Minecraft account.")
async def minecraft(ctx, platform: Option(Enum('Platform', ['Java', 'Bedrock']), "Platform type"), ign: Option(str, "Your in-game name")):

    user = {
        "id": str(ctx.author.id),
        "forums": "",
        "java": "",
        "bedrock": ""
    }

    # Check if user already connected their account
    old_profile = get_user_info(str(ctx.author.id), users)

    msg = f"Successfully connected your {platform.name} account! " + platform_emoji(platform.name)
    if old_profile is not None:
        user.update({"forums": old_profile["forums"]})
        user.update({"java": old_profile["java"]})
        user.update({"bedrock": old_profile["bedrock"]})
        if old_profile[platform.name.lower()] != "":
            msg = f"Successfully updated your {platform.name} account details."
        users.remove(old_profile)

    user.update({platform.name.lower(): ign})

    users.append(user)
    db_json.save()

    await ctx.respond(msg)


# run the bot
bot.run(botInfo["token"])