from helperfunctions import *
async def minecraft_impl(ctx, platform, ign, users, db_json):

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