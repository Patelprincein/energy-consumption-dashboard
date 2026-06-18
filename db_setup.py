import sqlite3
import pandas as pd
import os
import glob

def setup_database():
    db_path = 'energy_data.db'
    # Connect to SQLite (creates the file if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # We will load the raw CSV files directly into SQL without cleaning them yet
    raw_files = glob.glob('data/raw/*.csv')
    
    if not raw_files:
        print("No raw data found in 'data/raw/'. Please run generate_data.py first.")
        return

    print(f"Found {len(raw_files)} raw datasets. Loading into {db_path}...")

    for file_path in raw_files:
        file_name = os.path.basename(file_path)
        table_name = os.path.splitext(file_name)[0]
        
        # Read raw CSV using pandas
        df = pd.read_csv(file_path)
        
        # Load directly into SQL SQLite table, replacing if it already exists
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"Loaded '{table_name}' table with {len(df)} rows.")
        
    print("\nDatabase setup complete. Raw tables are available in 'energy_data.db'")
    
    # Just to verify, let's list the tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in DB:", [t[0] for t in tables])
    
    conn.close()

if __name__ == "__main__":
    setup_database()
