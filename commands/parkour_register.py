from helperfunctions import get_user_info
from helperfunctions import make_path

async def register_impl(ctx, bot, platform, mode, map_name, level, discord_id, value, evidence_link, db_json, parkour_db_json, users):
    parkour_db = parkour_db_json.data

    response_string = "Added new record:"
    
    # In case the discord tag was used as input, extract the id
    if discord_id[:2] == "<@":
        discord_id = discord_id[2:-1]
    
    # convert value in format mm:ss:ttt to thousands of a second
    # Example: "01:23:456" -> 1*60*1000 + 23*1000 + 456 = 83456
    try:
        minutes, seconds, millis = value.split(":")
        total_millis = int(minutes) * 60 * 1000 + int(seconds) * 1000 + int(millis)
        value = total_millis
    except Exception: # If format is invalid, inform the user
        await ctx.respond("Invalid time format, use mm:ss:ttt e.g. 01:23:456 for 1 minute 23 seconds and 456 thousands", ephemeral=True)
        return

    evidence_id = ""
    time_stamp = ""
    if evidence_link:
        evidence_id = evidence_link[29:] # remove discord domain part
        # Get evidence time-stamp
        id_list = evidence_id.split("/")
        evi_channel = bot.get_channel(int(id_list[1]))
        msg = await evi_channel.fetch_message(int(id_list[2]))
        time_stamp = msg.created_at.isoformat()


    # create record object to store
    parkour_record = {
        "record_holder": discord_id,
        "value": value,
        "evidence": evidence_id,
        "time": time_stamp
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

