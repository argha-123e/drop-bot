import time
import asyncio
import random
import discord

from utils.data_utils import update_drop_data
from utils.constants import *

# Emoji's (bots own emojis to use)
CONFETTI_EMOJI = discord.PartialEmoji(
    name='confetti', id=1438155456823431343, 
    animated=True 
    ) # link https://cdn.discordapp.com/emojis/1437356632723165244.webp?size=96&animated=true


async def start_giveaway(self, channel, winners, giveaway_duration, PRIZE, is_chat_drop: bool, pay_channel):
        self.gwy_running += 1
        
        if isinstance(PRIZE, str):
            prize = PRIZE
        elif type(PRIZE) == int:
            prize = f"{PRIZE:,} OWO"

        end_time = int(time.time()) + (int(giveaway_duration * 60) - 4)
        embed = discord.Embed(
            title="Giveaway Started! <a:confetti:1438155456823431343>",
            description=f"Prize **{prize}**\nWinners: {winners}\nEnds: <t:{end_time}:R>\n\nReact with <a:confetti:1438155456823431343> to join!",
            color=MAIN_COLOR
        )
        embed.set_footer(text=f"Picking winner in {giveaway_duration} minutes!")
        msg = await channel.send(embed=embed)

        # add reaction to gwy msg so ppls can react on it to join
        await msg.add_reaction(CONFETTI_EMOJI)
        

        giveaway_msg = msg  # store it for later

        await asyncio.sleep(int(giveaway_duration * 60)) # sleep for the duration

        msg = await channel.fetch_message(msg.id)
        reaction = discord.utils.get(msg.reactions, emoji=CONFETTI_EMOJI)

        if not reaction:
            print("reactions not found")
            try:
                await giveaway_msg.reply("❌ No reactions. Giveaway canceled.")
                result_embed_edit = discord.Embed(
                    title="Giveaway Ended! <a:confetti:1438155456823431343>",
                    description=f"❌ No reactions. Giveaway canceled.",
                    color=ERROR_COLOR
                    )
                await msg.edit(embed=result_embed_edit)
            except:
                print("drop msg not found")
                self.gwy_running -= 1
            return False
        users = [user async for user in reaction.users() if not user.bot]
        users = [u for u in users if not u.bot]  # Remove bots

        if not users:
            print("users not found")
            self.gwy_running -= 1

            try:
                await giveaway_msg.reply("❌ No valid users entered.")
                result_embed_edit = discord.Embed(
                title="Giveaway Ended! <a:confetti:1438155456823431343>",
                description=f"❌ No valid users entered.",
                color=ERROR_COLOR)
                await msg.edit(embed=result_embed_edit)
            except:
                print("drop msg not found")
            return False

        winners_list = random.sample(users, min(winners, len(users)))

        winner_mention = f""
        for winner in winners_list:
            winner_mention = winner_mention + f"{winner.mention} "

        

        # suppose winners_list is a list of Member objects or IDs
        winner_ids = [w.id if hasattr(w, "id") else int(w) for w in winners_list]

        if is_chat_drop:
            update_drop_data(self.db, giveaway_msg.guild.id, PRIZE, winner_ids)
            
            await pay_channel.send(f"{winner_mention}won **{prize}**", allowed_mentions=discord.AllowedMentions(users=False))


        result_embed = discord.Embed(
            title="🎊 Winner!",
            description=f"congratulations you have won **{prize}** <a:confetti:1438155456823431343>",
            color=SUCCESS_COLOR
        )
        
        if giveaway_msg:
            try:
            # ✅ Confirm the message still exists on Discord
                find_msg = await giveaway_msg.channel.fetch_message(giveaway_msg.id)
            except discord.NotFound:
                print("⚠️ Giveaway message not found (deleted?)")
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
        try:
            await msg.edit(embed=result_embed_edit)
        except:
            print("gwy msg not found")

        self.gwy_running -= 1
        return True