import os
import re
import struct
import pandas as pd
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from datetime import datetime
from azure.identity import DefaultAzureCredential
import pyodbc

load_dotenv()

def get_pyodbc_attrs(access_token: str) -> dict:
    # Same as proven script
    SQL_COPT_SS_ACCESS_TOKEN = 1256
    enc_token = access_token.encode('utf-16-le')
    token_struct = struct.pack('=i', len(enc_token)) + enc_token
    return {SQL_COPT_SS_ACCESS_TOKEN: token_struct}

def extract_extracted_name_folder_and_filename(blob_path, pattern):
    folder_name, file_name = os.path.split(blob_path)
    extracted_name_match = re.search(pattern, file_name, re.IGNORECASE)
    extracted_name = extracted_name_match.group(1) if extracted_name_match else None
    return {
        'extracted_name': extracted_name,
        'folder_name': folder_name,
        'file_name': file_name
    }

def list_pdfs_from_blob_storage():
    storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    container_name = os.getenv("AZURE_BLOB_CONTAINER_NAME")

    if not storage_account_name or not container_name:
        print("Azure storage account name or container name is not set in environment variables.")
        return pd.DataFrame()

    try:
        blob_service_url = f"https://{storage_account_name}.blob.core.windows.net"
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(account_url=blob_service_url, credential=credential)
        container_client = blob_service_client.get_container_client(container_name)
    except Exception as e:
        print("Failed to connect to Azure Blob Storage:")
        print(str(e))
        return pd.DataFrame()

    try:
        blob_paths = [blob.name for blob in container_client.list_blobs() if blob.name.lower().endswith('.pdf')]
    except Exception as e:
        print("Failed to list blobs in the container:")
        print(str(e))
        return pd.DataFrame()

    extraction_pattern = os.getenv("EXTRACTION_PATTERN")
    extracted_data = [extract_extracted_name_folder_and_filename(blob_path, extraction_pattern) for blob_path in blob_paths]
    df = pd.DataFrame(extracted_data)
    df.dropna(subset=['extracted_name'], inplace=True)

    before_dropping = len(df)
    df.drop_duplicates(subset=['extracted_name', 'folder_name'], inplace=True)
    after_dropping = len(df)
    duplicates_removed = before_dropping - after_dropping
    if duplicates_removed > 0:
        print(f"Removed {duplicates_removed} duplicate extracted_name + folder_name combinations.")

    print("Extracted DataFrame:")
    print(df.head())
    return df

def upsert_using_temp_staging(df, table_name):
    db_server = os.getenv("MSSQL_SERVER")
    db_name = os.getenv("MSSQL_DATABASE")

    if not all([db_server, db_name]):
        print("Database server or name is not set in environment variables.")
        return

    # Obtain Azure AD token (as in the proven script)
    try:
        credential = DefaultAzureCredential()
        token = credential.get_token("https://database.windows.net/.default")
        access_token = token.token
    except Exception as e:
        print("Failed to obtain access token for SQL Database:")
        print(str(e))
        return

    # Construct connection URL as in proven script - no Authentication, no UID/PWD
    connection_url = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={db_server};"
        f"DATABASE={db_name};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
    )

    attrs = get_pyodbc_attrs(access_token)

    try:
        # Connect just like the proven script
        with pyodbc.connect(connection_url, attrs_before=attrs) as connection:
            connection.autocommit = False
            cursor = connection.cursor()

            # Create temporary staging table
            staging_table_name = "#staging_blob_pdfs"
            create_table_sql = f"""
            CREATE TABLE {staging_table_name} (
                extracted_name VARCHAR(12),
                folder_name VARCHAR(255),
                file_name VARCHAR(255),
                timestamp_created_utc DATETIME,
                PRIMARY KEY (extracted_name, folder_name)
            );
            """
            cursor.execute(create_table_sql)
            print(f"Temporary staging table {staging_table_name} created.")

            current_utc = datetime.utcnow()
            df['timestamp_created_utc'] = pd.Timestamp(current_utc)

            # Insert records into staging table
            insert_sql = f"""
            INSERT INTO {staging_table_name} (extracted_name, folder_name, file_name, timestamp_created_utc)
            VALUES (?, ?, ?, ?);
            """
            records = df[['extracted_name', 'folder_name', 'file_name', 'timestamp_created_utc']].values.tolist()
            cursor.executemany(insert_sql, records)
            print(f"Inserted {len(records)} records into temporary staging table.")

            # Perform MERGE operation
            merge_sql = f"""
            MERGE INTO {table_name} AS target
            USING {staging_table_name} AS source
            ON target.extracted_name = source.extracted_name AND target.folder_name = source.folder_name
            WHEN MATCHED THEN 
                UPDATE SET 
                    file_name = source.file_name, 
                    timestamp_created_utc = source.timestamp_created_utc
            WHEN NOT MATCHED BY TARGET THEN
                INSERT (extracted_name, folder_name, file_name, timestamp_created_utc) 
                VALUES (source.extracted_name, source.folder_name, source.file_name, source.timestamp_created_utc)
            WHEN NOT MATCHED BY SOURCE THEN
                DELETE;
            """
            cursor.execute(merge_sql)
            print("MERGE operation completed successfully.")

            connection.commit()

    except pyodbc.Error as e:
        print("An error occurred during the upsert:")
        print(str(e))

if __name__ == "__main__":
    df = list_pdfs_from_blob_storage()
    if not df.empty:
        target_table = os.getenv("TARGET_SQL_TABLE")
        upsert_using_temp_staging(df, target_table)
    else:
        print("No data to upsert.")
