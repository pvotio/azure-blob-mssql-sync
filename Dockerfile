FROM python:3.13.6-slim-bullseye

WORKDIR /app

# Install required system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    unixodbc \
    unixodbc-dev \
    libgssapi-krb5-2 \
    curl \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install ODBC Driver 18
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-archive-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-archive-keyring.gpg] https://packages.microsoft.com/repos/microsoft-debian-bullseye-prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm /etc/apt/sources.list.d/mssql-release.list \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Define ODBC driver
RUN echo "[ODBC Driver 18 for SQL Server]\nDescription=Microsoft ODBC Driver 18 for SQL Server\nDriver=/opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.0.so.1.1\nUsageCount=1\n" >> /etc/odbcinst.ini

# Enable unixODBC tracing
RUN echo "[ODBC]\nTrace=Yes\nForceTrace=Yes\nTraceFile=/tmp/odbc.log\n" >> /etc/odbcinst.ini

ENV ODBCDriverTrace=1
ENV ODBCDriverTraceFile=/tmp/odbcdriver.log

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Wrapper script for logging
RUN echo '#!/bin/bash\n\
set -e\n\
python main.py || true\n\
echo "=== Contents of /tmp/odbc.log (if any) ==="\n\
if [ -f /tmp/odbc.log ]; then cat /tmp/odbc.log; else echo "No /tmp/odbc.log found"; fi\n\
echo "=== Contents of /tmp/odbcdriver.log (if any) ==="\n\
if [ -f /tmp/odbcdriver.log ]; then cat /tmp/odbcdriver.log; else echo "No /tmp/odbcdriver.log found"; fi\n\
' > /app/run_and_log.sh

RUN chmod +x /app/run_and_log.sh

ENTRYPOINT ["/app/run_and_log.sh"]

