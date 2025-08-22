from helperfunctions import get_user_info
from helperfunctions import make_path
from helperfunctions import to_millis
from helperfunctions import from_millis

from commands.parkour_info import parkour_info_impl

def summary(platform, mode, map_name, level, record_holders, scores, evidence, record_path):
    # Create response message
    summary = f'''\n> **Platform:** {platform}
                    > **Game:** Parkour
                    > **Mode:** {mode}
                    > **Record:** {map_name} {level}
                    > **Holder(s):** {["<@"+str(discord_id)+">" for discord_id in record_holders] if record_holders else "N/A"}
                    > **Score:** {[from_millis(score) for score in scores] if scores else 'N/A'}
                    > **Evidence:** { ["https://discord.com/channels/" + evidence_id for evidence_id in evidence] if evidence else "N/A"}
-# debug: {record_path}'''
    return summary

def add_record_to_user(record_path, discord_id, db_json, users):
    # Add records to the record holders in the user db
    # if user specified then add record to user's list of records
    user = get_user_info(discord_id, users)
    if user:
        user_records = user.setdefault("parkour_records", [])
        if record_path not in user_records:
                user_records.append(record_path)
        else:
            user_records.remove(record_path).append(record_path)
        db_json.save(indent=4)

async def register_impl(ctx, bot, platform, mode, map_name, level, discord_id, score, evidence_link, db_json, parkour_db_json, users):
    parkour_db = parkour_db_json.data

    response_string = "✅ Added new record"
    
    # In case the discord tag was used as input, extract the id
    try:
        if discord_id:
            discord_id = [discord_id[2:-1]] if discord_id[:2] == "<@" else [discord_id]
        else:
            discord_id = []
    except Exception as e:
        await ctx.respond(f"`discord_id` only accepts a discord ID or tag\n-# {e}", ephemeral=True)
        return
    
    # convert value in format mm:ss:ttt to thousands of a second
    # Example: "01:23:456" -> 1*60*1000 + 23*1000 + 456 = 83456
    try:
        if score:
            score = [to_millis(score)]
        else:
            score = []
    except Exception as e:
        await ctx.respond(e, ephemeral=True)
        return
    

    evidence_id = []
    time_stamp  = []
    try:
        if evidence_link:
            evidence_id = [evidence_link[29:]] # remove discord domain part
            # Get evidence time-stamp
            id_list = evidence_id[0].split("/") # Split id lists into guild, channel and msg id
            channel = bot.get_channel(int(id_list[1]))
            msg = await channel.fetch_message(int(id_list[2]))
            time_stamp = [msg.created_at.isoformat()]
    except Exception as e:
        await ctx.respond(f"`evidence_link` must use format `https://discord.com/channels/000000000000000000/000000000000000000/0000000000000000000`\n-# {e}", ephemeral=True)
        return

    # create record object to store
    parkour_record = {
        "record_holders": [],
        "score": [],
        "evidence": [],
        "time": []
    }
    
    # Traverse and create missing keys
    parkour_db[platform][mode].setdefault(map_name, {})
    parkour_record = parkour_db[platform][mode][map_name].setdefault(level, parkour_record)

    # Generate path name for storing record under the user id
    record_path = make_path(platform,mode,map_name,level)

    # Record not set OR beaten
    try:
        if not parkour_record["score"] or score[0] < parkour_record["score"][0]:
            # remove old record holders' records in the users table
            old_holders = [ parkour_record["record_holders"][i] for i, s in enumerate(parkour_record["score"]) if s == parkour_record["score"][0] ]
            for id in old_holders:
                users[id]["parkour_records"].remove(record_path)
            
            # prepend id, score, evidence and time
            parkour_record["record_holders"] = discord_id + parkour_record["record_holders"]
            parkour_record["score"]          = score + parkour_record["score"]
            parkour_record["evidence"]       = evidence_id + parkour_record["evidence"]
            parkour_record["time"]           = time_stamp + parkour_record["time"]

            if discord_id: add_record_to_user(record_path, discord_id[0], db_json, users)
        # Record set and not beaten
        else:
            # if the score was tied, add a record to the user
            if score[0] == parkour_record["score"]: add_record_to_user(record_path, discord_id[0], db_json, users)

            # Here we have to add record_holders, score, evidence and time to their respective lists
            # and sort them, first based on score, then based on oldest time.
            parkour_record["record_holders"].extend(discord_id)
            parkour_record["score"].extend(score)
            parkour_record["evidence"].extend(evidence_id)
            parkour_record["time"].extend(time_stamp)

            # Zip all lists together for sorting
            combined = list(zip(
                parkour_record["record_holders"],
                parkour_record["score"],
                parkour_record["evidence"],
                parkour_record["time"]
            ))

            # Sort by score, then by time_stamp (oldest first)
            combined.sort(key=lambda x: (x[1], x[3]))

            # Unzip back to individual lists
            parkour_record["record_holders"], parkour_record["score"], parkour_record["evidence"], parkour_record["time"] = map(list, zip(*combined))
    except Exception as e:
        await ctx.respond(f"`discord_id`, `score` and `evidence_link` can not be empty once the record has been claimed.\n-# {e}")
        return
    
    # store record object
    parkour_db_json.save(indent=4)


    await parkour_info_impl(ctx, platform, mode, map_name, level, parkour_db_json, users, response_string)

