import discord
from helperfunctions import *

async def submit_impl(ctx, bot, platform, game, record, evidence, attachment, botInfo, users, db_json, queue_json, queue, score=""):
    if game.lower() == "parkour" and score == "":
        await ctx.respond("Use `/parkour submit` for Parkour submissions :)")
        return
    
    user = get_user_info(str(ctx.author.id), users)
    # Check if the user has connected their account.
    if (user == None):
        await ctx.respond("Use /connect to connect your account before making a submission.")
        return
    
    platform_IGN = user[platform.lower()]
    if platform_IGN == "":
        await ctx.respond(f"You haven't connected your {platform} account yet!")
        return
    
    # Check if the queue isn't full
    if queue["inqueue"] >= 9999:
        await ctx.respond("Queue full, wait for submissions to be reviewed.")
        return

    s_id = generate_random_id(queue)

    # Send a summary of the submission in the submission channel
    summary = f"> **Platform:** {platform}\n> **Game:** {game}\n> **Record:** {record}\n {f'> **Score:** {score}\n' if score else ''}> **Evidence:**\n> {evidence}\n"
    summary += f"Your submission will be reviewed! <@{ctx.author.id}>\n-# To cancel this submission use code: {s_id}"
    if attachment is not None:
        try:
            result = await attachment.to_file()
        except Exception as e:
            print(f"Error: {e}")
        else:
            interaction: discord.Interaction = await ctx.respond(summary, file=result)
            print("Function executed successfully")
    else:
        interaction: discord.Interaction = await ctx.respond(summary)

    # Get a link to the summary message
    message = await interaction.original_response()
    message_link = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"

    # Create the message for in the queue

    # Create the embed for in the queue
    description = f"<@{ctx.author.id}>\n**IGN:** {platform_IGN}\n**Platform:** {platform}\n**Game:** {game}\n{forums_link(user, platform_IGN)}"
    embedVar = discord.Embed(title=f"New submission from:", description=description, color=0xfecc52)
    #embedVar.add_field(name="Details", value=f"", inline=False)
    embedVar.add_field(name="Record", value=record, inline=False)
    if score:
        embedVar.add_field(name=f"Score: {score}", value="", inline=False)
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
        "IGN": platform_IGN,
        "forums": user["forums"],
        "platform": platform,
        "GM": game,
        "message": record,
        "score": score
    }

    queue["submissions"].append(submission)
    queue["inqueue"] += 1
    queue_json.save(indent=2)

    # update submission count
    botInfo["submissions"] += 1
    db_json.save(indent=2)