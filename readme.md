### Azure Blob Storage to SQL Database Upsert

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Docker](https://img.shields.io/badge/docker-enabled-blue.svg)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [Required Variables](#required-variables)
  - [Using a `.env` File (Optional)](#using-a-env-file-optional)
- [Usage](#usage)
- [Deployment](#deployment)
  - [Building the Docker Image](#building-the-docker-image)
  - [Running the Docker Container Locally](#running-the-docker-container-locally)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Overview

This Python application extracts PDF file information from Azure Blob Storage and upserts the data into an Azure SQL Database. It is containerized using Docker and deployed to an Azure Kubernetes Service (AKS) cluster, leveraging Azure Workload Identity for secure authentication without the need for connection strings or SQL credentials.

## Features

- **Azure Managed Identity Authentication**
- **Dockerized Application**
- **Azure Kubernetes Service (AKS) Deployment**
- **Configurable Extraction Patterns and Target Tables**
- **Bulk Upsert Operations with Temporary Tables**: Leverages temporary SQL tables for efficient data processing that automatically cleans up after the operation.

## Architecture

1. **Azure Blob Storage**: Source for PDF files.
2. **Azure SQL Database**: Target for upserted data.
3. **Python Script**: Handles file extraction and database upserts.
4. **Docker Container**: Containerizes the application.
5. **AKS Deployment**: Deploys the containerized app on AKS.

## Prerequisites

- **Python 3.11**
- **Docker**
- **Azure CLI**
- **Kubectl**
- **Azure Account**

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

### 2. Configure Environment Variables

Create a `.env` file in the project root directory with the following variables:

```env
AZURE_STORAGE_ACCOUNT_NAME=your_storage_account_name
AZURE_BLOB_CONTAINER_NAME=your_blob_container_name
MSSQL_SERVER=your_sql_server.database.windows.net
MSSQL_DATABASE=your_database_name
DB_DRIVER=ODBC Driver 18 for SQL Server
TARGET_SQL_TABLE=clients.products_blob_pdfs
EXTRACTION_PATTERN=([A-Za-z0-9]{12})\.pdf$
```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `AZURE_STORAGE_ACCOUNT_NAME` | Azure Storage account name |
| `AZURE_BLOB_CONTAINER_NAME` | Name of the Azure Blob container |
| `MSSQL_SERVER` | SQL server URL |
| `MSSQL_DATABASE` | Name of the target database |
| `DB_DRIVER` | ODBC driver for SQL Server |
| `TARGET_SQL_TABLE` | SQL table for upserting data |
| `EXTRACTION_PATTERN` | Regex pattern for extracting file information |

### Using a `.env` File (Optional)

Instead of setting environment variables manually, you can use a `.env` file as shown in the configuration step above.

## Usage

Run the script locally with:

```bash
python src/your_script.py
```

## Deployment

### Building the Docker Image

```bash
docker build -t your-dockerhub-username/your-image-name:tag .
```

### Running the Docker Container Locally

```bash
docker run --env-file .env your-dockerhub-username/your-image-name:tag
```

## Contributing

1. **Fork the Repository**
2. **Create a New Branch**

```bash
git checkout -b feature/YourFeatureName
```

3. **Make Your Changes**
4. **Commit Your Changes**

```bash
git commit -m "Add feature XYZ"
```

5. **Push to Your Fork**

```bash
git push origin feature/YourFeatureName
```

6. **Create a Pull Request**

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or support, please contact [clem@arqs.io](mailto:clem@arqs.io).


