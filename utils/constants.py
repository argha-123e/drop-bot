from dotenv import load_dotenv
from os import getenv
from colorama import Fore
from sys import platform

is_server:bool = False 
'''Used to know if the shard is on local pc or on cloud'''

if platform == "win32":
    is_server = False
else:
    is_server = True

# owners
owner_ids = [
    1206904635420450856
]

# dev id
DEV_ID:int = [
    1206904635420450856
]

# allowed users
allowed_users = [
    1315914791851655229,
    1310835757715423284,
    1315914791851655229
]


# Embed Colors
MAIN_COLOR = 0x5865F2
SUCCESS_COLOR = 0x43FF33
ERROR_COLOR = 0xFF0000


# Load .env variables
# load_dotenv()
# TOKEN: str = getenv("TOKEN")

def get_token() -> str:
    load_dotenv()
    if is_server:
        return getenv("TOKEN")
    return getenv("PVT_TOKEN")

# owo plans
OWO_PLANS: dict = {
    100: 500_000,
    250: 1_000_000,
    500: 2_000_000,
    1000: 3_250_000,
    2500: 4_250_000,
    5000: 5_000_000,
    10000: 6_500_000,
}

# hcg plans
HCG_PLANS: dict = {
    100: 350_000,
    250: 700_000,
    500: 1_400_000,
    1000: 2_250_000,
    2500: 3_000_000,
    5000: 3_500_000,
    10000: 4_550_000,
}

# discord msg char limit
MAX_DISCORD_LEN: int = 1900

# PREFIX
PREFIX = "."

# gwy limit
gwy_limit = 100

# gwy time limit
gwy_time_limit:int = 60

# logger webhooks 
sub_WEBHOOK: str = getenv("sub_WEBHOOK")
func_WEBHOOK: str = getenv("func_WEBHOOK")
sql_WEBHOOK: str = getenv("sql_WEBHOOK")
gwy_WEBHOOK: str = getenv("gwy_WEBHOOK")
data_backup_WEBHOOK: str = getenv("data_db_backup")

# Print colors
RED = Fore.RED
GREEN = Fore.GREEN
BLUE = Fore.BLUE
YELLOW = Fore.YELLOW
CYAN = Fore.CYAN
RESET = Fore.RESET



# platform
footer_txt = "Drop Bot • made with 💖"
if not is_server:
    footer_txt = "Drop Bot • made with 💖 (pc)"
else:
    footer_txt = "Drop Bot • made with 💖"