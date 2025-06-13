import sqlite3
from datetime import datetime

class PlateHistory:
    def __init__(self, db_path='src/data/plates.db'):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS plate_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate TEXT NOT NULL,
                camera_id TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        
        # Criação de índice para acelerar a verificação de duplicatas
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_unique_entry 
            ON plate_history (plate, camera_id, timestamp)
        ''')
        
        self.conn.commit()


    from datetime import datetime

    def add_entry(self, plate, camera_id):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.cursor.execute('''
            SELECT 1 FROM plate_history 
            WHERE plate = ? AND camera_id = ? AND timestamp = ?
            LIMIT 1
        ''', (plate, camera_id, timestamp))

        if self.cursor.fetchone() is None:
            self.cursor.execute('''
                INSERT INTO plate_history (plate, camera_id, timestamp)
                VALUES (?, ?, ?)
            ''', (plate, camera_id, timestamp))
            self.conn.commit()
            print(f"[{camera_id}] Entrada adicionada ao histórico: {plate} - {timestamp}")
        else:
            print(f"[{camera_id}] Entrada duplicada ignorada: {plate} - {timestamp}")


    def list_all(self, limit=None):
        query = 'SELECT plate, camera_id, timestamp FROM plate_history ORDER BY timestamp DESC'
        if limit:
            query += f' LIMIT {limit}'
        self.cursor.execute(query)
        return self.cursor.fetchall()


    def search_by_plate(self, plate):
        self.cursor.execute('SELECT plate, camera_id, timestamp FROM plate_history WHERE plate = ?', (plate,))
        return self.cursor.fetchall()

    def clear_history(self):
        self.cursor.execute('DELETE FROM plate_history')
        self.conn.commit()
        print("Histórico de placas limpo com sucesso.")

    def __del__(self):
        self.conn.close()
