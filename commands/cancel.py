async def cancel_impl(ctx, bot, scode, botInfo, queue_json, queue):
    # Find the submission in the queue db
    submission = None
    for sub in queue["submissions"]:
        if int(sub["id"]) == scode:
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