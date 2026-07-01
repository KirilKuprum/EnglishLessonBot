import datetime
import psycopg2
import json
import os

class DataBase:
    def __init__(self, table_name=None, region=None):
        db_name = os.getenv("DB_NAME", "eng_bot_db")
        db_user = os.getenv("DB_USER", "bot_admin")
        db_pass = os.getenv("DB_PASSWORD", "my_strong_password")
        db_host = os.getenv("DB_HOST", "127.0.0.1")
        db_port = os.getenv("DB_PORT", "5432")

        self.conn_params = f"dbname={db_name} user={db_user} password={db_pass} host={db_host} port={db_port}"
        
        conn = psycopg2.connect(self.conn_params)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY, 
                current_cards TEXT, 
                current_index INTEGER DEFAULT 0, 
                status TEXT,
                stats_correct INTEGER DEFAULT 0,
                stats_wrong INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id SERIAL PRIMARY KEY,
                user_id TEXT,
                passed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                correct_count INTEGER,
                wrong_count INTEGER,
                total_words INTEGER
            )
        """)
        
        conn.commit()
        cur.close()
        conn.close()

    def put_item(self, item: dict):
        conn = psycopg2.connect(self.conn_params)
        cur = conn.cursor()
        
        cards_json = json.dumps(item.get('current_cards', []))
        cur.execute(
            """INSERT INTO users (user_id, current_cards, current_index, status, created_at) 
               VALUES (%s, %s, %s, %s, %s) 
               ON CONFLICT (user_id) 
               DO UPDATE SET current_cards = %s, current_index = %s, status = %s""",
            (
                str(item['user_id']), cards_json, item.get('current_index', 0), item.get('status', 'pending'), str(datetime.datetime.now()),
                cards_json, item.get('current_index', 0), item.get('status', 'pending')
            )
        )
        conn.commit()
        cur.close()
        conn.close()

    def get_item(self, user_id):
        conn = psycopg2.connect(self.conn_params)
        cur = conn.cursor()
        cur.execute("SELECT user_id, current_cards, current_index, status, stats_correct, stats_wrong FROM users WHERE user_id = %s", (str(user_id),))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row:
            return {
                'user_id': row[0],
                'current_cards': json.loads(row[1]) if row[1] else [],
                'current_index': row[2],
                'status': row[3],
                'stats_correct': row[4],  
                'stats_wrong': row[5]
            }
        return None

    def update_index(self, user_id, index):
        conn = psycopg2.connect(self.conn_params)
        cur = conn.cursor()
        cur.execute("UPDATE users SET current_index = %s WHERE user_id = %s", (index, str(user_id)))
        conn.commit()
        cur.close() 
        conn.close()

    def update_status(self, user_id, status):
        conn = psycopg2.connect(self.conn_params)
        cur = conn.cursor()
        cur.execute("UPDATE users SET status = %s WHERE user_id = %s", (status, str(user_id)))
        conn.commit()
        cur.close() 
        conn.close()

    def update_stats(self, user_id, is_correct: bool):
        conn = psycopg2.connect(self.conn_params)
        cur = conn.cursor()
        if is_correct:
            cur.execute("UPDATE users SET stats_correct = stats_correct + 1 WHERE user_id = %s", (str(user_id),))
        else:
            cur.execute("UPDATE users SET stats_wrong = stats_wrong + 1 WHERE user_id = %s", (str(user_id),))
        conn.commit()
        cur.close() 
        conn.close()
        
   def add_to_history(self, user_id, correct, wrong, total):
        conn = psycopg2.connect(self.conn_params)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO history (user_id, correct_count, wrong_count, total_words) VALUES (%s, %s, %s, %s)",
            (str(user_id), correct, wrong, total)
        )
        conn.commit()
        cur.close()
        conn.close()

    def get_history(self, user_id):
        conn = psycopg2.connect(self.conn_params)
        cur = conn.cursor()
        cur.execute("SELECT passed_at, correct_count, wrong_count, total_words FROM history WHERE user_id = %s ORDER BY passed_at DESC", (str(user_id),))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
