from helperfunctions import platform_emoji
async def accept_impl(ctx, bot, scode, prevholder, newholder, botInfo, queue_json, queue):

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
    new_holder = submission["IGN"]
    if newholder:
        new_holder = newholder
    changelog_channel = bot.get_channel(int(botInfo["changelogChannelID"]))

    await changelog_channel.send(f"> {platform_emoji(submission['platform'])} {submission['platform']}\n> {submission['GM']}\n> {subMessage}\n> \n> `{prevholder} -> {new_holder}`\n> \n> {submission['submissionMessage']}")

    # Send reply to the reviewer that submitted the record
    await ctx.respond(f"Submission {scode} accepted")