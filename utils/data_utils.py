from .constants import *

def update_drop_data(db, server_id: int, PRIZE: int, winner_ids: list):
    import datetime
    drops = db.get_as_dict(table="drops", server_id=server_id, remark="entry")
    server = db.get_as_dict(table="servers", server_id=server_id)
    server = server[0]

    total_drops:int =  server["total_drops"]
    if total_drops == 0:
        total_drops = len(drops)

    total_owo:int = server["total_owo"]
    if total_owo == 0:
        for drop in drops:
            total_owo += drop["prize"]
    # increment totals
    total_drops += 1

    total_owo += PRIZE

    db.insert(
        table="drops",server_id=server_id , winner=winner_ids[0], prize=PRIZE, 
        time=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), remark="entry"
        )
    db.update(
        table="servers", pk_name="server_id", pk_value=server_id, 
        total_drops=total_drops, total_owo=total_owo
    )

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