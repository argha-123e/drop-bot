from .constants import *
from discord import Embed



inline = False


# about embed
#################################################################################################################
about = Embed(
            title="🌟 What We Offer",
            description=f"A fully automated chat-drop & giveaway system designed to boost activity, reward users, and grow your Discord server effortlessly.",
            color=MAIN_COLOR
        )
about.add_field(name="⭐ Automatic Drops", value="Drops appear automatically after a certain number of messages.\nPerfect for keeping chats active without staff involvement.", inline=inline)
about.add_field(name="⭐ Custom Rewards", value="""
Give anything you want as a prize:
- Coins (owo, dank etc.)
- Items (deco, nitro, nameplate, anything)
- Even special roles or surprises
*Fully customizable per server.*""", inline=inline)
about.add_field(name="⭐ Auto Giveaways", value="""
Run giveaways with:
- Custom timers
- random winner selection out of Reaction-based entries
- Everything handled 100% by the bot. (except payment)
""", inline=inline)
about.add_field(name="⭐ Server Stats", value="Track total drops, total rewards, history, and overall activity at a glance with `/stats`.", inline=inline)
about.add_field(name="⭐ Fast & Reliable", value="No lag, no crashes, simple setup, and efficient performance on any host", inline=inline)
about.set_footer(text=footer_txt)

# help embed 
#################################################################################################################
help = Embed(
    title="📦 Drop Bot — Quick Help",
    description=(
        "Automated chat drops & giveaways to boost activity. "
        "Commands are split between **on-message** and **slash**."
    ),
    color=MAIN_COLOR
)

# Slash commands for users
help.add_field(
    name="🕹 Slash Commands",
    value=(
        "`/drop <minutes> <prize> <winners>` — Start a giveaway in this channel.\n"
        "`/stats [server_id]` — Show server drops & subscription stats (owner or dev).\n"
        f"`{PREFIX}about` — get info about Drop Bot.\n"
    ),
    inline=inline
)

# Notes & limits
help.add_field(
    name="ⓘ Notes & Limits",
    value=(
        "• Only subscribed servers get chat-drops. **Trials are available for new servers.**\n"
        "• Giveaways are reaction-based. Prize can be any text or an integer amount.\n"
        "• Hard caps: giveaway duration ≤ 60 min, shard-wide concurrent giveaways limited.\n"
    ),
    inline=inline
)

# Examples
help.add_field(
    name="🔧 Examples",
    value=(
        f"`/drop 5 50000 1`  → 5-minute drop, 1 winner, 50,000 prize\n"
        f"`/stats`  → get chat-drop stats\n"
        f"`/about`  → get about Drop Bot\n"
    ),
    inline=inline
)

# Support / contact
help.add_field(
    name="📞 Support & Contact",
    value=(
        f"Need help or want to purchase subscription? open a support ticket in the [Support Server](https://discord.gg/uDcmHCMZuZ).\n"
        "For critical issues include exact commands and timestamps so we can reproduce."
    ),
    inline=inline
)

help.set_footer(text=footer_txt)