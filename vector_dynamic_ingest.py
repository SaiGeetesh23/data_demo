# vector_dynamic_ingest.py

import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
from langchain_milvus import Milvus
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain_core.documents import Document

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

ZILLIZ_CLOUD_URI = os.getenv('ZILLIZ_CLOUD_URI')
ZILLIZ_CLOUD_USERNAME = os.getenv('ZILLIZ_CLOUD_USERNAME')
ZILLIZ_CLOUD_PASSWORD = os.getenv('ZILLIZ_CLOUD_PASSWORD')

embedding_model = NVIDIAEmbeddings(
    model="nvidia/llama-3.2-nv-embedqa-1b-v2"
)

engine = create_engine(DB_URL)
df = pd.read_sql("SELECT platform_number, time, latitude, longitude FROM profiles", engine)

df['time'] = pd.to_datetime(df['time'])
df['year_month'] = df['time'].dt.to_period('M')

documents = []

for platform_num, group in df.groupby('platform_number'):
    doc = Document(
        page_content=f"Argo float {platform_num} active between {group['time'].min()} and {group['time'].max()}",
        metadata={'platform_number': int(platform_num)},
        id=f"float_{platform_num}"
    )
    documents.append(doc)

vector_db = Milvus(
    embedding_function=embedding_model,
    connection_args={
        "uri": ZILLIZ_CLOUD_URI,
        "user": ZILLIZ_CLOUD_USERNAME,
        "password": ZILLIZ_CLOUD_PASSWORD,
        "secure": True,
    },
    collection_name="LangChainCollection"
)

vector_db.add_documents(documents)

print("Vector DB updated.")
