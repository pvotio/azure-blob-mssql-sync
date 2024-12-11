# Azure Blob Storage to SQL Database Upsert

## Overview

This Python application extracts PDF file information from Azure Blob Storage and upserts the data into an Azure SQL Database. It is containerized using Docker and deployed to an Azure Kubernetes Service (AKS) cluster, leveraging Azure Workload Identity for secure authentication without the need for connection strings or SQL credentials.

## Features

- **Azure Managed Identity Authentication:** Securely authenticate with Azure Blob Storage and Azure SQL Database without managing secrets.
- **Dockerized Application:** Easily containerize and deploy the application.
- **Azure Kubernetes Service (AKS) Deployment:** Deploy the application to a scalable Kubernetes cluster.
- **Configurable Extraction Patterns and Target Tables:** Customize regex patterns for file extraction and specify target SQL tables via environment variables.
- **Bulk Upsert Operations:** Efficiently handle inserts, updates, and deletions in the SQL Database using a temporary staging table.

## Prerequisites

- **Azure Account:** Access to Azure resources like Blob Storage, SQL Database, and AKS.
- **Azure CLI:** Installed and configured.
- **Docker:** Installed for building and pushing Docker images.
- **Kubectl:** Installed and configured to interact with your AKS cluster.
- **Git:** For version control.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/arqs-io/azure-blob-mssql-sync.git
cd your-repo
```

### 2. Configure Environment Variables

Create a `.env` file in the project root directory with the following variables:

```env
AZURE_STORAGE_ACCOUNT_NAME=your_storage_account_name
AZURE_BLOB_CONTAINER_NAME=your_blob_container_name
DB_SERVER=your_sql_server.database.windows.net
DB_NAME=your_database_name
DB_DRIVER=ODBC Driver 18 for SQL Server
TARGET_SQL_TABLE=clients.products_blob_pdfs
EXTRACTION_PATTERN=([A-Za-z0-9]{12})\.pdf$
```

**Note:** Since the application uses Azure Managed Identity, you do not need to include `DB_USER` and `DB_PASSWORD`.

### 3. Install Python Dependencies

Ensure you have Python 3.11 installed. Then, install the required packages:

```bash
pip install -r requirements.txt
```

### 4. Build the Docker Image

Replace `your-dockerhub-username` and `your-image-name` with your Docker Hub username and desired image name.

```bash
docker build -t your-dockerhub-username/your-image-name:tag .
```

**Example:**

```bash
docker build -t johndoe/blob-sql-upsert:v1.0 .
```

### 5. Push the Docker Image to a Container Registry

#### Using Docker Hub:

```bash
docker login
docker push your-dockerhub-username/your-image-name:tag
```

#### Using Azure Container Registry (ACR):

1. **Log in to ACR:**

    ```bash
    az acr login --name your-acr-name
    ```

2. **Tag the image:**

    ```bash
    docker tag your-dockerhub-username/your-image-name:tag your-acr-name.azurecr.io/your-image-name:tag
    ```

3. **Push the image:**

    ```bash
    docker push your-acr-name.azurecr.io/your-image-name:tag
    ```

### 6. Set Up Azure Workload Identity

Follow the [Azure Workload Identity documentation](https://learn.microsoft.com/azure/aks/workload-identity-overview) to configure Azure Workload Identity for your AKS cluster. Ensure that:

- An Azure AD Managed Identity is created and assigned the necessary roles (e.g., Storage Blob Data Reader, SQL Database roles).
- A Kubernetes Service Account is created and annotated with the Managed Identity details.

### 7. Deploy to AKS

Apply the Kubernetes manifests (`namespace.yaml`, `service-account.yaml`, `deployment.yaml`) to deploy your application.

```bash
kubectl apply -f namespace.yaml
kubectl apply -f service-account.yaml
kubectl apply -f deployment.yaml
```

### 8. Verify the Deployment

Check the status of your pods:

```bash
kubectl get pods -n blob-sql-upsert
```

View logs for troubleshooting:

```bash
kubectl logs <pod-name> -n blob-sql-upsert
```

Replace `<pod-name>` with the name of your running pod.

## Usage

Once deployed, the application will:

1. **Authenticate with Azure Blob Storage** using Managed Identity.
2. **List all PDF files** in the specified container.
3. **Extract relevant information** based on the provided regex pattern.
4. **Authenticate with Azure SQL Database** using Managed Identity.
5. **Upsert the extracted data** into the specified SQL table.

## Customization

- **Extraction Pattern:** Modify the `EXTRACTION_PATTERN` in the `.env` file or Kubernetes ConfigMap to change how filenames are parsed.
- **Target SQL Table:** Change the `TARGET_SQL_TABLE` environment variable to specify a different SQL table for upserting data.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## Contact

For any questions or support, please contact [clem@arqs.io](mailto:clem@arqs.io).

---

## Customization Notes

- **Repository URL:** Replace `https://github.com/arqs-io/azure-blob-mssql-sync.git` with your actual repository URL.
- **Docker Image Names:** Replace placeholders with your actual Docker Hub or ACR details.
- **Contact Information:** Update the contact email to your own.

## LICENSE (MIT License)

Create a `LICENSE` file in your project root with the following content. Replace `[YEAR]` with the current year and `[YOUR NAME]` with your name or your organization's name.

```text
MIT License

Copyright (c) [YEAR] [YOUR NAME]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```


```text
MIT License

Copyright (c) 2024 John Doe

Permission is hereby granted, free of charge, to any person obtaining a copy
...
```

