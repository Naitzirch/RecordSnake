from helperfunctions import get_user_info
async def forums_impl(ctx, forums_link, users, db_json, cubecraft_link):
    # Check if the right link was used
    if not forums_link[0:len(cubecraft_link)] == cubecraft_link:
        await ctx.respond("Please use the link to your members page, it looks like:\nhttps://www.cubecraft.net/members/naitzirch.375456/")
        return
    
    user = {
        "forums": forums_link,
        "java": "",
        "bedrock": ""
    }

    # Check if user already connected their account
    old_profile = get_user_info(str(ctx.author.id), users)

    msg = "Successfully connected your Forums account!"
    if old_profile is not None:
        user["java"] = old_profile["java"]
        user["bedrock"] = old_profile["bedrock"]
        if old_profile["forums"] != "":
            msg = "Successfully updated your account details."

    users[str(ctx.author.id)] = user
    db_json.save()

    await ctx.respond(msg)