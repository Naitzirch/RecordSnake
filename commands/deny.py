import discord
async def deny_impl(ctx, bot, scode, feedback, botInfo, queue_json, queue):
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