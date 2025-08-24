from commands.submit import submit_impl
from helperfunctions import make_path
from helperfunctions import to_millis

async def submit_parkour_impl(ctx, bot, platform, mode, map_name, level, score, evidence, botInfo, users, db_json, queue_json, queue):
    # check if score is in the right format
    try:
        value = to_millis(score)
    except Exception:
        await ctx.respond("Invalid time format, use mm:ss:ttt e.g. 01:23:456 for 1 minute 23 seconds and 456 thousands", ephemeral=True)
        return
    
    game = "Parkour Best times"
    record = make_path(platform, mode, map_name, level)
    attachment = None
    
    await submit_impl(ctx, bot, platform, game, record, evidence, attachment, botInfo, users, db_json, queue_json, queue, score)