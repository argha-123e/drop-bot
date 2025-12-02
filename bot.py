import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import requests

# DATA BASE
import database as DB
db = DB.DB()

import atexit

DB.start_sqlite_web()
atexit.register(DB.stop_sqlite_web)

# giveaway command
from giveaway_cmd import start_giveaway


# from /utils
from utils.data_utils import * # functions related to data maniupulation
backup_data()
from utils.constants import * # constant variables
import utils.embed as embed # embeds 

# subscription manager
import submanager as submgm

SM = submgm.SubscriptionManager(db, sub_WEBHOOK)

db.cur.execute('''
    CREATE TABLE IF NOT EXISTS servers (
        server_id    INTEGER PRIMARY KEY,
        channel      INTEGER NOT NULL,
        pay_channel  INTEGER NOT NULL,
        msg_needed   INTEGER NOT NULL,
        prize        INTEGER NOT NULL,
        gwy_duration FLOAT NOT NULL,
        msg_count    INTEGER NOT NULL,
        total_drops  INTEGER,
        total_prize  INTEGER,
        sub          BOOLEAN NOT NULL,
        prize_name
        )''')

db.cur.execute("PRAGMA foreign_keys = ON;")

# total_prize
db.cur.execute('''
    CREATE TABLE IF NOT EXISTS drops (
        drop_id     INTEGER PRIMARY KEY,
        server_id   INTEGER NOT NULL,
        winner      INTEGER,
        prize       INTEGER NOT NULL,
        time        TEXT NOT NULL,
        remark      TEXT,
        FOREIGN KEY (server_id) REFERENCES servers(server_id)
);''')


db.cur.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        server_id   INTEGER PRIMARY KEY,
        sub_type    TEXT NOT NULL,      -- "monthly" or "revshare"
        value       INTEGER NOT NULL,   -- %, or monthly price tier
        end_date    TEXT,               -- only for monthly plans (ISO format)
        created_at  TEXT NOT NULL,
        months      INTEGER,
        FOREIGN KEY (server_id) REFERENCES servers(server_id)
    );""")

db.cur.execute("""
    CREATE TABLE IF NOT EXISTS trials (
        server_id   INTEGER PRIMARY KEY,
        trial       BOOLEAN,
        FOREIGN KEY (server_id) REFERENCES servers(server_id)
    );""")

if not db.exists(table="servers", server_id=1437310569387655249):
    db.insert(
        "servers", server_id =1437310569387655249, # insert a row in a table
        channel=1443974858445819955, pay_channel=1443974900929790072, msg_needed=5, 
        prize=15000, gwy_duration=.25, msg_count=0, total_drops=0, total_prize=0, sub=1, prize_name="OWO"
        )


def backup_and_reset_server(sid: str):
    """
    Move current drops data into backups keyed by timestamp,
    then clear drops data (but keep config).
    """
    drops = db.get_as_dict(table="drops", server_id=sid, remark="entry")
    
    for drop in drops:
        db.update(table="drops", pk_name="drop_id", pk_value=drop["drop_id"], remark="backup")

    db.update(table="servers", pk_name="server_id", pk_value=sid, total_prize=0, total_drops=0)
    return True

def get_server_stats(sid: int):
    """Return a dict of computed stats for server sid (string)."""

    # getting server speicific data
    servers_data = db.get_as_dict(table="servers", server_id=sid)[0]
    

    # extracting data
    total_drops = servers_data["total_drops"]
    total_prize = servers_data["total_prize"]
    if db.exists("subscriptions",server_id=sid):
        sub_data = db.get_as_dict("subscriptions", server_id=sid)[0]

        if sub_data["sub_type"] == "monthly":
            dev_fee = OWO_PLANS[sub_data["value"]]
        elif sub_data["sub_type"] == "revshare":
            dev_fee = int(total_prize * sub_data["value"])
        elif sub_data["sub_type"] == "trial":
            dev_fee = 0
            sub_data["value"] = "trial"

        dates = [sub_data["created_at"], sub_data["end_date"]]

        # getting server specific drop data
        drops = db.get_as_dict(table="drops", server_id=sid, remark="entry")
            
        history = drops
        return {
        "total_drops": total_drops,
        "total_prize": total_prize,
        "dev_fee": dev_fee,
        "dates": dates,
        "value": sub_data["value"],
        "history": history,
        "prize_name": servers_data["prize_name"]
    }
    else:
        # getting server specific drop data
        drops = db.get_as_dict(table="drops", server_id=sid, remark="entry")
        
        history = drops
        dev_fee="not a subscriber now"
        return {
            "total_drops": total_drops,
            "total_prize": total_prize,
            "dev_fee": dev_fee,
            "dates": ["N/A","N/A"],
            "value": "N/A",
            "history": history,
            "prize_name": servers_data["prize_name"]
        }

async def msg_count_saver(self):
    cycled:int = 0
    while True:
        servers = db.get_as_dict("servers")
        for server_id in self.SERVER_IDs:
            for server in servers:
                if server["server_id"] == server_id and server["sub"]:
                    if self.msg_count[str(server_id)] == server["msg_count"]:
                        pass
                    else:
                        db.update(
                            table="servers", pk_name="server_id", 
                            pk_value=server['server_id'], msg_count=self.msg_count[str(server_id)]
                            )
        if cycled % 60 == 0:
            self.SERVER_IDs = db.get_server_ids()
            self.TARGET_CHANNEL_ID = db.get_channel_ids()
            SM.check_subscriptions()
        elif cycled % 5 == 0 and is_server:
            backup_data()
        await asyncio.sleep(60)
        cycled += 1


def setup_msg_count(self):
    data = db.get_as_dict("servers")
    for server_id in self.SERVER_IDs:
        sid = str(server_id)
        for server in data:
            if server["server_id"] == server_id:
                self.msg_count[sid] = server["msg_count"]

# BOT CLASS
intents = discord.Intents.all()
class MyClient(commands.Bot):
    def __init__(self, SERVER_IDs, TARGET_CHANNEL_ID):
        super().__init__(command_prefix=PREFIX, intents=intents)
        self.db = db

        self.TARGET_CHANNEL_ID = TARGET_CHANNEL_ID
        self.SERVER_IDs = SERVER_IDs
        self.msg_count = {}

        self.gwy_running:int = 0
        self._gwy_tasks:list =[]

        setup_msg_count(self)


    async def on_ready(self):
        await self.tree.sync()
        print(GREEN+"Slash commands synced ✅")

        print(f"✅  Logged in as {self.user}"+RESET)
        SM.check_subscriptions()
        await msg_count_saver(self)
    async def on_message(self, message):
        # block own/bot msgs
        if message.author.bot:
            return

        if  message.content.startswith(PREFIX):
            await on_msg_handler(self, message)
        
        if message.channel.id in self.TARGET_CHANNEL_ID:
            # get data
            sid = str(message.guild.id)
            server = db.get_as_dict("servers", server_id=sid)[0]
            if not server["sub"]:
                return


            # setup variables
            msg_needed = server["msg_needed"]
            prize = server["prize"]

            # logic
            if not server["sub"]:
                return
            self.msg_count[sid] += 1
            print(CYAN+f"[{self.get_guild(message.guild.id).name}] Count: {self.msg_count[sid]}/{msg_needed}"+RESET)

            if self.msg_count[sid] >= msg_needed:
                self.msg_count[sid] = 0    


                task = asyncio.create_task(
                    self.start_giveaway_helper(
                        self.get_channel(server["channel"]), 1, 
                        server["gwy_duration"], prize, True, 
                        self.get_channel(server["pay_channel"]), server["prize_name"]
                        )
                        )
                self._gwy_tasks.append(task)          # track so you can cancel/inspect
                self.gwy_running = len(self._gwy_tasks)
            
    async def start_giveaway_helper(self, *args, **kwargs):
        try:
            await start_giveaway(self, *args, **kwargs)
        except Exception as e:
            print(e)

# starter
###################################################################################################################
def get_data():
        channel_ids = db.get_channel_ids()
        server_ids = db.get_server_ids()
        return [server_ids, channel_ids]


def start():
    data = True
    if data:
        client = MyClient(db.get_channel_ids(), db.get_server_ids())
        return client
    else:
        print(RED+"❌ No valid data found."+RESET)


client = start()

# on_message cmds handler
########################################################################################################################
async def on_msg_handler(self, message):
    if  message.content.startswith(PREFIX):
            # Split the message into command + args
            parts = message.content[len(PREFIX):].split()
            if len(parts) == 0:
                return

            cmd = parts[0]         # the command name
            args = parts[1:]       # list of arguments

            # Example command: ,test hello world
            if cmd == "ping":
                await message.reply(f"Pong! `{round(self.latency * 1000)}ms`")
            
            elif cmd == "count":
                if message.guild.id in self.SERVER_IDs:
                    await message.reply(f"`{self.msg_count[str(message.guild.id)]}`")

            elif cmd == "about":
                await message.channel.send(embed=embed.about)

            elif cmd == "help":
                await message.channel.send(embed=embed.help)

            elif cmd == "add_sub":
                if len(args) > 3:
                    arg3 = args[3]
                else:
                    arg3 = None
                try:
                    await add_sub(message, int(args[0]) or message.guild.id, args[1], args[2], arg3)
                    setup_msg_count(self)
                except Exception as e:
                    await message.reply(
                    f"error: {e}\n(maybe) wrong syntax\ntry: ``.add_sub <server id> <plan type> <months> <tier>``"
                        )

            elif cmd == "cancel_sub":
                await cancel_sub(message, int(args[0]))

            elif cmd == "sql":
                await sql_handler(self, message)
                self.SERVER_IDs = db.get_server_ids()
                self.TARGET_CHANNEL_ID = db.get_channel_ids()
                SM.check_subscriptions()
                
spacer = "--------------------------------------------------------------------------------------------------------------"
# subscription manager
################################################################################################################
async def add_sub(msg, server_id: int, plan_type: str, arg1: str, arg2):
    # dev only
    if msg.author.id not in owner_ids:
        return await msg.channel.send("Not allowed.")
    if server_id not in client.SERVER_IDs:
        return await msg.channel.send("server not in ``servers`` table")


    if plan_type == "revshare":
        percent = float(arg1.strip("%")) / 100
        result = SM.add_sub(server_id, "revshare", percent)
        if result[0]:
            requests.post(sub_WEBHOOK, json={
            "content": f"{spacer}\nSubscription added for server {server_id}\n## current server sub info\n```{result[2]}```"
            })
            return await msg.channel.send(
                f"Revshare subscription added for server `{server_id}` @ {percent*100}%\nreturn code: {result[1]}"
                )
        else:
            return await msg.channel.send(f"return code: {result[1]}")
    
    elif plan_type == "trial":
        days = int(arg1)
        result = SM.add_sub(server_id, "trial", days)
        if result[0]:
            requests.post(sub_WEBHOOK, json={
            "content": f"{spacer}\ntrial added for server {server_id}\n## current server sub info\n```{result[2]}```"
            })
            return await msg.channel.send(
                f"trial added for server `{server_id}` @ {0}%\nreturn code: {result[1]}"
                )
        else:
            return await msg.channel.send(f"return code: {result[1]}")


    # monthly
    months = int(arg1)
    tier = 1
    if arg2:
        tier = int(arg2)
    if tier not in OWO_PLANS:
        return await msg.channel.send("Invalid tier.")
    result = SM.add_sub(server_id, "monthly", tier, months=months)
    if result[0]:
        requests.post(sub_WEBHOOK, json={
            "content": f"{spacer}\nSubscription added for server {server_id}\n## current server sub info\n```{result[2]}```"
        })
        return await msg.channel.send(
            f"Monthly subscription added:\nServer: `{server_id}`\n"
            f"Months: `{months}`\nTier: `{tier}` → {submgm.OWO_PLANS[tier]:,} OWO/mo\nreturn code: {result[1]}"
        )


async def cancel_sub(msg, server_id: int):
    if msg.author.id not in owner_ids:
        return
    result = SM.cancel_sub(server_id)
    if result[0]:
        await msg.channel.send(f"Subscription cancelled for `{server_id}`")
    else:
        await msg.channel.send(f"return code: {result[1]}")

async def add_trial(msg, server_id: int, days: str):
    # dev only
    if msg.author.id not in owner_ids:
        return await msg.channel.send("Not allowed.")
    if server_id not in client.SERVER_IDs:
        return await msg.channel.send("server not in ``servers`` table")
    
    days = int(days)


    result = SM.add_sub(server_id, "trial", days)
    if result[0]:
        requests.post(sub_WEBHOOK, json={
        "content": f"{spacer}\ntrial added for server {server_id}\n## current server sub info\n```{result[2]}```"
        })
        return await msg.channel.send(
            f"trial added for server `{server_id}` @ {0}%\nreturn code: {result[1]}"
            )
    else:
        return await msg.channel.send(f"return code: {result[1]}")


# slash cmds
#########################################################################################################################

# /help command
@client.tree.command(name="help", description="Show Drop Bot quick help")
async def help_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(embed=embed.help, ephemeral=True)


# /drop command
@client.tree.command(name="drop", description="send a quick drop to currrent channel.")
async def drop(interaction: discord.Interaction, minutes: float, prize: str, winners: int):

    if client.gwy_running > gwy_limit and interaction.user.id not in allowed_users: # hard limit 100 gwys
        await interaction.response.send_message("shard is too busy, try again later",ephemeral=True)
        return
    
    if minutes > gwy_time_limit and interaction.user.id not in allowed_users: # hard cap of 60 minutes
        await interaction.response.send_message("try drops under 1hrs (60 minutes)",ephemeral=True)
        return
    
    if interaction.guild_id not in client.SERVER_IDs:
        if not db.get_sub_status(interaction.guild_id):
            return await interaction.response.send_message("this server isn't subscribed to Dropbot",ephemeral=True)

    await interaction.response.send_message(
        f"A drop of {minutes} min for {winners} winner(s) will be started with {prize} each",
        ephemeral=True
        )
    await client.start_giveaway(interaction.channel, winners, minutes, prize, False, None, None)


# /stats command
@client.tree.command(name="stats", description="Show chat drops stats for current server (owner only). Dev can query any server.")
@app_commands.describe(server_id="Optional server id")
async def stats(interaction: discord.Interaction, server_id: str = None):

    if server_id:
        sid = int(server_id)
    else:
        sid = interaction.guild_id
    if sid not in db.get_server_ids():
        await interaction.response.send_message("❌ Server not found.", ephemeral=True)
        return
    

    # permission: server owner or bot owner
    if interaction.user.id not in owner_ids:
        # must be querying current server and be owner
        if interaction.guild_id != sid or interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Only the server owner (or dev) can view these stats.", ephemeral=True)
            return
    try:
        stats = get_server_stats(sid)
    except Exception as e:
        print(e)
    if not stats:
        await interaction.response.send_message("No drops recorded for this server.", ephemeral=True)
        return
    
    if type(stats["value"]) == float:
        value = f"{int(stats['value']*100)}%"
    elif type(stats["value"]) == str:
        value = stats['value']
    else:
        value = f"{stats['value']:,} OWO/month"

    if type(stats["dev_fee"]) == int:
        dev_fee = f"{stats['dev_fee']:,}"
    else:
        dev_fee = stats["dev_fee"]
    

    # build embed
    embed = discord.Embed(title=f"📊 Giveaway Stats — {sid}", color=MAIN_COLOR)
    embed.add_field(name="Total drops", value=str(stats["total_drops"]), inline=True)
    embed.add_field(name=f"Total {stats['prize_name']} to pay out", value=f"{stats['total_prize']:,}", inline=True)
    embed.add_field(name=f"Developer fee ({value})", value=f"{dev_fee} owo", inline=True)
    embed.add_field(name="Subscription status", value=f"**Created at:** {stats['dates'][0]}\n**Expiring at:** {stats['dates'][1]}", inline=True)
    # show last few winners (if any)
    history = stats.get("history", [])[-6:]  # last 6 entries
    if history:
        hist_lines = []
        for h in history[::-1]:
            time_str = h.get("time")
            winners = h['winner']
            prize = f"{h.get('prize', 0):,}"
            hist_lines.append(f"{time_str} — winner(s): {winners} — {prize} {stats['prize_name']}")
        embed.add_field(name="Recent drops (UTC)", value="\n".join(hist_lines), inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


# /reset command (dev only)
@client.tree.command(name="reset_drops", description="(Dev only) Backup and reset drops data for a server")
@app_commands.describe(server_id="Server ID to reset (defaults to current server)")
async def reset_drops(interaction: discord.Interaction, server_id: str = None):
    if interaction.user.id not in owner_ids:
        await interaction.response.send_message("❌ Only the bot developer can run this.", ephemeral=True)
        return
    sid = server_id or str(interaction.guild_id)
    if int(sid) not in db.get_server_ids():
        await interaction.response.send_message("❌ Server not found.", ephemeral=True)
        return

    ts = backup_and_reset_server(sid)
    if ts:
        await interaction.response.send_message(f"✅ Backed up drops for server `{sid}` into backups and reset counts.", ephemeral=True)

if type(TOKEN) == str:
    client.run(TOKEN)
else:
    client.run(str(TOKEN))