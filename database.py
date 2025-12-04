import sqlite3
import subprocess
import os
from dotenv import load_dotenv
load_dotenv()
import time
from sys import platform
from utils.constants import *


class DB:
    def __init__(self, path="data.db"):
        self.conn = sqlite3.connect(path)
        self.cur = self.conn.cursor()


    def insert(self, table, **fields):
        cols = ', '.join(fields.keys())
        vals = tuple(fields.values())
        placeholders = ', '.join('?' for _ in fields)
        self.cur.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", vals)
        self.conn.commit()

    def update(self, table, pk_name, pk_value, **fields):
        set_clause = ', '.join(f"{k}=?" for k in fields)
        values = tuple(fields.values()) + (pk_value,)
        self.cur.execute(
            f"UPDATE {table} SET {set_clause} WHERE {pk_name}=?", 
            values
        )
        self.conn.commit()

    def delete(self, table, pk_name, pk_value):
        self.cur.execute(
            f"DELETE FROM {table} WHERE {pk_name}=?",
            (pk_value,)
        )
        self.conn.commit()


    def get(self, table, **filters):
        if filters:
            cond: str = ' AND '.join(f"{k}=?" for k in filters)
            vals:tuple = tuple(filters.values())
            self.cur.execute(f"SELECT * FROM {table} WHERE {cond}", vals)
        else:
            self.cur.execute(f"SELECT * FROM {table}")
        return self.cur.fetchall()
    
    def get_as_dict(self, table, **filters):
        result = self.get(table, **filters)
        col_names = [col[0] for col in self.cur.description]
        return [dict(zip(col_names, row)) for row in result]

    # helper functions
    def get_server(self, server_id):
        return self.get("servers", server_id=server_id)
    
    def get_server_ids(self):
        data = self.cur.execute(f"SELECT * FROM servers")
        return [row[0] for row in data] 
    
    def get_channel_ids(self):
        data = self.cur.execute(f"SELECT * FROM servers")
        return [row[1] for row in data] 
    
    def get_sub_status(self, server_id):
        return self.cur.execute(f"SELECT sub FROM servers WHERE server_id={server_id}").fetchall()[0][0]
    
    def exists(self, table, **filters):
        return len(self.get(table, **filters)) > 0



PORT = 21952
PASSWORD:str = os.getenv("SQLITE_WEB_PASSWORD")
DB_PATH = "data.db"
PROCESS = None
domain = "127.0.0.1"

# class db_panel:
def start_sqlite_web():
    global PROCESS, domain

    if PROCESS and PROCESS.poll() is None:
        print(GREEN+"[DB PANEL] Already running"+RESET)
        return
    
    if not is_server:
        PROCESS = subprocess.Popen(
            [
                "python",
                "-m", "sqlite_web",
                DB_PATH,
                "--host", "0.0.0.0",
                "--port", str(PORT),
                "--password", PASSWORD
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    else:
        PROCESS = subprocess.Popen(
            [
                "python",
                "-m", "sqlite_web",
                DB_PATH,
                "--host", "0.0.0.0",
                "--port", str(PORT),
                "--password", PASSWORD
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            )
    if is_server:
        domain = "fi8.bot-hosting.net"

    print(BLUE+f"[DB PANEL] Running on http://{domain}:{PORT}"+RESET)
    # print(f"[DB PANEL] Password: {PASSWORD}")

def stop_sqlite_web():
    global PROCESS

    print(YELLOW+"[DB PANEL] Trying to stop DB panel..."+RESET)

    if PROCESS and PROCESS.poll() is None:
        PROCESS.terminate()
        print(GREEN+"[DB PANEL] Terminated."+RESET)
    else:
        print(YELLOW+"[DB PANEL] Not running or already stopped."+RESET)