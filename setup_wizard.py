import discord
from discord import app_commands
from discord.ext import commands

from database import DB
db = DB()
cur = db.cur

from json import dumps

global bot_stored

bot_stored = None
# ----------------------- STEP 1: SELECT DROP CHANNEL ------------------------

class DropChannelSelect(discord.ui.Select):
    def __init__(self, channels, author):
        self.author = author
        options = [discord.SelectOption(label=ch.name, value=str(ch.id)) for ch in channels]
        super().__init__(placeholder="Select Chat-Drop Channel", options=options)

    async def callback(self, interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("Not for you.", ephemeral=True)

        drop_channel = int(self.values[0])
        await interaction.response.send_message(
            "Now select **Payment Channel**:",
            view=PaymentChannelView(self.author, drop_channel),
            ephemeral=True
        )


class DropChannelView(discord.ui.View):
    def __init__(self, author, channels):
        super().__init__(timeout=60)
        self.add_item(DropChannelSelect(channels, author))


# ----------------------- STEP 2: SELECT PAYMENT CHANNEL ---------------------

class PaymentChannelSelect(discord.ui.Select):
    def __init__(self, author, drop_channel, channels):
        self.author = author
        self.drop_channel = drop_channel
        options = [discord.SelectOption(label=ch.name, value=str(ch.id)) for ch in channels]
        super().__init__(placeholder="Select Payment Channel", options=options)

    async def callback(self, interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("Not for you.", ephemeral=True)

        pay_channel = int(self.values[0])

        await interaction.response.send_modal(
            MsgNeededModal(self.author, self.drop_channel, pay_channel)
        )


class PaymentChannelView(discord.ui.View):
    def __init__(self, author, drop_channel):
        super().__init__(timeout=60)
        channels = [c for c in author.guild.channels if isinstance(c, discord.TextChannel)]
        self.add_item(PaymentChannelSelect(author, drop_channel, channels))


# ----------------------- STEP 3: ENTER MESSAGE REQUIREMENT ------------------

class MsgNeededModal(discord.ui.Modal, title="Messages Needed per Drop"):
    msg_needed = discord.ui.TextInput(label="Enter a number (integer)", required=True)

    def __init__(self, author, drop_channel, pay_channel):
        super().__init__()
        self.author = author
        self.drop_channel = drop_channel
        self.pay_channel = pay_channel

    async def on_submit(self, interaction):
        if self.msg_needed.value.isdigit():
            await interaction.response.send_message(
                "Now select **prize Name** and **Prize Amount**",
                view=ModalBreakerView1(self.author, self.drop_channel, self.pay_channel, int(self.msg_needed.value)),
                ephemeral=True
            )
        else:
            await interaction.response.send_message("the value you entered is not a valid number (integer)")

# ----------------------- STEP 4: ADDING A BUTTON BEFORE MODAL ------------------

class ModalBreakerButton1(discord.ui.Button):
    def __init__(self, author, drop_channel, pay_channel, msg_needed):
        self.author = author
        self.drop_channel = drop_channel
        self.pay_channel = pay_channel
        self.msg_needed = msg_needed
        super().__init__(label="Click to add 'Prize Name' and 'Prize Amount'", emoji="👆")

    async def callback(self, interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("Not for you.", ephemeral=True)


        await interaction.response.send_modal(
            PrizeAmountModal(
                self.author,
                self.drop_channel,
                self.pay_channel,
                self.msg_needed
                )
            )

class ModalBreakerView1(discord.ui.View):
    def __init__(self, author, drop_channel, pay_channel, msg_needed):
        super().__init__(timeout=60)
        self.add_item(ModalBreakerButton1(author, drop_channel, pay_channel, msg_needed))

# ----------------------- STEP 5: ENTER PRIZE AMOUNT -------------------------

class PrizeAmountModal(discord.ui.Modal, title="Prize Amount and Prize per Drop"):
    prize_amount = discord.ui.TextInput(label="Enter Prize Amount", required=True)
    prize_name = discord.ui.TextInput(label="Enter Prize Name", required=True)

    def __init__(self, author, drop_channel, pay_channel, msg_needed):
        super().__init__()
        self.author = author
        self.drop_channel = drop_channel
        self.pay_channel = pay_channel
        self.msg_needed = msg_needed

    async def on_submit(self, interaction):
        if self.prize_amount.value.isdigit():
            await interaction.response.send_message(
                "Now add **Duration**",
                view=ModalBreakerView2(
                    self.author, self.drop_channel, 
                    self.pay_channel, self.msg_needed, 
                    int(self.prize_amount.value), self.prize_name.value),
                    ephemeral=True
                    )
        else:
            await interaction.response.send_message("the value you entered is not a valid number (integer)")
        
        

# ----------------------- STEP 6: ADDING A BUTTON BEFORE MODAL ------------------

class ModalBreakerButton2(discord.ui.Button):
    def __init__(self, author, drop_channel, pay_channel, msg_needed, prize_amount, prize_name):
        self.author = author
        self.drop_channel = drop_channel
        self.pay_channel = pay_channel
        self.msg_needed = msg_needed
        self.prize_amount = prize_amount
        self.prize_name = prize_name
        super().__init__(label="Click to add 'Duration'", emoji="👆")

    async def callback(self, interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("Not for you.", ephemeral=True)


        await interaction.response.send_modal(
            FinalPrizeModal(
                self.author,
                self.drop_channel,
                self.pay_channel,
                self.msg_needed,
                self.prize_amount,
                self.prize_name
                )
            )

class ModalBreakerView2(discord.ui.View):
    def __init__(self, author, drop_channel, pay_channel, msg_needed, prize_amount, prize_name):
        super().__init__(timeout=60)
        self.add_item(ModalBreakerButton2(author, drop_channel, pay_channel, msg_needed, prize_amount, prize_name))

# ----------------------- STEP 5: PRIZE NAME + DURATION ----------------------

class FinalPrizeModal(discord.ui.Modal, title="Final Step"):
    global bot_stored
    duration = discord.ui.TextInput(label="Giveaway Duration (max 5 minutes)", required=True)

    def __init__(self, author, drop_channel, pay_channel, msg_needed, prize_amount, prize_name):
        super().__init__()
        self.author = author
        self.drop_channel = drop_channel
        self.pay_channel = pay_channel
        self.msg_needed = msg_needed
        self.prize_amount = prize_amount
        self.prize_name = prize_name

    async def on_submit(self, interaction):

        try:
            duration = int(self.duration.value)
            if duration > 5:
                return await interaction.response.send_message("❌ Max duration is 5 minutes.", ephemeral=True)
        except:
            return await interaction.response.send_message("❌ Duration must be a number.", ephemeral=True)
        
        if db.exists(table="servers", server_id=interaction.guild.id):
            old_data = db.get_as_dict(table="servers", server_id=interaction.guild.id)[0]
            pretty_old_data = dumps(old_data, indent=4)
        try:
            # if interaction.guild.owner.id != interaction.user.id:
            await interaction.user.send(f"`{interaction.guild.name}` previous config data\n```{pretty_old_data}```")
        except discord.Forbidden:
            dm_status = "I couldn't DM you (DMs are closed)."
        except Exception as e:
            dm_status = f"Error sending DMs: {e}"

        # Insert into DB
        cur.execute(
            "INSERT OR REPLACE INTO servers (server_id, channel, pay_channel, msg_needed, prize, gwy_duration, msg_count, total_drops, total_prize, sub, prize_name) VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0, 0, ?)",
            (
                interaction.guild.id,
                self.drop_channel,
                self.pay_channel,
                self.msg_needed,
                self.prize_amount,
                duration,
                self.prize_name
            )
        )
        db.conn.commit()

        await interaction.response.send_message(
            f"✅ Setup complete for **{interaction.guild.name}**!",
            ephemeral=True
        )

        bot_stored.checker()

# ----------------------- COMMAND --------------------------------------------

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Start server setup wizard")
    @app_commands.default_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Admins only.", ephemeral=True)

        channels = [c for c in interaction.guild.channels if isinstance(c, discord.TextChannel)]

        continue_button = discord.ui.Button(label="YES, continue", style=discord.ButtonStyle.green) # , emoji="✅"
        exit_button = discord.ui.Button(label="NO", style=discord.ButtonStyle.red) #, emoji="❌"

        view = discord.ui.View().add_item(continue_button)
        view.add_item(exit_button)

        async def continue_button_callback(interaction):
            continue_button.disabled = True
            exit_button.disabled = True
            await interaction.response.edit_message(
            content="Hello and welcome to the setup wizard\nSelect **Chat-Drop Channel**:",
            view=DropChannelView(interaction.user, channels),
        )
        continue_button.callback = continue_button_callback

        async def exit_button_callback(interaction):
            continue_button.disabled = True
            exit_button.disabled = True
            await interaction.response.edit_message(view=view)
        
        exit_button.callback = exit_button_callback


        if db.exists(table="servers", server_id=interaction.guild.id):
            await interaction.response.send_message(
                f"`{interaction.guild.name}` already has a setup config. do you want to overwrite it?",
                view=view,
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
            "Hello and welcome to the setup wizard\nSelect **Chat-Drop Channel**:",
            view=DropChannelView(interaction.user, channels),
            ephemeral=True
            )
            


async def setup(bot):
    global bot_stored
    bot_stored = bot
    await bot.add_cog(Setup(bot))
