import discord
from discord.ext import commands
import asyncio
import os
import random
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

TOKEN = os.getenv("TOKEN")
SERVER_ID = int(os.getenv("SERVER_ID"))
TARGET_CHANNEL_ID = int(os.getenv("CHANNEL"))
MSG_NEEDED = int(os.getenv("MSG_NEEDED"))
PRIZE = int(os.getenv("PRIZE"))
# Embed Colors
MAIN_COLOR = 0x5865F2
SUCCESS_COLOR = 0x43FF33
ERROR_COLOR = 0xFF0000

# Giveaway timer(seconds)
GIVEAWAY_DURATION = 5

# Emoji's
CONFETI_EMOJI = discord.PartialEmoji(name='confeti', id=1437356994142142514, animated=True)


intents = discord.Intents.all()

class MyClient(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=".", intents=intents)
        self.msg_count = 0

    async def on_ready(self):
        await self.tree.sync()
        self.channel = self.get_channel(TARGET_CHANNEL_ID)
        if self.channel is None:
            print("❌ Channel not found!")
            return
        print(f"✅ Logged in as {self.user}")
    async def on_message(self, message):
        # block own/bot msgs
        if message.author.bot:
            return
        
        
        
        # only count messages in giveaway channel
        if message.channel.id == TARGET_CHANNEL_ID:
            self.msg_count += 1
            print(f" Count: {self.msg_count}/{MSG_NEEDED}")

            if self.msg_count >= MSG_NEEDED:
                self.msg_count = 0
                await self.start_giveaway(self.channel)

        await self.process_commands(message)

    async def start_giveaway(self, channel):
        embed = discord.Embed(
            title="<a:confeti:1437356994142142514> Giveaway Started! <a:confeti:1437356994142142514>",
            description=f"React with <a:confeti:1437356994142142514> to join!\n\n**Prize → __{PRIZE:,}__ OWO**",
            color=MAIN_COLOR
        )
        embed.set_footer(text=f"Picking winner in {GIVEAWAY_DURATION} seconds!")
        msg = await channel.send(embed=embed)
        self.last_giveaway_msg = msg  # store it for later

        await msg.add_reaction("<a:confeti:1437356994142142514>")

        await asyncio.sleep(GIVEAWAY_DURATION)

        msg = await channel.fetch_message(msg.id)
        reaction = discord.utils.get(msg.reactions, emoji=CONFETI_EMOJI)

        if not reaction:
            return await channel.send("❌ No reactions. Giveaway canceled.")
        users = [user async for user in reaction.users() if not user.bot]
        users = [u for u in users if not u.bot]  # Remove bots

        if not users:
            return await channel.send("❌ No valid users entered.")

        winner = random.choice(users)

        result_embed = discord.Embed(
            title="🎊 Winner!",
            description=f"{winner.name} won __**{PRIZE:,}**__ OWO <a:confeti:1437356994142142514><a:confeti:1437356994142142514>",
            color=SUCCESS_COLOR
        )

        if hasattr(self, "last_giveaway_msg") and self.last_giveaway_msg:
            try:
            # ✅ Confirm the message still exists on Discord
                find_msg = await self.last_giveaway_msg.channel.fetch_message(self.last_giveaway_msg.id)
            except discord.NotFound:
                print("⚠️ Giveaway message not found (deleted?)")
                find_msg = None
        if find_msg:   
            await self.last_giveaway_msg.reply(
                content=winner.mention,
                embed=result_embed,
                allowed_mentions=discord.AllowedMentions(users=True))
        else:
            await channel.send(
                content=winner.mention,
                embed=result_embed,
                allowed_mentions=discord.AllowedMentions(users=True)
                )
        self.last_giveaway_msg = None
client = MyClient()
client.run(TOKEN)
