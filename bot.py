import discord
from discord.ext import commands
import asyncio
import os
import json
import random
import datetime
from dotenv import load_dotenv

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
GIVEAWAY_DURATION = 5

# Emoji's
CONFETI_EMOJI = discord.PartialEmoji(name='confeti', id=1437356994142142514, animated=True)


intents = discord.Intents.all()

class MyClient(commands.Bot):
    def __init__(self, SERVER_ID, TARGET_CHANNEL_ID, PRIZE, MSG_NEEDED, prefix):
        super().__init__(command_prefix=".", intents=intents)
        self.msg_count = 0
        self.TARGET_CHANNEL_ID = TARGET_CHANNEL_ID
        self.SERVER_ID = SERVER_ID
        self.PRIZE = PRIZE
        self.MSG_NEEDED = MSG_NEEDED
        self.prefix = prefix

    async def on_ready(self):
        await self.tree.sync()
        self.channel = self.get_channel(self.TARGET_CHANNEL_ID)
        if self.channel is None:
            print("❌ Channel not found!")
            return
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
                await self.start_giveaway(self.channel)

        await self.process_commands(message)

    async def start_giveaway(self, channel):
        embed = discord.Embed(
            title="<a:confeti:1437356994142142514> Giveaway Started! <a:confeti:1437356994142142514>",
            description=f"React with <a:confeti:1437356994142142514> to join!\n\n**Prize → __{self.PRIZE:,}__ OWO**",
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
            description=f"congratulations {winner.name} you have won __**{self.PRIZE:,}**__ OWO <a:confeti:1437356994142142514><a:confeti:1437356994142142514>",
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



def get_data():
        data = load_data()
        servers = []
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        for SERVER_ID, details in data.items():
            prefix = details.get("prefix", ",")
            TARGET_CHANNEL_ID = details.get("channel", "null")
            PRIZE = details.get("prize", 15000)
            MSG_NEEDED = details.get("msg_needed", 100)
            servers.append((SERVER_ID, TARGET_CHANNEL_ID, PRIZE, MSG_NEEDED, prefix))
            print(servers)
        return servers

def start_bot(SERVER_ID, TARGET_CHANNEL_ID, PRIZE, MSG_NEEDED, prefix):
    client = MyClient(SERVER_ID, TARGET_CHANNEL_ID, PRIZE, MSG_NEEDED, prefix)
    client.run(TOKEN)
def start():
    servers = get_data()
    if not servers:
        print("❌ No valid token found.")
        return
    tasks = [start_bot(s[0], s[1], s[2], s[3],s[4]) for s in servers]
    
start()
