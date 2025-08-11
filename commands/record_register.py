from helperfunctions import get_hash
from helperfunctions import get_user_info

async def register_impl(ctx, bot, platform, game, record_name, mode, discord_id, evidence_id, record_db_json, users, records):
    record_id = get_hash(platform, game, record_name)

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
    print(user)


    await ctx.respond("Hi")

