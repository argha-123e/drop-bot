import sqlite3

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

    
    def get_server(self, server_id):
        return self.get("servers", server_id=server_id)
    
    def get_server_ids(self):
        data = self.cur.execute(f"SELECT * FROM servers")
        return [row[0] for row in data] 
    
    def get_channel_ids(self):
        data = self.cur.execute(f"SELECT * FROM servers")
        return [row[1] for row in data] 
    
    def exists(self, table, **filters):
        return len(self.get(table, **filters)) > 0