# load.py

import pandas as pd
import xarray as xr
import glob
import os
import numpy as np

BASE_DIR = './FloatDATA/2026'
search_pattern = os.path.join(BASE_DIR, '*.nc')

all_files = glob.glob(search_pattern)

if not all_files:
    print("No NetCDF files found.")
    exit()

all_argo_data = []

for file_path in all_files:
    try:
        with xr.open_dataset(file_path) as ds:
            platform_number = int(ds['PLATFORM_NUMBER'].values[0])

            if np.issubdtype(ds['JULD'].dtype, np.datetime64):
                profile_time = ds['JULD'].values
            else:
                reference_date = pd.to_datetime(ds['REFERENCE_DATE_TIME'].values.astype(str))
                profile_time = reference_date + pd.to_timedelta(ds['JULD'].values, unit='D')

            df = pd.DataFrame({
                'platform_number': platform_number,
                'time': profile_time,
                'latitude': ds['LATITUDE'].values,
                'longitude': ds['LONGITUDE'].values,
                'cycle_number': ds['CYCLE_NUMBER'].values,
                'pressure_adjusted': list(ds['PRES_ADJUSTED'].values),
                'temp_adjusted': list(ds['TEMP_ADJUSTED'].values),
                'psal_adjusted': list(ds['PSAL_ADJUSTED'].values),
            })

            df = df.explode(
                ['pressure_adjusted', 'temp_adjusted', 'psal_adjusted'],
                ignore_index=True
            )

            all_argo_data.append(df)

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

final_df = pd.concat(all_argo_data, ignore_index=True)
final_df.dropna(inplace=True)

output_file = 'argo_data.parquet'
final_df.to_parquet(output_file)

print("Parquet generated.")
