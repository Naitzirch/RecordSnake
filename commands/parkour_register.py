from helperfunctions import get_user_info
from helperfunctions import make_path

async def register_impl(ctx, bot, platform, mode, map_name, level, discord_ids, value, evidence_links, db_json, parkour_db_json, users):
    parkour_db = parkour_db_json.data

    response_string = "Added new record:"
    
    discord_ids = discord_ids.split(",")
    # In case the discord tag was used as input, extract the id
    discord_ids = [discord_id[2:-1] if discord_id[:2] == "<@" else discord_id for discord_id in discord_ids]
    
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
    if evidence_links:
        evidence_ids = [evidence_link[29:] for evidence_link in evidence_links.split(",")] # remove discord domain part
        # Get evidence time-stamp
        id_lists = [evidence_id.split("/") for evidence_id in evidence_ids] # Split id lists into guild, channel and msg id
        # evi_channels = [bot.get_channel(int(id_list[1])) for id_list in id_lists]
        msgs = [await id_list[1].fetch_message(int(id_list[2])) for id_list in id_lists]
        time_stamps = [msg.created_at.isoformat() for msg in msgs]


    # create record object to store
    parkour_record = {
        "record_holders": [],
        "value": value,
        "evidence": [],
        "time": []
    }
    
    # Traverse and create missing keys
    parkour_db[platform][mode].setdefault(map_name, {})
    old_parkour_record = parkour_db[platform][mode][map_name].get(level, {})
    old_value = old_parkour_record.get("value", 0)
    record_holders = parkour_record["record_holders"]
    evidence = parkour_record["evidence"]
    time = parkour_record["time"]
    if 0 < old_value == value: # record equals old
        record_holders.extend(discord_ids)
        evidence.extend(evidence_ids)
    else: # record not set / beaten
        record_holders = discord_ids
    


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

