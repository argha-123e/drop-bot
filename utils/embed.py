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

about.set_thumbnail(url="https://cdn.discordapp.com/avatars/1438150894071058533/568c0cc9f3df4fdd5eca299de6cc5914.webp?size=1024")

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
help.set_thumbnail(url="https://cdn.discordapp.com/avatars/1438150894071058533/568c0cc9f3df4fdd5eca299de6cc5914.webp?size=1024")

# Slash commands for users
help.add_field(
    name="🕹 Slash Commands",
    value=(
        "`/drop <minutes> <prize> <winners>` — Start a giveaway in this channel.\n"
        "`/stats [server_id]` — Show server chat drops & subscription stats (owner or dev).\n"
        "`/setup` — runs setup wizard to setup you're server.\n"
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
        "`/setup` — runs setup wizard to setup you're server.\n"
        f"`/stats`  → get chat-drop stats\n"
        f"`.about`  → get about Drop Bot\n"
        f"`.plans`  → get Drop Bot active plans\n"
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

# plan embed 
#################################################################################################################
plan = Embed(
    title="SUBSCRIPTION PLANS",
    description=(
        ""
    ),
    color=MAIN_COLOR
)
plan.set_author(name="Drop Bot")
plan.set_thumbnail(url="https://cdn.discordapp.com/avatars/1438150894071058533/568c0cc9f3df4fdd5eca299de6cc5914.webp?size=1024")

plan.add_field(name="1-100 members",value=(f"{OWO_PLANS[100]:,} OWO or {HCG_PLANS[100]:,} hcg/month"),inline=inline)
plan.add_field(name="101-250 members",value=(f"{OWO_PLANS[250]:,} OWO or {HCG_PLANS[250]:,} hcg/month"),inline=inline)
plan.add_field(name="251-500 members",value=(f"{OWO_PLANS[500]:,} OWO or {HCG_PLANS[500]:,} hcg/month"),inline=inline)
plan.add_field(name="501-1000 members",value=(f"{OWO_PLANS[1000]:,} OWO or {HCG_PLANS[1000]:,} hcg/month"),inline=inline)
plan.add_field(name="501-1000 members",value=(f"{OWO_PLANS[2500]:,} OWO or {HCG_PLANS[2500]:,} hcg/month"),inline=inline)
plan.add_field(name="1001-5000 members",value=(f"{OWO_PLANS[5000]:,} OWO or {HCG_PLANS[5000]:,} hcg/month"),inline=inline)
plan.add_field(name="5001-10000 members",value=(f"{OWO_PLANS[10000]:,} OWO or {HCG_PLANS[10000]:,} hcg/month"),inline=inline)
plan.set_footer(text=footer_txt) 