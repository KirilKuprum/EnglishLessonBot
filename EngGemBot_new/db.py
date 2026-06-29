import datetime
import psycopg2

class DataBase:
    def __init__(self, table_name, region):
        self.conn_params = "dbname=eng_bot_db user=bot_admin password=my_strong_password host=127.0.0.1"
        conn = psycopg2.connect(self.conn_params)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, data TEXT, current_index INTEGER, created_at TEXT)")
        conn.commit()
        cur.close()
        conn.close()

    def put_item(self, item: dict):
        conn = psycopg2.connect(self.conn_params)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (user_id, data, created_at) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO UPDATE SET data = %s",
            (str(item['user_id']), str(item.get('data', '')), str(datetime.datetime.now()), str(item.get('data', '')))
        )
        conn.commit()
        cur.close()
        conn.close()

    def get_item(self, user_id: int):
        conn = psycopg2.connect(self.conn_params)
        cur = conn.cursor()
        cur.execute("SELECT user_id, data FROM users WHERE user_id = %s", (str(user_id),))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return {'user_id': row[0], 'data': row[1]} if row else None

    def update_index(self, user_id, index):
        conn = psycopg2.connect(self.conn_params)
        cur = conn.cursor()
        cur.execute("UPDATE users SET current_index = %s WHERE user_id = %s", (index, str(user_id)))
        conn.commit()
        cur.close()
        conn.close()
