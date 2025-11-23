from dotenv import load_dotenv
from os import getenv

# dev id
DEV_ID:int = 1206904635420450856


# Embed Colors
MAIN_COLOR = 0x5865F2
SUCCESS_COLOR = 0x43FF33
ERROR_COLOR = 0xFF0000


# Load .env variables
load_dotenv()
TOKEN: str = getenv("TOKEN")

# owo plans
PLAN_OWO: dict = {
    100: 500_000,
    250: 1_000_000,
    500: 2_000_000,
    1000: 4_000_000,
    5000: 7_000_000,
    10000: 10_000_000,
}

# discord msg char limit
MAX_DISCORD_LEN: int = 1900

# PREFIX
PREFIX = "."

# gwy limit
gwy_limit = 100

# gwy time limit
gwy_time_limit:int = 60