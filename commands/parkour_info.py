import json
import discord
from datetime import datetime

from helperfunctions import from_millis
from helperfunctions import make_path
from helperfunctions import get_data_from_path


async def parkour_info_impl(ctx, platform, mode, map_name, level, parkour_db_json, users, message=None):
    parkour_db = parkour_db_json.data

    identifier = "Platform:\nMap:\nLevel:\nDifficulty:"
    identifier_value = f"{platform}\n{map_name}\n{level}\n{mode}"
    try:
        level = parkour_db[platform][mode][map_name][level]
    except:
        await ctx.respond("This map or level does not exist", ephemeral=True)
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

    dates = [datetime.fromisoformat(time).strftime("`%d/%m/%y`") for time in times]
    evidence = ["https://discord.com/channels/" + e for e in evidence]
    date_evidence = list(zip(dates, evidence))
    date_evidence = [de[0] + "          " + de[1] for de in date_evidence]
    if not date_evidence: date_evidence = ["N/A　　　N/A"]
    
    with open("textures.json", "r") as f:
        textures = json.load(f)
        texture = get_data_from_path(textures, make_path(platform, "Game", "Parkour", "Mode", mode, "map_name", map_name))
        if texture == {}:
            texture = get_data_from_path(textures, make_path(platform, "Game", "Parkour", "Default"))
        embed_color = discord.Colour(int(get_data_from_path(textures, make_path(platform, "Game", "Parkour", "Mode", mode, "color"))))

    embed = (
        discord.Embed(
            title="Parkour Info",
            description=message,
            color=embed_color,
        )
        .add_field(name="Identifier", value=identifier)
        .add_field(name="Value"     , value=identifier_value)
        .add_field(name="‎", value="‎")
        .add_field(name="Holder(s)", value="`" + "`\n`".join(holders) + "`")
        .add_field(name="Score", value="`" + "`\n`".join(scores) + "`")
        .add_field(name="Date         Evidence", value="\n".join(date_evidence))
        .set_thumbnail(url=texture)
    )

    await ctx.respond(embed=embed)