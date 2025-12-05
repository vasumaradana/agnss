import sqlite3
import pandas as pd
import os
from typing import Optional, Dict, Any

DB_PATH = "agnss.db"

def init_db():
    """Initialize the SQLite database with the required schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create cells table
    # Schema based on OpenCellID CSV format:
    # radio, mcc, mnc, lac, cid, psc, lon, lat, range, samples, changeable, created, updated, averageSignal
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cells (
            radio TEXT,
            mcc INTEGER,
            mnc INTEGER,
            lac INTEGER,
            cid INTEGER,
            psc INTEGER,
            lon REAL,
            lat REAL,
            range INTEGER,
            samples INTEGER,
            changeable INTEGER,
            created INTEGER,
            updated INTEGER,
            averageSignal INTEGER,
            PRIMARY KEY (radio, mcc, mnc, lac, cid)
        )
    ''')
    
    # Create index for fast lookup
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_cell_lookup 
        ON cells (mcc, mnc, lac, cid, radio)
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

def import_csv(csv_path: str):
    """Import OpenCellID CSV data into the database."""
    if not os.path.exists(csv_path):
        print(f"Error: File {csv_path} not found.")
        return

    print(f"Importing data from {csv_path}...")
    
    # OpenCellID CSV headers (implied, as the files often don't have headers)
    # Based on the file view: GSM,310,260,51051,44473,0,-71.11,42.3588,1033,19,1,1459813819,1745016670,0
    # radio, mcc, mnc, lac, cid, psc, lon, lat, range, samples, changeable, created, updated, averageSignal
    columns = [
        "radio", "mcc", "mnc", "lac", "cid", "psc", 
        "lon", "lat", "range", "samples", "changeable", 
        "created", "updated", "averageSignal"
    ]
    
    chunk_size = 100000
    conn = sqlite3.connect(DB_PATH)
    
    try:
        for chunk in pd.read_csv(csv_path, names=columns, chunksize=chunk_size):
            chunk.to_sql("cells", conn, if_exists="append", index=False)
            print(f"Imported {len(chunk)} rows...")
            
        print("Import completed successfully.")
    except Exception as e:
        print(f"Error during import: {e}")
    finally:
        conn.close()

def get_cell_location(mcc: int, mnc: int, lac: int, cid: int, radio: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Query the database for a cell tower's location."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT lat, lon, range FROM cells WHERE mcc=? AND mnc=? AND lac=? AND cid=?"
    params = [mcc, mnc, lac, cid]
    
    if radio:
        query += " AND radio=?"
        params.append(radio)
        
    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

if __name__ == "__main__":
    # Example usage
    init_db()
    # import_csv("310.csv") # Uncomment to run import
