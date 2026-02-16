# storeinpostgres.py

import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

engine = create_engine(DB_URL)

create_tables_sql = """
CREATE TABLE IF NOT EXISTS floats (
    platform_number INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS profiles (
    profile_id SERIAL PRIMARY KEY,
    platform_number INTEGER REFERENCES floats(platform_number),
    time TIMESTAMP,
    latitude REAL,
    longitude REAL,
    cycle_number INTEGER,
    UNIQUE (platform_number, cycle_number)
);

CREATE TABLE IF NOT EXISTS measurements (
    measurement_id SERIAL PRIMARY KEY,
    profile_id INTEGER REFERENCES profiles(profile_id),
    pressure_adjusted REAL,
    temp_adjusted REAL,
    psal_adjusted REAL,
    UNIQUE (profile_id, pressure_adjusted)
);
"""

with engine.connect() as connection:
    connection.execute(text(create_tables_sql))
    connection.commit()

df = pd.read_parquet("argo_data.parquet")

with engine.connect() as connection:
    with connection.begin():

        # floats
        floats_df = df[['platform_number']].drop_duplicates()
        floats_df.to_sql("temp_floats", connection, if_exists="replace", index=False)

        connection.execute(text("""
            INSERT INTO floats(platform_number)
            SELECT platform_number FROM temp_floats
            ON CONFLICT DO NOTHING;
        """))

        # profiles
        profiles_df = df[['platform_number','cycle_number','time','latitude','longitude']].drop_duplicates()
        profiles_df.to_sql("temp_profiles", connection, if_exists="replace", index=False)

        connection.execute(text("""
            INSERT INTO profiles(platform_number,cycle_number,time,latitude,longitude)
            SELECT platform_number,cycle_number,time,latitude,longitude
            FROM temp_profiles
            ON CONFLICT (platform_number,cycle_number)
            DO UPDATE SET time=EXCLUDED.time;
        """))

        # measurements
        profiles_ids = pd.read_sql("SELECT profile_id, platform_number, cycle_number FROM profiles", connection)

        merged = pd.merge(df, profiles_ids, on=['platform_number','cycle_number'])

        merged[['profile_id','pressure_adjusted','temp_adjusted','psal_adjusted']].to_sql(
            "temp_measurements",
            connection,
            if_exists="replace",
            index=False
        )

        connection.execute(text("""
            INSERT INTO measurements(profile_id,pressure_adjusted,temp_adjusted,psal_adjusted)
            SELECT profile_id,pressure_adjusted,temp_adjusted,psal_adjusted
            FROM temp_measurements
            ON CONFLICT (profile_id,pressure_adjusted)
            DO UPDATE SET
                temp_adjusted=EXCLUDED.temp_adjusted,
                psal_adjusted=EXCLUDED.psal_adjusted;
        """))

        connection.execute(text("DROP TABLE temp_floats;"))
        connection.execute(text("DROP TABLE temp_profiles;"))
        connection.execute(text("DROP TABLE temp_measurements;"))

print("PostgreSQL updated.")
