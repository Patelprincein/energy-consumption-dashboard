import sqlite3
import pandas as pd
import numpy as np
import os

def clean_data_pipeline():
    print("Starting Data Cleaning Pipeline...")
    
    # Connect to the database
    db_path = 'energy_data.db'
    if not os.path.exists(db_path):
        print("Database not found! Process aborted.")
        return
        
    conn = sqlite3.connect(db_path)
    
    # 1. Clean East Coast Data
    print("Cleaning East Coast Data...")
    east_df = pd.read_sql("SELECT * FROM east_coast_energy_2024", conn)
    # Convert string datetime to actual datetime objects
    east_df['Datetime'] = pd.to_datetime(east_df['Datetime'])
    # Handle missing values: We'll use linear interpolation for time-series holes
    east_df['Consumption_MW'] = east_df['Consumption_MW'].interpolate(method='linear')
    # Standardize column mappings for a unified schema
    east_df = east_df.rename(columns={
        'Datetime': 'timestamp', 
        'Region': 'region', 
        'Consumption_MW': 'consumption_mw'
    })
    
    # 2. Clean West Coast Data
    print("Cleaning West Coast Data...")
    west_df = pd.read_sql("SELECT * FROM west_coast_power_24", conn)
    # Format was DD/MM/YYYY HH:MM - Parse it correctly
    west_df['Date'] = pd.to_datetime(west_df['Date'], format='%d/%m/%Y %H:%M')
    # Fix the strings ("N/A", "Error") mixed into the column by forcing numeric, invalid to NaN
    west_df['Usage_kW'] = pd.to_numeric(west_df['Usage_kW'], errors='coerce')
    # Interpolate the newly injected NaNs
    west_df['Usage_kW'] = west_df['Usage_kW'].interpolate(method='linear')
    # Convert kW to MW to standardize across regions
    west_df['consumption_mw'] = west_df['Usage_kW'] / 1000.0
    # Standardize names and columns
    west_df['Area'] = 'West_Coast' 
    west_df = west_df.rename(columns={'Date': 'timestamp', 'Area': 'region'})
    west_df = west_df[['timestamp', 'region', 'consumption_mw']] # drop old usage_kw column
    
    # 3. Clean Midwest Data
    print("Cleaning Midwest Data...")
    midwest_df = pd.read_sql("SELECT * FROM midwest_elec_data_2024", conn)
    midwest_df['time_stamp'] = pd.to_datetime(midwest_df['time_stamp'])
    
    # Handle extreme outliers (Wait! We injected values like -500 and very large values)
    # Let's cap negative values to 0, and clip extreme highs
    # Specifically, if power > 2000 MW, it's likely our 10x error
    midwest_df['power_mw'] = midwest_df['power_mw'].apply(lambda x: np.nan if x < 0 or x > 2000 else x)
    midwest_df['power_mw'] = midwest_df['power_mw'].interpolate(method='linear')
    
    # Standardize columns
    midwest_df['location'] = 'Midwest'
    midwest_df = midwest_df.rename(columns={'time_stamp': 'timestamp', 'location': 'region', 'power_mw': 'consumption_mw'})
    
    # Combine All Cleaned Data
    print("Combining all regional datasets...")
    combined_df = pd.concat([east_df, west_df, midwest_df], ignore_index=True)
    
    # Sort by timestamp to ensure chronological order
    combined_df = combined_df.sort_values(by='timestamp').reset_index(drop=True)
    
    # Export Clean Data back to SQL
    combined_df.to_sql('clean_energy_data', conn, if_exists='replace', index=False)
    print("Cleaned data saved to 'clean_energy_data' table in SQLite.")
    
    # Export to Excel as requested
    excel_path = 'Cleaned_Energy_Data.xlsx'
    # We will export a subset or aggregated chunk if it's too huge, but 3 regions * 8760 hours = 26,280 rows.
    # Excel handles 26k rows instantly.
    print(f"Exporting data to {excel_path}...")
    combined_df.to_excel(excel_path, sheet_name='Clean_Data', index=False)
    print("Data cleaning pipeline successfully finished!")
    
    conn.close()

if __name__ == "__main__":
    clean_data_pipeline()
