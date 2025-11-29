from .constants import *
import requests
import datetime as dt

    # SQL cmd
##################################################################################################################
async def sql_handler(self, message):
    import discord
    if message.author.id != DEV_ID:
        return
    db = self.db

    if message.content.startswith(PREFIX + "sql "):
        query = message.content[len(PREFIX) + 4:]

        try:
            result = db.cur.execute(query)

            rows = result.fetchall()
            
            if rows:
                col_names = [col[0] for col in db.cur.description]
                db.conn.commit()
                as_dict = [dict(zip(col_names, row)) for row in rows]
                await pretty_json(self, message, as_dict)
            else:
                await message.channel.send("Query executed. No rows returned.")

        except Exception as e:
            await message.channel.send(f"Error:\n```{e}```")

# pretty json helper
async def pretty_json(self, message, as_dict):
    from json import dumps
    # Pretty JSON formatting
    pretty_json = dumps(as_dict, indent=4)

    # If too long, fall back to compact format
    if len(pretty_json) > MAX_DISCORD_LEN:
        compact_json = dumps(as_dict)
        if len(compact_json) > MAX_DISCORD_LEN:
            await message.channel.send("Output too large to send.")
        else:
            await message.channel.send(f"```json\n{compact_json}\n```")
    else:
        await message.channel.send(f"```json\n{pretty_json}\n```")

def backup_data():
    file_path = "data.db"

    with open(file_path, "rb") as f:
        time = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M:%S")
        files = {
            "file": ("data.db", f, "application/octet-stream")
        }

        data = {
            "content": f"latest database backup [{time}]:"
        }

        response = requests.post(data_backup_WEBHOOK, data=data, files=files)
        print(YELLOW+f"{time} data backed up, response code: {response.status_code}"+RESET)