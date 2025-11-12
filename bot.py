import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os
import json
import random
import datetime
import tempfile
from dotenv import load_dotenv
import time

DATA_FILE = "data.json"

def load_data(path=DATA_FILE):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: failed to load {path}: {e} — returning empty dict")
        return {}
    
def atomic_save(path, data):
    dirn = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=dirn, prefix=".tmp_accounts_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)  # atomic replace
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass
def get_account(user_id):
    accounts = load_data()
    return accounts.get(str(user_id))

def update_data_helper(user_id, key, value):
    accounts = load_data()
    uid = str(user_id)

    if uid not in accounts:
        raise ValueError(f"Account {uid} not found")

    accounts[uid][key] = value
    atomic_save(DATA_FILE, accounts)
    return True

def update_data(self, key, value):
    update_data_helper(self.user_id, key, value)
    if key == "result":
        self.result = value
    elif key == "last_bet":
        self.last_bet = value
    elif key == "last_timestamp":
        self.timestamp = value


# Load .env variables
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Embed Colors
MAIN_COLOR = 0x5865F2
SUCCESS_COLOR = 0x43FF33
ERROR_COLOR = 0xFF0000

# Giveaway timer(seconds)
GIVEAWAY_DURATION = 0.334

# Emoji's (bots own emojis to use)
CONFETI_EMOJI = discord.PartialEmoji(name='confetti', id=1437356994142142514, animated=True) # link https://cdn.discordapp.com/emojis/1437356632723165244.webp?size=96&animated=true

intents = discord.Intents.all()

class MyClient(commands.Bot):
    def __init__(self, SERVER_ID, TARGET_CHANNEL_ID, PRIZE, MSG_NEEDED, prefix, PAY_CHANNEL):
        super().__init__(command_prefix=".", intents=intents)
        self.msg_count = 0
        self.TARGET_CHANNEL_ID = TARGET_CHANNEL_ID
        self.SERVER_ID = SERVER_ID
        self.PRIZE = PRIZE
        self.MSG_NEEDED = MSG_NEEDED
        self.prefix = prefix
        self.PAY_CHANNEL = PAY_CHANNEL

    async def on_ready(self):
        await self.tree.sync()
        self.channel = self.get_channel(self.TARGET_CHANNEL_ID)
        if self.channel is None:
            print("❌ general Channel not found!")
            return
        self.paychannel = self.get_channel(self.PAY_CHANNEL)
        if self.paychannel is None:
            print("❌pay Channel not found!")
            return
        
        await self.tree.sync()
        print("Slash commands synced ✅")

        print(f"✅ Logged in as {self.user}")
    async def on_message(self, message):
        # block own/bot msgs
        if message.author.bot:
            return
        
        # only count messages in giveaway channel
        if message.channel.id == self.TARGET_CHANNEL_ID:
            self.msg_count += 1
            print(f" Count: {self.msg_count}/{self.MSG_NEEDED}")

            if self.msg_count >= self.MSG_NEEDED:
                self.msg_count = 0
                await self.start_giveaway(self.channel, 1, GIVEAWAY_DURATION, f"{self.PRIZE:,} OWO")
                

        await self.process_commands(message)

    async def start_giveaway(self, channel, winners, giveaway_duration, prize: str):
        end_time = int(time.time()) + (int(giveaway_duration * 60)) + 2
        embed = discord.Embed(
            title="Giveaway Started! <a:confetti:1437356994142142514>",
            description=f"Prize **{prize}**\nWinners: {winners}\nEnds: <t:{end_time}:R>\n\nReact with <a:confetti:1437356994142142514> to join!",
            color=MAIN_COLOR
        )
        embed.set_footer(text=f"Picking winner in {giveaway_duration} minutes!")
        msg = await channel.send(embed=embed)
        giveaway_msg = msg  # store it for later

        # add reaction to gwy msg so ppls can react on it to join
        await msg.add_reaction("<a:confetti:1437356994142142514>")

        await asyncio.sleep(int(giveaway_duration * 60))

        msg = await channel.fetch_message(msg.id)
        reaction = discord.utils.get(msg.reactions, emoji=CONFETI_EMOJI)

        if not reaction:
            print("reactions not found")
            try:
                await giveaway_msg.reply("❌ No reactions. Giveaway canceled.")
                result_embed_edit = discord.Embed(
                    title="Giveaway Ended! <a:confetti:1437356994142142514>",
                    description=f"❌ No reactions. Giveaway canceled.",
                    color=ERROR_COLOR
                    )
                await msg.edit(embed=result_embed_edit)
            except:
                print("drop msg not found")
            return
        users = [user async for user in reaction.users() if not user.bot]
        users = [u for u in users if not u.bot]  # Remove bots

        if not users:
            print("users not found")
            try:
                await giveaway_msg.reply("❌ No valid users entered.")
                result_embed_edit = discord.Embed(
                title="Giveaway Ended! <a:confetti:1437356994142142514>",
                description=f"❌ No valid users entered.",
                color=ERROR_COLOR)
                await msg.edit(embed=result_embed_edit)
            except:
                print("drop msg not found")
            return

        winners_list = random.sample(users, min(winners, len(users)))

        winner_mention = f""
        for winner in winners_list:
            winner_mention = winner_mention + f"{winner.mention} "

        await self.paychannel.send(f"{winner_mention}won **{prize}**", allowed_mentions=discord.AllowedMentions(users=False))

        result_embed = discord.Embed(
            title="🎊 Winner!",
            description=f"congratulations you have won **{prize}** <a:confetti:1437356994142142514><a:confetti:1437356994142142514>",
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
            title="Giveaway Ended! <a:confetti:1437356994142142514>",
            description=f"Participant(s): {len(users)}!\n{winner_mention} won **{prize}**",
            color=SUCCESS_COLOR
        )
        try:
            await msg.edit(embed=result_embed_edit)
        except:
            print("gwy msg not found")
        giveaway_msg = None

    


def get_data():
        data = load_data()
        temp = []
        servers = []
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        for SERVER_ID, details in data.items():
            prefix = details.get("prefix", ",")
            TARGET_CHANNEL_ID = details.get("channel", "null")
            PRIZE = details.get("prize", 15000)
            MSG_NEEDED = details.get("msg_needed", 100)
            PAY_CHANNEL = details.get("pay_channel", None)
            servers.append((SERVER_ID, TARGET_CHANNEL_ID, PRIZE, MSG_NEEDED, prefix, PAY_CHANNEL))
            servers = list(servers[0])
        return servers

def start():
    servers = get_data()
    if not servers:
        print("❌ No valid token found.")
        return
    client = MyClient(servers[0], servers[1], servers[2], servers[3], servers[4], servers[5])
    return client
    

client = start()

@client.tree.command(name="drop", description="send a drop to currrent channel.")
async def drop(interaction: discord.Interaction, minutes: float, prize: str, winners: int):
    await interaction.response.send_message(
        f"A drop of {minutes} min for {winners} winner(s) will be started with {prize} each"
        )
    await client.start_giveaway(interaction.channel, winners, minutes, prize)

client.run(TOKEN)