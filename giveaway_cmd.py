import time
import asyncio
import random
import discord

from utils.constants import *

# Emoji's (bots own emojis to use)
if is_server:
    CONFETTI_EMOJI = discord.PartialEmoji(
        name='confetti', id=1438155456823431343, 
        animated=True 
        ) # link https://cdn.discordapp.com/emojis/1437356632723165244.webp?size=96&animated=true
else:
    # Emoji's (bots own emojis to use)
    CONFETTI_EMOJI = discord.PartialEmoji(
        name='confetti', id=1446197705415327874, 
        animated=True 
        )


def update_drop_data(db, server_id: int, PRIZE: int, winner_ids: list, msg_id: int, remark: str):
    import datetime
    drops = db.get_as_dict(table="drops", server_id=server_id, remark="entry")
    server = db.get_as_dict(table="servers", server_id=server_id)
    server = server[0]

    total_drops:int =  server["total_drops"]
    if total_drops == 0:
        total_drops = len(drops)

    total_prize:int = server["total_prize"]
    if total_prize == 0:
        for drop in drops:
            total_prize += drop["prize"]
    # increment totals
    total_drops += 1

    total_prize += PRIZE

    db.insert(
        table="drops",server_id=server_id , winner=winner_ids[0], prize=PRIZE, 
        time=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), remark=remark, msg_id=msg_id
        )
    db.update(
        table="servers", pk_name="server_id", pk_value=server_id, 
        total_drops=total_drops, total_prize=total_prize
    )

async def start_giveaway(self, channel, winners, giveaway_duration, PRIZE, is_chat_drop, pay_channel, prize_name):
    self.gwy_running = len(self._gwy_tasks)
    try:
        if isinstance(PRIZE, str):
            prize = PRIZE
        elif type(PRIZE) == int:
            prize = f"{PRIZE:,} {prize_name}"

        end_time = int(time.time()) + (int(giveaway_duration * 60))
        embed = discord.Embed(
            title="Giveaway Started! <a:confetti:1438155456823431343>",
            description=f"Prize: **{prize}**\nWinners: {winners}\nEnds: <t:{end_time}:R>\n\nReact with <a:confetti:1438155456823431343> to join!",
            color=MAIN_COLOR
        )
        embed.set_footer(text=footer_txt)
        msg = await channel.send(embed=embed)

        # add reaction to gwy msg so ppls can react on it to join
        await msg.add_reaction(CONFETTI_EMOJI)
        

        giveaway_msg = msg  # store it for later


        await asyncio.sleep(int(giveaway_duration * 60)) # sleep for the duration

        msg: discord.Message = await channel.fetch_message(msg.id)
        reaction = discord.utils.get(msg.reactions, emoji=CONFETTI_EMOJI)

        if not reaction:
            try:
                await giveaway_msg.reply("❌ No reactions. Giveaway canceled.")
                result_embed_edit = discord.Embed(
                    title="Giveaway Ended! <a:confetti:1438155456823431343>",
                    description=f"❌ No reactions. Giveaway canceled.",
                    color=ERROR_COLOR
                    )
                result_embed_edit.set_footer(text=footer_txt)
                await msg.edit(embed=result_embed_edit)
            except:
                self.gwy_running -= 1
            return False
        users = [user async for user in reaction.users() if not user.bot]
        users = [u for u in users if not u.bot]  # Remove bots

        if not users:
            self.gwy_running -= 1

            try:
                await giveaway_msg.reply("❌ No valid users entered.")
                result_embed_edit = discord.Embed(
                title="Giveaway Ended! <a:confetti:1438155456823431343>",
                description=f"❌ No valid users entered.",
                color=ERROR_COLOR)
                result_embed_edit.set_footer(text=footer_txt)
                await msg.edit(embed=result_embed_edit)
            except:
                pass
            return False

        winners_list = random.sample(users, min(winners, len(users)))

        winner_mention = f""
        for winner in winners_list:
            winner_mention = winner_mention + f"{winner.mention} "

        

        # suppose winners_list is a list of Member objects or IDs
        winner_ids = [w.id if hasattr(w, "id") else int(w) for w in winners_list]

        if is_chat_drop:
            update_drop_data(self.db, giveaway_msg.guild.id, PRIZE, winner_ids, msg.id, "entry")
            
            await pay_channel.send(f"giveaway msg link: {msg.jump_url}\n{winner_mention}won **{prize}**", allowed_mentions=discord.AllowedMentions(users=False))
        else:
            update_drop_data(self.db, giveaway_msg.guild.id, PRIZE, winners, msg.id, "/drop")


        result_embed = discord.Embed(
            title="🎊 Winner!",
            description=f"congratulations you have won **{prize}** <a:confetti:1438155456823431343>",
            color=SUCCESS_COLOR
        )
        result_embed.set_footer(text=footer_txt)
        
        if giveaway_msg:
            try:
            # ✅ Confirm the message still exists on Discord
                find_msg = await giveaway_msg.channel.fetch_message(giveaway_msg.id)
            except discord.NotFound:
                find_msg = None
        if find_msg:   
            await giveaway_msg.reply(
                content=winner_mention,
                embed=result_embed,
                allowed_mentions=discord.AllowedMentions(users=True))
        else:
            await channel.send(
                content=winner_mention,
                embed=result_embed,
                allowed_mentions=discord.AllowedMentions(users=True)
                )
        result_embed_edit = discord.Embed(
            title="Giveaway Ended! <a:confetti:1438155456823431343>",
            description=f"Participant(s): {len(users)}!\n{winner_mention} won **{prize}**",
            color=SUCCESS_COLOR
        )
        result_embed_edit.set_footer(text=footer_txt)
        try:
            await msg.edit(embed=result_embed_edit)
        except:
            pass

        return True
    except asyncio.CancelledError:
        # handle external cancellation cleanly
        try:
            await channel.send("(error) Giveaway cancelled. report in support server")
        except:
            pass
        raise
    finally:
        # cleanup: remove finished task from list
        self._gwy_tasks = [t for t in self._gwy_tasks if not t.done()]
        self.gwy_running = len(self._gwy_tasks)


async def reroll(self, message: discord.Message, msg_id):
    if not message.author.guild_permissions.administrator:
        return await message.reply("You can't use this cmd, this is admin only.")
    db = self.db

    # getting data's
    drops_data = db.get_as_dict(table="drops", msg_id=msg_id)[0]
    server_data = db.get_as_dict(table="servers", server_id=drops_data["server_id"])[0]

    # getting channel id
    channel_id = int(server_data["channel"])
    channel = self.get_channel(channel_id)

    pay_channel_id = int(server_data["pay_channel"])
    pay_channel = self.get_channel(pay_channel_id)

    # setting up is_chat_drop
    if drops_data["remark"] == "entry":
        is_chat_drop = True
    else:
        return message.reply("sorry, this feature isnt availble for user made drops using `/drop` (comming soon)")

    # setting up PRIZE
    PRIZE = drops_data["prize"]

    if isinstance(PRIZE, str):
        prize = PRIZE
    elif type(PRIZE) == int:
        prize_name = server_data["prize_name"]
        prize = f"{PRIZE:,} {prize_name}"

    # getting the gwy message
    msg = await channel.fetch_message(msg_id)
    reaction = discord.utils.get(msg.reactions, emoji=CONFETTI_EMOJI)

    if not reaction:
        try:
            await msg.reply("❌ No reactions. Giveaway canceled.")
            result_embed_edit = discord.Embed(
                title="Giveaway Ended! <a:confetti:1438155456823431343>",
                description=f"❌ No reactions. Giveaway canceled.",
                color=ERROR_COLOR
                )
            result_embed_edit.set_footer(text=footer_txt)
            await msg.edit(embed=result_embed_edit)
        except:
            self.gwy_running -= 1
        return False
    users = [user async for user in reaction.users() if not user.bot]
    users = [u for u in users if not u.bot]  # Remove bots

    if not users:
        self.gwy_running -= 1
        try:
            await msg.reply("❌ No valid users entered.")
            result_embed_edit = discord.Embed(
            title="Giveaway Ended! <a:confetti:1438155456823431343>",
            description=f"❌ No valid users entered.",
            color=ERROR_COLOR)
            result_embed_edit.set_footer(text=footer_txt)
            await msg.edit(embed=result_embed_edit)
        except:
            pass
        return False

    winners_list = random.sample(users, min(1, len(users)))

    winner_mention = f""
    for winner in winners_list:
        winner_mention = winner_mention + f"{winner.mention} "

    

    # suppose winners_list is a list of Member objects or IDs
    winner_ids = [w.id if hasattr(w, "id") else int(w) for w in winners_list]

    if is_chat_drop:
        update_drop_data(self.db, msg.guild.id, PRIZE, winner_ids, msg.id, "entry")
        
        await pay_channel.send(f"`rerolled` giveaway msg link: {msg.jump_url}\n{winner_mention}won **{prize}**", allowed_mentions=discord.AllowedMentions(users=False))
    else:
        update_drop_data(self.db, msg.guild.id, PRIZE, 1, msg.id, "/drop")


    result_embed = discord.Embed(
            title="🎊 Winner!",
            description=f"congratulations you have won **{prize}** <a:confetti:1438155456823431343>",
            color=SUCCESS_COLOR
        )
    result_embed.set_footer(text=footer_txt)
    
    if msg:
        try:
        # ✅ Confirm the message still exists on Discord
            find_msg = await msg.channel.fetch_message(msg.id)
        except discord.NotFound:
            find_msg = None
    if find_msg:   
        await msg.reply(
            content=winner_mention,
            embed=result_embed,
            allowed_mentions=discord.AllowedMentions(users=True))
    else:
        await channel.send(
            content=winner_mention,
            embed=result_embed,
            allowed_mentions=discord.AllowedMentions(users=True)
            )
    result_embed_edit = discord.Embed(
        title="Giveaway Ended! <a:confetti:1438155456823431343>",
        description=f"Participant(s): {len(users)}!\n{winner_mention} won **{prize}**",
        color=SUCCESS_COLOR
    )
    result_embed_edit.set_footer(text=footer_txt)
    try:
        await msg.edit(embed=result_embed_edit)
    except:
        pass
                