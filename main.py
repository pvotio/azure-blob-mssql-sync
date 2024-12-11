import os
import re
import pandas as pd
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from azure.identity import ManagedIdentityCredential, DefaultAzureCredential

# Load environment variables once
load_dotenv()

def extract_extracted_name_folder_and_filename(blob_path, pattern):
    """
    Extract extracted_name, folder name, and filename from the blob path using the provided regex pattern.
    """
    folder_name, file_name = os.path.split(blob_path)
    extracted_name_match = re.search(pattern, file_name)
    extracted_name = extracted_name_match.group(1) if extracted_name_match else None
    return {
        'extracted_name': extracted_name,
        'folder_name': folder_name,
        'file_name': file_name
    }

def list_pdfs_from_blob_storage():
    """
    Connects to Azure Blob Storage using Managed Identity, lists all PDF files in the specified container,
    and extracts extracted_name, folder name, and file name for each blob.
    """
    storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    container_name = os.getenv("AZURE_BLOB_CONTAINER_NAME")

    if not storage_account_name or not container_name:
        print("Azure storage account name or container name is not set in environment variables.")
        return pd.DataFrame()  # Return empty DataFrame

    try:
        # Construct the Blob service URL
        blob_service_url = f"https://{storage_account_name}.blob.core.windows.net"
        # Use DefaultAzureCredential which works with Managed Identity
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

    # Ensure uniqueness of extracted_name + folder_name
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
    """
    Upsert a DataFrame to an MSSQL table using SQLAlchemy and a temporary staging table.
    Handles inserts, updates, and deletes in bulk.
    """
    db_server = os.getenv("DB_SERVER")
    db_name = os.getenv("DB_NAME")
    db_driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")  # Default driver

    if not all([db_server, db_name]):
        print("Database server or name is not set in environment variables.")
        return

    try:
        credential = DefaultAzureCredential()
        token = credential.get_token("https://database.windows.net/.default")
        access_token = token.token
    except Exception as e:
        print("Failed to obtain access token for SQL Database:")
        print(str(e))
        return

    connection_string = f"mssql+pyodbc://@{db_server}/{db_name}?driver={db_driver}&Authentication=ActiveDirectoryAccessToken"

    try:
        engine = create_engine(
            connection_string,
            connect_args={
                "azure_access_token": access_token
            },
            fast_executemany=True  # Enable fast executemany for bulk inserts
        )
    except Exception as e:
        print("Failed to create SQLAlchemy engine:")
        print(str(e))
        return

    staging_table_name = "#staging_products_blob_pdfs"

    try:
        with engine.connect() as connection:
            with connection.begin():
                # Create temporary staging table
                create_table_sql = f"""
                CREATE TABLE {staging_table_name} (
                    extracted_name VARCHAR(12),
                    folder_name VARCHAR(255),
                    file_name VARCHAR(255),
                    timestamp_created_utc DATETIME,
                    PRIMARY KEY (extracted_name, folder_name)
                );
                """
                connection.execute(text(create_table_sql))
                print(f"Temporary staging table {staging_table_name} created with composite primary key (extracted_name, folder_name).")

                # Add timestamp_created_utc column
                current_utc = datetime.utcnow()
                df['timestamp_created_utc'] = pd.Timestamp(current_utc)

                # Convert DataFrame to list of dictionaries
                records = df.to_dict(orient='records')

                # Bulk insert into temporary table
                insert_sql = f"""
                INSERT INTO {staging_table_name} (extracted_name, folder_name, file_name, timestamp_created_utc)
                VALUES (:extracted_name, :folder_name, :file_name, :timestamp_created_utc);
                """
                connection.execute(text(insert_sql), records)
                print(f"Inserted {len(records)} unique records into temporary staging table.")

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
                connection.execute(text(merge_sql))
                print("MERGE operation completed successfully with composite key (extracted_name, folder_name).")
    except SQLAlchemyError as e:
        print("An error occurred during the upsert using temporary staging table:")
        print(str(e))
    finally:
        engine.dispose()

if __name__ == "__main__":
    df = list_pdfs_from_blob_storage()
    if not df.empty:
        target_table = os.getenv("TARGET_SQL_TABLE")
        upsert_using_temp_staging(df, target_table)
    else:
        print("No data to upsert.")
