from helperfunctions import get_user_info
from helperfunctions import make_path

async def register_impl(ctx, bot, platform, mode, map_name, level, value, discord_id, evidence_link, db_json, parkour_db_json, users):
    parkour_db = parkour_db_json.data

    response_string = "Added new record:"
    evidence_id = evidence_link[29:] # remove discord domain part

    # In case the discord tag was used as input, extract the id
    if discord_id[:2] == "<@":
        discord_id = discord_id[2:-1]

    # create record object to store
    parkour_record = {
        "record_holder": discord_id,
        "value": value,
        "evidence": evidence_id
    }
    
    # Traverse and create missing keys
    parkour_db[platform][mode].setdefault(map_name, {})
    parkour_db[platform][mode][map_name][level] = parkour_record
    # store record object
    parkour_db_json.save(indent=2)

    # if user is specified then add record to user's list of records
    user = get_user_info(discord_id, users)
    record_path = make_path(platform,mode,map_name,level)
    if user:
        user_records = user.get("parkour_records")
        if user_records:
            if record_path not in user_records:
                user["parkour_records"].append(record_path)
        else:
            user["records"] = [record_path]
        db_json.save(indent=2)

    summary = f'''\n> **Platform:** {platform}
                    > **Game:** Parkour
                    > **Mode:** {mode if mode else "N/A"}
                    > **Record:** {map_name} {level}
                    > **Holder:** {"<@"+str(discord_id)+">" if discord_id else "N/A"}
                    > **Evidence:** { "https://discord.com/channels/" + evidence_id if evidence_id else "N/A"}
-# debug: {record_path}'''

    response_string += summary

    await ctx.respond(response_string)

