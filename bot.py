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
#
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

# data logging helpler func's
import datetime

DEV_ID = 123456789012345678  # <- replace with your actual dev Discord ID

def _sanitize_prize(Prize):
    """Convert prize (str or int) like '15,000' or 15000 to int."""
    if isinstance(Prize, int):
        return Prize
    try:
        return int(str(Prize).replace(",", "").strip())
    except Exception:
        return 0

def ensure_server_schema(sid: str, data: dict):
    """Ensure drops and backups keys exist for a server dict (mutates data)."""
    server = data.setdefault(sid, {})
    server.setdefault("drops", {"total_drops": 0, "total_owo": 0, "history": []})
    server.setdefault("backups", {})  # map timestamp -> snapshot
    return server

def update_drop_data(server_id: int, Prize, winners_list):
    print(Prize)
    """
    Record a finished giveaway.
    - server_id: int or str
    - prize: str or int
    - winners_list: list of user IDs (or strings)
    """
    sid = str(server_id)
    data = load_data()
    if sid not in data:
        # nothing configured for this server — don't create server config silently
        print(f"[update_drop_data] server {sid} not found in data.json")
        return False

    server = ensure_server_schema(sid, data)
    drops = server["drops"]

    prize_val = _sanitize_prize(Prize)
    print(589375975375757357)
    print(prize_val)
    # increment totals
    drops["total_drops"] = drops.get("total_drops", 0) + 1
    drops["total_owo"] = drops.get("total_owo", 0) + prize_val

    # append history entry (store user IDs for later)
    drops.setdefault("history", []).append({
        "time": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "winners": [str(u) for u in winners_list],
        "prize": prize_val
    })

    atomic_save(DATA_FILE, data)
    return True

def get_server_stats(sid: str):
    """Return a dict of computed stats for server sid (string)."""
    data = load_data()
    if sid not in data:
        return None
    server = ensure_server_schema(sid, data)
    drops = server.get("drops", {})
    total_drops = drops.get("total_drops", 0)
    total_owo = drops.get("total_owo", 0)
    dev_fee = int(total_owo * 0.10)  # 10%
    total_needed = total_owo + dev_fee
    history = drops.get("history", [])
    return {
        "total_drops": total_drops,
        "total_owo": total_owo,
        "dev_fee": dev_fee,
        "total_needed": total_needed,
        "history": history
    }

def backup_and_reset_server(sid: str):
    """
    Move current drops data into backups keyed by timestamp,
    then clear drops data (but keep config).
    """
    data = load_data()
    if sid not in data:
        return False
    server = data[sid]
    server.setdefault("backups", {})
    drops_snapshot = server.get("drops", {"total_drops":0, "total_owo":0, "history":[]})
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    server["backups"][timestamp] = {"drops": drops_snapshot}
    # reset drops
    server["drops"] = {"total_drops": 0, "total_owo": 0, "history": []}
    atomic_save(DATA_FILE, data)
    return timestamp


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
CONFETTI_EMOJI = discord.PartialEmoji(name='confetti', id=1438155456823431343, animated=True) # link https://cdn.discordapp.com/emojis/1437356632723165244.webp?size=96&animated=true

# dev id
DEV_ID = 1206904635420450856
#DEV_ID = 123456789012345678 

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
        
        #await self.tree.sync()
        #print("Slash commands synced ✅")

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
                await self.start_giveaway(self.channel, 1, GIVEAWAY_DURATION, f"{self.PRIZE:,} OWO", True)
                

        await self.process_commands(message)

    async def start_giveaway(self, channel, winners, giveaway_duration, prize: str, is_chat_drop: bool):
        end_time = int(time.time()) + (int(giveaway_duration * 60)) + 2
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
            return
        users = [user async for user in reaction.users() if not user.bot]
        users = [u for u in users if not u.bot]  # Remove bots

        if not users:
            print("users not found")
            try:
                await giveaway_msg.reply("❌ No valid users entered.")
                result_embed_edit = discord.Embed(
                title="Giveaway Ended! <a:confetti:1438155456823431343>",
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

        # suppose winners_list is a list of Member objects or IDs
        winner_ids = [w.id if hasattr(w, "id") else int(w) for w in winners_list]
        if is_chat_drop:
            update_drop_data(channel.guild.id, self.PRIZE, winner_ids)


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

# /drop command
@client.tree.command(name="drop", description="send a drop to currrent channel.")
async def drop(interaction: discord.Interaction, minutes: float, prize: str, winners: int):
    await interaction.response.send_message(
        f"A drop of {minutes} min for {winners} winner(s) will be started with {prize} each"
        )
    await client.start_giveaway(interaction.channel, winners, minutes, prize, False)

# /stats command
@client.tree.command(name="stats", description="Show chat drops stats for current server (owner only). Dev can query any server.")
@app_commands.describe(server_id="Optional server id (dev only)")
async def stats(interaction: discord.Interaction, server_id: str = None):
    sid = server_id or str(interaction.guild_id)
    data = load_data()
    if sid not in data:
        await interaction.response.send_message("❌ Server not found.", ephemeral=True)
        return

    # permission: server owner or dev
    if interaction.user.id != DEV_ID:
        # must be querying current server and be owner
        if str(interaction.guild_id) != sid or interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Only the server owner (or dev) can view these stats.", ephemeral=True)
            return

    stats = get_server_stats(sid)
    if not stats:
        await interaction.response.send_message("No drops recorded for this server.", ephemeral=True)
        return

    # build embed
    embed = discord.Embed(title=f"📊 Giveaway Stats — {sid}", color=MAIN_COLOR)
    embed.add_field(name="Total drops", value=str(stats["total_drops"]), inline=True)
    embed.add_field(name="Total OWO paid out", value=f"{stats['total_owo']:,}", inline=True)
    embed.add_field(name="Developer fee (10%)", value=f"{stats['dev_fee']:,}", inline=True)
    embed.add_field(name="Total OWO needed", value=f"{stats['total_needed']:,}", inline=True)
    # show last few winners (if any)
    history = stats.get("history", [])[-6:]  # last 6 entries
    if history:
        hist_lines = []
        for h in history[::-1]:
            time_str = h.get("time")
            winners = ", ".join(h.get("winners", []))
            prize = f"{h.get('prize', 0):,}"
            hist_lines.append(f"{time_str} — {winners} — {prize} OWO")
        embed.add_field(name="Recent drops (UTC)", value="\n".join(hist_lines), inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

# /reset command (dev only)
@client.tree.command(name="reset_drops", description="(Dev only) Backup and reset drops data for a server")
@app_commands.describe(server_id="Server ID to reset (defaults to current server)")
async def reset_drops(interaction: discord.Interaction, server_id: str = None):
    if interaction.user.id != DEV_ID:
        await interaction.response.send_message("❌ Only the bot developer can run this.", ephemeral=True)
        return
    sid = server_id or str(interaction.guild_id)
    data = load_data()
    if sid not in data:
        await interaction.response.send_message("❌ Server not found.", ephemeral=True)
        return

    ts = backup_and_reset_server(sid)
    await interaction.response.send_message(f"✅ Backed up drops for server `{sid}` into backups at `{ts}` and reset counts.", ephemeral=True)

client.run(TOKEN)