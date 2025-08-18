from helperfunctions import *
async def minecraft_impl(ctx, platform, ign, users, db_json):

    user = {
        "forums": "",
        "java": "",
        "bedrock": ""
    }

    # Check if user already connected their account
    old_profile = get_user_info(str(ctx.author.id), users)


    msg = f"Successfully connected your {platform.name} account! " + platform_emoji(platform.name)
    if old_profile is not None:
        user["forums"] = old_profile["forums"]
        user["java"] = old_profile["java"]
        user["bedrock"] = old_profile["bedrock"]
        if old_profile[platform.name.lower()] != "":
            msg = f"Successfully updated your {platform.name} account details."

    user[platform.name.lower()] = ign

    users[str(ctx.author.id)] = user
    db_json.save()

    await ctx.respond(msg)