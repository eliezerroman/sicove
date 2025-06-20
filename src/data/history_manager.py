import sqlite3
from datetime import datetime

class PlateHistory:
    def __init__(self, db_path='src/data/plates.db'):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_table()

    def _create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plate_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate TEXT NOT NULL,
                camera_id TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_unique_entry 
            ON plate_history (plate, camera_id, timestamp)
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS registered_plates (
               plate TEXT PRIMARY KEY
            )
        ''')
        self.conn.commit()
        cursor.close()

    def is_plate_registered(self, plate):
        cursor = self.conn.cursor()
        cursor.execute('SELECT 1 FROM registered_plates WHERE plate = ?', (plate,))
        result = cursor.fetchone()
        cursor.close()
        return result is not None

    def register_plate(self, plate):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO registered_plates (plate) VALUES (?)', (plate,))
        self.conn.commit()
        cursor.close()

    def remove_plate(self, plate):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM registered_plates WHERE plate = ?', (plate,))
        self.conn.commit()
        cursor.close()

    def list_registered(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT plate FROM registered_plates')
        plates = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return plates

    def add_entry(self, plate, camera_id):
        cursor = self.conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute('''
            SELECT 1 FROM plate_history 
            WHERE plate = ? AND camera_id = ? AND timestamp = ?
            LIMIT 1
        ''', (plate, camera_id, timestamp))

        if cursor.fetchone() is None:
            cursor.execute('''
                INSERT INTO plate_history (plate, camera_id, timestamp)
                VALUES (?, ?, ?)
            ''', (plate, camera_id, timestamp))
            self.conn.commit()
            print(f"[{camera_id}] Entrada adicionada ao histórico: {plate} - {timestamp}")
        else:
            print(f"[{camera_id}] Entrada duplicada ignorada: {plate} - {timestamp}")
        cursor.close()

    def list_all(self, limit=None):
        cursor = self.conn.cursor()
        query = 'SELECT plate, camera_id, timestamp FROM plate_history ORDER BY timestamp DESC'
        if limit:
            query += f' LIMIT {limit}'
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        return results

    def search_by_plate(self, plate):
        cursor = self.conn.cursor()
        cursor.execute('SELECT plate, camera_id, timestamp FROM plate_history WHERE plate = ?', (plate,))
        results = cursor.fetchall()
        cursor.close()
        return results

    def clear_history(self):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM plate_history')
        self.conn.commit()
        cursor.close()
        print("Histórico de placas limpo com sucesso.")

    def __del__(self):
        self.conn.close()
