import discord
from helperfunctions import *

async def disc_impl(ctx, bot, other_user, users):
    discord_id = other_user.id if other_user else ctx.author.id # gives int type id

    # Get user info by looking in the db for discord id
    user = get_user_info(str(discord_id), users)

    if user == None:
        if other_user == None:
            await ctx.respond("Please connect your account using `/connect` to view your stats!")
            return
        await ctx.respond("This person has not connected their account 🥲")
        return

    disc_user = bot.get_user(discord_id)
    guild_member = ctx.guild.get_member(discord_id)
    forums = forums_link(user)

    # Get external data of this player
    df = get_ext_player_data()

    # Filter the df based on platform. 3 cases: either both networks, java or bedrock
    ign_j = user["java"]
    ign_b = user["bedrock"]
    platform = ""
    xpd = pd.DataFrame()
    if ign_j != "" and ign_b != "":
        platform = "Java & Bedrock"
        df_temp = df.loc[df['Platform'].isin(['Java & Bedrock', ''])]
        # Get row index of this player (we need the row below it as well in this case)
        ri = df_temp.index[(df_temp['Player'].str.lower() == ign_j.lower()) & (df_temp["Platform"] == "Java & Bedrock")].to_list()
        if ri:
            xpd = df_temp.loc[ri[0]:ri[0]+1, :]
    if ign_j != "" and xpd.empty:
        platform = "Java"
        df_temp = df.loc[df['Platform'].isin(['Java'])]
        xpd = df_temp.loc[df_temp['Player'].str.lower() == ign_j.lower()]
        xpd.loc[len(xpd)] = ['', '', '', '', '', '', '', ''] # append a second empty row for the "bedrock" part
    if ign_b != "" and (xpd.empty or xpd["Position"].values[0] == ""):
        platform = "Bedrock"
        df_temp = df.loc[df['Platform'].isin(['Bedrock'])]
        xpd = df_temp.loc[df_temp['Player'].str.lower() == ign_b.lower()]
        xpd.loc[-1] = ['', '', '', '', '', '', '', ''] # prepend a second empty row for the "java" part

    description = ""
    description += f"**Java:** {ign_j}\n".replace("_", "\_")
    description += f"**Bedrock:** {ign_b}\n".replace("_", "\_")

    position = "_"
    if len(xpd) == 2:
        platform = xpd['Platform'].values[0]
        position = int(xpd['Position'].values[0])
        records = xpd['Records'].values[0]
        OCR = xpd['OCR'].values[0] + "\n" + xpd['OCR'].values[1]
        LCR = xpd['LCR'].values[0] + "\n" + xpd['LCR'].values[1]
        
        description += f"**Platforms:** {platform}\n"
        description += f"**Position:** # {position}\n"
        description += f"**Records:** {records}\n\n"
        description += f"**Latest Record:**\n{LCR}\n"
        description += f"**Oldest Record:**\n{OCR}\n\n"
    else:
        description += f"**Platforms:** {platform}\n"
        description += f"**Records:** 0\n\n"

    description += f"{forums}"

    # Fancy colours for top 3
    colour = guild_member.roles[-1].colour
    if position == 1:
        colour = discord.Colour.gold()
    if position == 2:
        colour = discord.Colour.from_rgb(192,192,192)
    if position == 3:
        colour = discord.Colour.orange()

    embed = discord.Embed(
        title=f"{disc_user.display_name}'s user info",
        description=description,
        color=colour
    )
 
    embed.set_author(name="CCGRC", icon_url=ctx.guild.icon.url)

    if ign_j == '':
        ign_j = 'bedrock'

    embed.set_thumbnail(url=f"https://mc-heads.net/head/{ign_j.lower()}")

    if disc_user:
        embed.set_footer(text=f"{discord_id}", icon_url=disc_user.display_avatar)
    elif discord_id:
        embed.set_footer(text=f"{discord_id}")

    await ctx.respond(embed=embed)