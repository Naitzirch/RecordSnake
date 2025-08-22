import discord
from datetime import datetime

from helperfunctions import from_millis

async def parkour_info_impl(ctx, platform, mode, map_name, level, parkour_db_json, users):
    parkour_db = parkour_db_json.data

    identifier = "Platform:\nMap:\nLevel:\nDifficulty:"
    identifier_value = f"{platform}\n{map_name}\n{level}\n{mode}"
    try:
        level = parkour_db[platform][mode][map_name][level]
    except:
        ctx.respond("This map or level does not exist", ephemeral=True)
        return

    try:
        holders = level["record_holders"]
        scores  = level["score"]
        times   = level["time"]
        evidence= level["evidence"]
        holders = [users[id][platform.lower()] for id in holders]
        scores  = [from_millis(score) for score in scores]
        if not holders: holders = ["N/A"]
        if not scores: scores = ["N/A"]
    except Exception as e:
        await ctx.respond(f"Something went wrong retrieving this level's information.\n-# {e}")
        return

    dates = [datetime.fromisoformat(time).strftime("%d/%m/%y") for time in times]
    evidence = ["https://discord.com/channels/" + e for e in evidence]
    date_evidence = list(zip(dates, evidence))
    date_evidence = [de[0] + "          " + de[1] for de in date_evidence]
    
    embed = (
        discord.Embed(
            title="Parkour Info",
            color=discord.Colour.blue(),
        )
        .add_field(name="Identifier", value=identifier)
        .add_field(name="Value"     , value=identifier_value)
        .add_field(name="‎", value="‎")
        .add_field(name="Holder(s)", value="\n".join(holders))
        .add_field(name="Score", value="\n".join(scores))
        .add_field(name="Date         Evidence", value="\n".join(date_evidence))
        .set_thumbnail(url="https://minecraft.wiki/images/Golden_Boots_(item)_JE3_BE3.png")
    )

    await ctx.respond(embed=embed)