from helperfunctions import get_hash
from helperfunctions import get_user_info

async def register_impl(ctx, bot, platform, game, record_name, mode, discord_id, evidence_link, db_json, record_db_json, users, records):
    response_string = "Added new record:"
    record_id = get_hash(platform, game, record_name)
    evidence_id = evidence_link[29:] # remove discord domain part

    # In case the discord tag was used as input, extract the id
    if discord_id[:2] == "<@":
        discord_id = discord_id[2:-1]

    record = {
        "platform": platform.name,
        "game": game,
        "mode": mode,
        "record": record_name,
        "record_holder": discord_id,
        "evidence": evidence_id
    }
    
    records[record_id] = record
    record_db_json.save(indent=2)

    user = get_user_info(discord_id, users)
    if user:
        user_records = user.get("records")
        if user_records:
            if record_id not in user_records:
                user["records"].append(record_id)
            else:
                response_string = "Updated record:"
        else:
            user["records"] = [record_id]
        db_json.save(indent=2)

    summary = f'''\n> **Platform:** {platform.name}
                    > **Game:** {game}
                    > **Mode:** {mode if mode else "N/A"}
                    > **Record:** {record_name}
                    > **Holder:** {"<@"+str(discord_id)+">" if discord_id else "N/A"}
                    > **Evidence:** { "https://discord.com/channels/" + evidence_id if evidence_id else "N/A"}
-# RID: {record_id}'''

    response_string += summary

    await ctx.respond(response_string)

