from helperfunctions import get_user_info
from helperfunctions import make_path

def to_millis(time_str):
    """Convert mm:ss:ttt string to milliseconds. Raises ValueError if format is invalid."""
    minutes, seconds, millis = time_str.split(":")
    return int(minutes) * 60 * 1000 + int(seconds) * 1000 + int(millis)

def from_millis(millis):
    """Convert milliseconds to mm:ss:ttt string."""
    minutes = millis // (60 * 1000)
    millis %= (60 * 1000)
    seconds = millis // 1000
    millis %= 1000
    return f"{minutes:02}:{seconds:02}:{millis:03}"

def summary(platform, mode, map_name, level, record_holders, score, evidence, record_path):
    # Create response message
    summary = f'''\n> **Platform:** {platform}
                    > **Game:** Parkour
                    > **Mode:** {mode}
                    > **Record:** {map_name} {level}
                    > **Holder(s):** {["<@"+str(discord_id)+">" for discord_id in record_holders] if record_holders else "N/A"}
                    > **Score:** {from_millis(score)}
                    > **Evidence:** { ["https://discord.com/channels/" + evidence_id for evidence_id in evidence] if evidence else "N/A"}
-# debug: {record_path}'''
    return summary

async def register_impl(ctx, bot, platform, mode, map_name, level, discord_ids, value, evidence_links, db_json, parkour_db_json, users):
    parkour_db = parkour_db_json.data

    response_string = "✅ Added new record:"
    
    discord_ids = discord_ids.replace(" ", "").split(",") if discord_ids else [] # remove whitespace and turn string of ids into list
    # In case the discord tag was used as input, extract the id
    discord_ids = [discord_id[2:-1] if discord_id[:2] == "<@" else discord_id for discord_id in discord_ids]
    
    # convert value in format mm:ss:ttt to thousands of a second
    # Example: "01:23:456" -> 1*60*1000 + 23*1000 + 456 = 83456
    try:
        value = to_millis(value)
    except Exception:
        await ctx.respond("Invalid time format, use mm:ss:ttt e.g. 01:23:456 for 1 minute 23 seconds and 456 thousands", ephemeral=True)
        return

    evidence_ids = []
    time_stamps = []
    if evidence_links:
        evidence_ids = [evidence_link[29:] for evidence_link in evidence_links.replace(" ", "").split(",")] # remove white space and discord domain part
        # Get evidence time-stamp
        id_lists = [evidence_id.split("/") for evidence_id in evidence_ids] # Split id lists into guild, channel and msg id
        msgs = [await bot.get_channel(int(id_list[1])).fetch_message(int(id_list[2])) for id_list in id_lists]
        time_stamps = [msg.created_at.isoformat() for msg in msgs]


    # create record object to store
    parkour_record = {
        "record_holders": [],
        "value": 0,
        "evidence": [],
        "time": []
    }
    
    # Traverse and create missing keys
    parkour_db[platform][mode].setdefault(map_name, {})
    parkour_record = parkour_db[platform][mode][map_name].setdefault(level, parkour_record)

    # Generate path name for storing record under the user id
    record_path = make_path(platform,mode,map_name,level)

    if 0 < parkour_record["value"] == value: # record equals old

        # If the given holders are already in the record_holders list, update their evidence and time_stamp
        duplicate_id_idxs = []
        for id_idx in range(len(discord_ids)):
            try:
                pr_idx = parkour_record["record_holders"].index(discord_ids[id_idx])
                parkour_record["evidence"][pr_idx] = evidence_ids[id_idx]
                parkour_record["time"][pr_idx] = time_stamps[id_idx]
                duplicate_id_idxs.append(id_idx)
            except:
                pass
        # Then remove holders that were already in the list
        for i in duplicate_id_idxs:
            discord_ids.pop(i)
            evidence_ids.pop(i)
            time_stamps.pop(i)

        # update parkour_db
        parkour_record["record_holders"].extend(discord_ids)
        parkour_record["evidence"].extend(evidence_ids)
        parkour_record["time"].extend(time_stamps)
    elif value < parkour_record["value"] or parkour_record["value"] == 0: # record beaten / not set
        # remove old record holders' records in the users table
        for id in parkour_record["record_holders"]:
            users[id]["parkour_records"].remove(record_path)

        parkour_record["record_holders"] = discord_ids  # add new users in the parkour_db
        parkour_record["value"]          = value        # update value
        parkour_record["evidence"]       = evidence_ids # update evidence list
        parkour_record["time"]           = time_stamps  # update timestamps list
    else:
        parkour_db_json.save(indent=4)
        response_string = "❌ Something went wrong, current entry:"
        response_string += summary(platform, mode, map_name, level, parkour_record["record_holders"], parkour_record["value"], parkour_record["evidence"], record_path)
        response_string += "\nIf you meant to do this, maybe first try to delete the record using:\n"
        response_string += f"```/parkour delete platform:{platform} mode:{mode} map:{map_name} level:{level}```"
        await ctx.respond(response_string)
        return
    
    # store record object
    parkour_db_json.save(indent=4)

    # Add records to the record holders in the user db
    # if user specified then add record to user's list of records
    for discord_id in discord_ids:
        user = get_user_info(discord_id, users)
        if user:
            user_records = user.setdefault("parkour_records", [])
            if record_path not in user_records:
                    user_records.append(record_path)
            else:
                user_records = [record_path]
            db_json.save(indent=4)

    response_string += summary(platform, mode, map_name, level, parkour_record["record_holders"], value, parkour_record["evidence"], record_path)

    await ctx.respond(response_string)

