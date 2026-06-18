import pandas as pd
import numpy as np
import random
import os
from datetime import datetime, timedelta

def generate_messy_data():
    os.makedirs('data/raw', exist_ok=True)
    
    # 1. East Coast Data - Mostly clean, but missing some consumption values
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='h')
    east_df = pd.DataFrame({'Datetime': dates})
    east_df['Region'] = 'East_Coast'
    # Base load + daily pattern + seasonal pattern
    base_load = 500
    daily_pattern = np.sin(np.pi * east_df['Datetime'].dt.hour / 12) * 200
    seasonal_pattern = np.sin(np.pi * east_df['Datetime'].dt.dayofyear / 182.5) * 300
    east_df['Consumption_MW'] = base_load + daily_pattern + seasonal_pattern + np.random.normal(0, 50, len(east_df))
    
    # Inject missing values
    missing_indices = random.sample(range(len(east_df)), int(len(east_df) * 0.05))
    east_df.loc[missing_indices, 'Consumption_MW'] = np.nan
    east_df.to_csv('data/raw/east_coast_energy_2024.csv', index=False)
    
    # 2. West Coast Data - Different date format, strings mixed in consumption column
    west_df = pd.DataFrame({'Date': dates.strftime('%d/%m/%Y %H:%M')}) # DD/MM/YYYY
    west_df['Area'] = 'West Coast'
    # Base load + different patterns
    west_df['Usage_kW'] = (base_load + daily_pattern * 1.5 + seasonal_pattern * 0.8 + np.random.normal(0, 40, len(west_df))) * 1000 # in kW instead of MW
    
    # Inject strings ("N/A", "Error") into numeric column
    error_indices = random.sample(range(len(west_df)), int(len(west_df) * 0.02))
    west_df['Usage_kW'] = west_df['Usage_kW'].astype(object)
    west_df.loc[error_indices, 'Usage_kW'] = random.choices(['N/A', 'Error', 'Down'], k=len(error_indices))
    west_df.to_csv('data/raw/west_coast_power_24.csv', index=False)
    
    # 3. Midwest Data - Extreme outliers, missing rows entirely, mixed column names
    # Start with a clean set then corrupt it
    midwest_dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='h')
    # Drop some random hours entirely
    drop_indices = random.sample(range(len(midwest_dates)), int(len(midwest_dates) * 0.01))
    midwest_dates = midwest_dates.drop(midwest_dates[drop_indices])
    
    midwest_df = pd.DataFrame({'time_stamp': midwest_dates})
    midwest_df['location'] = 'Mid-West'
    
    base_load_mw = 400
    midwest_df['power_mw'] = base_load_mw + np.sin(np.pi * midwest_df['time_stamp'].dt.hour / 12) * 150 + np.random.normal(0, 30, len(midwest_df))
    
    # Inject extreme outliers (e.g., negative values, sudden 10x spikes)
    outlier_indices = random.sample(range(len(midwest_df)), 50)
    midwest_df.loc[outlier_indices[:25], 'power_mw'] = midwest_df.loc[outlier_indices[:25], 'power_mw'] * 10
    midwest_df.loc[outlier_indices[25:], 'power_mw'] = -500 # impossible negative
    
    midwest_df.to_csv('data/raw/midwest_elec_data_2024.csv', index=False)

    print("Messy raw datasets successfully generated in 'data/raw/'.")

if __name__ == "__main__":
    generate_messy_data()
