from helperfunctions import platform_emoji
from helperfunctions import get_user_info

from commands.parkour_register import register_impl

async def send_submitter_reply(bot, botInfo, submission, beaten):
    subMessage = submission["message"][0:47]
    if len(submission["message"]) > 47:
        subMessage = subMessage + "..."
    
    if (submission["submissionMessage"]):
        linkToSubmission = f"\nLink to your submission: {submission['submissionMessage']}"

    feedback_channel = bot.get_channel(int(botInfo["feedbackChannelID"]))
    if beaten:
        reply = f"✅ <@{submission['Uid']}> Your {submission['GM']} submission for \"{subMessage}\" has been accepted!{linkToSubmission}"
    else:
        reply = f"☑️ <@{submission['Uid']}> You didn't beat the record, but your {submission['GM']} submission for \"{subMessage}\" has been added to the scoreboard!{linkToSubmission}"
    await feedback_channel.send(reply)

async def send_changelog(bot, botInfo, submission, prevholder, custom_new_holder):
    new_holder = submission["IGN"]
    if custom_new_holder:
        new_holder = custom_new_holder
    changelog_channel = bot.get_channel(int(botInfo["changelogChannelID"]))

    subMessage = submission["message"][0:47]
    await changelog_channel.send(
        f"> {platform_emoji(submission['platform'])} {submission['platform']}\n\
        > {submission['GM']}\n\
        > {subMessage}\n\
        > \n\
        > `{prevholder} -> {new_holder}`\n\
        > \n> {submission['submissionMessage']}"
    )

async def accept_impl(ctx, bot, scode, prevholders, newholders, botInfo, queue_json, queue, db_json, parkour_db_json, users):

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

    beaten = True
    if submission["GM"] == "Parkour Best times":
        message = submission["message"]
        beaten, prevholders, newholders = await register_impl(
            ctx,
            bot,
            *message.split("."),
            str(submission["Uid"]),
            submission["score"],
            submission["submissionMessage"],
            db_json,
            parkour_db_json,
            users
        )
        platform = submission["platform"]
        prevholders = " ".join([users.get(prevholder, {}).get(platform.lower(), "Not Connected") for prevholder in prevholders]) if prevholders else "N/A"
        newholders = " ".join([users.get(newholder, {}).get(platform.lower(), "Not Connected") for newholder in newholders]) if newholders else "N/A"

    # send accept message
    await send_submitter_reply(bot, botInfo, submission, beaten)

    # update the changelog
    if beaten: await send_changelog(bot, botInfo, submission, prevholders, newholders)

    # Send reply to the reviewer that submitted the record
    await ctx.respond(f"Submission {scode} accepted")