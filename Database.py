import sqlite3
class Database:
    def __init__(self, db_name):
        self.db_name = db_name

    def setup_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS network_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                ping_latency REAL,
                packet_loss REAL,
                download_speed REAL,
                upload_speed REAL,
                status TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def insert_log(self, ping_latency, packet_loss, download_speed, upload_speed, status):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO network_logs (timestamp, ping_latency, packet_loss, download_speed, upload_speed, status)
            VALUES (datetime('now'), ?, ?, ?, ?, ?)
        ''', (ping_latency, packet_loss, download_speed, upload_speed, status))
        conn.commit()
        conn.close()
