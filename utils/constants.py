from dotenv import load_dotenv
from os import getenv
from colorama import Fore

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
    100: 750_000,
    250: 1_000_000,
    500: 2_500_000,
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